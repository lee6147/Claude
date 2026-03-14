# GitHub Actions + AI 코드 리뷰 자동화

> PR을 올리면 AI가 자동으로 코드를 리뷰해요 — 팀 리뷰 전에 기본적인 이슈를 미리 잡아주는 워크플로우

## 개요

코드 리뷰는 소프트웨어 품질의 핵심이지만, 리뷰어의 시간은 한정되어 있어요. AI 코드 리뷰를 GitHub Actions로 연결하면 PR이 올라올 때마다 자동으로 1차 리뷰가 진행돼요. 스타일 위반, 잠재적 버그, 보안 이슈 같은 기본 사항을 AI가 먼저 잡아주고, 사람은 비즈니스 로직과 아키텍처에 집중할 수 있어요.

## 사전 준비

- GitHub 레포 (public 또는 private)
- OpenAI API 키 또는 Anthropic API 키
- GitHub Actions 사용 가능한 환경

## 설정

### Step 1: 워크플로우 파일 생성

`.github/workflows/ai-review.yml` 파일을 만들어요:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: AI PR Review
        uses: coderabbitai/ai-pr-reviewer@latest
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        with:
          debug: false
          review_simple_changes: false
          review_comment_lgtm: false
```

### Step 2: API 키 등록

GitHub 레포 → Settings → Secrets and variables → Actions에서 시크릿을 추가해요:

```bash
# GitHub CLI로도 등록할 수 있어요
gh secret set OPENAI_API_KEY --body "sk-your-api-key"
```

### Step 3: 리뷰 규칙 커스터마이징

레포 루트에 `.coderabbit.yaml` 파일을 만들어서 리뷰 동작을 세밀하게 조정할 수 있어요:

```yaml
language: ko
reviews:
  profile: chill        # assertive | chill
  request_changes_workflow: false
  high_level_summary: true
  poem: false
  review_status: true
  path_filters:
    - "!dist/**"
    - "!*.lock"
    - "!**/*.min.js"
  auto_review:
    enabled: true
    drafts: false
chat:
  auto_reply: true
```

## 사용 방법

설정이 끝나면 PR을 올릴 때마다 AI 리뷰가 자동으로 달려요. 흐름은 이래요:

1. 개발자가 PR 생성
2. GitHub Actions가 트리거되어 AI 리뷰 실행
3. AI가 변경된 파일을 분석하고 PR 코멘트로 결과 작성
4. 개발자가 AI 피드백 확인 후 수정
5. 사람 리뷰어가 최종 검수

### AI 리뷰 코멘트에 답장하기

AI 리뷰 코멘트에 답글을 달면 추가 설명을 받을 수 있어요:

| 명령어 | 동작 |
|--------|------|
| `@coderabbitai explain` | 해당 코드 블록의 상세 설명 |
| `@coderabbitai suggest` | 개선 코드 제안 |
| `@coderabbitai resolve` | 해당 코멘트 해결 처리 |

## 다른 도구 비교

| 도구 | 특징 | 가격 |
|------|------|------|
| CodeRabbit | PR 요약 + 라인별 리뷰, 대화 기능 | 무료 (오픈소스), 유료 (private) |
| GitHub Copilot Code Review | GitHub 네이티브, 별도 설정 최소 | Copilot 구독 포함 |
| Graphite Agent | 스택 PR 지원, 자동 수정 제안 | 무료 플랜 있음 |
| CodeAnt AI | 보안 중심 분석, SAST 통합 | 무료 플랜 있음 |

## 커스터마이징

| 설정 | 기본값 | 설명 |
|------|--------|------|
| `review_simple_changes` | `false` | 단순 변경(이름 변경 등)도 리뷰할지 |
| `review_comment_lgtm` | `false` | 문제없는 파일에도 LGTM 코멘트 남길지 |
| `path_filters` | 없음 | 리뷰 대상 파일 필터 (glob 패턴) |
| `language` | `en` | 리뷰 코멘트 언어 |
| `profile` | `chill` | 리뷰 톤 (chill: 부드러움, assertive: 엄격) |

## 직접 만드는 경량 AI 리뷰 액션

외부 도구 없이 직접 구현하고 싶다면, diff를 추출해서 LLM API에 보내는 방식도 가능해요:

```yaml
name: Custom AI Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Get diff
        id: diff
        run: |
          DIFF=$(git diff origin/main...HEAD -- '*.ts' '*.py' '*.js' | head -c 10000)
          echo "diff<<EOF" >> $GITHUB_OUTPUT
          echo "$DIFF" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: AI Review
        uses: actions/github-script@v7
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        with:
          script: |
            const diff = `${{ steps.diff.outputs.diff }}`;
            const response = await fetch('https://api.anthropic.com/v1/messages', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'x-api-key': process.env.ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01'
              },
              body: JSON.stringify({
                model: 'claude-sonnet-4-20250514',
                max_tokens: 1024,
                messages: [{
                  role: 'user',
                  content: `다음 코드 diff를 리뷰해주세요. 버그, 보안 이슈, 개선점을 찾아주세요.\n\n${diff}`
                }]
              })
            });
            const result = await response.json();
            const review = result.content[0].text;

            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `## 🤖 AI 코드 리뷰\n\n${review}`
            });
```

## 문제 해결

| 문제 | 해결 |
|------|------|
| AI 리뷰가 트리거되지 않음 | Actions 탭에서 워크플로우 활성화 확인, `on` 이벤트 타입 점검 |
| API 키 에러 | Secrets에 키가 정확히 등록되었는지 확인 |
| 리뷰 코멘트가 너무 많음 | `path_filters`로 대상 파일 제한, `review_simple_changes: false` 설정 |
| Private 레포에서 권한 에러 | `permissions` 블록에 `pull-requests: write` 추가 확인 |
| 큰 PR에서 타임아웃 | diff 크기를 제한하거나, 파일 단위로 분할 리뷰 |

---

**더 자세한 가이드:** [claude-code/playbooks](../claude-code/playbooks/)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
