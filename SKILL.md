---
name: mobi-helper
description: >-
  마비노기 모바일(Mabinogi Mobile) PC 클라이언트 AI 커넥터(MabinogiMobile_CLI) 연동 스킬.
  사용자가 "모비에서 ~", "모비에 ~", "모비노기에서 ~" 등으로 요청하는 경우 이 스킬을 트리거하여 실행합니다.
  캐릭터 정보/인벤토리/퀘스트 동기화, 일괄 채집/가공 요청, 챗봇 지식 조회 및 인게임 채팅 전달, 인게임 제어 요청 시 사용합니다.
---

# mobi-helper (마비노기 모바일 헬퍼 스킬)

마비노기 모바일 PC 클라이언트 AI 커넥터(`MabinogiMobile_CLI.exe`)를 활용하여 캐릭터 상태 동기화, 일괄 채집/가공(재고 보충), 챗봇 지식 조회 및 인게임 채팅 전달을 수행합니다.

---

## 1. 공통 필수 원칙 (Invariants)

1. **연결 상태 점검**: `data/environments.json`의 CLI 경로를 확인하고 `<CLI경로> status` 실행 (`{"pipe":"connected"}` 확인). 연결 끊김 시 인게임 AI 제어 옵션 확인 요청.
2. **한글/비-ASCII 인코딩**: 한글 파라미터나 JSON Body는 반드시 **UTF-8 Base64**로 인코딩하여 `base64:<Base64문자열>` 형태로 CLI에 전달.
3. **명령어 응답 저장**: CLI 명령어 실행에 대한 응답 결과는 항상 `data/response/<명령어>.json` 형태로 저장.
4. **파이썬 스크립트 우선 실행**: 파이썬 실행 환경(`.venv\Scripts\python.exe` 등)이 갖추어져 있다면, 단계별 수동 CLI 직접 호출 대신 정의된 해당 공용 파이썬 스크립트(`scripts/`)를 바로 실행합니다.
5. **사용자 정의 규칙 우선**: `data/workflows_custom.md`가 존재하면 기본 워크플로우보다 최우선 적용.
6. **⚠️ 시험적 기능 사전 고지 및 승인 필수**: '일괄 가공 요청' 및 '생활 스킬 집중 육성' 등 `[시험적 기능]`으로 지정된 작업은 시작 전 반드시 사용자에게 시험적 기능이라서 정상 동작하지 않을 수 있음을 명확히 고지하고 진행 승인(동의)을 받은 후 실행합니다.
7. **워크플로우-파이썬 로직 정합성(Sync) 유지**: 모든 워크플로우 문서의 절차·판단 로직과 `scripts/` 파이썬 스크립트의 처리 로직은 항상 완전한 정합성과 동기화를 유지합니다.
8. **오래된 타 캐릭터 상태 처리**: 저장된 다른 캐릭터의 상태(`최종 갱신 일시`)가 너무 오래된 경우(기본 3일 초과 등), 재고 확인 시에는 참고로만 사용하고, 채집 시 부족분 계산 및 보류 판정에는 반영하지 않습니다(부족분으로 산출하여 채집 대상에 포함).

---

## 2. 작업 라우팅 가이드 (해당 파일만 참조)

사용자 요청의 유형에 따라 **아래의 해당 전용 워크플로우 파일 1개만 확인**하여 작업을 수행하십시오:

| 요청 유형 | 대표 예시 발화 | 참조할 전용 워크플로우 파일 |
| :--- | :--- | :--- |
| **정보 저장 및 동기화** | `"캐릭터 정보 저장해줘"`, `"동기화해줘"`, `"인벤토리 갱신해줘"` | [`references/workflows/info_sync.md`](./references/workflows/info_sync.md) |
| **일괄 채집 요청** | `"일괄 채집해줘"`, `"재고 보충해줘"`<br>*(※ 개별 채집 요청을 수행하는 워크플로우가 아님)* | [`references/workflows/stock_gathering.md`](./references/workflows/stock_gathering.md) |
| **일괄 가공 요청**<br>*(⚠️ 시험적 기능)* | `"일괄 가공해줘"`<br>*(시작 전 정상 동작하지 않을 수 있음을 고지하고 승인 필요)* | [`references/workflows/stock_altering.md`](./references/workflows/stock_altering.md) |
| **생활 스킬 집중 육성**<br>*(⚠️ 시험적 기능)* | `"생활 노가다 알아서 해줘"`, `"생활 스킬 레벨 올리자"`, `"생활 스킬 레벨 올려줘"`<br>*(시작 전 정상 동작하지 않을 수 있음을 고지하고 승인 필요)* | [`references/workflows/life_skill_leveling.md`](./references/workflows/life_skill_leveling.md) |
| **챗봇 지식 & 인게임 채팅** | `"모비에 안녕하세요 라고 말해줘"`, `"모비에 ~공략 말해줘"`, `"모비에서 채팅으로 쳐줘"` | [`references/workflows/chatbot_chat.md`](./references/workflows/chatbot_chat.md) |
| **기타 인게임 액션** | `"악보 연주해줘"`, `"소셜 액션 해줘"`, `"상태 확인해줘"` | [`references/cli_guide.md`](./references/cli_guide.md) |

---

## 3. 세부 레퍼런스 색인

필요 시에만 아래 문서를 추가로 참조합니다:
* **표준 공용 스크립트 목록**: [`scripts/README.md`](./scripts/README.md)
* **환경 설정 정의 및 스키마**: [`references/environments.md`](./references/environments.md)
* **데이터 관리 원칙 및 명명 규칙**: [`references/data_management.md`](./references/data_management.md)
* **전역 상수 정의**: [`references/constants.md`](./references/constants.md)
* **데이터 작성 템플릿**: [`references/templates/README.md`](./references/templates/README.md)
* **부록 및 환경 팁**: [`references/appendix/README.md`](./references/appendix/README.md)
