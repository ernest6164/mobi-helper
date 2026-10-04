# 사용자 및 시스템 환경 설정 정의서 (Environments Specification)

* **최종 갱신 일시**: 2026-10-05
* **연계 설정 파일**: [`data/environments.json`](../data/environments.json)
* **관리 원칙**:
  * 마비노기 모바일 헬퍼의 모든 시스템 실행 경로, 계정 환경, 채팅 및 재고 관리 기본 설정값은 `data/environments.json` 파일에서 단일 통합 관리합니다.
  * 본 문서는 `data/environments.json`의 스키마 구조, 각 설정 필드의 정의 및 기본값을 설명하는 표준 레퍼런스 문서입니다.
  * 공용 스크립트(`scripts/`) 및 AI 에이전트는 본 문서의 스키마에 따라 `data/environments.json`으로부터 환경값을 동적으로 로드합니다.

---

## 1. `data/environments.json` 스키마 및 구조 정의

```json
{
  "paths": {
    "cli": "C:\\Nexon\\MabinogiMobile\\MabinogiMobile_CLI.exe",
    "pythonVenv": ".venv\\Scripts\\python.exe",
    "git": "C:\\Program Files\\Git\\cmd\\git.exe",
    "dataDir": "data",
    "scriptsDir": "scripts"
  },
  "inGame": {
    "defaultServer": "던컨",
    "activeCharacter": "Saki"
  },
  "chatSettings": {
    "maxLength": 50,
    "defaultMaxChunks": 3,
    "rateLimitSeconds": 2.5
  },
  "stockSettings": {
    "otherCharStockThreshold": 10,
    "priorityOrder": "bottom-up"
  }
}
```

---

## 2. 세부 필드 명세

### 1) `paths` (실행 및 디렉토리 경로)
| 필드명 | 타입 | 기본 예시값 | 설명 |
| :--- | :---: | :--- | :--- |
| `cli` | `string` | `C:\Nexon\MabinogiMobile\MabinogiMobile_CLI.exe` | 마비노기 모바일 AI 커넥터 CLI 실행 파일 절대 경로 |
| `pythonVenv` | `string` | `.venv\Scripts\python.exe` | 프로젝트 전용 Python 가상환경 인터프리터 경로 |
| `git` | `string` | `C:\Program Files\Git\cmd\git.exe` | 로컬 Git 버전 관리 도구 실행 절대 경로 |
| `dataDir` | `string` | `data` | 시스템 운영 데이터 및 명시적 관리 문서 디렉토리 |
| `scriptsDir` | `string` | `scripts` | 공용 스크립트 라이브러리 디렉토리 |

### 2) `inGame` (인게임 기본 계정/서버 설정)
| 필드명 | 타입 | 기본 예시값 | 설명 |
| :--- | :---: | :--- | :--- |
| `defaultServer` | `string` | `"던컨"` | 기본 활동 서버명 |
| `activeCharacter` | `string` | `"Saki"` | 현재 접속 및 작업 기준 활성 캐릭터명 |

### 3) `chatSettings` (인게임 채팅 전송 규칙)
| 필드명 | 타입 | 기본 예시값 | 설명 |
| :--- | :---: | :--- | :--- |
| `maxLength` | `number` | `50` | 1회 발화 최대 글자 수 (`MAX_CHAT_LENGTH`) |
| `defaultMaxChunks` | `number` | `3` | 일반 지식/공략 전달 시 기본 최대 청크 수 (`DEFAULT_MAX_CHAT_CHUNKS`) |
| `rateLimitSeconds` | `number` | `2.5` | 연속 채팅 전송 간 대기 쿨다운 시간(초) (`CHAT_RATE_LIMIT_SECONDS`) |

### 4) `stockSettings` (재고 및 채집 관리 규칙)
| 필드명 | 타입 | 기본 예시값 | 설명 |
| :--- | :---: | :--- | :--- |
| `otherCharStockThreshold` | `number` | `10` | 타 캐릭터 보유 시 채집 보류 판정 임계치 (개) |
| `priorityOrder` | `string` | `"bottom-up"` | `target.md` 목표 채집물 우선순위 정렬 방식 (`bottom-up` / `top-down`) |

---

## 3. 관리 및 활용 지침

1. **단일 진실 공급원(Single Source of Truth)**:
   * 도구 경로 변경, 기본 캐릭터 변경 등의 환경 변경 사항은 항상 `data/environments.json`에 최신으로 반영합니다.
2. **스크립트 우선 참조**:
   * 모든 공용 스크립트는 `data/environments.json`의 `paths.cli`를 최우선으로 읽어 CLI 경로를 탐색합니다.
