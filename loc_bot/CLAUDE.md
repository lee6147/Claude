# loc_bot

Telegram을 통해 로컬 Claude Code CLI를 원격 조종하는 봇. Desktop의 여러 프로젝트를 관리하며, AI 에이전트가 실제 개발을 수행한다.

## Core Flows

| 기능 | 핵심 파일 | 설명 |
|------|----------|------|
| 봇 진입점 | `src/main.py` | 앱 시작, 핸들러 등록 |
| Telegram 핸들러 | `src/bot/handlers.py` | 명령어 처리, 메시지 라우팅 |
| Claude Code 실행 | `src/claude/executor.py` | CLI 서브프로세스 실행 |
| 프로젝트 관리 | `src/projects/manager.py` | 프로젝트 등록/조회/스캔 |
| DB 스키마 | `src/db/database.py` | SQLite 테이블 정의 |
| DB 모델 | `src/db/models.py` | CRUD 쿼리 함수 |
| 설정 | `config/settings.py` | 환경변수 로드 |

## Development Commands

```bash
# 의존성 설치
pip install -r requirements.txt

# 봇 실행
python -m src.main

# 타입 체크
python -m mypy src/ --ignore-missing-imports

# 테스트
python -m pytest tests/
```

## Permissions

### 허용
- `src/` 내 모든 파일 수정
- `tests/` 내 테스트 파일 추가/수정
- `requirements.txt` 패키지 추가
- `config/settings.py` 설정 수정

### 금지
- `.env` 파일 직접 수정 (토큰 노출 위험)
- `data/` 디렉토리의 DB 파일 직접 조작
- `--dangerously-skip-permissions` 플래그 제거 금지 (봇 기능에 필수)
- 다른 Desktop 프로젝트 디렉토리 직접 수정 (Claude Code를 통해서만 접근)

## Codex 리뷰 워크플로 (코드 변경 시 필수)

> **절대 규칙 (최우선)**: 코드를 변경하면 — 커밋 여부와 무관하게 — 반드시 Codex 리뷰를 실행해야 한다.
> 코드 수정 → Codex 리뷰 → PASS 확인 → 그 다음에 커밋.
> Codex가 PASS 판정을 내려야만 커밋할 수 있다. FAIL 시 수정 후 재리뷰.
> **이 규칙은 어떤 상황에서도 건너뛸 수 없다. 사소한 수정도 예외 없음.**

```bash
# 1. 코드 작성 + 테스트 통과 확인
python -m pytest tests/ -v

# 2. Claude가 리뷰 요청 파일 작성
#    → .agents/claude/review-request-latest.md

# 3. Codex 실행 (비대화형)
codex exec --full-auto "Read .agents/claude/review-request-latest.md and review the changes. Write results to .agents/codex/"

# 4. 리뷰 결과 확인
#    → .agents/codex/review-result-*.md

# 5. PASS 시에만 커밋
```

### 빠른 실행: `/codex-review` 커스텀 명령어 사용

### 리뷰 디렉토리 구조
```
.agents/
├── claude/                     # Claude → Codex 리뷰 요청
│   ├── review-request-template.md
│   └── review-request-latest.md
└── codex/                      # Codex → 리뷰 결과
    └── review-result-*.md
```

## Architecture Notes

- **인증**: `ALLOWED_USER_IDS`로 허용된 사용자만 봇 사용 가능
- **실행 흐름**: Telegram 메시지 → handlers.py → executor.py → Claude Code CLI → 결과 반환
- **DB**: SQLite (aiosqlite), 프로젝트 목록 + 작업 히스토리 + 실수 로그 저장
- **보안**: 봇은 반드시 본인만 사용하도록 ALLOWED_USER_IDS 설정 필수
