# 플레이북 12: 컨텍스트 관리

> AI 코딩 도구의 컨텍스트 윈도우를 효과적으로 관리하는 실전 가이드

## 언제 쓰나요?

- 프로젝트가 커져서 AI가 파일을 다 읽지 못할 때
- "컨텍스트가 너무 길다"는 에러가 자주 나올 때
- AI에게 정확한 코드를 생성하게 하고 싶은데 엉뚱한 결과가 나올 때
- 모노레포나 대규모 코드베이스에서 AI 도구를 쓰기 시작할 때

## 소요 시간

15-25분

## 사전 준비

- AI 코딩 도구 설치 (Claude Code, Cursor, Copilot 등)
- 관리할 프로젝트 코드베이스
- (선택) `.claudeignore` 또는 `.cursorignore` 설정 파일

## Step 1: 컨텍스트 예산 파악하기

AI 도구마다 한 번에 처리할 수 있는 토큰 수가 다릅니다. 먼저 내 도구의 한계를 알아야 해요.

| 도구 | 컨텍스트 윈도우 | 실질 사용 가능 |
|------|----------------|---------------|
| Claude Code (Sonnet 4) | 200K 토큰 | ~150K (시스템 프롬프트 제외) |
| Claude Code (Opus 4) | 200K 토큰 | ~150K |
| Cursor | 모델별 상이 | Tab: ~10K, Chat: ~60K |
| GitHub Copilot | ~8K 토큰 | ~6K (자동 완성 기준) |

```bash
# 프로젝트의 대략적인 토큰 수 확인 (1토큰 ≈ 4글자 기준)
find src/ -name '*.ts' -o -name '*.tsx' | xargs wc -c | tail -1
# 결과를 4로 나누면 대략적인 토큰 수
```

> **팁:** 전체 코드베이스를 한번에 넣을 필요는 없어요. 작업에 필요한 파일만 선별하는 게 핵심입니다.

## Step 2: 불필요한 파일 제외하기

AI가 읽을 필요 없는 파일을 미리 제외하면 토큰을 크게 절약할 수 있어요.

### `.claudeignore` 설정

```gitignore
# 빌드 산출물
dist/
build/
.next/
node_modules/

# 자동 생성 파일
*.lock
package-lock.json
yarn.lock

# 미디어/바이너리
*.png
*.jpg
*.svg
*.woff2

# 테스트 스냅샷
__snapshots__/
*.snap

# 대용량 데이터
fixtures/
seed-data/
```

### Cursor `.cursorignore`

```gitignore
# 동일한 패턴 적용
node_modules/
dist/
*.lock
__snapshots__/
```

| 제외 대상 | 이유 | 절약 효과 |
|-----------|------|----------|
| `node_modules/` | 외부 라이브러리, AI가 읽을 필요 없음 | 수십만 토큰 |
| `*.lock` | 의존성 잠금 파일, 사람이 수정하지 않음 | 수만 토큰 |
| `dist/`, `build/` | 빌드 산출물, 소스와 중복 | 수만 토큰 |
| `__snapshots__/` | 테스트 스냅샷, 자동 생성 | 수천~수만 토큰 |

## Step 3: 컨텍스트 프론트로딩

AI에게 작업을 요청할 때, 가장 중요한 정보를 맨 앞에 배치하세요.

```bash
# ❌ 비효율적: 모든 파일을 열고 "수정해줘"
claude "src/ 디렉토리의 모든 파일을 읽고 버그를 찾아줘"

# ✅ 효과적: 핵심 파일을 명시하고 구체적으로 요청
claude "다음 파일을 참고해서 UserService의 인증 버그를 수정해줘:
1. src/services/user-service.ts (메인 로직)
2. src/types/user.ts (타입 정의)
3. src/middleware/auth.ts (인증 미들웨어)
에러: 토큰 만료 시 401 대신 500이 반환됨"
```

### CLAUDE.md로 프로젝트 맵 만들기

프로젝트 루트에 `CLAUDE.md`를 만들어두면 AI가 매번 전체 구조를 스캔하지 않아도 돼요.

```markdown
# 프로젝트 구조

## 핵심 디렉토리
- `src/api/` — REST API 엔드포인트
- `src/services/` — 비즈니스 로직
- `src/models/` — DB 모델 (Prisma)
- `src/utils/` — 유틸리티 함수

## 자주 수정하는 파일
- `src/api/routes.ts` — 라우팅 설정
- `src/services/auth.ts` — 인증 로직
- `prisma/schema.prisma` — DB 스키마

## 코딩 컨벤션
- TypeScript strict mode
- 함수형 패턴 선호 (class 사용 최소화)
- 에러는 Result 타입으로 처리
```

## Step 4: 청킹 전략

대규모 작업은 한 번에 하지 말고, 단계별로 나눠서 진행하세요.

```bash
# ❌ 한 번에 모든 것을 요청
claude "전체 프로젝트를 TypeScript로 마이그레이션해줘"

# ✅ 파일/모듈 단위로 나눠서 요청
claude "src/utils/format.js를 TypeScript로 변환해줘.
기존 테스트 src/utils/__tests__/format.test.js가 통과하도록 해줘"

# 다음 파일로 이동
claude "src/utils/validate.js를 TypeScript로 변환해줘.
방금 변환한 format.ts의 패턴을 따라줘"
```

| 전략 | 적합한 상황 | 주의점 |
|------|------------|--------|
| 파일 단위 | 마이그레이션, 리팩토링 | 파일 간 의존성 순서 주의 |
| 기능 단위 | 새 기능 추가 | 인터페이스 먼저 정의 |
| 레이어 단위 | 아키텍처 변경 | 하위 레이어부터 시작 |
| 테스트 단위 | 테스트 추가 | 핵심 경로부터 시작 |

## Step 5: 컨텍스트 리프레시

긴 대화에서는 AI의 컨텍스트가 흐려질 수 있어요. 적절한 시점에 리프레시하세요.

```bash
# 긴 작업 중간에 컨텍스트 정리
claude "지금까지 한 작업을 정리해줘:
1. 어떤 파일을 수정했는지
2. 남은 작업이 뭔지
3. 다음에 할 일"

# 새 세션에서 이어가기
claude "이전 작업 요약:
- src/api/users.ts: REST → GraphQL 전환 완료
- src/api/posts.ts: 아직 미전환
다음: posts.ts를 같은 패턴으로 전환해줘"
```

### `/compact` 명령 활용 (Claude Code)

```bash
# Claude Code에서 컨텍스트가 길어졌을 때
/compact

# 특정 주제에 집중하도록 요약 지시
/compact "인증 관련 변경사항에 집중해서 정리해줘"
```

## 체크리스트

- [ ] `.claudeignore` / `.cursorignore` 파일 설정 완료
- [ ] `CLAUDE.md` 또는 프로젝트 맵 문서 작성
- [ ] 불필요한 파일(lock, dist, snapshots) 제외 확인
- [ ] 대규모 작업을 청크 단위로 분할할 계획 수립
- [ ] 긴 세션에서 `/compact` 또는 수동 요약 활용 습관화

## 다음 단계

→ [플레이북 09: AI 문서 자동화](09-documentation.md)
→ [모노레포 + AI 워크플로우](../../workflows/monorepo-ai-workflow.md)

---

**더 자세한 가이드:** [claude-code/playbooks](../playbooks/)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
