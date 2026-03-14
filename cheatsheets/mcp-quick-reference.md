# MCP 서버 빠른 참조

> Claude Code에 연결할 수 있는 MCP 서버 한눈에 보기

## 설치 & 관리 명령어

| 명령어 | 설명 |
|--------|------|
| `claude mcp add <name> <cmd>` | MCP 서버 등록 |
| `claude mcp add --global <name> <cmd>` | 글로벌 등록 |
| `claude mcp list` | 등록된 서버 목록 |
| `claude mcp remove <name>` | 서버 제거 |
| `/mcp` (세션 내) | 연결 상태 확인 |

## 인기 MCP 서버

### 데이터 & 검색

| 서버 | 설치 | 용도 |
|------|------|------|
| **PostgreSQL** | `claude mcp add pg npx -y @anthropic-ai/mcp-postgres -- $DATABASE_URL` | DB 조회/분석 |
| **SQLite** | `claude mcp add sqlite npx -y @anthropic-ai/mcp-sqlite -- ./db.sqlite` | 로컬 DB |
| **Brave Search** | `claude mcp add search npx -y @anthropic-ai/mcp-brave-search` | 웹 검색 |
| **Filesystem** | `claude mcp add fs npx -y @anthropic-ai/mcp-filesystem -- /path` | 파일 탐색 |

### 개발 도구

| 서버 | 설치 | 용도 |
|------|------|------|
| **GitHub** | `claude mcp add gh npx -y @anthropic-ai/mcp-github` | PR/이슈/레포 |
| **Sentry** | `claude mcp add sentry npx -y @anthropic-ai/mcp-sentry` | 에러 트래킹 |
| **Linear** | `claude mcp add linear npx -y @anthropic-ai/mcp-linear` | 프로젝트 관리 |
| **Slack** | `claude mcp add slack npx -y @anthropic-ai/mcp-slack` | 메시지/검색 |

### 클라우드 & 인프라

| 서버 | 설치 | 용도 |
|------|------|------|
| **AWS** | `claude mcp add aws npx -y @anthropic-ai/mcp-aws` | AWS 리소스 |
| **Cloudflare** | `claude mcp add cf npx -y @anthropic-ai/mcp-cloudflare` | Workers/KV/D1 |
| **Vercel** | `claude mcp add vercel npx -y @anthropic-ai/mcp-vercel` | 배포 관리 |

## 환경변수 (필요한 서버)

```bash
# ~/.zshrc 또는 .env에 추가
export GITHUB_TOKEN="ghp_..."
export BRAVE_API_KEY="BSA..."
export SENTRY_AUTH_TOKEN="sntrys_..."
export DATABASE_URL="postgresql://..."
```

## 활용 시나리오

### 🔍 코드 + DB 통합 분석
```
> users 테이블 스키마를 확인하고,
> src/api/users.ts의 쿼리가 올바른지 검증해줘
```

### 🐛 에러 추적 + 코드 수정
```
> Sentry에서 가장 빈번한 에러를 확인하고,
> 관련 코드를 찾아서 수정해줘
```

### 📋 이슈 → 구현
```
> GitHub 이슈 #42의 내용을 확인하고,
> 구현 계획을 세운 뒤 코드를 작성해줘
```

### 🔎 검색 + 적용
```
> Next.js 15에서 바뀐 캐싱 전략을 검색하고,
> 우리 프로젝트에 적용할 부분을 알려줘
```

## 팁

1. **너무 많이 연결하지 마세요** — 3-5개가 적당. 많으면 Claude가 혼란스러워합니다.
2. **환경변수 사용** — 토큰을 JSON에 하드코딩하지 마세요.
3. **프로젝트별 설정** — 글로벌보다 프로젝트 `.claude/mcp-servers.json`이 깔끔합니다.
4. **`/mcp`로 확인** — 세션 시작 시 서버 연결 상태를 체크하세요.

---

**상세 가이드:** [claude-code/playbooks/05-mcp-tools.md](../claude-code/playbooks/05-mcp-tools.md)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
