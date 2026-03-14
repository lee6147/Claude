# 플레이북 08: AI 배포 자동화

> AI로 배포 파이프라인을 구축하고 안전하게 운영하는 단계별 가이드

## 언제 쓰나요?

- 새 프로젝트의 CI/CD 파이프라인을 처음 세팅할 때
- 기존 배포 프로세스에 자동 검증을 추가하고 싶을 때
- 롤백 전략이 없거나 수동으로 처리하고 있을 때
- 배포 후 헬스체크를 체계적으로 관리하고 싶을 때

## 소요 시간

20-40분

## 사전 준비

- CI/CD 플랫폼 접근 권한 (GitHub Actions, GitLab CI 등)
- 배포 대상 환경 (staging, production)
- 모니터링 도구 (Datadog, Grafana 등) 연동 가능

## Step 1: 배포 설정 파일 생성

AI에게 프로젝트 구조를 보여주고 배포 파이프라인을 생성하세요. 프로젝트에 맞는 최적의 설정을 만들어줍니다.

```bash
# 프로젝트 구조를 기반으로 CI/CD 설정 생성
claude "이 프로젝트에 맞는 GitHub Actions 워크플로우를 만들어줘.
조건:
- PR 머지 시 staging 자동 배포
- main 태그 push 시 production 배포
- 빌드 → 테스트 → 배포 순서
- 실패 시 Slack 알림"

# 기존 설정 개선
claude "이 GitHub Actions 워크플로우를 검토하고 개선해줘.
특히 캐싱, 병렬 실행, 보안 측면에서" < .github/workflows/deploy.yml
```

AI가 생성하는 워크플로우 예시:

```yaml
# .github/workflows/deploy.yml
name: Deploy Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm test
      - run: pnpm lint

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        run: |
          echo "Deploying to staging..."
          # 실제 배포 명령어

  deploy-production:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://your-app.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          echo "Deploying to production..."
```

## Step 2: 배포 전 자동 검증

배포 전에 AI가 변경사항을 분석해서 위험 요소를 미리 잡아줍니다.

```bash
# 배포 전 변경사항 위험도 분석
claude "다음 diff를 보고 배포 위험도를 평가해줘.
체크 항목:
1. 데이터베이스 마이그레이션 포함 여부
2. 환경 변수 변경 여부
3. 브레이킹 체인지 가능성
4. 롤백 시 주의사항" < <(git diff origin/main...HEAD)

# package.json 변경 시 의존성 안전성 체크
claude "package.json에 추가/변경된 의존성의 보안 상태와 안정성을 평가해줘.
deprecated 패키지나 알려진 취약점이 있는지 확인" < package.json
```

CI/CD 파이프라인에 검증 단계를 추가하는 패턴:

```yaml
  pre-deploy-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Check migration files
        run: |
          MIGRATION_FILES=$(git diff --name-only origin/main...HEAD | grep -c "migration" || true)
          if [ "$MIGRATION_FILES" -gt 0 ]; then
            echo "⚠️ 마이그레이션 파일 감지: 수동 확인 필요"
            echo "migration_detected=true" >> $GITHUB_OUTPUT
          fi
      - name: Check env changes
        run: |
          ENV_CHANGES=$(git diff origin/main...HEAD -- '.env*' '*.env' | wc -l || true)
          if [ "$ENV_CHANGES" -gt 0 ]; then
            echo "⚠️ 환경 변수 변경 감지"
          fi
```

## Step 3: 헬스체크 구현

배포 후 서비스가 정상인지 자동으로 확인하는 체계를 만드세요.

```bash
# 헬스체크 엔드포인트 코드 생성
claude "이 Express 앱에 /health 엔드포인트를 추가해줘.
체크 항목: DB 연결, Redis 연결, 외부 API 응답 시간
각 항목의 상태와 응답 시간을 JSON으로 반환" < src/app.ts
```

AI가 생성하는 헬스체크 코드 예시:

