# 시스템 종속 환경 설정 및 노하우 관리 가이드

* **갱신 일시**: 2026년 10월 5일

본 프로젝트는 머신/사용자 환경에 종속적인 설정과 시스템 노하우를 분리하여 관리합니다.

---

## 1. `data/environments.json`
* 로컬 머신 및 사용자 고유의 실행 경로(`cli`, `pythonVenv`, `git` 등)와 기본 인게임 환경 설정값을 단일 JSON으로 통합 관리합니다.
* 구조 및 상세 명세는 [`references/environments.md`](../environments.md) 및 [`references/templates/environments_json.md`](../templates/environments_json.md)를 참조합니다.

## 2. `data/know-how.md`
* 시스템 종속적인 도구 사용 노하우, 문제 해결 팁, 배치 파일 실행법 등을 관리합니다.

## 3. 공용 저장소 비종속 및 데이터 관리 원칙
* 생성이 명시된 모든 문서는 `data/` 디렉토리에서 일괄 관리되며, `.gitignore`를 통해 비식별 개인정보 및 로컬 환경이 안전하게 보호됩니다. (상세 내용은 [`references/data_management.md`](../data_management.md) 참조)
