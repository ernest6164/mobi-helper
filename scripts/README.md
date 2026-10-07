# 공용 스크립트 라이브러리 (Scripts Library)

본 디렉토리는 마비노기 모바일 헬퍼 시스템에서 반복적으로 사용되는 핵심 기능(데이터 동기화, 재고 계산, 자동 채집, 안전 인게임 채팅 전달 등)을 표준화하여 제공하는 **버전 관리(Git 추적) 공용 스크립트 저장소**입니다.

---

## 1. 운영 및 활용 원칙

1. **파이썬 스크립트 즉시 실행 원칙**:
   * 프로젝트 루트의 Python 가상환경(`.venv`)이 갖추어져 있는 경우, 단계별 수동 CLI 호출 대신 표준 워크플로우가 구현된 공용 파이썬 스크립트를 바로 실행합니다.
2. **워크플로우-스크립트 로직 정합성 및 동기화(Sync) 원칙**:
   * 본 디렉토리의 모든 스크립트 로직은 `references/workflows/*.md` 워크플로우 문서의 절차·판단 기준과 항상 1:1 정합성과 동기화를 유지합니다.
3. **환경 비종속성 및 매개변수화 원칙**:
   * 특정 머신이나 사용자 환경에 종속적인 하드코딩 경로(CLI 실행 경로, 특정 캐릭터명, 데이터 디렉토리 등)는 스크립트 내부에 포함하지 않습니다.
   * 모든 가변 설정은 CLI 매개변수(`--cli-path`, `--char-name`, `--data-dir` 등)로 전달받으며, 로컬 기본값은 `data/environments.json`([`references/environments.md`](../references/environments.md))을 참조합니다.
4. **가상환경 실행 원칙**:
   * 모든 스크립트는 프로젝트 루트의 Python 가상환경(`.venv`) 인터프리터를 통해 실행하는 것을 원칙으로 합니다.
   * 실행 예시: `.venv\Scripts\python.exe scripts/<스크립트명>.py [인자]`

---

## 2. 스크립트 목록 및 상세 사용법

### 1. `sync_character.py` (캐릭터 전체 상태 및 데이터 동기화)

* **설명**: 현재 접속 중인 캐릭터의 전체 상태(`get_my_info`, `get_current_environment`, `get_inventory`), 인벤토리/개인금고/공용금고 CSV, 퀘스트/일일·주간미션 MD 문서를 원클릭으로 일괄 동기화하고 `data/characters/README.md` 색인표를 최신화합니다.
* **사용 시점**:
  * 사용자가 `"현재 캐릭터 정보 저장해줘"`, `"정보 동기화해줘"`, `"상태 확인해줘"` 등을 요청했을 때
  * 캐릭터 접속 직후 또는 주요 활동 전/후 상태 최신화
* **주요 매개변수**:
  * `--char-name` *(필수)*: 현재 접속 중인 캐릭터 이름 (예: `Saki`, `아미나`)
  * `--cli-path` *(선택)*: `MabinogiMobile_CLI.exe` 경로 (미지정 시 `data/environments.json` 자동 탐색)
  * `--data-dir` *(선택)*: 데이터 저장 경로 (기본값: `../data`)
* **실행 예시**:
  ```powershell
  .venv\Scripts\python.exe scripts/sync_character.py --char-name Saki
  .venv\Scripts\python.exe scripts/sync_character.py --char-name 아미나 --cli-path C:\Nexon\MabinogiMobile\MabinogiMobile_CLI.exe
  ```

---

### 2. `send_chat.py` (인게임 채팅 안전 전달)

* **설명**: 한글 UTF-8 Base64 인코딩을 자동으로 처리하고, 50자 제한(`MAX_CHAT_LENGTH`) 분할, 2.5초 대기(`CHAT_RATE_LIMIT_SECONDS`), 레이트 리밋 발생 시 자동 재시도, 기본 3청크 제한(`DEFAULT_MAX_CHAT_CHUNKS`)을 준수하여 인게임 채팅을 안전하게 전송합니다.
* **사용 시점**:
  * 챗봇 지식 조회 후 인게임 대리 전달, 단순 인사말 전달, 공략 가이드 전송 등
* **주요 매개변수**:
  * `--message`: 단일 발화 문장
  * `--messages`: 복수 문장 리스트
  * `--delay` *(선택)*: 연속 메시지 간 대기 시간 초 (기본값: `2.5`)
  * `--max-chunks` *(선택)*: 최대 전송 청크 수 (기본값: `3`, `0` 지정 시 무제한)
  * `--cli-path` *(선택)*: CLI 실행 파일 경로
