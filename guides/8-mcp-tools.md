# 가이드 08: MCP 서버 활용

> Claude Code에 외부 도구를 연결해서 능력을 확장하는 방법

## MCP (Model Context Protocol)란?

MCP는 AI 모델이 외부 도구와 데이터에 접근하는 표준 프로토콜입니다.
Claude Code에 MCP 서버를 연결하면:

- 🔍 데이터베이스 직접 조회
- 📁 파일 시스템 탐색
- 🌐 API 호출
- 🛠️ 외부 서비스 통합

이 모든 것을 대화 안에서 할 수 있습니다.

## 설정 방법

### 1. CLI로 추가 (권장)

```bash
# 프로젝트 단위 설정
claude mcp add <서버이름> <명령어>
# → .claude/mcp-servers.json에 저장

# 모든 프로젝트에서 사용 (글로벌)
claude mcp add --global <서버이름> <명령어>
# → ~/.claude/mcp-servers.json에 저장
```

### 2. settings.json 직접 편집

설정 파일에서 직접 MCP 서버를 등록할 수도 있습니다.

| 범위 | 파일 | 용도 |
|------|------|------|
| 전역 | `~/.claude.json` | 모든 프로젝트에 적용 |
| 프로젝트 | `.claude/settings.json` | 해당 프로젝트만 |

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token"
      }
    }
  }
}
```

특정 프로젝트에서 필요 없는 서버를 끄려면:

```json
{
  "disabledMcpServers": ["filesystem", "supabase"]
}
```

## 자주 쓰는 MCP 서버

### 파일 시스템 (filesystem)

```bash
claude mcp add filesystem npx -y @anthropic-ai/mcp-filesystem -- /path/to/directory
```

**활용 예:**
```
> 프로젝트의 모든 TODO 주석을 찾아줘
> src 폴더의 파일 구조를 분석해줘
```

### PostgreSQL

```bash
claude mcp add postgres npx -y @anthropic-ai/mcp-postgres -- postgresql://user:pass@localhost/db
```

**활용 예:**
```
> users 테이블의 스키마를 보여줘
> 최근 7일간 가입자 수를 일별로 조회해줘
> 느린 쿼리를 찾아서 인덱스를 제안해줘
```

### GitHub

```bash
claude mcp add github npx -y @anthropic-ai/mcp-github
# GITHUB_TOKEN 환경변수 필요
```

### Context7 (라이브러리 문서)

최신 라이브러리 공식 문서를 실시간으로 조회합니다.

```bash
claude mcp add context7 npx -y @context7/mcp-server
```

### Vercel (배포)

```json
{
  "vercel": {
    "type": "http",
    "url": "https://mcp.vercel.com"
  }
}
```

### Brave Search (웹 검색)

```bash
claude mcp add brave-search npx -y @anthropic-ai/mcp-brave-search
# BRAVE_API_KEY 환경변수 필요
```

### Sentry (에러 트래킹)

```bash
claude mcp add sentry npx -y @anthropic-ai/mcp-sentry
# SENTRY_AUTH_TOKEN 환경변수 필요
```

## MCP 서버 관리

```bash
# 등록된 서버 목록 확인
claude mcp list

# 서버 제거
claude mcp remove <서버이름>

# 서버 상태 확인 (Claude Code 세션 내에서)
/mcp
```

## 커스텀 MCP 서버 만들기

사내 시스템에 맞는 MCP 서버를 직접 만들 수 있습니다.

```typescript
// my-mcp-server.ts
import { McpServer } from "@anthropic-ai/mcp";

const server = new McpServer("my-tools");

server.tool("get_deploy_status", "배포 상태 확인", {
  environment: { type: "string", enum: ["dev", "staging", "prod"] }
}, async ({ environment }) => {
  // 배포 시스템 API 호출
  const status = await checkDeploy(environment);
  return { content: [{ type: "text", text: JSON.stringify(status) }] };
});

server.start();
```

```bash
# 등록
claude mcp add my-tools npx tsx my-mcp-server.ts
```

## 팀 설정 공유

`.claude/mcp-servers.json`을 Git에 커밋하면 팀 전체가 같은 MCP 설정을 사용할 수 있습니다.

```json
{
  "postgres": {
    "command": "npx",
    "args": ["-y", "@anthropic-ai/mcp-postgres", "--", "$DATABASE_URL"]
  },
  "github": {
    "command": "npx",
    "args": ["-y", "@anthropic-ai/mcp-github"]
  }
}
```

> ⚠️ **주의:** 비밀번호나 토큰은 환경변수(`$DATABASE_URL`)로 참조하세요. JSON에 직접 넣지 마세요.

## 주의사항

| 항목 | 설명 |
|------|------|
| **10개 이하 유지** | 활성 MCP 서버마다 스키마가 컨텍스트에 주입 → 토큰 소비 |
| **API 키 관리** | `.env` 또는 시스템 환경변수 사용 → JSON에 직접 넣지 마세요 |
| **서드파티 검증** | 공식 MCP 서버가 아니면 소스코드 확인 후 사용 |
| **HTTP vs stdio** | `type: "http"` = 원격 서버, `command` = 로컬 프로세스 |

## 트러블슈팅

| 증상 | 해결 |
|------|------|
| MCP 서버 연결 안 됨 | `npx -y <package>` 단독 실행으로 서버 테스트 |
| 토큰 에러 | API 키 유효성 확인, 권한 범위 (scope) 체크 |
| 느린 응답 | 불필요한 서버 비활성화, `disabledMcpServers` 활용 |
| 컨텍스트 부족 | MCP 서버 수 줄이기 (5개 이하 권장) |

## 체크리스트

- [ ] 프로젝트에 필요한 MCP 서버 식별
- [ ] `claude mcp add`로 등록
- [ ] `/mcp`로 연결 상태 확인
- [ ] 팀 공유가 필요하면 `.claude/mcp-servers.json` 커밋
- [ ] 민감한 정보는 환경변수로 관리

## 다음 단계

→ [09. 보안 체크](./09-security.md)
