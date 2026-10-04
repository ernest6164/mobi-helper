---
name: mobi-helper
description: >-
  마비노기 모바일(Mabinogi Mobile) PC 클라이언트 AI 커넥터(MabinogiMobile_CLI) 연동 스킬.
  캐릭터 정보/인벤토리/퀘스트 동기화, 재고 보충/채집, 챗봇 지식 조회 및 인게임 채팅 전달,
  또는 "모비노기/마비노기 모바일/모비에서 ~해줘" 등 인게임 제어 요청 시 사용합니다.
---

# mobi-helper (마비노기 모바일 헬퍼 스킬)

마비노기 모바일 PC 클라이언트 AI 커넥터(`MabinogiMobile_CLI.exe`)를 활용하여 캐릭터 상태 동기화, 자동 채집/재고 보충, 챗봇 지식 조회 및 인게임 채팅 전달을 수행합니다.

---

## 1. 공통 필수 원칙 (Invariants)

1. **연결 상태 점검**: `data/environments.json`의 CLI 경로를 확인하고 `<CLI경로> status` 실행 (`{"pipe":"connected"}` 확인). 연결 끊김 시 인게임 AI 제어 옵션 확인 요청.
2. **한글/비-ASCII 인코딩**: 한글 파라미터나 JSON Body는 반드시 **UTF-8 Base64**로 인코딩하여 `base64:<Base64문자열>` 형태로 CLI에 전달.
3. **가상환경 실행**: 공용 스크립트는 반드시 프로젝트 가상환경(`.venv\Scripts\python.exe`)으로 실행.
4. **사용자 정의 규칙 우선**: `data/workflows_custom.md`가 존재하면 기본 워크플로우보다 최우선 적용.

---

## 2. 작업 라우팅 가이드 (해당 파일만 참조)

사용자 요청의 유형에 따라 **아래의 해당 전용 워크플로우 파일 1개만 확인**하여 작업을 수행하십시오:

| 요청 유형 | 대표 예시 발화 | 참조할 전용 워크플로우 파일 |
| :--- | :--- | :--- |
| **정보 저장 및 동기화** | `"캐릭터 정보 저장해줘"`, `"동기화해줘"`, `"인벤토리 갱신해줘"` | [`references/workflows/info_sync.md`](./references/workflows/info_sync.md) |
| **재고 보충 및 채집** | `"재고 보충해줘"`, `"부족한 재료 채집해줘"`, `"목표치까지 모아줘"` | [`references/workflows/stock_replenishment.md`](./references/workflows/stock_replenishment.md) |
| **챗봇 지식 & 인게임 채팅** | `"모비에 안녕하세요 라고 말해줘"`, `"모비에 ~공략 말해줘"`, `"모비에서 채팅으로 쳐줘"` | [`references/workflows/chatbot_chat.md`](./references/workflows/chatbot_chat.md) |
| **기타 인게임 액션** | `"악보 연주해줘"`, `"가공해줘"`, `"제작해줘"`, `"소셜 액션 해줘"` | [`references/cli_guide.md`](./references/cli_guide.md) |

---

## 3. 세부 레퍼런스 색인

필요 시에만 아래 문서를 추가로 참조합니다:
* **표준 공용 스크립트 목록**: [`scripts/README.md`](./scripts/README.md)
* **환경 설정 정의 및 스키마**: [`references/environments.md`](./references/environments.md)
* **데이터 관리 원칙 및 명명 규칙**: [`references/data_management.md`](./references/data_management.md)
* **전역 상수 정의**: [`references/constants.md`](./references/constants.md)
* **데이터 작성 템플릿**: [`references/templates/README.md`](./references/templates/README.md)
* **부록 및 환경 팁**: [`references/appendix/README.md`](./references/appendix/README.md)
