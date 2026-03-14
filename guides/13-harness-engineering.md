# 가이드 13: 하네스 엔지니어링

> 프롬프트를 잘 쓰는 것만으로는 부족해요 — AI 코딩 에이전트가 일하는 '환경' 자체를 설계하는 실전 가이드

## 소요 시간

25-35분

## 사전 준비

- AI 코딩 도구 사용 경험 (Claude Code, Cursor, Copilot 등)
- 기본적인 CI/CD 개념 이해
- 프로젝트 하나 이상 운영 경험

## 하네스 엔지니어링이 뭔가요?

프롬프트 엔지니어링은 "모델에게 뭘 시킬까"에 집중해요. 하네스 엔지니어링은 한 발 더 나아가서 "모델이 일하는 환경을 어떻게 만들까"를 다뤄요.

말(horse) 비유로 생각하면 이해가 쉬워요. 아무리 빠르고 힘센 말이라도, 마구(harness) 없이는 방향을 잡을 수 없어요. AI 에이전트도 마찬가지예요 — 모델이 아무리 똑똑해도, 실행 환경이 엉망이면 결과물도 엉망이에요.

```
┌─────────────────────────────────────┐
│          하네스 (Harness)           │
│                                     │
│  ┌───────────┐  ┌───────────────┐  │
│  │   Model   │  │   Surfaces    │  │
│  │ (AI 모델) │  │ (도구/인터페이스) │  │
│  └─────┬─────┘  └───────┬───────┘  │
│        │                │          │
│  ┌─────▼────────────────▼───────┐  │
│  │     Feedback Loops           │  │
│  │  (테스트, 린터, CI, 로그)    │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## 핵심 구조: Model + Harness + Surfaces

| 구성요소 | 역할 | 예시 |
|----------|------|------|
| **Model** | 코드를 생성하는 AI | Claude, GPT, Codex |
| **Harness** | 에이전트의 실행 환경 전체 | 문서, 린터, CI, 테스트, 격리 환경 |
| **Surfaces** | 에이전트가 접근하는 도구와 인터페이스 | 터미널, 파일시스템, API, 브라우저 |

핵심 인사이트: **에이전트의 성능은 모델 능력 × 하네스 품질**이에요. 모델을 바꾸지 않아도, 하네스를 개선하면 결과가 확 달라져요.

## Step 1: 문서 구조 설계

에이전트는 코드를 읽기 전에 문서를 먼저 읽어요. 그래서 프로젝트 문서가 곧 에이전트의 "지도"예요.

```markdown
# AGENTS.md (프로젝트 루트)

## 프로젝트 개요
- 기술 스택: Next.js 15 + TypeScript + Supabase
- 아키텍처: App Router, Server Components 우선

## 디렉토리 규칙
- /src/app → 페이지 라우팅
- /src/lib → 공유 유틸리티
- /src/components → UI 컴포넌트

## 코딩 컨벤션
- 함수 컴포넌트만 사용
- Zod로 모든 외부 입력 검증
- 에러는 Result 패턴으로 처리
```

**문서 작성 팁:**

| 원칙 | 설명 |
|------|------|
| 명령형으로 작성 | "~할 수 있다" 대신 "~하세요" |
| 경로는 절대경로 | 상대경로는 에이전트가 헷갈림 |
| 주기적으로 정리 | 오래된 문서는 과감히 삭제 |
| 진입점은 하나 | `AGENTS.md` → 세부 문서 링크 |

## Step 2: 기계적 제약 설정

에이전트는 "규칙을 지켜주세요"라고 말해도 까먹어요. 대신 **기계적으로 강제**하세요.

```json
// .eslintrc.json — 아키텍처 경계 강제
{
  "rules": {
    "import/no-restricted-paths": ["error", {
      "zones": [{
        "target": "./src/components",
        "from": "./src/app",
        "message": "컴포넌트에서 페이지 모듈을 임포트하지 마세요"
      }]
    }]
  }
}
```

```yaml
# .github/workflows/ci.yml — PR마다 자동 검증
name: Agent Guard
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run lint        # 컨벤션 체크
      - run: npm run typecheck   # 타입 안전성
      - run: npm test            # 기능 검증
      - run: npm run build       # 빌드 가능 여부
```

**왜 기계적 제약이 중요한가요?**

에이전트가 코드를 생성하면 사람보다 훨씬 빠르게 패턴이 퍼져요. 잘못된 패턴 하나가 10개, 100개 파일로 복제되기 전에 CI에서 잡아야 해요.

## Step 3: 피드백 루프 구축

에이전트가 "내가 잘하고 있는지" 스스로 확인할 수 있는 루프를 만들어주세요.

```bash
# 테스트 주도 피드백 루프 예시
claude "이 함수에 대한 테스트를 먼저 작성하고,
테스트가 통과할 때까지 구현을 반복해줘.
매 시도마다 npm test 결과를 확인해"
```

효과적인 피드백 루프의 3가지 조건:

| 조건 | 설명 | 구현 방법 |
|------|------|----------|
| **빠른 감지** | 문제를 즉시 발견 | 테스트, 린터, 타입 체크 |
| **명확한 신호** | 뭐가 틀렸는지 알려줌 | 구조화된 에러 메시지 |
| **저렴한 롤백** | 쉽게 되돌림 | Git 브랜치, 스냅샷 |

## Step 4: 워크트리 격리

여러 에이전트가 동시에 작업할 때, 서로 간섭하면 안 돼요.

```bash
# Git worktree로 에이전트별 작업 공간 분리
git worktree add ../feature-auth feature/auth
git worktree add ../feature-dashboard feature/dashboard

