#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
execute_altering.py - 일괄 가공 단발성 자동화 공용 스크립트

기능:
    - target_altering.md 목표치 점검 및 전체 보유량(인벤토리 + 금고) 비교
    - 우선순위: 아래쪽 항목 우선 (Bottom-Up)
    - 완료 가공물 일괄 수령 (complete_altering_work)
    - 빈 슬롯에 부족한 가공물 의뢰 등록 (execute_altering)
    - data/last_altering_collected.json 수령 내역 기록
    - 1회 수령 및 등록 완료 후 즉시 종료 (단발성 요청)

사용 예시:
    python scripts/execute_altering.py
"""

import argparse
import base64
import datetime
import json
import os
import subprocess
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


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
    raise FileNotFoundError("CLI 도구 경로를 찾을 수 없습니다.")


def run_cli_cmd(cli_path, cmd, body=None, data_dir="data"):
    args = [cli_path, cmd]
    if body is not None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        b64 = base64.b64encode(payload).decode("ascii")
        args.append(f"base64:{b64}")

    res = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")

    resp_dir = os.path.join(data_dir, "response")
    os.makedirs(resp_dir, exist_ok=True)
    resp_file = os.path.join(resp_dir, f"{cmd}.json")

    # CLI 응답 파싱
    parsed = None
    if res.stdout and res.stdout.strip():
        try:
            parsed = json.loads(res.stdout)
            with open(resp_file, "w", encoding="utf-8") as f:
                f.write(res.stdout)
            return parsed
        except Exception:
            pass

    # %LOCALAPPDATA%\MabinogiMobileCLI\last-response.json 백업 확인
    last_resp = os.path.expandvars(r"%LOCALAPPDATA%\MabinogiMobileCLI\last-response.json")
    if os.path.exists(last_resp):
        try:
            with open(last_resp, "r", encoding="utf-8") as f:
                parsed = json.load(f)
            with open(resp_file, "w", encoding="utf-8") as f:
                json.dump(parsed, f, ensure_ascii=False, indent=2)
            return parsed
        except Exception:
            pass

    with open(resp_file, "w", encoding="utf-8") as f:
        f.write(res.stdout or "")
    return {"raw": res.stdout, "returncode": res.returncode}


def load_target_altering(target_file):
    targets = []
    if not os.path.exists(target_file):
        return targets
    with open(target_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("|") and not line.startswith("| :---") and not line.startswith("| 카테고리"):
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 3:
                    cat, item_name, count_str = parts[0], parts[1], parts[2]
                    try:
                        targets.append((cat, item_name, int(count_str)))
                    except ValueError:
                        pass
    return targets


def get_current_stock(cli_path, data_dir):
    items_data = run_cli_cmd(cli_path, "get_items", data_dir=data_dir)
    stock = {}
    if isinstance(items_data, list):
        item_list = items_data
    elif isinstance(items_data, dict):
        item_list = items_data.get("items", []) + items_data.get("bankItems", []) + items_data.get("sharedBankItems", [])
    else:
        item_list = []

    for it in item_list:
        name = it.get("DisplayName") or it.get("Name")
        count = it.get("Count", 0) or it.get("Amount", 0) or 1
        if name:
            stock[name] = stock.get(name, 0) + count
    return stock


def collect_completed_works(cli_path, data_dir, total_collected_items):
    collected_count_total = 0
    while True:
        works_data = run_cli_cmd(cli_path, "get_altering_works", data_dir=data_dir)
        works = works_data.get("works", [])
        completed_works = [w for w in works if w.get("IsCompleted") or w.get("State") == "Completed"]

        if not completed_works:
            break

        print(f"\n[+] 완료된 가공 작업물 발견: {len(completed_works)}건")
        target_work = completed_works[0]
        item_name = target_work.get("DisplayName", "")
        facility = target_work.get("FacilityName", "알 수 없음")

        print(f"[*] 시설 [{facility}] 이동 및 수령 시도 (대상 품목: {item_name})...")
        res = run_cli_cmd(cli_path, "complete_altering_work", {"displayName": item_name}, data_dir=data_dir)

        if isinstance(res, dict) and "error" in res:
            print(f"[!] 수령 중 오류 발생: {res.get('error')} - {res.get('message')}")
            break

        collected = res.get("collected", 0) if isinstance(res, dict) else 0
        collected_count_total += collected
        rewards = res.get("rewards", []) if isinstance(res, dict) else []
        critical_rewards = res.get("criticalRewards", []) if isinstance(res, dict) else []

        print(f"[*] [{facility}] {collected}건 수령 완료:")
        for r in rewards + critical_rewards:
            r_name = r.get("Name") or r.get("DisplayName")
            r_amt = r.get("Amount", 0) or r.get("Count", 0)
            if r_name:
                total_collected_items[r_name] = total_collected_items.get(r_name, 0) + r_amt
                print(f"    - {r_name}: +{r_amt}개")

        time.sleep(1.0)

    # 수령 기록 저장
    if collected_count_total > 0:
        history_file = os.path.join(data_dir, "last_altering_collected.json")
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump({
                "last_updated": datetime.datetime.now().isoformat(),
                "total_collected": collected_count_total,
                "items": total_collected_items
            }, f, ensure_ascii=False, indent=2)

    return collected_count_total


def register_alterable_works(cli_path, data_dir, shortages, max_facility_slots=7):
    works_data = run_cli_cmd(cli_path, "get_altering_works", data_dir=data_dir)
    works = works_data.get("works", [])
    
    # 시설별 현재 작업 수 계산
    facility_counts = {}
    for w in works:
        fac = w.get("FacilityName", "기타")
        facility_counts[fac] = facility_counts.get(fac, 0) + 1

    registered_works = []
    full_facilities = set()

    # 부족 품목 상태 복사
    active_shortages = []
    for cat, item_name, target_count, owned, diff in shortages:
        active_shortages.append({
            "cat": cat,
            "item_name": item_name,
            "target": target_count,
            "owned": owned,
            "diff": diff
        })

    def try_register_one(entry, available_recipes):
        cat = entry["cat"]
        item_name = entry["item_name"]
        if cat in full_facilities or entry["diff"] <= 0:
            return None

        current_fac_count = facility_counts.get(cat, 0)
        if current_fac_count >= max_facility_slots:
            full_facilities.add(cat)
            return None

        # 가공 레시피 매칭
        matched_recipe = None
        produced_per_work = 1
        for r_name, r_info in available_recipes.items():
            if r_name == item_name or r_name.startswith(f"{item_name}(") or f"({item_name})" in r_name:
                matched_recipe = r_name
                produced_per_work = r_info.get("ProducedPerWork", 1) or 1
                break

        if not matched_recipe:
            return None

        print(f"[*] 대기열 등록 시도: [{cat}] {matched_recipe} (현재 슬롯: {current_fac_count}/{max_facility_slots}, 남은 부족량: {entry['diff']})...")
        res = run_cli_cmd(cli_path, "execute_altering", {"displayName": matched_recipe}, data_dir=data_dir)

        if isinstance(res, dict) and "error" in res:
            err = res.get("error", "")
            msg = res.get("message", "")
            print(f"[!] 등록 실패: {err} - {msg}")
            if "queue" in err.lower() or "full" in err.lower() or "slot" in err.lower() or "limit" in err.lower():
                full_facilities.add(cat)
            return None
        else:
            print(f"[+] 대기열 등록 성공: {matched_recipe}")
            registered_works.append(matched_recipe)
            facility_counts[cat] = facility_counts.get(cat, 0) + 1
            entry["diff"] -= produced_per_work
            time.sleep(1.0)
            return matched_recipe

    # 1차 기본 배정: 후보 품목당 1회씩 균등 의뢰
    print("\n--- [1차 기본 배정: 후보 품목당 1회씩 균등 의뢰] ---")
    alterable_data = run_cli_cmd(cli_path, "get_alterable_items", data_dir=data_dir)
    alterable_items = alterable_data.get("items", []) if isinstance(alterable_data, dict) else []
    available_recipes = {it["DisplayName"]: it for it in alterable_items if it.get("Alterable") and it.get("DisplayName")}

    for entry in active_shortages:
        try_register_one(entry, available_recipes)

    # 2차 추가 배정: 슬롯이 남은 시설에 대해 최우선 순위 품목부터 추가 의뢰
    print("\n--- [2차 추가 배정: 잔여 슬롯 우선순위 집중 추가 의뢰] ---")
    while True:
        made_progress = False
        alterable_data = run_cli_cmd(cli_path, "get_alterable_items", data_dir=data_dir)
        alterable_items = alterable_data.get("items", []) if isinstance(alterable_data, dict) else []
        available_recipes = {it["DisplayName"]: it for it in alterable_items if it.get("Alterable") and it.get("DisplayName")}

        if not available_recipes:
            break

        for entry in active_shortages:
            cat = entry["cat"]
            if cat in full_facilities or entry["diff"] <= 0:
                continue
            if facility_counts.get(cat, 0) >= max_facility_slots:
                full_facilities.add(cat)
                continue

            registered = try_register_one(entry, available_recipes)
            if registered:
                made_progress = True
                break  # 성공 시 최우선 순위 품목부터 다시 확인

        if not made_progress:
            break

    return registered_works


def main():
    parser = argparse.ArgumentParser(description="마비노기 모바일 일괄 가공 단발성 자동화 스크립트")
    parser.add_argument("--data-dir", default="data", help="데이터 디렉토리 경로")
    parser.add_argument("--cli-path", default=None, help="MabinogiMobile_CLI.exe 경로")
    parser.add_argument("--target-file", default=None, help="목표치 파일 경로 (기본값: data/target_altering.md)")
    args = parser.parse_args()

    cli_path = resolve_cli_path(args.cli_path, args.data_dir)
    print(f"[*] CLI 경로: {cli_path}")

    # 1. 연결 확인
    st = run_cli_cmd(cli_path, "status", data_dir=args.data_dir)
    if st.get("pipe") != "connected":
        print(f"[오류] 게임 클라이언트와 파이프가 연결되어 있지 않습니다: {st}")
        sys.exit(1)
    print("[+] CLI 파이프 연결 정상 확인 (pipe: connected)")

    # 2. 현재 캐릭터 확인
    my_info = run_cli_cmd(cli_path, "get_my_info", data_dir=args.data_dir)
    char_name = my_info.get("Name") or my_info.get("CharacterName") or my_info.get("character_name") or "알 수 없음"
    print(f"[+] 현재 활성 캐릭터: {char_name}")

    # 3. 목표치 로드
    target_file = args.target_file or os.path.join(args.data_dir, "target_altering.md")
    targets = load_target_altering(target_file)
    print(f"[+] 가공 목표치 항목: 총 {len(targets)}개 로드 완료")
    print("[*] 실행 모드: 단발성(1회), 우선순위 규칙: Bottom-Up (목록 아래쪽 우선)")

    total_collected_items = {}
    print("\n================ [일괄 가공 단발성 실행] ================")

    # 4. 완료 작업물 일괄 수령
    collected_count = collect_completed_works(cli_path, args.data_dir, total_collected_items)

    # 5. 현재 재고 및 부족 품목 파악
    stock = get_current_stock(cli_path, args.data_dir)
    shortages = []
    for cat, item_name, target_count in targets:
        owned = stock.get(item_name, 0)
        diff = target_count - owned
        if diff > 0:
            shortages.append((cat, item_name, target_count, owned, diff))

    # 6. 우선순위 정렬: Bottom-Up (목록 아래쪽 우선)
    shortages.reverse()
    print(f"[*] 목표 미달 품목: 총 {len(shortages)}개")

    # 7. 신규 가공 의뢰 등록
    all_registered_works = register_alterable_works(cli_path, args.data_dir, shortages)

    # 8. 최종 결과 요약 및 종료
    print("\n" + "=" * 60)
    print("=== 일괄 가공 단발성 실행 완료 요약 ===")
    print(f"새로 등록된 가공 작업: 총 {len(all_registered_works)}건")
    for r in all_registered_works:
        print(f"  * {r}")
    print(f"\n수령한 가공품 총량:")
    if total_collected_items:
        for k, v in total_collected_items.items():
            print(f"  * {k}: +{v}개")
    else:
        print("  (수령된 아이템 없음)")
    print("=" * 60)


if __name__ == "__main__":
    main()
