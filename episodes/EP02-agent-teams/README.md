# EP02: 에이전트 팀즈 — AI 여러 명이 동시에 코딩하면 어떻게 될까?

> Claude Code의 멀티 에이전트 기능을 사용해 프로젝트를 병렬로 개발하는 실전 코드와 설정

## 📺 영상

**[YouTube에서 보기](https://youtube.com/@ten-builder)**

## 이 에피소드에서 다루는 것

- 에이전트 팀즈가 뭔지, 왜 혼자 코딩하는 것보다 빠른지
- tmux로 여러 Claude Code 에이전트를 동시에 띄우는 방법
- 역할 분담 프롬프트를 설계하는 실전 패턴
- 에이전트끼리 충돌 없이 협업하는 구조 만들기

## 에이전트 팀즈란?

하나의 프로젝트에 여러 AI 에이전트를 동시에 투입하는 방식이에요. 프론트엔드 담당, 백엔드 담당, 테스트 담당 — 이렇게 역할을 나눠서 병렬로 작업하면 개발 속도가 확 올라가요.

핵심 아이디어는 간단해요:

> "한 명이 순서대로 하면 30분, 세 명이 나눠서 하면 10분"

Claude Code는 `--model` 옵션과 프롬프트 파일을 조합해서 각 에이전트에 서로 다른 역할을 줄 수 있어요.

## 사전 준비

- Claude Code 설치: `npm install -g @anthropic-ai/claude-code`
- tmux 설치: `brew install tmux`
- Anthropic API 키 설정 완료

## 핵심 코드 & 설정

### 프로젝트 구조

```
my-project/
├── CLAUDE.md              # 전체 프로젝트 컨텍스트
├── prompts/
│   ├── 01-frontend.md     # 프론트엔드 에이전트 역할
│   ├── 02-backend.md      # 백엔드 에이전트 역할
│   └── 03-testing.md      # 테스트 에이전트 역할
└── run-agent-team.sh      # 팀 실행 스크립트
```

### 역할 프롬프트 작성하기

에이전트마다 **담당 영역**과 **건드리면 안 되는 영역**을 명확히 정해야 해요.

#### `prompts/01-frontend.md`

```markdown
# 프론트엔드 에이전트

## 담당 범위
- src/components/ 디렉토리의 모든 React 컴포넌트
- src/pages/ 디렉토리의 페이지 컴포넌트
- src/styles/ 디렉토리의 CSS/Tailwind 설정

## 금지 영역
- src/api/ 디렉토리는 절대 수정하지 마세요
- database/ 디렉토리에 접근하지 마세요

## 작업 지시
1. 할 일 목록 페이지를 만들어줘 (src/pages/TodoList.tsx)
2. 할 일 카드 컴포넌트를 만들어줘 (src/components/TodoCard.tsx)
3. 다크 모드 토글 버튼을 추가해줘
```

#### `prompts/02-backend.md`

```markdown
# 백엔드 에이전트

## 담당 범위
- src/api/ 디렉토리의 모든 API 라우트
- database/ 디렉토리의 스키마와 마이그레이션

## 금지 영역
- src/components/ 디렉토리는 절대 수정하지 마세요
- src/pages/ 디렉토리에 접근하지 마세요

## 작업 지시
1. Todo CRUD API를 만들어줘 (src/api/todos.ts)
2. SQLite 스키마를 정의해줘 (database/schema.sql)
3. API 응답은 항상 { data, error, status } 형태로 통일해줘
```

#### `prompts/03-testing.md`

```markdown
# 테스트 에이전트

## 담당 범위
- tests/ 디렉토리의 모든 테스트 파일
- jest.config.ts 설정

## 금지 영역
- src/ 디렉토리의 소스 코드를 직접 수정하지 마세요

## 작업 지시
1. 다른 에이전트가 작성한 코드의 테스트를 작성해줘
2. 10초 간격으로 src/ 디렉토리 변경을 감시하고, 새 파일이 생기면 테스트를 추가해줘
3. 테스트 커버리지가 80% 이상이 되도록 해줘
```

### 팀 실행 스크립트

tmux를 사용해서 여러 에이전트를 한 화면에 띄울 수 있어요.

```bash
# 기본 실행 (3개 에이전트 동시 시작)
./run-agent-team.sh prompts/

# 미리보기만 (실제 실행 안 함)
./run-agent-team.sh prompts/ --dry

# 권한 확인 건너뛰기 (자동화용)
./run-agent-team.sh prompts/ --skip-perms
```

실행하면 이런 레이아웃이 만들어져요:

```
┌─────────────────┬──────────────────┐
│   frontend      │   backend        │
├─────────────────┴──────────────────┤
│              testing               │
└────────────────────────────────────┘
```

### 수동으로 에이전트 팀 구성하기

스크립트 없이 tmux만으로도 가능해요.

```bash
# 1. tmux 세션 생성
tmux new-session -s agent-team

# 2. 화면 분할
tmux split-window -h          # 좌우 분할
tmux split-window -v          # 아래쪽 추가 분할

# 3. 각 패널에서 에이전트 실행
# 패널 0 (좌측)
claude "Read prompts/01-frontend.md and execute all instructions."

# 패널 1 (우측) — Ctrl+B → 화살표로 이동
claude "Read prompts/02-backend.md and execute all instructions."

# 패널 2 (하단) — Ctrl+B → 화살표로 이동  
claude "Read prompts/03-testing.md and execute all instructions."
```

## 충돌 방지 전략

여러 에이전트가 같은 파일을 동시에 수정하면 문제가 생겨요. 이걸 방지하는 패턴이에요.

| 전략 | 설명 | 적용 시점 |
|------|------|----------|
| 디렉토리 격리 | 에이전트마다 담당 폴더를 분리 | 항상 |
| 금지 영역 명시 | 프롬프트에 "이 폴더는 수정 금지" 기재 | 항상 |
| 인터페이스 먼저 | 공통 타입/API 스펙을 먼저 정의하고 시작 | 프로젝트 초기 |
| 순차 실행 | 의존성 있는 작업은 순서대로 (백엔드 → 프론트엔드) | 의존성이 강할 때 |

## CLAUDE.md 공유 컨텍스트

모든 에이전트가 참조하는 프로젝트 설정 파일이에요. 공통 규칙을 여기에 넣으면 에이전트끼리 일관된 코드를 작성해요.

```markdown
# 프로젝트: Todo App

## 기술 스택
- React 19 + TypeScript
- Tailwind CSS v4
- SQLite + Drizzle ORM
- Vitest for testing

## 코딩 컨벤션
- 함수형 컴포넌트만 사용
- 변수명은 camelCase
- API 응답 타입은 src/types/api.ts에 정의
- 에러 처리는 try-catch + 사용자 친화적 메시지

## 디렉토리 규칙
- 각 에이전트는 자신의 담당 디렉토리만 수정할 것
- 공통 타입은 src/types/에 정의하고, 읽기만 허용
```

## 유용한 tmux 단축키

| 단축키 | 기능 |
|--------|------|
| `Ctrl+B` → 화살표 | 패널 간 이동 |
| `Ctrl+B` → `z` | 현재 패널 확대/축소 |
| `Ctrl+B` → `d` | 세션 분리 (에이전트는 계속 실행) |
| `tmux attach -t agent-team` | 분리된 세션 다시 연결 |
| `Ctrl+B` → `[` | 스크롤 모드 (위로 올려서 로그 확인) |

## 실전 팁

### 에이전트 수는 3~5개가 적당해요

너무 많으면 API 속도 제한에 걸리고, 파일 충돌 가능성도 올라가요. 3개로 시작해서 익숙해지면 5개까지 늘려보세요.

### CLAUDE.md에 "절대 규칙"을 넣어두세요

각 에이전트가 프로젝트 전체 규칙을 알고 있어야 일관된 코드가 나와요. 특히 타입 정의와 네이밍 컨벤션은 필수예요.

### 테스트 에이전트는 마지막에 실행해도 괜찮아요

프론트엔드/백엔드 에이전트가 코드를 어느 정도 작성한 뒤에 테스트 에이전트를 투입하면 더 효과적이에요. `AGENT_DELAY` 환경 변수로 시작 시간을 조절할 수 있어요.

## 더 알아보기

- [run-agent-team.sh 스크립트](../../episodes/ep5-agent-teams-with-tmux/run-agent-team.sh) — 레포에 포함된 실행 스크립트
- [Claude Code 공식 문서](https://docs.anthropic.com/en/docs/claude-code) — Agent Teams 상세 설정
- [VS Code 멀티 에이전트 개발 가이드](https://code.visualstudio.com/blogs/2026/02/05/multi-agent-development) — VS Code 환경에서의 멀티 에이전트 패턴

---

**구독하기:** [@ten-builder](https://youtube.com/@ten-builder) | [뉴스레터](https://maily.so/tenbuilder)
