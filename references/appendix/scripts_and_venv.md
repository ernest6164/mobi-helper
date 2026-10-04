# 로컬 스크립트 및 Python venv 가상환경 활용 가이드

* **갱신 일시**: 2026년 10월 5일

AI 에이전트를 통해 텍스트나 데이터를 대량으로 직접 파싱하면 컨텍스트 토큰 소모량이 커질 수 있습니다. 이를 최적화하기 위해 로컬 스크립트 라이브러리와 Python venv 가상환경을 활용합니다.

---

## 1. 공용 스크립트 라이브러리(`scripts/`) 활용
* 데이터 동기화, 재고 계산, 자동 채집, 채팅 발화 등 공통 표준 기능은 `scripts/`에 구현된 공용 스크립트 라이브러리를 우선 활용합니다.
* 각 스크립트의 매개변수 및 사용법은 [`scripts/README.md`](../../scripts/README.md)를 참조합니다.

## 2. 개별 커스텀 스크립트(`scratch/`) 활용
* 일회성 실험, 특수 파싱 매크로, 개인화된 작업 코드는 `scripts/`를 복사하여 `scratch/` 디렉토리에서 자유롭게 변형하여 작성합니다.

## 3. Python venv 가상환경 필수 사용
* 로컬 Python 스크립트 실행 시 오염 방지 및 일관된 환경을 위해 반드시 프로젝트 내 **`venv` 가상환경(`python.exe`)**을 통해 실행합니다.
* 구체적인 인터프리터 경로 및 실행 방식은 `data/know-how.md` 및 `data/environments.json`([`references/environments.md`](../environments.md))을 참조합니다.
