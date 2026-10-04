# 템플릿: 시스템 및 환경 설정 (`environments.json`)

* **대상 파일**: `data/environments.json`
* **설명**: `MabinogiMobile_CLI.exe` 도구 경로, 가상환경, 기본 캐릭터/서버 및 전역 규칙을 정의하는 JSON 파일입니다. (상세 명세는 [`references/environments.md`](../environments.md) 참조)

---

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
