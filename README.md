# MobiStockManager (마비노기 모바일 헬퍼 스킬)

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

---

## 2. 🚀 스킬 설치 및 등록 방법

사용 중인 AI 에이전트와의 채팅창에 아래 문장을 그대로 입력하시면, 에이전트가 환경에 맞춰 자동으로 스킬을 다운로드하고 설치를 완료합니다.

```text
https://github.com/ernest6164/mobi-helper 저장소의 스킬을 내 글로벌 스킬에 설치해줘
```

---

## 3. 📁 프로젝트 디렉토리 구조

```text
MobiStockManager/
├── SKILL.md                 # 스킬 메인 정의 및 실행 워크플로우 (핵심)
├── README.md                # 스킬 소개, 지원 명령어 및 디렉토리 구조 안내
├── AGENTS.md                # 워크스페이스 기본 운영 지침
├── references/              # 온디맨드 세부 참고 문서
│   ├── workflow.md          # 1. 정보 저장/확인 및 2. 재고 보충 상세 작업 흐름
│   ├── cli_guide.md         # CLI 통신 프로토콜, Capabilities 및 UTF-8 Base64 규칙
│   ├── data_management.md   # 캐릭터 정합성 관리 원칙 및 파일 명명 규칙
│   ├── templates.md         # data/ 생성 파일들의 표준 작성 템플릿
│   └── appendix.md          # CSV 뷰어, 스크립트 작성 팁, Git 및 특정 에이전트 환경 설정 가이드
├── data/                    # 운영 중 생성/관리되는 데이터 (Git 제외)
│   ├── characters.md
│   ├── (서버명)_(캐릭터명).md
│   ├── (서버명)_(캐릭터명)_inventory.csv
│   ├── (서버명)_(캐릭터명)_bank.csv
│   ├── (서버명)_bank_all.csv
│   ├── (서버명)_(캐릭터명)_quest.md
│   ├── target.md
│   ├── recipes.csv
│   └── path.txt
└── scratch/                 # 일회성 임시 스크립트 디렉토리 (Git 제외)
```

---

## 📚 관련 문서 안내

* [`SKILL.md`](./SKILL.md): 스킬 진입점 및 메인 워크플로우
* [`references/workflow.md`](./references/workflow.md): 상세 표준 작업 흐름 (저장/확인 & 재고 보충)
* [`references/cli_guide.md`](./references/cli_guide.md): AI 커넥터 CLI 연동 및 명령어 명세
* [`references/data_management.md`](./references/data_management.md): 데이터 관리 원칙
* [`references/templates.md`](./references/templates.md): 데이터 문서 템플릿
* [`references/appendix.md`](./references/appendix.md): 부록 및 특정 환경/에이전트 설정 가이드