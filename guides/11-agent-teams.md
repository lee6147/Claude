# 가이드 11: 에이전트 팀

> AI 에이전트 여러 명을 동시에 투입해서 프로젝트를 병렬로 빌드하는 방법

## 핵심 원칙

> **역할 분리 + 파일 경계 = 충돌 없는 병렬 개발**

```
역할 1 → 파일 A, B     ← 서로 다른 파일만
역할 2 → 파일 C, D        건드리면 충돌 없음
역할 3 → 파일 E, F
```

## 왜 에이전트 팀인가

AI 에이전트 하나로 프로젝트를 만들면 한계가 있어요:

| 단일 에이전트 | 에이전트 팀 |
|--------------|------------|
| 컨텍스트 윈도우 한 개 | 에이전트별 독립 컨텍스트 |
| 순차 실행 (직렬) | 동시 실행 (병렬) |
| 파일이 많아지면 품질 저하 | 역할별 전문화로 품질 유지 |
| 30분에 5-8개 파일 | 30분에 20개 이상 파일 |

핵심은 **분업**이에요. 프론트엔드 아키텍트, 컴포넌트 엔지니어, 데이터 엔지니어처럼 역할을 나누면 각 에이전트가 자기 영역에만 집중해요.

## Step 1: 역할 분리 설계

에이전트 팀의 성패는 **역할 설계**에서 결정돼요.

### 규칙

1. **자기 파일만 건드린다** — 각 에이전트가 만드는 파일이 겹치면 안 돼요
2. **공유 인터페이스를 먼저 정의한다** — 타입, 데이터 구조는 한 에이전트가 먼저 만들어요
3. **의존성 방향은 단방향** — A→B는 OK, A↔B 양방향 의존은 피해요

### 예시: SaaS 대시보드 5인 팀

| 역할 | 담당 파일 | 의존성 |
|------|----------|--------|
| 프론트엔드 아키텍트 | layout.tsx, page.tsx, Sidebar, TopBar | 없음 (가장 먼저 시작) |
| 컴포넌트 엔지니어 | KPICard, ChartCard, DataTable | 아키텍트의 레이아웃 구조 |
| 페이지 빌더 | analytics, settings, help 페이지 | 컴포넌트 import |
| 데이터 엔지니어 | types, mock data, API 유틸 | 없음 (가장 먼저 시작) |
| UX 디자이너 | globals.css, 애니메이션, 반응형 | 컴포넌트 구조 |

**포인트:** 아키텍트와 데이터 에이전트를 먼저 시작하면, 나머지 에이전트가 그 결과물을 import할 수 있어요.

## Step 2: 프롬프트 파일 작성

각 에이전트에게 줄 프롬프트를 `.md` 파일로 작성해요.

### 프롬프트 구조

```markdown
You are a [역할]. [한 줄 미션].

## Your files (create ONLY these — do not touch any other files):

### src/components/KPICard.tsx
Props: title, value, change, icon. 카드 UI 설명.

### src/components/ChartCard.tsx
Props: title, data. 차트 UI 설명.

## Tech stack: Next.js 15 + React 19 + Tailwind CSS 4

Create all files now, in order: KPICard.tsx → ChartCard.tsx.
```

**핵심 패턴:**
- `"Your files (create ONLY these)"` — 이 문구가 파일 충돌을 방지해요
- 파일별로 `###` 헤더 + 구체적 스펙
- 마지막에 실행 순서 지시

### 디렉토리 구조

```
prompts/
├── 01-layout.md        # 프론트엔드 아키텍트
├── 02-components.md    # 컴포넌트 엔지니어
├── 03-pages.md         # 페이지 빌더
├── 04-data.md          # 데이터 엔지니어
└── 05-styles.md        # UX 디자이너
```

파일명의 숫자 접두사(`01-`, `02-`)는 정렬용이에요. 실행 순서와는 무관하고, 모든 에이전트는 동시에 시작해요.

## Step 3: 실행

### 자동 실행 (run-agent-team.sh)

```bash
# 미리보기 — 에이전트 구성과 레이아웃 확인
./templates/run-agent-team.sh prompts/ --dry

# 실행 — tmux 세션에서 에이전트 5개 동시 시작
./templates/run-agent-team.sh prompts/
```

`--dry` 플래그로 먼저 확인하는 걸 추천해요:

