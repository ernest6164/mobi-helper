#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
sync_character.py - 캐릭터 전체 상태, 인벤토리/금고 CSV, 퀘스트/미션 동기화 공용 스크립트

사용 예시:
    python scripts/sync_character.py --char-name Saki
    python scripts/sync_character.py --char-name 아미나 --cli-path C:\Nexon\MabinogiMobile\MabinogiMobile_CLI.exe
"""

import argparse
import csv
import datetime
import json
import os
import re
import subprocess
import sys


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


def run_cli_command(cli_path, command_name, *args):
    cmd = [cli_path, command_name] + list(args)
    res = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    try:
        return json.loads(res.stdout)
    except Exception:
        return {}


def clean_html(text):
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text)


def sync_character(char_name, cli_path, data_dir):
    char_dir = os.path.join(data_dir, "characters")
    os.makedirs(char_dir, exist_ok=True)

    # 1. 상태 및 데이터 조회
    status = run_cli_command(cli_path, "status")
    if status.get("pipe") != "connected":
        print(f"[오류] CLI 커넥터 연결 상태가 아닙니다: {status}", file=sys.stderr)
        return False

    env = run_cli_command(cli_path, "get_current_environment")
    info = run_cli_command(cli_path, "get_my_info")
    inventory = run_cli_command(cli_path, "get_inventory")
    items = run_cli_command(cli_path, "get_items")
    quests = run_cli_command(cli_path, "get_quests")
    daily_missions = run_cli_command(cli_path, "get_daily_missions")
    weekly_missions = run_cli_command(cli_path, "get_weekly_missions")

    server_name = info.get("RealmName") or env.get("RealmName") or "던컨"
    now = datetime.datetime.now()
    timestamp_full = now.strftime("%Y-%m-%d %H:%M")
    timestamp_date = now.strftime("%Y-%m-%d")

    print(f"[*] 동기화 시작: 서버=[{server_name}], 캐릭터=[{char_name}]")

    # 2. 인벤토리 및 금고 CSV 작성
    inv_csv = os.path.join(char_dir, f"{server_name}_{char_name}_inventory.csv")
    bank_csv = os.path.join(char_dir, f"{server_name}_{char_name}_bank.csv")
    bank_all_csv = os.path.join(char_dir, f"{server_name}_bank_all.csv")

    item_list = items if isinstance(items, list) else items.get("Items", [])
    inv_items, bank_items, bank_all_items = [], [], []

    for it in item_list:
        loc = it.get("Location", "")
        if loc in ("inventory", "bag", "gathered", "cooked"):
            inv_items.append(it)
        elif loc in ("character_storage", "bank"):
            bank_items.append(it)
        elif loc in ("account_storage", "account_bank", "bank_all"):
            bank_all_items.append(it)

    fieldnames = ["Location", "DisplayName", "Category", "CategoryDisplayName", "Count", "IsLocked"]

    def write_csv(filepath, item_rows):
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in item_rows:
                writer.writerow({
                    "Location": r.get("Location", ""),
                    "DisplayName": r.get("DisplayName", ""),
                    "Category": r.get("Category", ""),
                    "CategoryDisplayName": r.get("CategoryDisplayName", ""),
                    "Count": r.get("Count", 1),
                    "IsLocked": r.get("IsLocked", False)
                })

    write_csv(inv_csv, inv_items)
    write_csv(bank_csv, bank_items)
    write_csv(bank_all_csv, bank_all_items)

    # 3. 개별 캐릭터 MD 작성
    char_md = os.path.join(char_dir, f"{server_name}_{char_name}.md")
    vitals = info.get("Vitals", {})

    cur_weight = inventory.get("CurrentInventoryWeight", vitals.get("InventoryWeightCurrent", ""))
    max_weight = inventory.get("MaxInventoryWeight", vitals.get("InventoryWeightMax", ""))
    cur_hp = vitals.get("HealthCurrent", "")
    max_hp = vitals.get("HealthMax", info.get("HealthMax", {}).get("Value", ""))

    combat_score = info.get("CombatScore", {}).get("Value", "")
    living_score = info.get("LivingScore", {}).get("Value", "")
    job_name = info.get("EnabledCombatJobDisplayName", "")
    level_val = info.get("Level", "")

    md_content = f"""# 캐릭터 정보: {char_name}
**최종 갱신 일시**: {timestamp_full}

## 기본 정보
* **타이틀**: {info.get("Title", "")}
* **서버**: {server_name}
* **레벨**: {level_val}
* **직업**: {job_name}

## 스탯 및 점수
* **전투력**: {combat_score}
* **생활력**: {living_score}
* **매력**: {info.get("AttractivenessScore", {}).get("Value", "")}
* **데코 점수**: {info.get("DecorScore", {}).get("Value", "")}

## 기타 상태
* **인벤토리 무게**: {cur_weight} / {max_weight}
* **현재 체력**: {cur_hp} / {max_hp}

