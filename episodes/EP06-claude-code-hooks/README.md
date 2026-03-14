# EP06: Claude Code Hooks — 코딩 에이전트에 자동화를 입히다

> Claude Code 훅으로 린팅, 알림, 위험 명령 차단까지 자동화하는 실전 설정 가이드

## 📺 영상

**[YouTube에서 보기](https://youtube.com/@ten-builder)**

## 이 에피소드에서 다루는 것

- Claude Code 훅 시스템의 동작 원리와 12가지 이벤트
- `.claude/settings.json`에 훅을 설정하는 방법
- 실전 훅 5선: 린팅, 포매팅, 알림, 차단, 감사 로그
- 팀 프로젝트에서 훅을 공유하는 전략

## 훅이 필요한 이유

Claude Code가 코드를 생성하면 보통 이런 과정을 거쳐요:

1. 코드 작성 → 2. 수동으로 린트 실행 → 3. 결과 확인 → 4. 다시 수정 요청

매번 이걸 반복하면 시간이 낭비돼요. 훅을 쓰면 **도구 실행 직후 자동으로 린팅**이 돌아가고, **위험한 명령은 실행 전에 차단**되고, **세션이 끝나면 알림**이 와요.

## 핵심 개념: 라이프사이클 이벤트

훅은 Claude Code 세션의 특정 시점에 끼어드는 스크립트예요.

| 이벤트 | 시점 | 활용 |
|--------|------|------|
| `PreToolUse` | 도구 실행 직전 | 위험 명령 차단 |
| `PostToolUse` | 도구 실행 직후 | 린팅, 포매팅 |
| `Notification` | 알림 발생 시 | Slack/Discord 전송 |
| `Stop` | 세션 종료 시 | 데스크톱 알림 |
| `SessionStart` | 세션 시작 시 | 환경 검증 |

전체 12개 이벤트가 있지만, 실무에서 자주 쓰는 건 위 5개예요.

## 설정 파일 구조

훅은 `.claude/settings.json`에 정의해요:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "npx eslint --fix $CLAUDE_FILE_PATH",
        "timeout": 10000
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "bash .claude/hooks/check-dangerous.sh",
        "timeout": 5000
      }
    ]
  }
}
```

핵심 필드 3가지:

| 필드 | 설명 |
|------|------|
| `matcher` | 실행할 도구 이름 (정규식 지원) |
| `command` | 실행할 셸 명령어 |
| `timeout` | 타임아웃 (ms, 기본 60초) |

## 실전 훅 5선

### 1. 파일 저장 후 자동 린팅

Claude가 파일을 쓰거나 수정할 때마다 ESLint가 자동으로 돌아가요.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "npx eslint --fix $CLAUDE_FILE_PATH 2>/dev/null || true"
      }
    ]
  }
}
```

`$CLAUDE_FILE_PATH` 환경변수에 수정된 파일 경로가 자동으로 들어와요.

### 2. 위험 명령 차단

`rm -rf`, `DROP TABLE` 같은 명령을 사전에 막아요.

```bash
#!/bin/bash
# .claude/hooks/check-dangerous.sh

DANGEROUS_PATTERNS=(
  "rm -rf /"
  "DROP TABLE"
  "DROP DATABASE"
  "format c:"
  "> /dev/sda"
)

INPUT=$(cat "$CLAUDE_TOOL_INPUT" 2>/dev/null || echo "$CLAUDE_COMMAND")

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$INPUT" | grep -qi "$pattern"; then
    echo "BLOCK: 위험 명령 감지 — $pattern"
    exit 1
  fi
done

exit 0
```

`exit 1`을 반환하면 해당 도구 실행이 차단돼요.

### 3. 세션 종료 알림

긴 작업이 끝나면 macOS 알림으로 알려줘요.

```json
{
  "hooks": {
    "Stop": [
      {
        "command": "osascript -e 'display notification \"Claude Code 작업 완료\" with title \"텐빌더\"'"
      }
    ]
  }
}
```