```
=== Agents (5) ===

  [1] layout — 22 lines (prompts/01-layout.md)
  [2] components — 18 lines (prompts/02-components.md)
  [3] pages — 15 lines (prompts/03-pages.md)
  [4] data — 20 lines (prompts/04-data.md)
  [5] styles — 16 lines (prompts/05-styles.md)

=== Layout ===

  ┌────────────┬─────────────┬────────────┐
  │   layout   │  components │   pages    │
  ├─────────────┴──────┬──────┴────────────┤
  │       data         │      styles       │
  └────────────────────┴────────────────────┘
```

### 수동 실행 (tmux 직접)

스크립트 없이 직접 하려면:

```bash
# 1. tmux 세션 생성
tmux new-session -d -s team

# 2. 패널 분할
tmux split-window -h -t team
tmux split-window -v -t team:0.0

# 3. 각 패널에서 Claude Code 실행
tmux send-keys -t team:0.0 "claude" Enter
tmux send-keys -t team:0.1 "claude" Enter
tmux send-keys -t team:0.2 "claude" Enter

# 4. 접속
tmux attach -t team
```

### 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `CLAUDE_MODEL` | `sonnet` | 사용할 모델 |
| `TMUX_SESSION` | `agent-team` | tmux 세션 이름 |
| `AGENT_DELAY` | `5` | 에이전트 간 시작 간격 (초) |
| `WORK_DIR` | `./output` | 작업 디렉토리 |

```bash
# 예: opus 모델로 실행
CLAUDE_MODEL=opus ./templates/run-agent-team.sh prompts/
```

## Step 4: 모니터링 & 개입

### tmux 단축키

| 단축키 | 동작 |
|--------|------|
| `Ctrl+B` → `화살표` | 패널 이동 |
| `Ctrl+B` → `z` | 현재 패널 전체화면 토글 |
| `Ctrl+B` → `d` | 디태치 (에이전트는 계속 실행) |
| `tmux attach -t agent-team` | 다시 접속 |

### 개입이 필요한 순간

- **권한 요청이 뜨면** — 해당 패널로 이동해서 승인
- **에러가 반복되면** — 해당 에이전트를 중단하고 프롬프트 수정 후 재시작
- **파일 충돌이 보이면** — 두 에이전트 모두 중단, 역할 경계 재설정

## 실전 팁

### 시작 순서 전략

데이터/타입 에이전트를 먼저 시작하세요. 다른 에이전트가 import할 타입과 목 데이터가 먼저 준비되면 충돌이 줄어들어요.

```bash
# AGENT_DELAY를 넉넉하게 (데이터 에이전트가 먼저 파일 생성할 시간)
AGENT_DELAY=10 ./templates/run-agent-team.sh prompts/
```

### 에이전트 수 가이드

| 에이전트 수 | 적합한 상황 |
|------------|------------|
| 2-3개 | 소규모 기능 (API + 프론트엔드) |
| 4-5개 | 풀스택 앱 (레이아웃 + 컴포넌트 + 페이지 + 데이터 + 스타일) |
| 6개 이상 | 비용/속도 주의. 대부분 5개면 충분 |

### 비용 참고

- 에이전트 5개 × 30분 = 단일 에이전트 150분 분량의 API 호출
- Claude Pro/Max 구독이면 동시 세션 가능
- API 사용 시 병렬 호출 비용 확인

### 적용 사례

| 사례 | 에이전트 구성 |
|------|-------------|
| SaaS 대시보드 | 아키텍트 + 컴포넌트 + 페이지 + 데이터 + UX |
| API + 프론트엔드 | API 엔지니어 + 프론트엔드 + 테스트 |
| 리팩토링 | 테스트 작성 + 코드 변경 + 문서 업데이트 |
| 모노레포 | 패키지 A + 패키지 B + 공유 라이브러리 |

## 체크리스트

```
□ 역할별 담당 파일 리스트 작성
□ 파일 충돌 없는지 확인 (겹치는 파일 없어야 함)
□ 공유 인터페이스/타입 먼저 정의
□ "Your files (create ONLY these)" 패턴 적용
□ run-agent-team.sh --dry로 레이아웃 확인
□ 데이터 에이전트를 가장 먼저 시작
□ 실행 후 빌드 테스트
```

---

📮 영상에서 사용한 에이전트 팀 프롬프트 5개를 받아보세요 → [maily.so/tenbuilder](https://maily.so/tenbuilder)
