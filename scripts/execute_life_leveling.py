#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
execute_life_leveling.py - 생활 스킬 집중 육성 1시간 순환 루프 자동화 스크립트

기능:
    - 사전 인터랙션 결과(집중 육성 스킬군, 레벨) 및 가공 대기열/도구/무게 사전 점검
    - 최단 시간 가공물(Shortest Duration Altering) 우선 선정 및 레시피 매칭
    - 1시간(60분) 동안 채집 ➔ 가공 ➔ 제작 사이클 무인 순환 반복
    - 인벤토리 무게 95% 초과 시 안전 정지 또는 소모 제작 우선 실행
    - 세션 종료 후 최종 가공물 수령 및 캐릭터 인벤토리/MD 전체 데이터 동기화
    - 1시간 성과 통계(채집량, 가공량, 제작량, 소요 시간) 보고서 출력

사용 예시:
    python scripts/execute_life_leveling.py --focus-skill 목공 --duration-minutes 60
    python scripts/execute_life_leveling.py --focus-skill 대장 --skill-level 10
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

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# 생활 스킬군별 최단시간 1차 가공물 및 핵심 원자재 매핑
SKILL_PRESETS = {
    "목공": {
        "altering_targets": ["목재", "목재+"],
        "raw_materials": ["통나무", "나뭇가지", "굵은 나뭇가지"],
        "crafting_keywords": ["캠프파이어 키트", "목공", "나무"]
    },
    "대장": {
        "altering_targets": ["철괴(철 광석)", "철괴(광석)", "강철괴"],
        "raw_materials": ["철 광석", "광석", "석탄"],
        "crafting_keywords": ["못", "숏소드", "대거"]
    },
    "방직": {
        "altering_targets": ["실", "옷감", "식물 섬유", "가죽", "옷감+"],
        "raw_materials": ["양털", "거미줄", "식물 섬유", "생가죽"],
        "crafting_keywords": ["붕대", "장갑", "로브"]
    },
    "약품": {
        "altering_targets": ["새록 버섯 진액", "튼튼 버섯 가루", "숨숨꽃 가루", "마력 기폭제"],
        "raw_materials": ["새록 버섯", "튼튼 버섯", "숨숨꽃", "베이스 허브", "마나 허브"],
        "crafting_keywords": ["회복 물약", "생명력 포션", "비약"]
    },
    "요리": {
        "altering_targets": ["물에 불린 쌀", "물에 불린 콩", "마요네즈", "밀가루"],
        "raw_materials": ["쌀", "콩", "밀", "달걀", "우유"],
        "crafting_keywords": ["밥", "두부", "음식"]
    },
    "균형": {
        "altering_targets": ["목재", "철괴(철 광석)", "옷감", "새록 버섯 진액"],
        "raw_materials": ["통나무", "철 광석", "양털", "새록 버섯"],
        "crafting_keywords": ["캠프파이어 키트", "못", "붕대"]
    }
}


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
    raise FileNotFoundError("CLI 도구 경로를 찾을 수 없습니다. data/environments.json을 확인하십시오.")


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

    # JSON 파싱 시도
    parsed = None
    if res.stdout and res.stdout.strip():
        try:
            parsed = json.loads(res.stdout)
            with open(resp_file, "w", encoding="utf-8") as f:
                json.dump(parsed, f, ensure_ascii=False, indent=2)
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


def get_current_items(cli_path, data_dir):
    res = run_cli_cmd(cli_path, "get_items", data_dir=data_dir)
    if isinstance(res, list):
        return res
    if isinstance(res, dict) and "items" in res:
        return res["items"]
    return []


def stop_action(cli_path, data_dir="data"):
    return run_cli_cmd(cli_path, "stop_action", data_dir=data_dir)


