# 가이드 01: AI 코딩 환경 세팅

> AI로 10배 빠르게 빌드하기 위한 환경을 30분 안에 세팅하는 가이드

## AI 코딩 도구 선택

| 도구 | 용도 | 설치 |
|------|------|------|
| **Claude Code** | CLI 기반 AI 코딩 | `npm i -g @anthropic-ai/claude-code` |
| **Cursor** | AI IDE | [cursor.sh](https://cursor.sh) |
| **GitHub Copilot** | 인라인 자동완성 | VS Code 확장 |

**추천 조합:** Claude Code (아키텍처/리팩토링) + Copilot (인라인 완성)

## Quick Start

```bash
# macOS 원클릭 설정
curl -sSL https://raw.githubusercontent.com/ten-builder/ten-builder/main/templates/macos-setup.sh | bash
```

수동 설치를 원한다면 아래 단계를 따라하세요.

## 수동 설치

### 1. Claude Code 설치

```bash
npm install -g @anthropic-ai/claude-code
```

### 2. 프로젝트 설정 파일 복사

```bash
# Claude Code 설정 — 프로젝트 루트에 CLAUDE.md 배치
curl -O https://raw.githubusercontent.com/ten-builder/ten-builder/main/templates/CLAUDE.md.template
mv CLAUDE.md.template CLAUDE.md
# 프로젝트에 맞게 수정 후 사용

# Cursor 설정 (선택)
curl -O https://raw.githubusercontent.com/ten-builder/ten-builder/main/templates/cursorrules.template
mv cursorrules.template .cursorrules

# AI 관련 shell alias (선택)
curl -O https://raw.githubusercontent.com/ten-builder/ten-builder/main/templates/.zshrc.ai
cat .zshrc.ai >> ~/.zshrc && source ~/.zshrc
rm .zshrc.ai
```

### 3. MCP 서버 연결 (선택)

MCP(Model Context Protocol)를 연결하면 Claude Code가 GitHub, DB 등 외부 도구에 직접 접근할 수 있어요.

```bash
# 예: GitHub MCP 서버 추가
claude mcp add github npx -y @anthropic-ai/mcp-github
```

자세한 내용은 [08. MCP 도구 활용](./08-mcp-tools.md)을 참고하세요.

## 확인

```bash
# Claude Code가 정상 작동하는지 확인
claude --version
claude "안녕, 테스트야"
```

## 다음 단계

→ [02. 프로젝트 초기 설정](./02-project-setup.md)
