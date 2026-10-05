#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
send_chat.py - 마비노기 모바일 인게임 채팅(write_chat) 안전 전송 공용 스크립트

기능:
    - 한글 UTF-8 Base64 자동 인코딩
    - 50자 제한(MAX_CHAT_LENGTH) 준수 및 자동 분할
    - 2초 전송 쿨다운 및 레이트 리밋 발생 시 자동 재시도
    - 기본 3청크 제한(DEFAULT_MAX_CHAT_CHUNKS) 지원 (옵션으로 확장 가능)

사용 예시:
    python scripts/send_chat.py --message "안녕하세요?"
    python scripts/send_chat.py --messages "1번 메시지" "2번 메시지" "3번 메시지"
    python scripts/send_chat.py --text-file path/to/text.txt --max-chunks 5
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time


def resolve_cli_path(cli_path_arg, data_dir):
    if cli_path_arg and os.path.exists(cli_path_arg):
        return cli_path_arg
    env_file = os.path.join(data_dir, "environments.json")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                env_data = json.load(f)
                cli = env_data.get("paths", {}).get("cli")
                if cli and os.path.exists(cli):
                    return cli
        except Exception:
            pass
    path_file = os.path.join(data_dir, "path.txt")
    if os.path.exists(path_file):
        with open(path_file, "r", encoding="utf-8") as f:
            line = f.readline().strip()
            if line and os.path.exists(line):
                return line
    default_cli = r"C:\Nexon\MabinogiMobile\MabinogiMobile_CLI.exe"
    if os.path.exists(default_cli):
        return default_cli
    raise FileNotFoundError(
        "CLI 도구 경로를 찾을 수 없습니다. --cli-path 인자를 전달하거나 data/environments.json을 확인하십시오."
    )


def split_into_chunks(text, max_len=50):
    """50자 이하로 자연스럽게 텍스트 분할"""
    if len(text) <= max_len:
        return [text]
    chunks = []
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        while len(line) > max_len:
            # 쉼표나 공백 기준 분할 시도
            cut_idx = max_len
            for sep in [" ", ",", ".", "!", "?"]:
                idx = line.rfind(sep, 0, max_len)
                if idx > 15:
                    cut_idx = idx + 1
                    break
            chunks.append(line[:cut_idx].strip())
            line = line[cut_idx:].strip()
        if line:
            chunks.append(line)
    return chunks


def send_single_chat(cli_path, msg, data_dir=None, max_retries=4):
    b64_str = base64.b64encode(msg.encode("utf-8")).decode("ascii")
    arg = f"base64:{b64_str}"

    for attempt in range(max_retries):
        res = subprocess.run(
            [cli_path, "write_chat", arg],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
        try:
            data = json.loads(res.stdout)
            if data_dir:
                resp_dir = os.path.join(data_dir, "response")
                os.makedirs(resp_dir, exist_ok=True)
                with open(os.path.join(resp_dir, "write_chat.json"), "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            if data.get("error") == "rate_limited":
                wait_t = float(data.get("retryAfterSeconds", 2)) + 0.5
                print(f"[*] 레이트 리밋 발생. {wait_t:.1f}초 대기 후 재시도...")
                time.sleep(wait_t)
                continue
            elif "message" in data:
                print(f"[+] 전송 성공 ({len(msg)}자): {msg}")
                return True
            elif "error" in data:
                print(f"[-] 전송 실패: {data}", file=sys.stderr)
                return False
        except Exception:
            print(f"[-] 응답 파싱 오류: {res.stdout.strip()}", file=sys.stderr)
            return False
    return False


def main():
    parser = argparse.ArgumentParser(description="마비노기 모바일 인게임 채팅 전송 스크립트")
    parser.add_argument("--message", help="단일 메시지 텍스트")
    parser.add_argument("--messages", nargs="+", help="복수 메시지 텍스트 리스트")
    parser.add_argument("--cli-path", default=None, help="MabinogiMobile_CLI.exe 실행 경로")
    parser.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "data"), help="data 디렉토리 경로")
    parser.add_argument("--delay", type=float, default=2.5, help="연속 메시지 간 대기 시간 (초, 기본값: 2.5초)")
    parser.add_argument("--max-chunks", type=int, default=3, help="최대 전송 청크 수 (기본값: 3, 0 지정 시 무제한)")

    args = parser.parse_args()
    data_dir = os.path.abspath(args.data_dir)
    cli_path = resolve_cli_path(args.cli_path, data_dir)

    raw_messages = []
    if args.messages:
        raw_messages = args.messages
    elif args.message:
        raw_messages = [args.message]
    else:
        print("[오류] --message 또는 --messages 인자가 필요합니다.", file=sys.stderr)
        sys.exit(1)

    # 50자 분할 및 청크 구성
    final_chunks = []
    for m in raw_messages:
        final_chunks.extend(split_into_chunks(m, max_len=50))

    if args.max_chunks > 0 and len(final_chunks) > args.max_chunks:
        print(f"[*] 청크 수가 {len(final_chunks)}개로 기본 제한({args.max_chunks}개)을 초과하여 상위 {args.max_chunks}개만 전송합니다.")
        final_chunks = final_chunks[:args.max_chunks]

    print(f"[*] 총 {len(final_chunks)}개의 채팅 메시지를 순차 전송합니다.")
    all_success = True
    for i, chunk in enumerate(final_chunks):
        success = send_single_chat(cli_path, chunk, data_dir=data_dir)
        if not success:
            all_success = False
            break
        if i < len(final_chunks) - 1:
            time.sleep(args.delay)

    if all_success:
        print("[+] 모든 메시지 전송 완료")
    else:
        print("[-] 일부 메시지 전송 실패", file=sys.stderr)
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
