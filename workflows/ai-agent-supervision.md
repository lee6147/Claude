# AI 에이전트 감독 워크플로우

> AI 코딩 에이전트를 자율 실행시키면서도 품질을 유지하는 감독 체계 — 승인 게이트, 모니터링, 롤백까지

## 개요

Claude Code, Codex, Cursor Background Agent 같은 자율 코딩 에이전트가 늘어나면서, "시키면 알아서 해주니 편하다"와 "결과를 못 믿겠다" 사이에서 고민하는 개발자가 많아요. 핵심은 **완전 자동도 완전 수동도 아닌, 적절한 체크포인트를 설계하는 것**이에요.

이 워크플로우는 AI 에이전트를 실행하면서도 사람이 중요한 순간에 개입할 수 있는 감독 구조를 만들어요.

## 사전 준비

- Claude Code 또는 Codex CLI 설치
- Git 레포 (로컬)
- 기본적인 셸 스크립트 이해

## 감독 레벨 정의

프로젝트 특성에 따라 세 가지 레벨로 나눠서 운영해요.

| 레벨 | 이름 | 설명 | 적합한 작업 |
|------|------|------|------------|
| L1 | 자율 실행 | 결과만 확인 | 테스트 작성, 문서 생성, 린트 수정 |
| L2 | 승인 게이트 | 주요 단계에서 사람이 확인 | 리팩토링, API 변경, 설정 수정 |
| L3 | 페어 모드 | 실시간으로 함께 작업 | 아키텍처 변경, 보안 관련, 신규 기능 |

## 설정

### Step 1: 감독 설정 파일 만들기

프로젝트 루트에 `.ai-supervision.yaml`을 만들어요:

```yaml
# .ai-supervision.yaml
supervision:
  default_level: L2

  rules:
    # 파일 패턴별 레벨 지정
    - pattern: "*.test.*"
      level: L1
      reason: "테스트 파일은 자율 실행"

    - pattern: "src/api/**"
      level: L3
      reason: "API 변경은 페어 모드"

    - pattern: "*.config.*"
      level: L2
      reason: "설정 파일은 승인 필요"

    - pattern: "Dockerfile*"
      level: L2
      reason: "인프라 변경은 승인 필요"

  notifications:
    on_complete: true
    on_error: true
    channel: "slack"  # slack, discord, terminal
```

### Step 2: 승인 게이트 스크립트

`scripts/ai-gate.sh`를 만들어서, AI가 변경한 파일을 자동으로 분류하고 필요하면 멈춰요:

```bash
#!/bin/bash
# scripts/ai-gate.sh — AI 에이전트 실행 후 승인 게이트

set -e

CHANGED_FILES=$(git diff --name-only HEAD~1)
NEEDS_REVIEW=false

for file in $CHANGED_FILES; do
  # API 디렉토리 변경 감지
  if [[ "$file" == src/api/* ]]; then
    echo "⚠️  API 변경 감지: $file"
    NEEDS_REVIEW=true
  fi

  # 설정 파일 변경 감지
  if [[ "$file" == *.config.* ]] || [[ "$file" == *Dockerfile* ]]; then
    echo "⚠️  설정 변경 감지: $file"
    NEEDS_REVIEW=true
  fi
done

if [ "$NEEDS_REVIEW" = true ]; then
  echo ""
  echo "🔍 승인이 필요한 변경이 있어요."
  echo "변경 내용을 확인하세요:"
  git diff HEAD~1 --stat
  echo ""
  read -p "계속 진행할까요? (y/n): " answer
  if [[ "$answer" != "y" ]]; then
    echo "❌ 롤백합니다."
    git reset --hard HEAD~1
    exit 1
  fi
fi

echo "✅ 승인 완료. 계속 진행합니다."
```

### Step 3: 자동 롤백 안전망

AI 에이전트 실행 전에 체크포인트를 만들어두면 문제가 생겼을 때 바로 돌아갈 수 있어요:

```bash
#!/bin/bash
# scripts/ai-safe-run.sh — 체크포인트 + 자동 롤백

CHECKPOINT=$(git rev-parse HEAD)
echo "📌 체크포인트: $CHECKPOINT"

# AI 에이전트 실행 (예: Claude Code)
claude -p "$1" --allowedTools Edit,Write,Bash

# 테스트 실행
if ! npm test 2>/dev/null; then
  echo "❌ 테스트 실패 — 체크포인트로 롤백"
  git reset --hard "$CHECKPOINT"
  git clean -fd
  exit 1
fi

echo "✅ 테스트 통과"
```

## 사용 방법

### L1: 자율 실행 (테스트 작성)

```bash
# 테스트만 생성 — 결과만 나중에 확인
claude -p "src/utils.ts에 대한 단위 테스트를 작성해줘" \
  --allowedTools Edit,Write \
  2>&1 | tee logs/ai-run-$(date +%Y%m%d-%H%M).log
```

### L2: 승인 게이트 (리팩토링)

```bash
# 리팩토링 실행 후 게이트 체크
./scripts/ai-safe-run.sh "auth 모듈을 리팩토링해줘"
./scripts/ai-gate.sh
```

### L3: 페어 모드 (아키텍처)

```bash
# 대화형으로 함께 작업
claude
# > 결제 시스템 아키텍처를 변경하고 싶어요.
# > 현재 구조를 분석하고 개선안을 제시해줘.
# (매 제안마다 직접 확인하고 피드백)
```

## 모니터링 대시보드

AI 에이전트의 작업 이력을 추적하는 간단한 로그 구조예요:

```bash
#!/bin/bash
# scripts/ai-monitor.sh — 실행 이력 요약

LOG_DIR="logs"
echo "=== AI 에이전트 실행 요약 ==="
echo ""
echo "최근 5회 실행:"
ls -lt "$LOG_DIR"/ai-run-*.log 2>/dev/null | head -5 | while read line; do
  file=$(echo "$line" | awk '{print $NF}')
  errors=$(grep -c "ERROR\|❌" "$file" 2>/dev/null || echo 0)
  lines=$(wc -l < "$file")
  echo "  📄 $(basename $file) — ${lines}줄, 에러 ${errors}건"
done

echo ""
echo "이번 주 통계:"
echo "  실행: $(ls "$LOG_DIR"/ai-run-*.log 2>/dev/null | wc -l)회"
echo "  롤백: $(grep -rl "롤백" "$LOG_DIR"/ 2>/dev/null | wc -l)회"
```

## 커스터마이징

| 설정 | 기본값 | 설명 |
|------|--------|------|
| `default_level` | L2 | 패턴에 매칭되지 않는 파일의 감독 레벨 |
| `notifications.channel` | terminal | 알림 채널 (slack, discord, terminal) |
| `notifications.on_complete` | true | 작업 완료 시 알림 |
| 로그 보관 기간 | 30일 | `logs/` 디렉토리 정리 주기 |

## 문제 해결

| 문제 | 해결 |
|------|------|
| 게이트가 너무 자주 걸려요 | `default_level`을 L1로 낮추고, 민감한 경로만 L2/L3으로 지정 |
| 롤백했는데 새 파일이 남아있어요 | `git clean -fd`로 untracked 파일도 정리 |
| 로그가 너무 쌓여요 | cron으로 30일 이상 로그 자동 삭제: `find logs/ -mtime +30 -delete` |
| AI가 감독 설정 파일을 수정해요 | `.ai-supervision.yaml`을 `--ignorePatterns`에 추가 |

---

**더 자세한 가이드:** [claude-code/playbooks](../claude-code/playbooks/)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