def check_preconditions(cli_path, data_dir):
    """사전 조건 점검: 연결 상태, 대기열, 인벤토리 무게, 도구"""
    print("=" * 70)
    print("=== [1단계: 사전 조건 및 환경 점검] ===")
    print("=" * 70)

    # 1. 파이프 연결 확인
    st = run_cli_cmd(cli_path, "status", data_dir=data_dir)
    if st.get("pipe") != "connected":
        print(f"[오류] 게임 클라이언트와 연결되어 있지 않습니다: {st}", file=sys.stderr)
        return False

    print("[+] CLI 파이프 정상 연결 확인 (pipe: connected)")

    # 2. 인벤토리 무게 점검
    inv = run_cli_cmd(cli_path, "get_inventory", data_dir=data_dir)
    cur_w = inv.get("CurrentInventoryWeightAsDecimal", 0)
    max_w = inv.get("MaxInventoryWeightAsDecimal", 2090)
    ratio = (cur_w / max_w * 100) if max_w > 0 else 0
    print(f"[+] 인벤토리 무게: {cur_w:.1f} / {max_w:.1f} ({ratio:.1f}%)")
    if ratio >= 95.0:
        print("[경고] 인벤토리 무게가 95% 이상으로 너무 꽉 차 있습니다. 정리가 필요합니다.", file=sys.stderr)

    # 3. 가공 대기열 사전 점검 및 완료 작업물 수령
    works_data = run_cli_cmd(cli_path, "get_altering_works", data_dir=data_dir)
    works = works_data.get("works", [])
    completed_works = [w for w in works if w.get("IsCompleted") or w.get("State") == "Completed"]

    if completed_works:
        print(f"[*] 사전 정리: 완료된 기존 가공 작업물 {len(completed_works)}건 자동 수령 중...")
        for w in completed_works:
            name = w.get("DisplayName", "")
            run_cli_cmd(cli_path, "complete_altering_work", {"displayName": name}, data_dir=data_dir)
            time.sleep(0.5)

    # 잔여 작업 중 장시간(10분 초과) 작업 점검
    works_data = run_cli_cmd(cli_path, "get_altering_works", data_dir=data_dir)
    works = works_data.get("works", [])
    long_works = [w for w in works if w.get("RemainingSeconds", 0) > 600]
    print(f"[+] 현재 가공 슬롯 사용량: 총 {len(works)}건 (10분 초과 장기 작업: {len(long_works)}건)")
    if len(works) >= 6:
        print("[안내] 가공 대기열 슬롯이 거의 꽉 차 있습니다. 시작 전 인게임에서 대기열을 비워두는 것을 권장합니다.")

    return True


def collect_completed_works(cli_path, data_dir, session_stats):
    """완료된 가공 작업물 일괄 수령"""
    works_data = run_cli_cmd(cli_path, "get_altering_works", data_dir=data_dir)
    works = works_data.get("works", [])
    completed = [w for w in works if w.get("IsCompleted") or w.get("State") == "Completed"]

    collected_count = 0
    for w in completed:
        item_name = w.get("DisplayName", "")
        fac = w.get("FacilityName", "공방")
        res = run_cli_cmd(cli_path, "complete_altering_work", {"displayName": item_name}, data_dir=data_dir)
        if isinstance(res, dict) and not res.get("error"):
            c_cnt = res.get("collected", 1)
            collected_count += c_cnt
            session_stats["altered"][item_name] = session_stats["altered"].get(item_name, 0) + c_cnt
            print(f"    [가공 수령] [{fac}] {item_name} {c_cnt}건 수령 완료")
            time.sleep(0.5)

    return collected_count


def register_shortest_altering(cli_path, data_dir, target_alter_names, session_stats, max_slots=7):
    """최단 시간 가공물 우선 등록"""
    works_data = run_cli_cmd(cli_path, "get_altering_works", data_dir=data_dir)
    works = works_data.get("works", [])
    if len(works) >= max_slots:
        return 0

    alterable_data = run_cli_cmd(cli_path, "get_alterable_items", data_dir=data_dir)
    items = alterable_data.get("items", []) if isinstance(alterable_data, dict) else []
    avail_recipes = {it["DisplayName"]: it for it in items if it.get("Alterable")}

    registered = 0
    for target in target_alter_names:
        matched = None
        for r_name in avail_recipes:
            if r_name == target or r_name.startswith(f"{target}(") or f"({target})" in r_name:
                matched = r_name
                break

        if matched:
            print(f"    [가공 의뢰] 최단시간 가공물 등록 시도: {matched}...")
            res = run_cli_cmd(cli_path, "execute_altering", {"displayName": matched}, data_dir=data_dir)
            if isinstance(res, dict) and not res.get("error"):
                registered += 1
                session_stats["registered_altering"][matched] = session_stats["registered_altering"].get(matched, 0) + 1
                print(f"    [+] {matched} 가공 대기열 등록 성공")
                time.sleep(0.8)
                break  # 1회 루프당 1건 우선 등록 후 다음 스텝 진행
            else:
                err = res.get("error") if isinstance(res, dict) else "unknown"
                print(f"    [-] 등록 실패 ({err})")

    return registered


