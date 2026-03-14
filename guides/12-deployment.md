# 가이드 12: AI 배포 자동화

> CI/CD 파이프라인부터 롤백까지 — AI 도구로 배포를 자동화하는 실전 가이드

## 소요 시간

20-30분

## 사전 준비

- GitHub 레포지토리와 GitHub Actions 활성화
- 배포 대상 환경 (Vercel, AWS, Docker 등)
- Claude Code CLI 설치 완료

## Step 1: 배포 스크립트 생성

AI에게 프로젝트에 맞는 배포 설정을 만들어달라고 요청하세요.

```bash
# Claude Code에 배포 파이프라인 생성 요청
claude "이 프로젝트에 GitHub Actions CI/CD 파이프라인을 만들어줘. 
lint → test → build → deploy 순서로, 
main 브랜치 push 시 자동 배포되게 해줘"
```

**프롬프트 팁:**

| 상황 | 프롬프트 예시 |
|------|-------------|
| 기본 파이프라인 | `GitHub Actions로 CI/CD 만들어줘` |
| Docker 배포 | `Docker 이미지 빌드하고 ECR에 푸시하는 워크플로우 만들어줘` |
| Vercel 배포 | `Vercel 프리뷰 + 프로덕션 배포 워크플로우 만들어줘` |
| 모노레포 | `변경된 패키지만 빌드/배포하는 워크플로우 만들어줘` |

## Step 2: 환경별 설정 분리

배포 환경마다 다른 설정이 필요합니다. AI로 환경 분리를 깔끔하게 처리하세요.

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.ref == 'refs/heads/main' && 'production' || 'preview' }}
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install & Build
        run: |
          npm ci
          npm run build

      - name: Run Tests
        run: npm test

      - name: Deploy
        run: npm run deploy
        env:
          DEPLOY_ENV: ${{ vars.DEPLOY_ENV }}
          API_URL: ${{ secrets.API_URL }}
```

```bash
# Claude Code로 환경 설정 검토
claude "deploy.yml 파일을 검토해줘. 
시크릿 노출 위험이나 빠진 스텝이 있는지 확인해줘"
```

## Step 3: 헬스체크 추가

배포 후 서비스가 정상인지 자동으로 확인하는 단계를 추가하세요.

```bash
# 헬스체크 스크립트 생성
claude "배포 후 헬스체크 스크립트를 만들어줘.
/health 엔드포인트 확인, 3회 재시도, 
실패 시 Slack 알림 보내는 구조로"
```

**기본 헬스체크 패턴:**

```bash
#!/bin/bash
# scripts/health-check.sh

URL="${1:-https://api.example.com/health}"
MAX_RETRIES=3
RETRY_DELAY=10

for i in $(seq 1 $MAX_RETRIES); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
  if [ "$STATUS" = "200" ]; then
    echo "✅ 헬스체크 통과 (시도 $i/$MAX_RETRIES)"
    exit 0
  fi
  echo "⏳ 헬스체크 실패 ($STATUS), ${RETRY_DELAY}초 후 재시도..."
  sleep $RETRY_DELAY
done

echo "❌ 헬스체크 실패 — 롤백이 필요합니다"
exit 1
```

## Step 4: 자동 롤백 구성

배포 실패 시 이전 버전으로 자동 복구하는 구조를 만드세요.

```bash
# Claude Code로 롤백 로직 생성
claude "배포 실패 시 자동 롤백하는 GitHub Actions 스텝을 추가해줘.
이전 성공 배포의 커밋 해시를 기록해두고, 
헬스체크 실패 시 해당 커밋으로 되돌리는 구조로"
```

**롤백 워크플로우:**

```yaml
# deploy.yml에 추가
      - name: Health Check
        id: health
        continue-on-error: true
        run: ./scripts/health-check.sh ${{ vars.APP_URL }}

      - name: Rollback on Failure
        if: steps.health.outcome == 'failure'
        run: |
          echo "🔄 롤백 시작..."
          PREV_SHA=$(cat .last-successful-deploy 2>/dev/null || echo "")
          if [ -n "$PREV_SHA" ]; then
            git checkout $PREV_SHA
            npm ci && npm run build && npm run deploy
            echo "✅ 롤백 완료: $PREV_SHA"
          else
            echo "❌ 이전 배포 기록 없음 — 수동 복구 필요"
            exit 1
          fi

      - name: Record Successful Deploy
        if: steps.health.outcome == 'success'
        run: echo "${{ github.sha }}" > .last-successful-deploy
```

## Step 5: 배포 모니터링

배포 후 에러율과 성능을 추적하는 습관을 만드세요.

```bash
# 배포 후 에러 로그 분석
claude "최근 배포 후 에러 로그를 분석해줘.
새로 발생한 에러 패턴이 있는지, 
이전 버전 대비 에러율 변화가 있는지 확인해줘"
```

| 모니터링 항목 | 도구 | 확인 주기 |
|--------------|------|----------|
| 에러율 | Sentry, Datadog | 배포 직후 30분 |
| 응답 시간 | APM 도구 | 배포 직후 1시간 |
| CPU/메모리 | CloudWatch, Grafana | 배포 직후 1시간 |
| 사용자 피드백 | 에러 리포트 채널 | 배포 당일 |

## 체크리스트

- [ ] CI/CD 파이프라인 구성 완료
- [ ] 환경별 설정 분리 (preview / production)
- [ ] 시크릿 관리 설정 (GitHub Secrets)
- [ ] 헬스체크 스크립트 추가
- [ ] 자동 롤백 로직 구현
- [ ] 배포 후 모니터링 설정
- [ ] 팀에 배포 프로세스 공유

## 흔한 실수 & 해결

| 실수 | 해결 |
|------|------|
| 시크릿을 코드에 하드코딩 | GitHub Secrets + 환경변수로 분리 |
| 테스트 없이 바로 배포 | lint → test → build → deploy 순서 지키기 |
| 롤백 계획 없이 배포 | 이전 성공 버전 기록 + 자동 롤백 스텝 추가 |
| 배포 후 모니터링 안 함 | 헬스체크 + 30분 에러율 확인 습관화 |
| 모든 환경에 동일 설정 | 환경별 변수 분리 (`vars`, `secrets`) |

## 다음 단계

→ [가이드 10: Git 훅 자동화](10-hooks.md)로 커밋 전 자동 검사를 추가하세요.

---

**더 자세한 가이드:** [guides/](../guides/)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
