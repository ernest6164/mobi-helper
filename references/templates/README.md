# 데이터 문서 템플릿 및 작성 예시 (Templates)

* **갱신 일시**: 2026년 10월 5일

본 디렉토리는 `data/` 디렉토리에 생성 및 관리되는 모든 데이터 문서의 표준 포맷과 작성 예시를 세부 문서별로 분리하여 제공합니다.

---

## 템플릿 색인

| 번호 | 문서/데이터 종류 | 대상 파일 경로 | 템플릿 링크 | 설명 |
| :---: | :--- | :--- | :--- | :--- |
| 1-1 | 채집 재고 목표치 | `data/target_gathering.md` | [`target_gathering.md`](./target_gathering.md) | 채집물 재고 목표 수량 관리 테이블 |
| 1-2 | 가공 재고 목표치 | `data/target_altering.md` | [`target_altering.md`](./target_altering.md) | 가공 결과물 재고 목표 수량 및 자연어 예외 규칙 관리 문서 |
| 2 | 캐릭터 요약 색인 | `data/characters/README.md` | [`characters_summary.md`](./characters_summary.md) | 계정 내 전체 캐릭터 스탯/레벨 요약 색인 |

| 3 | 개별 캐릭터 상세 정보 | `data/characters/(서버)_(캐릭터).md` | [`character_detail.md`](./character_detail.md) | 캐릭터 상세 스탯, 점수, 무게 및 연관 파일 갱신 시각 |
| 4 | 인벤토리/보관함 CSV | `data/characters/*.csv` | [`inventory_bank_csv.md`](./inventory_bank_csv.md) | 인벤토리, 개인 금고, 공용 금고 아이템 CSV |
| 5 | 퀘스트 및 미션 진행 상황 | `data/characters/(서버)_(캐릭터)_quest.md` | [`quest_mission.md`](./quest_mission.md) | 퀘스트 및 일일/주간 미션 진행/완료/보상 수령 표 |
| 6 | 시스템 및 환경 설정 | `data/environments.json` | [`environments_json.md`](./environments_json.md) | CLI 도구 경로, 가상환경, 기본 설정 JSON |
| 7-1 | 가공 레시피 | `data/recipe_altering.md` | [`recipe_altering.md`](./recipe_altering.md) | 가공 시설별 레시피 및 재료 관리 테이블 |
| 7-2 | 제작 레시피 | `data/recipe_crafting.md` | [`recipe_crafting.md`](./recipe_crafting.md) | 제작 시설별 레시피 및 재료 관리 테이블 *(일반 제작 참고용)* |
| 8 | 사용자 정의 특수 규칙 | `data/workflows_custom.md` | [`workflows_custom.md`](./workflows_custom.md) | 2순위 최우선 적용되는 사용자 커스텀 규칙 |
| 9 | 챗봇 지식 색인 | `data/chatbot/README.md` | [`chatbot_index.md`](./chatbot_index.md) | 챗봇 지식베이스 공략/가이드 문서 색인 및 태그 목록 |
| 10 | 챗봇 개별 지식 문서 | `data/chatbot/(주제명).md` | [`chatbot_detail.md`](./chatbot_detail.md) | 공략 본문, 태그, 갱신 설정 및 50자 분할 전달문 |
