# loc_bot

Telegram을 통해 로컬 Claude Code CLI를 원격 조종하는 봇.

PC에 설치된 Claude Code CLI를 Telegram 메시지로 제어하여, 어디서든 코드 작성/수정/리뷰를 할 수 있다.

## 주요 기능

- Telegram 메시지로 Claude Code CLI에 프롬프트 전달
- 실시간 스트리밍 출력 (Status Card + 큐)
- 다중 프로젝트 관리 (`/register`, `/use`, `/scan`)
- 이미지 첨부 지원 (스크린샷 → Claude에게 전달)
- 작업 히스토리 저장 (SQLite)
- 실수 로그 기록 및 검색
- 사용자 인증 (허용된 사용자만 사용 가능)

## 사전 요구사항

- **Python 3.12+**
- **Claude Code CLI** ([설치 가이드](https://docs.anthropic.com/en/docs/claude-code))
  - `claude` 명령어가 PATH에 있어야 함
- **Telegram Bot Token** ([BotFather](https://t.me/BotFather)에서 발급)

## 설치

```bash
# 1. 저장소 클론
git clone https://github.com/your-username/loc_bot.git
cd loc_bot

# 2. 가상환경 생성
python -m venv .venv

# 3. 의존성 설치
# pip 사용
pip install -r requirements.txt

# 또는 uv 사용
uv pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일을 열어서 값을 채워넣으세요
```

## 설정

`.env` 파일에 다음 값을 설정:

| 변수 | 필수 | 설명 |
|------|------|------|
| `TELEGRAM_BOT_TOKEN` | O | BotFather에서 발급받은 토큰 |
| `ALLOWED_USER_IDS` | O | 허용할 Telegram 사용자 ID (쉼표 구분) |
| `CLAUDE_CLI_PATH` | X | Claude Code CLI 경로 (기본: `claude`) |
| `WORKSPACE_ROOT` | X | 프로젝트 상위 폴더 (기본: `~/Desktop`) |
| `DB_PATH` | X | SQLite DB 경로 (기본: `data/loc_bot.db`) |

Telegram 사용자 ID는 [@userinfobot](https://t.me/userinfobot)으로 확인할 수 있습니다.

## 실행

```bash
python -m src.main
```

## 봇 명령어

| 명령어 | 설명 |
|--------|------|
| `/start` | 봇 시작 |
| `/help` | 도움말 |
| `/register <경로>` | 프로젝트 디렉토리 등록 |
| `/use` | 활성 프로젝트 변경 |
| `/projects` | 등록된 프로젝트 목록 |
| `/scan` | 워크스페이스 자동 스캔 |
| `/new` | 새 대화 시작 |
| `/status` | 실행 중인 작업 상태 |
| `/stop` | 현재 작업 중지 |
| `/stop_all` | 모든 작업 중지 |
| `/restart` | 봇 프로세스 재시작 |
| `/history` | 작업 히스토리 조회 |

프로젝트를 선택한 후, 일반 텍스트 메시지를 보내면 Claude Code CLI에 전달됩니다.

## 프로젝트 구조

```
loc_bot/
├── src/
│   ├── main.py            # 진입점
│   ├── bot/handlers.py    # Telegram 명령어 핸들러
│   ├── claude/executor.py # Claude Code CLI 래퍼
│   ├── projects/manager.py# 프로젝트 관리
│   ├── db/database.py     # DB 스키마
│   └── db/models.py       # CRUD 함수
├── config/settings.py     # 환경변수 설정
├── tests/                 # 테스트
├── .env.example           # 환경변수 예시
└── requirements.txt       # 의존성
```

## 테스트

```bash
python -m pytest tests/ -v
```

## 보안 주의사항

- `ALLOWED_USER_IDS`를 반드시 설정하세요. 미설정 시 아무도 봇을 사용할 수 없습니다.
- `.env` 파일을 절대 커밋하지 마세요 (`.gitignore`에 포함됨).
- 이 봇은 로컬 PC에서 Claude Code CLI를 실행합니다. `--dangerously-skip-permissions` 플래그를 사용하므로, 반드시 본인만 접근 가능하도록 설정하세요.

## License

MIT