Linux에서는 `notify-send`를 쓰면 돼요:

```bash
notify-send "Claude Code" "작업 완료"
```

### 4. Discord/Slack 웹훅 알림

Notification 이벤트가 발생하면 Discord에 자동 전송해요.

```bash
#!/bin/bash
# .claude/hooks/notify-discord.sh

WEBHOOK_URL="$DISCORD_WEBHOOK_URL"
MESSAGE="🤖 Claude Code 알림: $CLAUDE_NOTIFICATION"

curl -s -H "Content-Type: application/json" \
  -d "{\"content\":\"$MESSAGE\"}" \
  "$WEBHOOK_URL"
```

```json
{
  "hooks": {
    "Notification": [
      {
        "command": "bash .claude/hooks/notify-discord.sh"
      }
    ]
  }
}
```

### 5. 감사 로그 기록

모든 도구 실행을 로그 파일에 기록해요. 나중에 "Claude가 뭘 했지?" 추적할 때 유용해요.

```bash
#!/bin/bash
# .claude/hooks/audit-log.sh

LOG_DIR=".claude/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/audit-$(date +%Y%m%d).log"

echo "[$(date -Iseconds)] Tool=$CLAUDE_TOOL_NAME File=$CLAUDE_FILE_PATH" >> "$LOG_FILE"
```

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": ".*",
        "command": "bash .claude/hooks/audit-log.sh"
      }
    ]
  }
}
```

## 팀 프로젝트 공유 전략

`.claude/settings.json`을 레포에 커밋하면 팀 전체가 동일한 훅을 사용해요.

```
프로젝트/
├── .claude/
│   ├── settings.json     ← 훅 설정 (커밋)
│   ├── hooks/            ← 훅 스크립트 (커밋)
│   │   ├── check-dangerous.sh
│   │   ├── notify-discord.sh
│   │   └── audit-log.sh
│   └── logs/             ← 감사 로그 (.gitignore)
```

`.gitignore`에 `.claude/logs/`만 추가하면 돼요.

## 따라하기

### Step 1: 설정 파일 생성

```bash
mkdir -p .claude/hooks
touch .claude/settings.json
```

### Step 2: 기본 훅 설정

```bash
cat > .claude/settings.json << 'EOF'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "npx eslint --fix $CLAUDE_FILE_PATH 2>/dev/null || true",
        "timeout": 10000
      }
    ],
    "Stop": [
      {
        "command": "osascript -e 'display notification \"작업 완료\" with title \"Claude Code\"'"
      }
    ]
  }
}
EOF
```

### Step 3: 위험 차단 스크립트 추가

```bash
cat > .claude/hooks/check-dangerous.sh << 'HOOKEOF'
#!/bin/bash
INPUT=$(cat "$CLAUDE_TOOL_INPUT" 2>/dev/null || echo "$CLAUDE_COMMAND")
BLOCKED=("rm -rf /" "DROP TABLE" "DROP DATABASE")
for p in "${BLOCKED[@]}"; do
  echo "$INPUT" | grep -qi "$p" && echo "BLOCK: $p" && exit 1
done
exit 0
HOOKEOF
chmod +x .claude/hooks/check-dangerous.sh
```

### Step 4: 훅 적용 확인

Claude Code를 실행하고 파일을 수정해 보세요. `PostToolUse` 훅이 자동으로 린팅을 실행하는 걸 확인할 수 있어요.

## 더 알아보기

- [Claude Code Hooks 공식 문서](https://code.claude.com/docs/en/hooks)
- [Claude Code Hooks 치트시트](../../cheatsheets/claude-code-hooks-cheatsheet.md)
- [플레이북 01: 프로젝트 셋업](../../claude-code/playbooks/01-project-setup.md)

---

**구독하기:** [@ten-builder](https://youtube.com/@ten-builder) | [뉴스레터](https://maily.so/tenbuilder)
