# mobi-helper (마비노기 모바일 헬퍼 스킬)

마비노기 모바일(PC 클라이언트)의 AI 커넥터(`MabinogiMobile_CLI.exe`)를 활용하여 캐릭터 정보, 인벤토리/금고 재고, 퀘스트 및 미션 진행 상황을 관리하고 채집 작업을 자동화하는 **AI 에이전트 스킬(Skill)** 패키지입니다.

---

## 1. 💬 지원 명령어 및 사용 예시

에이전트와의 자연어 대화를 통해 아래 작업을 수행할 수 있습니다.

* **캐릭터 및 퀘스트 정보 조회/동기화**
  * *"현재 캐릭터 정보 저장해줘"*, *"인벤토리 동기화해줘"*, *"퀘스트랑 일일/주간 미션 진행상황 기록해줘"*
* **재고 및 채집 관리**
  * *"재고 보충해줘"*, *"부족한 재료 채집해줘"*, *"나무 진액 목표치까지 모아줘"*
* **재고 목표 설정**
  * *"양털 목표 수량을 500개로 변경해줘"*
* **게임 지식/공략 조회 및 인게임 채팅 대리 전달 (챗봇)**
  * *"안녕하세요? 라고 말해줘"*, *"댄스타임이라고 말해"* (단순 발화 전달)
  * *"어비스 지옥 공략을 말해줘"*, *"양털을 채집하는 방법을 말해줘"* (지식 검색 및 인게임 채팅 전달)
  * *"에이렐 공략을 채팅 5개로 말해줘"*, *"햄펀길드 세줄요약 말해줘"* (지정 분량 요약 전달)


---

## 2. 🚀 스킬 설치 및 등록 방법

사용 중인 AI 에이전트와의 채팅창에 아래 문장을 그대로 입력하시면, 에이전트가 환경에 맞춰 자동으로 스킬을 다운로드하고 설치를 완료합니다.

```text
https://github.com/ernest6164/mobi-helper 저장소의 스킬을 내 글로벌 스킬에 설치해줘
```

---

## 3. 📁 프로젝트 디렉토리 구조

```text
mobi-helper/
├── SKILL.md                 # 스킬 메인 정의 및 실행 워크플로우 (핵심)
├── README.md                # 스킬 소개, 지원 명령어 및 디렉토리 구조 안내
├── AGENTS.md                # 워크스페이스 기본 운영 지침
├── scripts/                 # 공용 스크립트 라이브러리 (Git 버전 관리 대상)
│   ├── README.md            # 스크립트 목록, 설명 및 매개변수 가이드
│   ├── sync_character.py    # 캐릭터 전체 상태 및 CSV/MD 일괄 동기화
│   ├── send_chat.py         # 한글 UTF-8 Base64 안전 인게임 채팅 전송
│   ├── calculate_stock.py   # 재고 현황 계산 및 부족분 산출
│   └── execute_gathering.py # 재고 보충 자동 채집 실행 및 모니터링
├── references/              # 온디맨드 세부 참고 문서
│   ├── workflows.md         # 동기화, 재고 보충, 챗봇 지식 전달 상세 작업 흐름
│   ├── cli_guide.md         # CLI 통신 프로토콜, Capabilities 및 UTF-8 Base64 규칙
│   ├── data_management.md   # 캐릭터 정합성 관리 원칙 및 파일 명명 규칙
│   ├── environments.md      # 환경 설정 JSON 구조 정의 및 스키마 명세서
│   ├── constants.md         # 시스템 전역 설정값, 기본값 및 임계치 상수 명세
│   ├── templates.md         # data/ 생성 파일들의 표준 작성 템플릿
│   └── appendix.md          # CSV 뷰어, 스크립트 작성 팁, Git 및 특정 에이전트 환경 설정 가이드
├── data/                    # 운영 중 생성/관리되는 모든 명시적 문서 및 데이터 (Git 제외)
│   ├── environments.json    # CLI 도구 경로, 실행 환경 및 기본 설정 통합 JSON
│   ├── know-how.md          # 시스템 종속 실행 노하우 및 도구(Git, venv 등) 사용법
│   ├── TODO.md              # 작업 대기열 및 정합성 관리 대시보드
│   ├── workflows_custom.md  # 사용자 정의 특수 규칙 (API 응답 다음 2순위 적용)
│   ├── target.md            # 채집 목표 수량 설정 문서
│   ├── recipes.csv          # 가공/제작 레시피 데이터베이스
│   ├── characters/          # 캐릭터 관련 모든 정보 디렉토리
│   │   ├── README.md        # 계정 내 전체 캐릭터 요약 색인 시트 (구 characters.md)
│   │   ├── (서버명)_(캐릭터명).md
│   │   ├── (서버명)_(캐릭터명)_inventory.csv
│   │   ├── (서버명)_(캐릭터명)_bank.csv
│   │   ├── (서버명)_bank_all.csv
│   │   └── (서버명)_(캐릭터명)_quest.md
│   └── chatbot/             # 챗봇 지식베이스 디렉토리
│       ├── README.md        # 지식 문서 전체 색인(Index) 및 태그 목록
│       └── (주제명).md      # 개별 공략 및 가이드 지식 문서
└── scratch/                 # 일회성 임시 스크립트 및 중간 계산 결과물 (Git 제외)
```

---

## 📚 관련 문서 안내

* [`SKILL.md`](./SKILL.md): 스킬 진입점 및 메인 워크플로우
* [`scripts/README.md`](./scripts/README.md): 공용 스크립트 목록 및 매개변수 가이드
* [`references/workflows.md`](./references/workflows.md): 상세 표준 작업 흐름 (동기화, 재고 보충, 챗봇 지식)
* [`references/cli_guide.md`](./references/cli_guide.md): AI 커넥터 CLI 연동 및 명령어 명세
* [`references/data_management.md`](./references/data_management.md): 데이터 관리 원칙
* [`references/environments.md`](./references/environments.md): 환경 설정 정의 및 스키마 명세
* [`references/constants.md`](./references/constants.md): 시스템 전역 상수 정의
* [`references/templates.md`](./references/templates.md): 데이터 문서 템플릿
* [`references/appendix.md`](./references/appendix.md): 부록 및 특정 환경/에이전트 설정 가이드