```typescript
// src/routes/health.ts
interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: Record<string, CheckResult>;
  version: string;
  uptime: number;
}

interface CheckResult {
  status: 'pass' | 'fail';
  responseMs: number;
  message?: string;
}

app.get('/health', async (req, res) => {
  const checks: Record<string, CheckResult> = {};

  // DB 체크
  const dbStart = Date.now();
  try {
    await db.query('SELECT 1');
    checks.database = { status: 'pass', responseMs: Date.now() - dbStart };
  } catch (e) {
    checks.database = { status: 'fail', responseMs: Date.now() - dbStart, message: e.message };
  }

  // Redis 체크
  const redisStart = Date.now();
  try {
    await redis.ping();
    checks.redis = { status: 'pass', responseMs: Date.now() - redisStart };
  } catch (e) {
    checks.redis = { status: 'fail', responseMs: Date.now() - redisStart, message: e.message };
  }

  const allPassed = Object.values(checks).every(c => c.status === 'pass');
  const status = allPassed ? 'healthy' : 'degraded';

  res.status(allPassed ? 200 : 503).json({
    status,
    checks,
    version: process.env.APP_VERSION || 'unknown',
    uptime: process.uptime(),
  });
});
```

## Step 4: 롤백 전략 수립

배포 실패 시 빠르게 이전 버전으로 돌아가는 체계를 준비하세요.

```bash
# 롤백 스크립트 생성
claude "이 배포 환경에 맞는 롤백 스크립트를 만들어줘.
- Vercel: 이전 배포로 즉시 전환
- Docker: 이전 이미지 태그로 롤백
- K8s: 이전 리비전으로 롤백
각각 30초 이내에 롤백이 완료되어야 해"
```

| 배포 환경 | 롤백 명령어 | 소요 시간 |
|----------|------------|----------|
| Vercel | `vercel rollback` | 5-10초 |
| Docker Compose | `docker compose up -d --force-recreate` (이전 태그) | 10-20초 |
| Kubernetes | `kubectl rollout undo deployment/app` | 15-30초 |
| AWS ECS | `aws ecs update-service --force-new-deployment` | 30-60초 |

자동 롤백을 CI/CD에 넣는 패턴:

```yaml
  post-deploy-verify:
    needs: deploy-production
    runs-on: ubuntu-latest
    steps:
      - name: Health check
        id: health
        run: |
          for i in {1..5}; do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://your-app.com/health)
            if [ "$STATUS" == "200" ]; then
              echo "✅ 헬스체크 통과"
              exit 0
            fi
            echo "⏳ 재시도 $i/5..."
            sleep 10
          done
          echo "❌ 헬스체크 실패"
          exit 1

      - name: Auto rollback on failure
        if: failure()
        run: |
          echo "🔄 자동 롤백 실행..."
          # vercel rollback 또는 kubectl rollout undo
```

## Step 5: 모니터링 연동

배포 후 핵심 지표를 자동으로 추적하세요.

```bash
# 배포 후 모니터링 대시보드 설정 요청
claude "배포 후 모니터링해야 할 핵심 지표 5가지를 추천하고,
각 지표의 알림 임계값을 설정해줘.
현재 스택: Node.js + PostgreSQL + Redis"
```

배포 후 필수 모니터링 지표:

| 지표 | 정상 범위 | 알림 조건 |
|------|----------|----------|
| 응답 시간 (p95) | < 500ms | > 1000ms |
| 에러율 | < 0.1% | > 1% |
| CPU 사용률 | < 70% | > 85% |
| 메모리 사용률 | < 80% | > 90% |
| DB 커넥션 풀 | < 70% | > 85% |

## 체크리스트

- [ ] CI/CD 파이프라인 설정 완료
- [ ] 배포 전 자동 검증 단계 추가
- [ ] /health 엔드포인트 구현
- [ ] 롤백 스크립트 준비 및 테스트
- [ ] 모니터링 알림 설정
- [ ] staging 환경에서 전체 플로우 테스트
- [ ] 팀원에게 롤백 절차 공유

## 흔한 실수 & 해결

| 실수 | 해결 |
|------|------|
| 환경 변수를 코드에 직접 넣음 | GitHub Secrets 또는 환경별 설정 사용 |
| 롤백 테스트를 안 함 | 분기마다 롤백 드릴 실시 |
| 헬스체크 없이 배포 | /health 엔드포인트 필수 구현 |
| DB 마이그레이션 롤백 미준비 | down 마이그레이션도 함께 작성 |
| 배포 알림 미설정 | Slack/Discord 웹훅 연동 |

## 다음 단계

→ [GitHub Actions + AI 코드 리뷰](../../workflows/github-actions-ai-review.md)

---

**더 자세한 가이드:** [claude-code/playbooks](../playbooks/)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
