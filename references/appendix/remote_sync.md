# 원격 저장소(GitHub 등) 연동 및 동기화 가이드

* **갱신 일시**: 2026년 10월 5일

로컬에서 관리 중인 프로젝트 설정과 문서들을 원격 저장소(GitHub, GitLab 등)에 백업하여 안전하게 동기화할 수 있습니다.

---

## 1. 원격 저장소 연결
* GitHub 등 원격 호스팅 서비스에서 신규 저장소를 생성한 후, 로컬 프로젝트와 원격 저장소 주소를 연결하고 기본 브랜치를 설정합니다.
  ```bash
  git remote add origin <저장소 URL>
  git branch -M main
  ```

## 2. 인증 및 동기화
* 브라우저 기반 인증(Git Credential Manager) 또는 개인 액세스 토큰(PAT, Personal Access Token)을 활용하여 원격 인증을 완료합니다.
* 커밋된 변경 사항을 원격 저장소로 안전하게 푸시하여 백업을 완료합니다.
  ```bash
  git push -u origin main
  ```
