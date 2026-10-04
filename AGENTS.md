# 마비노기 모바일 헬퍼

본 문서는 마비노기 모바일 헬퍼 스킬 및 워크스페이스 운영을 위한 기본 규칙을 제공합니다.

---

## 1. 개요 및 운영 원칙

* **에이전트 독립성 및 범용성 원칙**:
  * 본 프로젝트는 **특정 AI 에이전트나 전용 툴체인에 의존하지 않으며**, 표준적인 명령 실행 및 파일 입출력이 가능한 모든 AI 에이전트/어시스턴트 환경에서 범용적으로 동작하도록 설계되었습니다.
  * 단, 특정 에이전트 플랫폼이나 특정 개발 도구/IDE 전용의 부가 기능 및 환경 설정 가이드는 예외적으로 [`references/appendix.md`](./references/appendix.md)에서 분리하여 다룹니다.
* **구체적 경로 및 환경 비종속성 원칙**:
  * 프로젝트 내 공용 문서에는 **특정 머신의 로컬 절대 경로, 특정 사용자 디렉토리 경로, 하드코딩된 실행 경로 등을 명시하지 않습니다.**
  * 도구의 위치는 동적 탐색 또는 `data/path.txt`와 같은 설정 파일을 통해 참조하도록 추상화하여 관리합니다.
  * 단, 특정 머신에 종속적인 도구 실행 경로(Git 경로, Python venv 가상환경 등) 및 환경 노하우는 로컬의 `scratch/know-how.md`에 저장하고 적극 참조하여 활용합니다.
* **스킬 기반 모듈 아키텍처**:
  * 메인 워크플로우 및 실행 지침: [`SKILL.md`](./SKILL.md)
  * 상세 작업 흐름 (동기화, 재고 보충, 챗봇 지식): [`references/workflows.md`](./references/workflows.md)
  * CLI 가이드 및 API 명세: [`references/cli_guide.md`](./references/cli_guide.md)
  * 데이터 관리 원칙: [`references/data_management.md`](./references/data_management.md)
  * 전역 상수 및 설정 정의: [`references/constants.md`](./references/constants.md)
  * 데이터 작성 템플릿: [`references/templates.md`](./references/templates.md)
  * 부록 및 특정 환경 가이드: [`references/appendix.md`](./references/appendix.md)
* **디렉토리 구조 및 관리 원칙**:
  * 명시적으로 작성을 지시받지 않은 일회성 스크립트, 시스템 종속 노하우(`scratch/know-how.md`) 및 **작업 대기열 문서(`scratch/TODO.md`)**는 항상 `scratch/` 폴더에서 작성 및 관리합니다.
  * 시스템 운영으로 파생되는 모든 데이터 문서(캐릭터 정보, 재고 CSV 등)는 `data/` 폴더에 생성 및 관리합니다.
  * `data/`와 `scratch/` 폴더는 `.gitignore`에 등록하여 Git 버전 관리에 포함되지 않도록 합니다.
* **개인정보 보호 및 비식별화 원칙**:
  * **비식별화되지 않은 개인정보(사용자 실명, 개인 식별자, 계정 정보, 민감 데이터 등)는 절대 Git 등 버전 관리 시스템에 등재되지 않도록 철저히 관리**합니다.
  * 모든 인게임 캐릭터 데이터 및 운영 데이터는 버전 관리에서 제외된 `data/` 및 `scratch/` 영역 내에서만 안전하게 관리합니다.

* **문서 갱신 일시**: 2026년 10월 5일

