---
name: mobi-helper
description: >-
  마비노기 모바일(Mabinogi Mobile) PC 클라이언트와 통신(MabinogiMobile_CLI)하여 캐릭터의 모든 상태,
  인벤토리, 금고, 퀘스트/미션 정보를 동기화하고, 재고 목표치(target.md)에 맞춰 부족한 채집물을
  자동으로 보충하거나, 게임 지식/공략을 검색 및 학습하여 인게임 채팅으로 대리 전달(write_chat)하는
  작업을 수행할 때 이 스킬을 사용합니다.
---

# mobi-helper (마비노기 모바일 헬퍼 스킬)

마비노기 모바일 PC 클라이언트의 AI 커넥터(`MabinogiMobile_CLI.exe`)를 활용하여 캐릭터의 전체 상태 및 인벤토리/금고 데이터를 동기화하고, 목표 재고에 맞춰 채집 및 제작 작업을 체계적으로 자동화하며, 게임 공략 및 지식을 관리하여 인게임 채팅으로 대리 전달합니다.

---

## 1. 사전 확인 및 연결 절차

1. **CLI 도구 경로 확인**:
   * `data/path.txt` 파일이 있는지 확인합니다.
   * 경로가 없으면 로컬 드라이브에서 `MabinogiMobile_CLI.exe`를 검색하여 유효한 경로를 `data/path.txt`에 기록합니다.
2. **연결 상태 점검**:
   ```powershell
   <CLI경로> status
   ```
   * `{"pipe":"connected"}`가 반환되면 정상 연결 상태입니다.
   * `disconnected` 상태인 경우, 사용자에게 인게임 **[메뉴(≡)] → [환경 설정] → [게임] → [AI 제어]** 옵션이 켜져 있는지 확인을 요청합니다.
3. **사용자 정의 특수 규칙 점검 (`data/workflows_custom.md`)**:
   * 특수 규칙이 존재할 경우, API 응답 다음으로 우선 적용(2순위)되어 스킬의 기존 기본 동작이나 워크플로우를 무시하거나 변경하여 동작합니다.


> [!IMPORTANT]
> **한글/비-ASCII 데이터 전송 규칙**: Windows 콘솔 인코딩 문제 방지를 위해, 한글이 포함된 문자열이나 JSON Body는 반드시 **UTF-8 Base64**로 인코딩하여 `base64:<Base64문자열>` 형태로 CLI에 전달해야 합니다.

---

## 2. 정보 저장 및 확인 절차 (Information Sync & State Inspection)

사용자가 `"현재 캐릭터 정보 저장해줘"`, `"정보 동기화해줘"`, `"상태 확인해줘"`, `"인벤토리 갱신해줘"` 등의 명령을 내렸을 때 수행합니다.

1. **접속 캐릭터명 확인**: 사용자에게 현재 접속 중인 캐릭터 이름을 확인 요청합니다. *(API 미제공)*
2. **캐릭터 전체 상태 및 환경 수집**: `get_current_environment`, `get_my_info`, `get_currencies`, `get_inventory`, `get_activity` 호출 → `data/characters/(서버)_(캐릭터).md` 작성/갱신
3. **인벤토리 및 보관함 수집**: `get_items` 호출 →
   * `data/characters/(서버)_(캐릭터)_inventory.csv` (가방)
   * `data/characters/(서버)_(캐릭터)_bank.csv` (개인 금고)
   * `data/characters/(서버)_bank_all.csv` (서버 공용 금고)
   * `data/characters/(서버)_(캐릭터).md` 내 CSV 갱신 일시 기록
4. **퀘스트 및 미션 수집**: `get_quests`, `get_daily_missions`, `get_weekly_missions` 호출 → `data/characters/(서버)_(캐릭터)_quest.md` 작성/갱신
5. **통합 요약 갱신**: `data/characters/README.md` 색인 시트에 해당 캐릭터 행 추가 및 갱신

---

## 3. 재고 보충 및 채집 작업 흐름 (Replenishment & Gathering)

사용자가 `"재고 보충해줘"`, `"재료 채워줘"`, `"부족한거 채집해줘"` 등의 명령을 내렸을 때 수행합니다.

1. **목표치 점검**:
   * `data/target.md`에서 대상 아이템의 목표치를 확인합니다.
   * 목표치가 없을 경우 템플릿(`references/templates.md`, 일괄 100개) 사용을 사용자에게 권유합니다.
   * 사용자가 템플릿 사용을 수락하면 그대로 적용하고, 거절 시 구체적인 목표 수량 입력을 요구합니다.
