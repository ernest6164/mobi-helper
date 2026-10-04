#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
execute_gathering.py - 재고 보충 자동 채집 실행 및 모니터링 공용 스크립트

기능:
    - target.md 역순 우선순위(Bottom-up) 및 타 캐릭터 보유 여부(10개 이상) 점검
    - 채집 도구 및 생활 스킬 레벨 사전 확인 (get_gatherable_items)
    - 인벤토리 무게 한도 실시간 점검 (98% 초과 시 안전 중단)
    - 백그라운드 채집 실행 및 목표 달성 시 즉시 stop_action 호출
    - 모달 방해(blocked) 시 최대 3회 재시도 및 오류 처리
    - 채집 완료 후 캐릭터 인벤토리 CSV/MD 데이터 자동 동기화

사용 예시:
    python scripts/execute_gathering.py --char-name Saki
    python scripts/execute_gathering.py --char-name 아미나 --single-item "양털" --single-count 100
"""

import argparse
import base64
import csv
import datetime
import glob
import json
import os
import re
import subprocess
import sys
import threading
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


def run_cli_cmd(cli_path, cmd, body=None):
    args = [cli_path, cmd]
    if body:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        b64 = base64.b64encode(payload).decode("ascii")
        args.append(f"base64:{b64}")
    res = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    resp_path = os.path.expandvars(r"%LOCALAPPDATA%\MabinogiMobileCLI\last-response.json")
    if os.path.exists(resp_path):
        try:
            with open(resp_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    try:
        return json.loads(res.stdout)
    except Exception:
        return {}


def get_current_items(cli_path):
    res = run_cli_cmd(cli_path, "get_items")
    if isinstance(res, list):
        return res
    if isinstance(res, dict) and "items" in res:
        return res["items"]
    return []


def get_inventory_weight(cli_path):
    return run_cli_cmd(cli_path, "get_inventory")


def get_activity_status(cli_path):
    return run_cli_cmd(cli_path, "get_activity")


def get_gatherable_list(cli_path):
    res = run_cli_cmd(cli_path, "get_gatherable_items")
    if isinstance(res, list):
        return res
    if isinstance(res, dict) and "items" in res:
        return res["items"]
    return []


def parse_targets(target_file_path):
    targets = []
    if not os.path.exists(target_file_path):
        return targets
    with open(target_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "|" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3 and parts[2].isdigit():
                    targets.append((parts[1], int(parts[2])))
                elif len(parts) == 2 and parts[1].isdigit():
                    targets.append((parts[0], int(parts[1])))
    return targets


def load_other_character_stocks(data_dir, current_char, server_name):
    char_dir = os.path.join(data_dir, "characters")
    if not os.path.exists(char_dir):
        char_dir = data_dir

    csv_files = glob.glob(os.path.join(char_dir, "*.csv"))
    if char_dir != data_dir:
        csv_files.extend(glob.glob(os.path.join(data_dir, "*.csv")))

    other_stocks = {}
    for csv_file in set(csv_files):
        fname = os.path.basename(csv_file)
        if "bank_all" in fname:
            continue
        match = re.search(rf"{server_name}_(.*?)\_(inventory|bank)\.csv", fname)
        if not match:
            match = re.search(r"(.*?)_(inventory|bank)\.csv", fname)
        if match:
            cname = match.group(1)
            if cname == current_char:
                continue
            if cname not in other_stocks:
                other_stocks[cname] = {}
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("DisplayName", "").strip()
                    cnt = int(row.get("Count", 0)) if row.get("Count") else 0
                    if name:
                        other_stocks[cname][name] = other_stocks[cname].get(name, 0) + cnt
    return other_stocks


def stop_action(cli_path):
    print("[*] 채집 중단 명령(stop_action) 전송...", flush=True)
    return run_cli_cmd(cli_path, "stop_action")


def sync_after_gathering(cli_path, data_dir, char_name, server_name):
    """채집 완료 후 캐릭터 인벤토리/금고 CSV 및 MD 갱신"""
    print("[*] 채집 결과 인벤토리 및 캐릭터 정보 갱신 중...", flush=True)
    char_dir = os.path.join(data_dir, "characters")
    os.makedirs(char_dir, exist_ok=True)

    items_data = get_current_items(cli_path)
    inv, bank, bank_all = [], [], []
    for it in items_data:
        loc = it.get("Location")
        if loc in ["inventory", "bag", "gathered", "cooked"]:
            inv.append(it)
        elif loc == "character_storage" or loc == "bank":
            bank.append(it)
        elif loc in ["account_storage", "account_bank", "bank_all"]:
            bank_all.append(it)

    fieldnames = ["Location", "DisplayName", "Category", "CategoryDisplayName", "Count", "IsLocked"]

    def write_csv(filename, data):
        path = os.path.join(char_dir, filename)
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in data:
                writer.writerow({
                    "Location": r.get("Location", ""),
                    "DisplayName": r.get("DisplayName", ""),
                    "Category": r.get("Category", ""),
                    "CategoryDisplayName": r.get("CategoryDisplayName", ""),
                    "Count": r.get("Count", 1),
                    "IsLocked": r.get("IsLocked", False)
                })

    write_csv(f"{server_name}_{char_name}_inventory.csv", inv)
    write_csv(f"{server_name}_{char_name}_bank.csv", bank)
    write_csv(f"{server_name}_bank_all.csv", bank_all)

    # Update individual character MD timestamp
    md_path = os.path.join(char_dir, f"{server_name}_{char_name}.md")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            c = f.read()
        c = re.sub(r"\*\*최종 갱신 일시\*\*: .*", f"**최종 갱신 일시**: {now_str}", c)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(c)


def execute_auto_gathering(char_name, server_name, cli_path, data_dir, target_file, single_item=None, single_count=None, threshold=10, max_rounds=0):
    status = run_cli_cmd(cli_path, "status")
    if status.get("pipe") != "connected":
        print(f"[오류] CLI 커넥터 연결 상태가 아닙니다: {status}", file=sys.stderr)
        return False

    print("=" * 70)
    print(f"=== 마비노기 모바일 자동 채집 시스템 시작 ===")
    print(f"* 캐릭터: [{char_name}] (서버: {server_name})")
    print(f"* 타 캐릭터 보류 임계값: {threshold}개 이상")
    print("=" * 70)

    # Check gatherable items capabilities
    gatherable = get_gatherable_list(cli_path)
    gatherable_names = set()
    for g in gatherable:
        if isinstance(g, dict):
            gatherable_names.add(g.get("DisplayName", ""))
        elif isinstance(g, str):
            gatherable_names.add(g)

    if single_item and single_count:
        targets = [(single_item, single_count)]
    else:
        targets = parse_targets(target_file)

    other_stocks = load_other_character_stocks(data_dir, char_name, server_name)
    session_gained = {}
    blocked_retries = {}
    rounds = 0

    while True:
        if max_rounds > 0 and rounds >= max_rounds:
            print(f"[*] 최대 채집 라운드 수({max_rounds})에 도달하여 종료합니다.")
            break

        # 1. Check current items
        curr_items = get_current_items(cli_path)
        curr_stock = {}
        for it in curr_items:
            n = it.get("DisplayName")
            curr_stock[n] = curr_stock.get(n, 0) + it.get("Count", 0)

        # 2. Select next target according to bottom-up priority
        reversed_targets = list(reversed(targets))
        next_target = None
        target_info = None

        for name, target_cnt in reversed_targets:
            curr = curr_stock.get(name, 0)
            deficit = target_cnt - curr
            if deficit <= 0:
                continue

            # Check other character stock
            held_by_others = False
            for cname, cstock in other_stocks.items():
                if cstock.get(name, 0) >= threshold:
                    held_by_others = True
                    break
            if held_by_others:
                continue

            # Check gatherable capability if list is available
            if gatherable_names and name not in gatherable_names:
                print(f"[경고] [{name}]은(는) 현재 생활 스킬 레벨 부족 또는 채집 도구 미보유로 채집할 수 없습니다. 건너뜁니다.")
                continue

            next_target = name
            target_info = (curr, target_cnt, deficit)
            break

        if not next_target:
            print("\n[+] 모든 목표 아이템이 충족되었거나 타 캐릭터에 보관되어 있어 채집을 완료합니다.")
            break

        curr_cnt, t_cnt, deficit = target_info
        rounds += 1
        print(f"\n>>> [라운드 {rounds}] 채집 목표: [{next_target}] | 현재: {curr_cnt} / 목표: {t_cnt} (부족분: {deficit}개)")

        # 3. Check inventory weight
        inv_w = get_inventory_weight(cli_path)
        if inv_w:
            cur_w = inv_w.get("CurrentInventoryWeightAsDecimal", 0)
            max_w = inv_w.get("MaxInventoryWeightAsDecimal", 2090)
            print(f"    인벤토리 무게: {cur_w} / {max_w} ({cur_w/max_w*100:.1f}%)")
            if cur_w >= max_w * 0.98:
                print("\n[경고] 인벤토리 무게가 한계(98%)에 도달했습니다. 채집을 안전하게 중단합니다.")
                break

        # 4. Start gathering in background thread
        gather_res = [None]

        def do_gather():
            res = run_cli_cmd(cli_path, "execute_gathering", {"displayName": next_target})
            gather_res[0] = res

        g_thread = threading.Thread(target=do_gather)
        g_thread.start()

        # 5. Monitor in real time
        while g_thread.is_alive():
            time.sleep(2.5)
            c_items = get_current_items(cli_path)
            c_cnt = sum(it.get("Count", 0) for it in c_items if it.get("DisplayName") == next_target)

            if c_cnt >= t_cnt:
                print(f"    [목표 도달] {next_target}: {c_cnt} >= {t_cnt}. 채집 중단 중...")
                stop_action(cli_path)
                break

        g_thread.join()

        # 6. Check auto-play status
        act = get_activity_status(cli_path)
        if act and act.get("IsAutoPlaying"):
            print(f"    인게임 자동 채집 진행 중. 실시간 진행도 모니터링 중...")
            while True:
                time.sleep(3.0)
                c_items = get_current_items(cli_path)
                c_cnt = sum(it.get("Count", 0) for it in c_items if it.get("DisplayName") == next_target)

                act = get_activity_status(cli_path)
                is_auto = act.get("IsAutoPlaying") if act else False

                if c_cnt >= t_cnt:
                    print(f"    [목표 도달] {next_target}: {c_cnt} >= {t_cnt}. 자동 진행 중단 중...")
                    stop_action(cli_path)
                    break
                if not is_auto:
                    print(f"    인게임 채집 동작 완료. 현재 수량: {c_cnt}/{t_cnt}")
                    break

        # 7. Evaluate round result
        post_items = get_current_items(cli_path)
        post_cnt = sum(it.get("Count", 0) for it in post_items if it.get("DisplayName") == next_target)
        gained = post_cnt - curr_cnt

        if gained > 0:
            session_gained[next_target] = session_gained.get(next_target, 0) + gained
            blocked_retries[next_target] = 0
            print(f"    [+] {next_target} 라운드 완료: +{gained}개 획득 (현재 {post_cnt}/{t_cnt})")
        else:
            print(f"    [-] 획득량 없음 (0개). 응답: {gather_res[0]}")

        # 8. Check error & retry on modal block
        resp = gather_res[0]
        if isinstance(resp, dict) and "error" in resp:
            err = resp["error"]
            if err == "blocked":
                blocked_retries[next_target] = blocked_retries.get(next_target, 0) + 1
                if blocked_retries[next_target] > 3:
                    print(f"\n[오류] 모달 창 방해 지속으로 {next_target} 채집을 중단합니다.", file=sys.stderr)
                    break
                else:
                    print(f"    일시적 모달 방해 발생. 3초 후 재시도 ({blocked_retries[next_target]}/3)...")
                    time.sleep(3)
            elif err in ["overweight", "tool_missing", "tool_broken", "not_enough_currency"]:
                print(f"\n[오류] 채집 중단 에러 발생: {err}", file=sys.stderr)
                break

        time.sleep(1)

    # Final sync
    sync_after_gathering(cli_path, data_dir, char_name, server_name)

    print("\n" + "=" * 50)
    print("=== 채집 세션 최종 결과 보고 ===")
    print("=" * 50)
    for k, v in session_gained.items():
        print(f"  * {k}: +{v}개 채집 완료")
    if not session_gained:
        print("  * 신규 채집된 내역이 없습니다.")
    print("=" * 50)
    return True


def main():
    default_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    env_file = os.path.join(default_data_dir, "environments.json")

    default_char = "Saki"
    default_server = "던컨"
    default_threshold = 10

    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                env_data = json.load(f)
                default_char = env_data.get("inGame", {}).get("activeCharacter", default_char)
                default_server = env_data.get("inGame", {}).get("defaultServer", default_server)
                default_threshold = env_data.get("stockSettings", {}).get("otherCharStockThreshold", default_threshold)
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="마비노기 모바일 자동 채집 실행 스크립트")
    parser.add_argument("--char-name", default=default_char, help=f"현재 채집을 수행할 캐릭터명 (기본값: {default_char})")
    parser.add_argument("--server", default=default_server, help=f"서버명 (기본값: {default_server})")
    parser.add_argument("--cli-path", default=None, help="MabinogiMobile_CLI.exe 경로")
    parser.add_argument("--data-dir", default=default_data_dir, help="data 디렉토리 경로")
    parser.add_argument("--target-file", default=None, help="target.md 경로")
    parser.add_argument("--single-item", default=None, help="단일 품목만 채집할 경우 아이템명")
    parser.add_argument("--single-count", type=int, default=None, help="단일 품목 목표 수량")
    parser.add_argument("--threshold", type=int, default=default_threshold, help=f"타 캐릭터 보유 보류 임계값 (기본값: {default_threshold})")
    parser.add_argument("--max-rounds", type=int, default=0, help="최대 채집 라운드 수 (0: 제한 없음)")

    args = parser.parse_args()
    data_dir = os.path.abspath(args.data_dir)
    cli_path = resolve_cli_path(args.cli_path, data_dir)
    target_file = args.target_file or os.path.join(data_dir, "target.md")

    execute_auto_gathering(
        char_name=args.char_name,
        server_name=args.server,
        cli_path=cli_path,
        data_dir=data_dir,
        target_file=target_file,
        single_item=args.single_item,
        single_count=args.single_count,
        threshold=args.threshold,
        max_rounds=args.max_rounds
    )


if __name__ == "__main__":
    main()
