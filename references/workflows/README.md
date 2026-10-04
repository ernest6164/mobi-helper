# 마비노기 모바일 헬퍼 표준 작업 흐름 (Workflows)

본 디렉토리는 마비노기 모바일 헬퍼 시스템에서 수행하는 핵심 작업 흐름을 규정합니다.

> [!IMPORTANT]
> **사용자 정의 특수 규칙(`data/workflows_custom.md`) 적용 원칙**:
> `data/workflows_custom.md` 파일이 존재하는 경우, 본 워크플로우에 정의된 기본 동작보다 최우선 적용됩니다.

---

## 세부 워크플로우 색인

| 절 | 작업 흐름명 | 문서 링크 | 핵심 요약 |
| :---: | :--- | :--- | :--- |
| **제1절** | **정보 저장 및 확인** | [`info_sync.md`](./info_sync.md) | 캐릭터 기본 정보, 스탯, 인벤토리/금고 CSV, 퀘스트/미션 저장 및 요약 색인 갱신 |
| **제2절** | **채집물 재고 보충** | [`stock_gathering.md`](./stock_gathering.md) | 채집 목표치(`target_gathering.md`) 점검, 타 캐릭터 재고(10개 기준) 확인, 우선순위 정렬, 사전 점검 및 채집 |
| **제3절** | **가공물 재고 보충** | [`stock_altering.md`](./stock_altering.md) | 가공 목표치(`target_altering.md`) 점검, 가공 시설/대기열 관리 및 결과물 수령 *(추후 워크플로우 정의)* |
| **제4절** | **제작물 재고 보충** | [`stock_crafting.md`](./stock_crafting.md) | 제작 목표치(`target_crafting.md`) 점검, 레시피/재료 확인 및 아이템 제작 실행 *(추후 워크플로우 정의)* |
| **제5절** | **챗봇 지식 조회 & 채팅 전달** | [`chatbot_chat.md`](./chatbot_chat.md) | 단순 발화/지식 질의 구분, 1주일 갱신 주기 관리, 50자 분할 및 최대 3개 청크 전송 |
