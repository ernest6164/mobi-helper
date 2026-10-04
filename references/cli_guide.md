# 마비노기 모바일 AI 커넥터 CLI 연동 가이드

* **갱신 일시**: 2026년 10월 4일

본 문서는 마비노기 모바일 PC 클라이언트와 통신하는 `MabinogiMobile_CLI.exe` 도구의 사용법 및 전체 명령어 명세를 다룹니다.

---

## 1. 사전 준비 (인게임 설정)

1. **마비노기 모바일(PC 버전) 클라이언트**를 실행합니다.
2. 게임 내 **[메뉴(≡)] → [환경 설정] → [게임] → [AI 제어]** 항목으로 이동합니다.
3. **'AI 커넥터 (MM AI 에이전트 활성화)' 옵션을 켬(ON)**으로 설정합니다.

위 설정이 완료되면 로컬 PC에 통신을 위한 CLI 실행 파일이 자동으로 세팅됩니다.
* 💡 **참고**: 일주일 동안 사용하지 않으면 보안 및 리소스 관리를 위해 해당 기능이 자동으로 비활성화됩니다. 추후 연결 트러블 슈팅 시 인게임 옵션이 켜져 있는지 가장 먼저 확인해 주세요.

---

## 2. 통신 브릿지 (`MabinogiMobile_CLI.exe`) 탐색 및 경로 관리

특정 설치 경로에 의존하지 않고 범용성을 유지하기 위해 절대 경로를 코드에 하드코딩하지 않습니다.

1. 먼저 `data/path.txt` 파일이 존재하는지 확인합니다.
2. 존재한다면 해당 파일에 적힌 경로로 CLI 도구를 호출합니다.
3. 존재하지 않는다면 로컬 드라이브에서 `MabinogiMobile_CLI.exe`를 검색하여 찾은 후 `data/path.txt`에 저장합니다.

---

## 3. 기본 통신 방법 및 명령어 구조

### 3.1. 연결 상태 확인
```powershell
MabinogiMobile_CLI status
```
* **정상 연결**: `{"pipe":"connected"}` (Exit code 0)
* **연결 실패**: Exit code 5 (`"pipe": "disconnected"`). 게임이 꺼져 있거나 인게임 AI 제어 옵션이 꺼져 있는 상태입니다.

### 3.2. 명령어 실행 포맷
```powershell
MabinogiMobile_CLI <명령어> [JSON 본문]
```
* 성공 시 Exit code 0을 반환하며, 결과는 JSON 형식의 텍스트로 표준 출력(stdout)됩니다.

---

## 4. 지원되는 제어 명령어 목록 (Capabilities)

### 4.1. 정보 조회 (Status, Inventory, Quests)
* `get_current_environment`: 현재 위치, 날씨, 인게임 시간 조회
* `get_my_info`: 내 캐릭터의 기본 정보, 스탯, 현재 체력(HP) 등 상태 조회
* `get_activity`: 현재 자동 진행, 이동, 전투, 액션 상태 조회
* `get_quests`: 퀘스트 트래커 항목 조회
* `get_daily_missions`: 캐릭터의 활성화된 일일 미션(목표, 진행도, 완료 여부, 수령 상태) 조회
* `get_weekly_missions`: 계정 내 활성화된 주간 미션 조회
* `get_currencies`: 보유 중인 주요 재화(골드 등) 잔액 조회
* `get_inventory`: 인벤토리의 현재 무게 / 최대 무게 조회
* `get_items`: 보유 중인 아이템(가방, 계정 금고, 캐릭터 금고) 및 채집물/요리 목록 조회
* `get_near_npcs`: 근처에 대화 가능한 NPC 목록 조회
* `get_near_pcs`: 근처에 있는 다른 플레이어 목록 조회

### 4.2. 채집 및 제작 (Gathering & Crafting)
* `get_gatherable_items`: 내 생활 스킬 레벨로 채집 가능한 모든 채집물과 도구 보유 여부 조회
* `execute_gathering`: 목표 수량에 도달할 때까지 특정 아이템 채집 수행 (낚시 전용 아이템은 자동 낚시 시작)
* `get_alterable_items`: 가공(Altering) 레시피와 필요 재료 조회 (추출물, 포자, 가루, 실, 목재 등)
* `get_altering_works`: 진행 중이거나 완료된 가공 작업 내역 및 남은 시간 조회
* `execute_altering`: 가공 레시피 대기열에 등록 (해당 시설로의 이동 포함)
* `complete_altering_work`: 특정 시설에서 완료된 모든 가공 작업물 수령 (해당 시설로의 이동 포함)
* `get_craftable_items`: 제작(Crafting) 레시피와 필요 재료 및 제작 가능 여부 조회
* `execute_crafting`: 아이템 제작 실행 (해당 시설로 이동 및 결과물 수령 포함)

### 4.3. 소셜 및 액션 (Social & Actions)
* `write_chat`: 채팅 메시지 전송
* `get_social_actions`: 사용 가능한 소셜 행동(모션) 및 표정 목록 조회
* `get_music_scores`: 보유 중인 악보 목록 조회
* `play_music_score`: 악보 연주 시작
* `get_instruments`: 보유 중인 악기 목록 조회
* `change_instrument`: 악기 장착 및 변경
* `stop_action`: 현재 취소 가능한 액션(악기 연주, 의자 앉기, 자동 진행, 채집 등) 중지
* `stand_up`: 앉은 상태에서 일어나기

---

## 5. ⚠️ 한글/비-ASCII 데이터 처리 규칙 (필수 준수)

Windows 콘솔(CP949 등) 환경의 인코딩 문제로 인해, 한국어가 포함된 데이터를 직접 인자로 넘기면 텍스트가 깨져 전송됩니다.

* **입력 시**: 한글이 포함된 문자열이나 JSON Body는 반드시 **UTF-8로 인코딩한 뒤 Base64로 변환**하여 `base64:` 접두사와 함께 전달해야 합니다.
  * *예시*: `"안녕"` -> UTF-8 Bytes -> Base64(`7JWI64WV`) -> `MabinogiMobile_CLI write_chat base64:7JWI64WV`
* **출력 시**: 응답받은 JSON 내부의 한글은 `\uXXXX` 형태의 유니코드 이스케이프로 출력됩니다. 표준 JSON 파서(`json.loads()` 등)로 파싱하면 자동으로 온전한 한글 텍스트로 변환됩니다.
  * `%LOCALAPPDATA%\MabinogiMobileCLI\last-response.json` 파일에서 직전 명령어의 순수 UTF-8 결과를 바로 읽어올 수도 있습니다.

---

## 6. 작업 시 주의사항

* **작업 대기 (Blocking)**: 채집, 가공 등 시간이 걸리는 행동은 즉시 응답을 반환하지 않고 게임 내 행동이 끝날 때까지 대기(Block)합니다. 강제로 프로세스를 종료하지 말고 행동이 완료될 때까지 대기해야 합니다.
* **사용자 확인 필요 (requiresConfirm)**: 재화 소모 등의 중요 작업은 유저의 인게임 승인이 필요할 수 있으므로, 응답 메시지에 유저 행동이 필요하다는 에러(`blocked`)가 반환되면 이를 사용자에게 알려주어야 합니다.
