# Pre-commit AI 훅

> 커밋 전에 AI가 코드를 자동 검사해요 — 실수를 push하기 전에 잡아주는 로컬 안전망

## 개요

코드 리뷰를 PR 단계에서만 하면 이미 늦을 때가 많아요. pre-commit 훅에 AI 검사를 붙이면 `git commit`을 실행하는 순간 코드를 분석해서, 명백한 버그나 스타일 문제를 로컬에서 바로 잡아줘요. CI까지 가기 전에 피드백을 받을 수 있어서 개발 사이클이 훨씬 빨라져요.

## 사전 준비

- Python 3.9+ (pre-commit 프레임워크 실행)
- [pre-commit](https://pre-commit.com/) 설치
- Anthropic API 키 또는 OpenAI API 키
- Git 레포 (로컬)

## 설정

### Step 1: pre-commit 프레임워크 설치

```bash
pip install pre-commit
cd your-project
pre-commit install
```

`pre-commit install`을 실행하면 `.git/hooks/pre-commit`이 자동으로 생성돼요.

### Step 2: AI 리뷰 스크립트 작성

프로젝트 루트에 `scripts/ai-review-hook.sh`를 만들어요:

```bash
#!/usr/bin/env bash
set -euo pipefail

# staged 파일만 대상
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|ts|tsx|jsx)$' || true)

if [ -z "$STAGED_FILES" ]; then
  echo "✅ AI 리뷰 대상 파일 없음"
  exit 0
fi

# diff 추출
DIFF=$(git diff --cached --unified=3 -- $STAGED_FILES)

# Claude API로 리뷰 요청
REVIEW=$(curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d "{
    \"model\": \"claude-sonnet-4-20250514\",
    \"max_tokens\": 1024,
    \"messages\": [{
      \"role\": \"user\",
      \"content\": \"다음 git diff를 리뷰해줘. 버그, 보안 이슈, 타입 에러만 짧게 지적해. 문제 없으면 LGTM만 출력해.\n\n$DIFF\"
    }]
  }" | python3 -c "import sys,json; print(json.load(sys.stdin)['content'][0]['text'])")

echo ""
echo "🤖 AI 코드 리뷰 결과:"
echo "─────────────────────"
echo "$REVIEW"
echo "─────────────────────"

# LGTM이면 통과, 아니면 경고만 표시 (커밋은 허용)
if echo "$REVIEW" | grep -qi "LGTM"; then
  echo "✅ AI 리뷰 통과"
  exit 0
else
  echo ""
  echo "⚠️  AI가 개선 사항을 발견했어요. 확인 후 커밋하세요."
  echo "    커밋을 강제하려면: git commit --no-verify"
  exit 1
fi
```

```bash
chmod +x scripts/ai-review-hook.sh
```

### Step 3: .pre-commit-config.yaml 설정

```yaml
repos:
  # 기본 포맷팅/린트
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json

  # Python 포맷팅
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black

  # Python 린트
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]

  # AI 코드 리뷰 (로컬 스크립트)
  - repo: local
    hooks:
      - id: ai-code-review
        name: AI Code Review
        entry: scripts/ai-review-hook.sh
        language: script
        stages: [pre-commit]
        pass_filenames: false
```

```bash
pre-commit install
```

## 사용 방법

설정이 끝나면 평소처럼 `git commit`하면 돼요:

```bash
git add .
git commit -m "feat: 새 기능 추가"

# 실행 순서:
# 1. trailing-whitespace → 포맷 정리
# 2. black → Python 코드 포맷팅
# 3. ruff → 린트 검사
# 4. ai-code-review → AI가 diff 분석
```

AI 리뷰에서 이슈가 발견되면 커밋이 중단돼요. 수정 후 다시 커밋하거나, 급할 때는 `--no-verify`로 건너뛸 수 있어요.

## 커스터마이징

| 설정 | 기본값 | 설명 |
|------|--------|------|
| 대상 확장자 | `.py, .js, .ts, .tsx, .jsx` | `grep -E` 패턴을 수정해서 변경 |
| AI 모델 | `claude-sonnet-4-20250514` | 빠른 응답이 필요하면 `claude-haiku-4-20250514`로 교체 |
| 리뷰 모드 | 경고 후 중단 (`exit 1`) | `exit 0`으로 바꾸면 경고만 표시하고 커밋 허용 |
| max_tokens | 1024 | 큰 diff는 2048로 올려도 OK |
| API 키 환경변수 | `ANTHROPIC_API_KEY` | `.bashrc`나 `.envrc`에 설정 |

## 비용 최적화 팁

AI API 호출에는 비용이 발생해요. 불필요한 호출을 줄이는 방법:

```bash
# 1. 파일 개수 제한 — 10개 이상이면 스킵
FILE_COUNT=$(echo "$STAGED_FILES" | wc -l)
if [ "$FILE_COUNT" -gt 10 ]; then
  echo "⏭️ staged 파일이 ${FILE_COUNT}개 — AI 리뷰 스킵"
  exit 0
fi

# 2. diff 크기 제한 — 5000자 이상이면 요약만 요청
DIFF_LEN=${#DIFF}
if [ "$DIFF_LEN" -gt 5000 ]; then
  DIFF="${DIFF:0:5000}...(truncated)"
fi
```

## 문제 해결

| 문제 | 해결 |
|------|------|
| `ANTHROPIC_API_KEY` 없다는 에러 | `export ANTHROPIC_API_KEY=sk-...`를 `.bashrc`에 추가 |
| API 호출이 느려요 (3초+) | Haiku 모델로 변경하면 1초 이내로 줄어요 |
| 큰 diff에서 API 에러 | max_tokens를 늘리거나 diff 크기 제한 추가 |
| pre-commit이 아예 안 돌아요 | `pre-commit install`을 다시 실행 |
| `--no-verify`를 너무 자주 써요 | `exit 1` → `exit 0`으로 바꿔서 경고만 표시 모드로 전환 |

---

**더 자세한 가이드:** [claude-code/playbooks](../claude-code/playbooks/)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