def execute_linked_crafting(cli_path, data_dir, keywords, session_stats):
    """연계 제작 가능한 기초 레시피 실행"""
    craftable_data = run_cli_cmd(cli_path, "get_craftable_items", data_dir=data_dir)
    items = craftable_data.get("items", []) if isinstance(craftable_data, dict) else []

    # 제작 가능하고 키워드가 매칭되는 레시피 탐색
    for it in items:
        if not it.get("Craftable"):
            continue
        dname = it.get("DisplayName", "")
        if any(kw in dname for kw in keywords):
            print(f"    [연계 제작] 수련용 아이템 제작 시도: {dname}...")
            res = run_cli_cmd(cli_path, "execute_crafting", {"displayName": dname}, data_dir=data_dir)
            if isinstance(res, dict) and not res.get("error"):
                session_stats["crafted"][dname] = session_stats["crafted"].get(dname, 0) + 1
                print(f"    [+] {dname} 제작 성공 및 수령 완료")
                time.sleep(1.0)
                return True
            else:
                print(f"    [-] 제작 실패: {res}")
                break

    return False


def execute_sub_gathering(cli_path, data_dir, raw_materials, session_stats, max_duration=120):
    """가공 유휴 시간 동안 1차 원자재 안전 채집"""
    gatherable = run_cli_cmd(cli_path, "get_gatherable_items", data_dir=data_dir)
    g_items = gatherable.get("items", []) if isinstance(gatherable, dict) else []
    valid_g = {g.get("DisplayName"): g for g in g_items if g.get("ToolOk", True)}

    target_mat = None
    for m in raw_materials:
        if m in valid_g:
            target_mat = m
            break

    if not target_mat:
        return 0

    print(f"    [보충 채집] 대기 시간 활용 채집 시작: [{target_mat}] (최대 {max_duration}초)...")
    
    # 백그라운드 채집 스레드 시작
    gather_thread = threading.Thread(
        target=lambda: run_cli_cmd(cli_path, "execute_gathering", {"displayName": target_mat}, data_dir=data_dir)
    )
    gather_thread.start()

    start_g = time.time()
    while gather_thread.is_alive():
        time.sleep(3.0)
        elapsed = time.time() - start_g

        # 무게 확인
        inv = run_cli_cmd(cli_path, "get_inventory", data_dir=data_dir)
        cur_w = inv.get("CurrentInventoryWeightAsDecimal", 0)
        max_w = inv.get("MaxInventoryWeightAsDecimal", 2090)
        if cur_w >= max_w * 0.95:
            print("    [!] 인벤토리 무게 95% 도달! 채집 긴급 중단...")
            stop_action(cli_path, data_dir)
            break

        if elapsed >= max_duration:
            print(f"    [*] 채집 배정 시간({max_duration}초) 만료. 채집 중단 중...")
            stop_action(cli_path, data_dir)
            break

    gather_thread.join()
    session_stats["gathered"][target_mat] = session_stats["gathered"].get(target_mat, 0) + 1
    return 1


def sync_final_data(cli_path, data_dir, char_name, server_name):
    """최종 세션 완료 후 캐릭터 인벤토리 및 스탯 동기화"""
    print("\n[*] 세션 종료 후 인벤토리 및 캐릭터 데이터 동기화 실행 중...", flush=True)
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    sync_script = os.path.join(scripts_dir, "sync_character.py")
    if os.path.exists(sync_script):
        subprocess.run(
            [sys.executable, sync_script, "--char-name", char_name, "--cli-path", cli_path, "--data-dir", data_dir],
            capture_output=True, text=True, encoding="utf-8"
        )
        print("[+] 캐릭터 데이터 동기화 완료")