2. **기준 캐릭터 재고 파악**: 현재 접속 중인 캐릭터의 인벤토리 및 금고 재고를 확인합니다.
3. **타 캐릭터 재고 확인**: 부족분 발생 시 다른 캐릭터의 CSV 데이터(`data/characters/` 하위)를 확인합니다.
4. **채집 보류 판단**: 다른 캐릭터에 재고가 **10개 이상** 있을 경우 채집을 보류합니다. *(10개 미만은 채집 진행)*
5. **우선순위 준수 및 도구/스킬 사전 점검**:
   * `data/target.md` 목록의 **아래쪽에 위치한 항목일수록 높은 우선순위**를 가집니다.
   * `get_gatherable_items`로 캐릭터의 생활 스킬 레벨과 필요 채집 도구 보유 여부를 사전에 점검합니다.
   * `get_inventory`로 잔여 무게를 확인한 후, `execute_gathering` 명령으로 부족분을 채집합니다.
6. **결과 보고 및 데이터 최신화**: 새로 채집된 수량과 타 캐릭터 잔여 재고를 보고하고 데이터를 최신화합니다.


---

## 4. 챗봇 지식 조회 및 인게임 채팅 전달 작업 흐름 (Chatbot Knowledge & Chat Delivery)

사용자가 `"안녕하세요? 라고 말해줘"`, `"어비스 지옥 공략을 말해줘"`, `"양털을 채집하는 방법을 말해줘"` 등의 형태로 요청했을 때 수행합니다.

1. **요청 분석 및 단순 발화 전달**:
   * `"안녕하세요? 라고 말해줘"` 등 검색이 불필요한 단순 발화 요청은 지식 검색 없이 즉시 인게임 채팅으로 직접 전달합니다.
2. **로컬 지식베이스 검색**: 지식/공략 질문의 경우 `data/chatbot/` 내의 문서 및 `README.md` 인덱스를 `#태그`와 키워드로 검색합니다.
3. **로컬 정보 존재 시**: 해당 내용을 바탕으로 메시지를 요약 구성하여 인게임 채팅으로 전송합니다.
4. **로컬 정보 부재 시**:
   * **인터넷 검색 가능 환경**: 인터넷 검색을 통해 정보를 조사 및 요약하여 인게임 채팅으로 전달하고, 조사된 내용을 `data/chatbot/`에 신규 문서로 저장 및 `README.md`에 인덱싱합니다.
   * **인터넷 검색 불가 환경**: 인게임 채팅을 전송하지 않고 사용자에게 정보를 찾을 수 없음을 안내합니다.
5. **메시지 구성 및 분할 규칙 준수**:
   * **접두사 생략 및 핵심 정보 전달**: `[공략 1/5]`, `[주제명]` 등의 불필요한 머리말/번호 접두사를 붙이지 않고 순수 핵심 정보 본문만 전달합니다.
   * **기본 제한**: 사용자의 명시적인 요청이 없는 경우, 전달 메시지는 **최대 3개(`DEFAULT_MAX_CHAT_CHUNKS`=3)**로 제한하며 핵심 내용을 3개 이내로 요약하여 전달합니다.
   * **명시적 요청 시**: `"전부 다 말해줘"`, `"자세하게 다 입력해줘"` 등 명시적 요청 시 개수 제한 없이 전체 내용을 전송합니다.
   * **전송 규칙**: 1회 50자(`MAX_CHAT_LENGTH`) 제한 분할, UTF-8 Base64 인코딩, 연속 전송 시 최소 2초 대기(`CHAT_RATE_LIMIT_SECONDS`)를 엄격히 준수합니다.



---

## 5. 상세 레퍼런스 문서

세부 명세, 워크플로우 다이어그램 및 템플릿 양식은 아래 문서를 참조합니다.

* **표준 작업 흐름(상세 플로우차트 및 절차)**: [references/workflows.md](./references/workflows.md)
* **CLI 전체 명령어 및 인코딩 가이드**: [references/cli_guide.md](./references/cli_guide.md)
* **데이터 관리 원칙 및 명명 규칙**: [references/data_management.md](./references/data_management.md)
* **시스템 전역 상수 정의**: [references/constants.md](./references/constants.md)
* **데이터 표준 포맷 및 작성 템플릿**: [references/templates.md](./references/templates.md)
* **부록 및 환경/도구 팁**: [references/appendix.md](./references/appendix.md)