* **실행 예시**:
  ```powershell
  .venv\Scripts\python.exe scripts/send_chat.py --message "안녕하세요? 오늘도 좋은 하루 되세요!"
  .venv\Scripts\python.exe scripts/send_chat.py --messages "에이렐 공략 1단계입니다." "보스가 캐스팅할 때 회피기를 사용하세요." --max-chunks 3
  ```

---

### 3. `calculate_stock.py` (재고 집계 및 부족분 산출)

* **설명**: 현재 캐릭터 및 타 캐릭터(인벤토리, 개인 금고, 서버 공용 금고)의 재고 데이터를 통합 분석하고, `data/target_gathering.md` (또는 지정된 목표 파일) 목표 수량과 비교하여 즉시 채집이 필요한 품목과 타 캐릭터 보유로 보류되는 품목을 분류하여 중간 결과물(`scratch/missing.json`) 생성 및 콘솔 보고서를 출력합니다.
  * **(오래된 타 캐릭터 상태 처리)**: 다른 캐릭터의 상태(`최종 갱신 일시`)가 일정 기간(기본 3일, `--stale-days`)을 초과한 경우, 재고 확인 보고서에는 참고용(`[참고: 오래됨]`)으로만 표시하고, 채집 부족분 계산 및 보류 판정에서는 제외합니다.
* **사용 시점**:
  * 채집 작업 전 부족분 현황 파악, `"재고 계산해줘"`, `"부족한 재료 알려줘"` 요청 시
* **주요 매개변수**:
  * `--current-char` *(선택)*: 기준 캐릭터명 (기본값: `Saki` 또는 `data/environments.json`의 `activeCharacter`)
  * `--server` *(선택)*: 서버명 (기본값: `던컨` 또는 `data/environments.json`의 `defaultServer`)
  * `--target-file` *(선택)*: 목표 설정 파일 경로 (기본값: `data/target_gathering.md`)
  * `--output-file` *(선택)*: 부족분 JSON 출력 경로 (임시 중간 결과물 기본값: `scratch/missing.json`)
  * `--threshold` *(선택)*: 타 캐릭터 보유 보류 임계값 (기본값: `10` 또는 `data/environments.json`의 `otherCharStockThreshold`)
  * `--stale-days` *(선택)*: 타 캐릭터 데이터 만료 일수 (기본값: `3.0` 또는 `data/environments.json`의 `otherCharStaleDays`)
  * `--priority` *(선택)*: 정렬 우선순위 방식 (`bottom-up` / `top-down`, 기본값: `bottom-up`)
* **실행 예시**:
  ```powershell
  .venv\Scripts\python.exe scripts/calculate_stock.py --current-char Saki
  .venv\Scripts\python.exe scripts/calculate_stock.py --current-char 아미나 --threshold 10 --stale-days 3
  ```

---

### 4. `execute_gathering.py` (자동 채집 루프 및 실시간 모니터링)

* **설명**: `target_gathering.md` 역순 우선순위(`BOTTOM_UP`)와 타 캐릭터 보유량(`OTHER_CHAR_STOCK_THRESHOLD`=10)을 검토하여 채집 대상을 결정하고, 생활 스킬/도구 사전 점검 및 인벤토리 무게 점검(98% 한도) 후 백그라운드 채집을 수행합니다. 목표 수량 도달 시 즉시 중단하며 완료 후 인벤토리 CSV 및 캐릭터 MD 문서를 자동 동기화합니다.
  * **(오래된 타 캐릭터 상태 처리)**: 타 캐릭터 데이터가 오래된 경우(`--stale-days` 초과), 채집 보류 대상에서 제외하여 실질 부족분으로 채집을 진행합니다.
* **사용 시점**:
  * `"재고 보충해줘"`, `"부족한거 채집해줘"`, `"양털 채집해줘"` 등의 요청 시
* **주요 매개변수**:
  * `--char-name` *(선택)*: 채집을 수행할 캐릭터명 (기본값: `Saki`)
  * `--server` *(선택)*: 서버명 (기본값: `던컨`)
  * `--target-file` *(선택)*: 목표 파일 경로 (기본값: `data/target_gathering.md`)
  * `--single-item` *(선택)*: 단일 특정 품목만 채집할 경우 아이템명 (예: `"양털"`)
  * `--single-count` *(선택)*: 단일 특정 품목의 목표 수량 (예: `100`)
  * `--threshold` *(선택)*: 타 캐릭터 보류 임계값 (기본값: `10`)
  * `--stale-days` *(선택)*: 타 캐릭터 데이터 만료 일수 (기본값: `3.0`)
  * `--max-rounds` *(선택)*: 최대 채집 라운드 수 (기본값: `0`, 무제한)
* **실행 예시**:
  ```powershell
  .venv\Scripts\python.exe scripts/execute_gathering.py --char-name Saki
  .venv\Scripts\python.exe scripts/execute_gathering.py --char-name 아미나 --single-item "양털" --single-count 100
  ```