# 각 worktree에서 독립적으로 에이전트 실행
cd ../feature-auth && claude "인증 모듈을 구현해줘"
cd ../feature-dashboard && claude "대시보드 페이지를 만들어줘"
```

| 격리 방식 | 장점 | 단점 |
|----------|------|------|
| Git worktree | 빠르고 가벼움 | 같은 레포 제한 |
| Docker 컨테이너 | 완전한 격리 | 초기 셋업 비용 |
| 브랜치만 분리 | 가장 간단함 | 로컬 파일 충돌 가능 |

## Step 5: 관찰 가능성 확보

에이전트가 뭘 하고 있는지 투명하게 보여야 해요.

```typescript
// 구조화된 로깅 — 에이전트도 읽을 수 있는 형태
import { logger } from './lib/logger';

export function processOrder(order: Order) {
  logger.info('order.process.start', {
    orderId: order.id,
    items: order.items.length,
    total: order.total
  });
  
  // ... 처리 로직
  
  logger.info('order.process.complete', {
    orderId: order.id,
    duration: Date.now() - start
  });
}
```

**관찰 가능성 체크리스트:**

- [ ] 구조화된 로그 (JSON 형태)
- [ ] 에러에 컨텍스트 포함 (어떤 요청에서, 어떤 데이터로)
- [ ] 메트릭 수집 (응답 시간, 에러율)
- [ ] 트레이스 연결 (요청 → 처리 → 응답 추적)

## Step 6: 장기 실행 에이전트 관리

큰 프로젝트에서는 에이전트가 여러 세션에 걸쳐 작업해요. 이때 "세션 간 기억"을 관리하는 게 핵심이에요.

```markdown
# TODO.md — 에이전트 간 인수인계 문서

## 완료된 작업
- [x] 인증 모듈 구현 (JWT + Refresh Token)
- [x] 사용자 프로필 API

## 현재 진행 중
- [ ] 대시보드 차트 컴포넌트 ← 지금 여기

## 다음 할 일
- [ ] 알림 시스템
- [ ] 결제 연동

## 주의사항
- Supabase RLS 정책이 아직 미적용 상태
- chart 라이브러리는 recharts 사용 (D3 아님)
```

이 패턴의 핵심은:
1. **첫 번째 에이전트**: 전체 계획을 세우고 TODO.md를 생성
2. **이후 에이전트**: TODO.md를 읽고 다음 작업을 이어서 진행
3. **매 세션 종료 시**: TODO.md를 업데이트하고 종료

## 최소 실행 가능 하네스 (MVH) 체크리스트

프로젝트에 바로 적용할 수 있는 최소 구성이에요.

| 항목 | 파일/설정 | 우선순위 |
|------|----------|---------|
| 진입 문서 | `AGENTS.md` 또는 `CLAUDE.md` | 필수 |
| 원커맨드 환경 | `docker compose up` 또는 `npm run dev` | 필수 |
| 기계적 검증 | ESLint + TypeScript + CI | 필수 |
| 테스트 루프 | `npm test` (에이전트가 직접 실행) | 필수 |
| 워크트리 격리 | Git worktree 또는 Docker | 권장 |
| 구조화된 로그 | JSON 로깅 + 트레이스 | 권장 |
| 세션 인수인계 | `TODO.md` 또는 상태 파일 | 선택 |

## 흔한 실수와 해결

| 실수 | 왜 문제인가 | 해결 |
|------|-----------|------|
| 문서 없이 시작 | 에이전트가 추측으로 코딩 | AGENTS.md 먼저 작성 |
| 린터 없이 운영 | 잘못된 패턴이 빠르게 퍼짐 | CI에 린트 필수 포함 |
| 하나의 긴 프롬프트 | 컨텍스트 초과로 품질 저하 | 태스크를 작게 분할 |
| 결과만 확인 | 과정에서 문제 놓침 | 구조화된 로그 + 트레이스 |
| 수동 리뷰에 의존 | 사람 시간이 병목 | 자동 검증 후 예외만 리뷰 |

## 다음 단계

하네스 엔지니어링은 "AI에게 코딩을 시키는 기술"에서 "AI가 잘 코딩할 수 있는 시스템을 만드는 기술"로의 전환이에요. 프롬프트를 다듬는 데 쓰는 시간의 절반을 하네스 개선에 투자하면, 훨씬 안정적인 결과를 얻을 수 있어요.

→ [에이전틱 코딩 치트시트](../cheatsheets/agentic-coding-cheatsheet.md)
→ [AI 에이전트 A-Z 에피소드](../episodes/EP03-ai-agent-az/README.md)
→ [모노레포 + AI 워크플로우](../workflows/monorepo-ai-workflow.md)

---

**더 자세한 가이드:** [claude-code/playbooks](../claude-code/playbooks/)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