def run_life_leveling_loop(char_name, server_name, cli_path, data_dir, focus_skill, duration_minutes=60):
    preset = SKILL_PRESETS.get(focus_skill, SKILL_PRESETS["균형"])
    altering_targets = preset["altering_targets"]
    raw_materials = preset["raw_materials"]
    crafting_keywords = preset["crafting_keywords"]

    print("=" * 70)
    print(f"=== 마비노기 모바일 1시간 생활 스킬 집중 육성 루프 가동 ===")
    print(f"* 캐릭터: [{char_name}] (서버: {server_name})")
    print(f"* 집중 육성 분야: [{focus_skill}]")
    print(f"* 최단 시간 우선 가공물: {altering_targets}")
    print(f"* 연계 채집 원자재: {raw_materials}")
    print(f"* 총 진행 시간: {duration_minutes}분 (약 {duration_minutes * 60}초)")
    print("=" * 70)

    session_stats = {
        "gathered": {},
        "altered": {},
        "registered_altering": {},
        "crafted": {}
    }

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    cycle = 0

    while time.time() < end_time:
        cycle += 1
        elapsed_min = (time.time() - start_time) / 60
        rem_min = (end_time - time.time()) / 60
        print(f"\n>>> [사이클 {cycle}] 진행 경과: {elapsed_min:.1f}분 / 남은 시간: {rem_min:.1f}분")

        # 1. 완료 가공물 일괄 수령
        collect_completed_works(cli_path, data_dir, session_stats)

        # 2. 빈 슬롯에 최단시간 가공물 등록
        register_shortest_altering(cli_path, data_dir, altering_targets, session_stats)

        # 3. 연계 제작 실행 (가능한 경우)
        execute_linked_crafting(cli_path, data_dir, crafting_keywords, session_stats)

        # 4. 가공 대기 시간 동안 원자재 보충 채집
        execute_sub_gathering(cli_path, data_dir, raw_materials, session_stats, max_duration=90)

        # 5. 안전 대기 및 루프 간격 조정
        time.sleep(2.0)

    # 1시간 만료 후 최종 마무리
    print("\n[*] 1시간 집중 육성 세션 만료. 안전 마무리 절차 시작...")
    stop_action(cli_path, data_dir)
    collect_completed_works(cli_path, data_dir, session_stats)
    sync_final_data(cli_path, data_dir, char_name, server_name)

    # 최종 보고서 출력
    print("\n" + "=" * 60)
    print("=== 1시간 생활 스킬 집중 육성 세션 성과 보고서 ===")
    print("=" * 60)
    print(f"* 총 진행 시간: {((time.time() - start_time) / 60):.1f}분 (총 {cycle}회 순환 완료)")
    print(f"* 집중 육성 분야: {focus_skill}")
    print("\n[채집 성과]")
    if session_stats["gathered"]:
        for k, v in session_stats["gathered"].items():
            print(f"  - {k}: {v}회 채집 세션 완료")
    else:
        print("  - 내역 없음")

    print("\n[가공 성과]")
    if session_stats["altered"]:
        for k, v in session_stats["altered"].items():
            print(f"  - {k}: 총 +{v}개 수령")
    else:
        print("  - 수령 내역 없음")

    print("\n[제작 성과]")
    if session_stats["crafted"]:
        for k, v in session_stats["crafted"].items():
            print(f"  - {k}: 총 {v}개 제작 완료")
    else:
        print("  - 제작 내역 없음")
    print("=" * 60)


def main():
    default_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    env_file = os.path.join(default_data_dir, "environments.json")

    default_char = "아미나"
    default_server = "던컨"

    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                env_data = json.load(f)
                default_char = env_data.get("inGame", {}).get("activeCharacter", default_char)
                default_server = env_data.get("inGame", {}).get("defaultServer", default_server)
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="마비노기 모바일 1시간 생활 스킬 집중 육성 자동화 스크립트 (⚠️ 시험적 기능)")
    parser.add_argument("--char-name", default=default_char, help=f"현재 캐릭터명 (기본값: {default_char})")
    parser.add_argument("--server", default=default_server, help=f"서버명 (기본값: {default_server})")
    parser.add_argument("--focus-skill", default="균형", choices=list(SKILL_PRESETS.keys()), help="집중 육성 스킬군")
    parser.add_argument("--skill-level", type=int, default=1, help="현재 생활 스킬 레벨")
    parser.add_argument("--duration-minutes", type=int, default=60, help="진행 시간(분 단위, 기본값: 60)")
    parser.add_argument("--cli-path", default=None, help="MabinogiMobile_CLI.exe 경로")
    parser.add_argument("--data-dir", default=default_data_dir, help="데이터 디렉토리 경로")
    parser.add_argument("--check-only", action="store_true", help="사전 조건 점검만 수행하고 종료")
    parser.add_argument("--confirm", action="store_true", help="시험적 기능 고지 확인 및 진행 승인 플래그")

    args = parser.parse_args()

    print("=" * 70)
    print("⚠️ [시험적 기능 안내 (Experimental Feature)]")
    print("본 '생활 스킬 집중 육성(1시간 루프)' 기능은 시험적 기능으로,")
    print("게임 내 시설 상태, 대기열, 동선 상황에 따라 정상 동작하지 않을 수 있습니다.")
    print("반드시 작업 시작 전 사전 승인(동의) 후 사용하십시오.")
    print("=" * 70)

    data_dir = os.path.abspath(args.data_dir)
    cli_path = resolve_cli_path(args.cli_path, data_dir)

    # 사전 조건 점검
    ok = check_preconditions(cli_path, data_dir)
    if not ok:
        sys.exit(1)


    if args.check_only:
        print("\n[+] 사전 점검 완료. 정상 종료합니다.")
        return

    run_life_leveling_loop(
        char_name=args.char_name,
        server_name=args.server,
        cli_path=cli_path,
        data_dir=data_dir,
        focus_skill=args.focus_skill,
        duration_minutes=args.duration_minutes
    )


if __name__ == "__main__":
    main()
