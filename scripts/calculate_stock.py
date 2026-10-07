#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
calculate_stock.py - 재고 현황 계산 및 부족분 산출 공용 스크립트

기능:
    - 현재 접속 캐릭터 및 타 캐릭터(인벤토리/개인금고/공용금고)의 재고 통합 집계
    - target_gathering.md (또는 target.md) 목표치 비교 및 부족분(missing.json) 산출
    - 타 캐릭터 보유량 10개 이상(OTHER_CHAR_STOCK_THRESHOLD) 시 보류 판정
    - 오래된 타 캐릭터 상태(기본 3일 초과, OTHER_CHAR_STALE_DAYS)는 참고용으로만 표기하고 채집 부족분 계산/보류에서 제외
    - 역순 우선순위(Bottom-up) 정렬 및 상세 보고서 출력

사용 예시:
    python scripts/calculate_stock.py --current-char Saki
    python scripts/calculate_stock.py --current-char 아미나 --target-file data/target_gathering.md
"""

import argparse
import csv
import datetime
import glob
import json
import os
import re
import sys


def parse_targets(target_file_path):
    """target.md 또는 대상 파일에서 아이템명 및 목표 수량 추출"""
    targets = []
    if not os.path.exists(target_file_path):
        return targets

    with open(target_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "|" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                # | 분류 | 아이템명 | 목표 수량 |
                if len(parts) >= 3 and parts[2].isdigit():
                    targets.append((parts[1], int(parts[2])))
                # | 아이템명 | 목표 수량 |
                elif len(parts) == 2 and parts[1].isdigit():
                    targets.append((parts[0], int(parts[1])))
    return targets


def get_character_update_info(data_dir, server_name, char_name):
    """
    캐릭터의 최종 갱신 일시를 파싱하여 datetime 객체 및 일시 문자열 반환.
    우선순위:
    1. data/characters/(서버)_(캐릭터).md 내 '**최종 갱신 일시**'
    2. data/characters/README.md 표 내 해당 캐릭터 행의 최종 갱신 일시
    3. 인벤토리 CSV 파일의 수정 시각 (mtime)
    """
    char_dir = os.path.join(data_dir, "characters")
    if not os.path.exists(char_dir):
        char_dir = data_dir

    # 1. 개별 MD 파일 확인
    md_candidates = [
        os.path.join(char_dir, f"{server_name}_{char_name}.md"),
        os.path.join(char_dir, f"{char_name}.md"),
    ]
    # 대소문자 무시 검색
    for f in glob.glob(os.path.join(char_dir, "*.md")):
        fname = os.path.basename(f).lower()
        if fname in [f"{server_name.lower()}_{char_name.lower()}.md", f"{char_name.lower()}.md"]:
            if f not in md_candidates:
                md_candidates.insert(0, f)

    for md_path in md_candidates:
        if os.path.exists(md_path):
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                m = re.search(r"\*\*최종 갱신 일시\*\*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}(?:\s+[0-9]{2}:[0-9]{2}(?::[0-9]{2})?)?)", content)
                if m:
                    date_str = m.group(1).strip()
                    fmt = "%Y-%m-%d %H:%M" if " " in date_str else "%Y-%m-%d"
                    return datetime.datetime.strptime(date_str, fmt), date_str
            except Exception:
                pass

    # 2. README.md 확인
    readme_path = os.path.join(char_dir, "README.md")
    if os.path.exists(readme_path):
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" in line:
                        parts = [p.strip() for p in line.split("|") if p.strip()]
                        if len(parts) >= 7 and parts[0].strip().lower() == char_name.lower():
                            date_str = parts[6].strip()
                            fmt = "%Y-%m-%d %H:%M" if " " in date_str else "%Y-%m-%d"
                            return datetime.datetime.strptime(date_str, fmt), date_str
        except Exception:
            pass

    # 3. CSV mtime
    csv_candidates = [
        os.path.join(char_dir, f"{server_name}_{char_name}_inventory.csv"),
        os.path.join(char_dir, f"{char_name}_inventory.csv"),
    ]
    for c in csv_candidates:
        if os.path.exists(c):
            mtime = os.path.getmtime(c)
            dt = datetime.datetime.fromtimestamp(mtime)
            return dt, dt.strftime("%Y-%m-%d %H:%M")

    return None, None


def load_character_stocks(data_dir, server_name):
    """data/characters 디렉토리에서 모든 CSV 파일 로드 및 캐릭터별 재고 집계"""
    char_dir = os.path.join(data_dir, "characters")
    if not os.path.exists(char_dir):
        char_dir = data_dir

    csv_pattern = os.path.join(char_dir, "*.csv")
    csv_files = glob.glob(csv_pattern)

    if char_dir != data_dir:
        csv_files.extend(glob.glob(os.path.join(data_dir, "*.csv")))

    character_stocks = {}  # {char_name: {item_name: count}}
    bank_all_stock = {}    # {item_name: count}

    for file_path in set(csv_files):
        fname = os.path.basename(file_path)
        if "bank_all" in fname:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("DisplayName", "").strip()
                    count = int(row.get("Count", 0)) if row.get("Count") else 0
                    if name:
                        bank_all_stock[name] = bank_all_stock.get(name, 0) + count
            continue

        match = re.search(rf"{server_name}_(.*?)\_(inventory|bank)\.csv", fname, re.IGNORECASE)
        if not match:
            # fallback pattern without server prefix if any
            match = re.search(r"(.*?)_(inventory|bank)\.csv", fname, re.IGNORECASE)

        if match:
            cname = match.group(1).strip()
            if cname not in character_stocks:
                character_stocks[cname] = {}
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("DisplayName", "").strip()
                    count = int(row.get("Count", 0)) if row.get("Count") else 0
                    if name:
                        character_stocks[cname][name] = character_stocks[cname].get(name, 0) + count

    return character_stocks, bank_all_stock


def calculate_shortage(current_char, server_name, data_dir, target_file, output_file, threshold, priority_order, stale_days=3.0):
    targets = parse_targets(target_file)
    if not targets:
        print(f"[경고] 목표 파일({target_file})에서 유효한 목표 항목을 찾지 못했습니다.", file=sys.stderr)

    char_stocks, bank_all_stock = load_character_stocks(data_dir, server_name)

    # 대소문자 무시하여 현재 캐릭터 매칭
    curr_char_key = None
    for cname in char_stocks:
        if cname.lower() == current_char.lower():
            curr_char_key = cname
            break

    curr_char_stock = char_stocks.get(curr_char_key, {}) if curr_char_key else {}
    
    # Other character stocks
    other_stocks = {c: s for c, s in char_stocks.items() if c.lower() != current_char.lower()}

    # 타 캐릭터 데이터 신선도/만료 상태 점검
    now = datetime.datetime.now()
    char_stale_info = {}
    for c in other_stocks:
        dt, dt_str = get_character_update_info(data_dir, server_name, c)
        if dt:
            diff_days = (now - dt).total_seconds() / 86400.0
            is_stale = (diff_days > stale_days)
            char_stale_info[c] = {
                "is_stale": is_stale,
                "days": diff_days,
                "date_str": dt_str
            }
        else:
            char_stale_info[c] = {
                "is_stale": True,
                "days": 999.0,
                "date_str": "알 수 없음"
            }

    missing = {}
    report_rows = []

    # Priority sorting
    ordered_targets = list(reversed(targets)) if priority_order == "bottom-up" else list(targets)

    for item_name, target_cnt in ordered_targets:
        # Total held by current character (inventory + personal bank + shared bank)
        curr_cnt = curr_char_stock.get(item_name, 0) + bank_all_stock.get(item_name, 0)
        deficit = target_cnt - curr_cnt

        # 타 캐릭터 보유 현황: 신선한 데이터와 오래된(stale) 데이터 분리
        fresh_holdings = {}
        stale_holdings = {}

        for c, s in other_stocks.items():
            cnt = s.get(item_name, 0)
            if cnt > 0:
                s_info = char_stale_info.get(c, {"is_stale": False, "days": 0.0})
                if s_info["is_stale"]:
                    stale_holdings[c] = (cnt, s_info["days"])
                else:
                    fresh_holdings[c] = (cnt, s_info["days"])

        fresh_max_char = max(fresh_holdings.items(), key=lambda x: x[1][0]) if fresh_holdings else (None, (0, 0.0))
        stale_max_char = max(stale_holdings.items(), key=lambda x: x[1][0]) if stale_holdings else (None, (0, 0.0))

        status = "충족"
        action_required = False
        postpone_reason = ""

        if deficit > 0:
            # 원칙: 저장된 다른 캐릭터 상태가 너무 오래된 경우 채집시 부족분 계산에 미반영!
            # 오직 최신(유효) 타 캐릭터의 보유량만 보류 판정에 사용
            if fresh_max_char[1][0] >= threshold:
                status = "보류 (타캐릭 보유)"
                postpone_reason = f"{fresh_max_char[0]}({fresh_max_char[1][0]}개)"
            else:
                status = "채집 필요"
                action_required = True
                missing[item_name] = deficit

        # 보고서 표기 (오래된 캐릭터 상태는 참고용으로 명시)
        other_info_parts = []
        if fresh_max_char[0] and fresh_max_char[1][0] > 0:
            other_info_parts.append(f"{fresh_max_char[0]}({fresh_max_char[1][0]}개)")
        if stale_max_char[0] and stale_max_char[1][0] > 0:
            days_int = int(stale_max_char[1][1])
            other_info_parts.append(f"{stale_max_char[0]}({stale_max_char[1][0]}개) [참고: 오래됨({days_int}일 전)]")

        other_info_str = ", ".join(other_info_parts) if other_info_parts else "-"

        report_rows.append({
            "item": item_name,
            "target": target_cnt,
            "current": curr_cnt,
            "deficit": max(0, deficit),
            "status": status,
            "other_info": other_info_str,
            "action": action_required
        })

    # Save missing.json
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(missing, f, ensure_ascii=False, indent=2)

    # Print Report
    print("=" * 85)
    print(f"=== 재고 현황 및 채집 대상 분석 보고서 ===")
    print(f"* 기준 캐릭터: {current_char} (서버: {server_name})")
    print(f"* 타 캐릭터 보유 기준(보류 임계치): {threshold}개 이상")
    print(f"* 타 캐릭터 데이터 만료 기준: {stale_days}일 초과 시 참고용 표기 및 보류 제외")
    print(f"* 우선순위 방식: {priority_order}")
    print("=" * 85)
    print(f"{'아이템명':<16} | {'목표':>6} | {'현재':>6} | {'부족분':>6} | {'상태':<16} | {'타 캐릭터 보유'}")
    print("-" * 85)
    for r in report_rows:
        print(f"{r['item']:<16} | {r['target']:>6} | {r['current']:>6} | {r['deficit']:>6} | {r['status']:<16} | {r['other_info']}")
    print("=" * 85)

    gather_needed = [r for r in report_rows if r["action"]]
    if gather_needed:
        print(f"[!] 즉시 채집 필요 품목 ({len(gather_needed)}건):")
        for g in gather_needed:
            print(f"  - {g['item']}: {g['deficit']}개 필요 (현재 {g['current']}/{g['target']})")
    else:
        print("[+] 모든 품목이 목표치를 달성했거나 타 캐릭터 보관 중으로 채집이 필요하지 않습니다.")

    print(f"\n[+] 부족분 데이터 저장 완료: {output_file}")
    return missing


def main():
    default_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    env_file = os.path.join(default_data_dir, "environments.json")
    
    default_char = "Saki"
    default_server = "던컨"
    default_threshold = 10
    default_stale_days = 3.0
    default_priority = "bottom-up"
    
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                env_data = json.load(f)
                default_char = env_data.get("inGame", {}).get("activeCharacter", default_char)
                default_server = env_data.get("inGame", {}).get("defaultServer", default_server)
                default_threshold = env_data.get("stockSettings", {}).get("otherCharStockThreshold", default_threshold)
                default_stale_days = float(env_data.get("stockSettings", {}).get("otherCharStaleDays", default_stale_days))
                default_priority = env_data.get("stockSettings", {}).get("priorityOrder", default_priority)
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="마비노기 모바일 재고 계산 및 부족분 산출 스크립트")
    parser.add_argument("--current-char", default=default_char, help=f"현재 기준 캐릭터명 (기본값: {default_char})")
    parser.add_argument("--server", default=default_server, help=f"서버명 (기본값: {default_server})")
    parser.add_argument("--data-dir", default=default_data_dir, help="data 디렉토리 경로")
    parser.add_argument("--target-file", default=None, help="목표치 마크다운 파일 경로 (기본값: data/target_gathering.md)")
    parser.add_argument("--output-file", default=None, help="부족분 JSON 저장 경로 (임시 계산 결과는 기본값: scratch/missing.json)")
    parser.add_argument("--threshold", type=int, default=default_threshold, help=f"타 캐릭터 보유 보류 임계값 (기본값: {default_threshold})")
    parser.add_argument("--stale-days", type=float, default=default_stale_days, help=f"타 캐릭터 데이터 만료 일수 (기본값: {default_stale_days}일)")
    parser.add_argument("--priority", choices=["bottom-up", "top-down"], default=default_priority, help=f"우선순위 정렬 방식 (기본값: {default_priority})")

    args = parser.parse_args()
    data_dir = os.path.abspath(args.data_dir)
    if args.target_file:
        target_file = args.target_file
    else:
        gathering_target = os.path.join(data_dir, "target_gathering.md")
        target_file = gathering_target if os.path.exists(gathering_target) else os.path.join(data_dir, "target.md")
    scratch_dir = os.path.abspath(os.path.join(data_dir, "..", "scratch"))
    output_file = args.output_file or os.path.join(scratch_dir, "missing.json")

    calculate_shortage(
        current_char=args.current_char,
        server_name=args.server,
        data_dir=data_dir,
        target_file=target_file,
        output_file=output_file,
        threshold=args.threshold,
        priority_order=args.priority,
        stale_days=args.stale_days
    )


if __name__ == "__main__":
    main()