## 데이터 업데이트 일시
* **{server_name}_{char_name}_inventory.csv**: {timestamp_full}
* **{server_name}_{char_name}_bank.csv**: {timestamp_full}
* **{server_name}_bank_all.csv**: {timestamp_full}
* **{server_name}_{char_name}_quest.md**: {timestamp_full}
"""
    with open(char_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 4. 퀘스트/미션 MD 작성
    quest_md = os.path.join(char_dir, f"{server_name}_{char_name}_quest.md")
    q_list = quests if isinstance(quests, list) else quests.get("Quests", [])
    d_list = daily_missions if isinstance(daily_missions, list) else daily_missions.get("Missions", [])
    w_list = weekly_missions if isinstance(weekly_missions, list) else weekly_missions.get("Missions", [])

    q_content = f"""# 퀘스트 및 미션 진행 상황: {char_name}

* **서버**: {server_name}
* **최종 갱신 일시**: {timestamp_full}

## 1. 퀘스트 진행 내역

| 구분 | 퀘스트명 | 세부 목표 | 진행 상태 | 완료 여부 |
| :--- | :--- | :--- | :--- | :---: |
"""
    for q in q_list:
        q_type = q.get("SourceDisplayName", "메인")
        q_title = q.get("QuestTitle", "")
        objs = q.get("Objectives", [])
        if objs:
            for obj in objs:
                desc = clean_html(obj.get("Description", ""))
                cnt = obj.get("Count", 0)
                goal = obj.get("Goal", 1)
                is_done = "✅ 완료" if obj.get("IsCompleted") else "진행 중"
                q_content += f"| {q_type} | {q_title} | {desc} | {cnt}/{goal} | {is_done} |\n"
        else:
            q_content += f"| {q_type} | {q_title} | - | - | 진행 중 |\n"

    if not q_list:
        q_content += "| - | 진행 중인 퀘스트가 없습니다 | - | - | - |\n"

    q_content += """
## 2. 일일 미션 수행 내역

| 미션명 | 내용 | 진행도 | 완료 여부 | 보상 수령 |
| :--- | :--- | :--- | :---: | :---: |
"""
    for d in d_list:
        title = d.get("Title", "")
        desc = d.get("Description", "")
        cur = d.get("CurrentCount", 0)
        goal = d.get("GoalCount", 1)
        is_done = "✅ 완료" if d.get("IsCompleted") else "진행 중"
        reward = "수령 완료" if d.get("IsRewardReceived") else "미수령"
        q_content += f"| {title} | {desc} | {cur}/{goal} | {is_done} | {reward} |\n"

    if not d_list:
        q_content += "| - | 일일 미션 정보가 없습니다 | - | - | - |\n"

    q_content += """
## 3. 주간 미션 수행 내역

| 미션명 | 내용 | 진행도 | 완료 여부 | 보상 수령 |
| :--- | :--- | :--- | :---: | :---: |
"""
    for w in w_list:
        title = w.get("Title", "")
        desc = w.get("Description", "")
        cur = w.get("CurrentCount", 0)
        goal = w.get("GoalCount", 1)
        is_done = "✅ 완료" if w.get("IsCompleted") else "진행 중"
        reward = "수령 완료" if w.get("IsRewardReceived") else "미수령"
        q_content += f"| {title} | {desc} | {cur}/{goal} | {is_done} | {reward} |\n"

    if not w_list:
        q_content += "| - | 주간 미션 정보가 없습니다 | - | - | - |\n"

    with open(quest_md, "w", encoding="utf-8") as f:
        f.write(q_content)

    # 5. characters/README.md 요약 시트 업데이트
    readme_path = os.path.join(char_dir, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = []
        found = False
        for line in lines:
            if line.startswith("**최종 갱신 일시**:"):
                new_lines.append(f"**최종 갱신 일시**: {timestamp_full}\n")
            elif f"| {char_name} |" in line:
                new_lines.append(f"| {char_name} | {server_name} | {job_name} | {level_val} | {combat_score} | {living_score} | {timestamp_date} |\n")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"| {char_name} | {server_name} | {job_name} | {level_val} | {combat_score} | {living_score} | {timestamp_date} |\n")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    # 6. data/environments.json activeCharacter 갱신
    env_file = os.path.join(data_dir, "environments.json")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                env_json = json.load(f)
            if "inGame" not in env_json:
                env_json["inGame"] = {}
            env_json["inGame"]["activeCharacter"] = char_name
            env_json["inGame"]["defaultServer"] = server_name
            with open(env_file, "w", encoding="utf-8") as f:
                json.dump(env_json, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[*] environments.json 갱신 실패 (무시됨): {e}", file=sys.stderr)

    print(f"[+] [{char_name}] 캐릭터 동기화 완료: 전투력 {combat_score}, 생활력 {living_score}")
    return True


def main():
    parser = argparse.ArgumentParser(description="마비노기 모바일 캐릭터 데이터 동기화 스크립트")
    parser.add_argument("--char-name", required=True, help="동기화할 현재 접속 캐릭터명 (필수)")
    parser.add_argument("--cli-path", default=None, help="MabinogiMobile_CLI.exe 실행 경로 (선택, 미지정 시 data/environments.json 참조)")
    parser.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "data"), help="data 디렉토리 경로 (기본값: ../data)")

    args = parser.parse_args()
    data_dir = os.path.abspath(args.data_dir)
    cli_path = resolve_cli_path(args.cli_path, data_dir)

    success = sync_character(args.char_name, cli_path, data_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
