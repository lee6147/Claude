# 가이드 10: Hooks 자동화

> Claude Code의 도구 실행 전후에 자동으로 검사/포맷/알림을 실행하는 Hooks 설정 가이드

## 핵심 원칙

> **Hooks = 자동 품질 게이트.** 사람이 잊어도 시스템이 잡아줘요.

```
사용자 요청 → Claude가 도구 선택 → PreToolUse 훅 → 도구 실행 → PostToolUse 훅
```

## Hook 유형

| 이벤트 | 시점 | 용도 |
|--------|------|------|
| `PreToolUse` | 도구 실행 **전** | 차단(exit 2) 또는 경고(stderr) |
| `PostToolUse` | 도구 실행 **후** | 분석, 포맷팅, 알림 |
| `Stop` | 응답 완료 후 | 코드 품질 검사 |
| `SessionStart` | 세션 시작 시 | 컨텍스트 로딩 |
| `SessionEnd` | 세션 종료 시 | 상태 저장 |
| `PreCompact` | 압축 실행 전 | 상태 백업 |

## Step 1: settings.json에 Hook 추가

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "node my-hook.js"
        }],
        "description": "Bash 명령어 실행 전 검사"
      }
    ]
  }
}
```

## Step 2: 실전 Hook 3선

### 1. 대용량 파일 생성 차단

800줄 이상 파일 생성을 막아요. 작은 모듈로 나누도록 유도해요.

```json
{
  "matcher": "Write",
  "hooks": [{
    "type": "command",
    "command": "node -e \"let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const i=JSON.parse(d);const c=i.tool_input?.content||'';const lines=c.split('\\n').length;if(lines>800){console.error('[Hook] BLOCKED: '+lines+'줄 — 800줄 초과');console.error('[Hook] 파일을 작은 모듈로 분리하세요');process.exit(2)}console.log(d)})\""
  }],
  "description": "800줄 초과 파일 생성 차단"
}
```

### 2. console.log 경고

편집 후 console.log가 남아있으면 경고해요.

```json
{
  "matcher": "Edit",
  "hooks": [{
    "type": "command",
    "command": "node -e \"let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const i=JSON.parse(d);const ns=i.tool_input?.new_string||'';if(/console\\.log/.test(ns)){console.error('[Hook] console.log 발견 — 커밋 전 제거하세요')}console.log(d)})\""
  }],
  "description": "console.log 경고"
}
```

### 3. git push 전 확인

push 전에 리뷰를 상기시켜요.

```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "node -e \"let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const i=JSON.parse(d);const cmd=i.tool_input?.command||'';if(/git push/.test(cmd)){console.error('[Hook] push 전 변경사항을 확인하세요')}console.log(d)})\""
  }],
  "description": "git push 전 알림"
}
```

## Step 3: Hook 스크립트 작성법

### 기본 구조

```javascript
// my-hook.js
let data = "";
process.stdin.on("data", (chunk) => (data += chunk));
process.stdin.on("end", () => {
  const input = JSON.parse(data);

  // 도구 정보
  const toolName = input.tool_name;     // "Bash", "Edit", "Write"
  const toolInput = input.tool_input;   // 도구별 파라미터
  const toolOutput = input.tool_output; // PostToolUse만

  // 경고 (비차단)
  console.error("[Hook] 경고 메시지");

  // 차단 (PreToolUse만)
  // process.exit(2);

  // 반드시 원본 데이터 출력
  console.log(data);
});
```

### Exit 코드

| 코드 | 동작 |
|------|------|
| `0` | 정상 통과 |
| `2` | **차단** (PreToolUse만) |
| 기타 | 에러 로깅 (차단 안 함) |

## Step 4: Matcher 패턴

| 패턴 | 매칭 대상 |
|------|----------|
| `"Bash"` | Bash 명령어만 |
| `"Edit"` | 파일 편집만 |
| `"Write"` | 파일 생성만 |
| `"Edit\|Write"` | 편집 또는 생성 |
| `"*"` | 모든 도구 |

## 체크리스트

```
□ 프로젝트에 맞는 Hook 3개 이상 설정
□ 대용량 파일 차단 Hook 적용
□ 디버그 코드 경고 Hook 적용
□ 위험 명령어 (rm -rf, force push) 차단 고려
□ Hook 테스트: 의도한 대로 차단/경고되는지 확인
□ 비동기 Hook은 async: true + timeout 설정
```

## 주의사항

- Hook 스크립트는 **반드시 stdout에 원본 데이터를 출력**해야 해요
- `process.exit(2)`는 PreToolUse에서만 차단 효과가 있어요
- Node.js 기반이면 Windows/macOS/Linux 모두 호환돼요
- 비동기 Hook(`async: true`)은 메인 흐름을 차단하지 않아요

---

📬 매주 AI 코딩 팁을 받아보세요 → [maily.so/tenbuilder](https://maily.so/tenbuilder)