---

### 5. `execute_altering.py` (일괄 가공 단발성 자동화) *(⚠️ 시험적 기능)*

* **주의**: **시험적 기능(Experimental)**입니다. 시설 대기열 및 인게임 환경에 따라 정상 동작하지 않을 수 있으므로 실행 전 사용자 승인이 필수입니다.
* **설명**: `target_altering.md`의 목표치 대비 전체 보유량(인벤토리 + 금고)을 분석하여 완료된 가공물을 일괄 수령하고, 빈 슬롯에 목표 미달 가공물을 우선순위(Bottom-Up 아래쪽 우선)대로 1회 대기열 등록한 뒤 변동된 인벤토리 데이터를 동기화하고 종료하는 단발성 실행 스크립트입니다.
* **사용 시점**:
  * `"일괄 가공해줘"`, `"가공품 재고 보충해줘"` 등의 단발성 요청 시
* **주요 매개변수**:
  * `--confirm` *(선택)*: 시험적 기능 고지 확인 및 진행 승인 플래그
  * `--char-name` *(선택)*: 캐릭터명 (미지정 시 `environments.json`의 `activeCharacter` 참조)
  * `--data-dir` *(선택)*: 데이터 저장 경로 (기본값: `data`)
  * `--cli-path` *(선택)*: `MabinogiMobile_CLI.exe` 경로 (미지정 시 `environments.json` 자동 탐색)
  * `--target-file` *(선택)*: 목표 파일 경로 (기본값: `data/target_altering.md`)
* **실행 예시**:
  ```powershell
  # 단발성 1회 수령 및 대기열 등록 (Bottom-Up 아래쪽 우선)
  .venv\Scripts\python.exe scripts/execute_altering.py --confirm
  ```

---

### 6. `execute_life_leveling.py` (1시간 생활 스킬 집중 육성 순환 루프) *(⚠️ 시험적 기능)*

* **주의**: **시험적 기능(Experimental)**입니다. 1시간 동안 복합 순환 제어가 진행되므로 시작 전 사용자에게 정상 동작하지 않을 수 있음을 고지하고 진행 승인을 받아야 합니다.
* **설명**: 집중 육성할 스킬군(목공, 대장, 방직, 약품, 요리 등)에 맞춰 최단 시간 1차 가공물을 선정하고, 1시간(60분) 동안 [완료 가공물 수령 ➔ 최단 시간 가공 등록 ➔ 연계 제작 ➔ 원자재 보충 채집]을 무인 자동 순환하여 생활 스킬 레벨과 생활력을 극대화합니다.
* **사용 시점**:
  * `"생활 노가다 알아서 해줘"`, `"생활 스킬 레벨 올리자"`, `"생활 스킬 레벨 올려줘"` 요청 시
* **주요 매개변수**:
  * `--confirm` *(선택)*: 시험적 기능 고지 확인 및 진행 승인 플래그
  * `--char-name` *(선택)*: 현재 캐릭터명 (기본값: `environments.json`의 `activeCharacter`)
  * `--server` *(선택)*: 서버명 (기본값: `던컨`)
  * `--focus-skill` *(선택)*: 집중 육성 스킬군 (`목공`, `대장`, `방직`, `약품`, `요리`, `균형`, 기본값: `균형`)
  * `--skill-level` *(선택)*: 현재 생활 스킬 레벨 (기본값: `1`)
  * `--duration-minutes` *(선택)*: 세션 진행 시간 (기본값: `60`분)
  * `--check-only` *(선택)*: 사전 조건(연결 상태, 인벤토리 무게, 가공 대기열 현황) 점검만 수행 후 종료
  * `--cli-path` *(선택)*: `MabinogiMobile_CLI.exe` 경로
* **실행 예시**:
  ```powershell
  # 사전 조건 점검만 수행
  .venv\Scripts\python.exe scripts/execute_life_leveling.py --check-only

  # 목공 집중 1시간 수련 루프 실행 (사전 승인 플래그 포함)
  .venv\Scripts\python.exe scripts/execute_life_leveling.py --focus-skill 목공 --duration-minutes 60 --confirm
  ```



---

## 3. 커스텀 스크립트 작성 안내 (`scratch/`)

* 사용자 고유의 반복 매크로 작업이나 특수 필터링이 필요한 경우, `scripts/` 내의 코드를 `scratch/` 디렉토리에 복사하여 자유롭게 수정해 사용하십시오.
* `scratch/` 디렉토리는 `.gitignore`에 등록되어 있어 Git 추적에서 제외되므로 민감한 로컬 설정이나 일회성 테스트 코드를 안전하게 보관할 수 있습니다.
