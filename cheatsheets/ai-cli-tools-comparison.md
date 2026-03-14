# AI CLI 도구 비교 — Claude Code vs Codex CLI vs Gemini CLI

> 2026년 터미널 AI 코딩 도구 3대장 기능 비교 — 한 페이지 요약

## 한눈에 비교

| 항목 | Claude Code | Codex CLI | Gemini CLI |
|------|-------------|-----------|------------|
| **제작사** | Anthropic | OpenAI | Google |
| **기본 모델** | Claude Opus 4.6 | GPT-5.4 / 5.3-codex | Gemini 3.1 Pro |
| **컨텍스트 윈도우** | 1M 토큰 (베타) | 400K 토큰 | 2M 토큰 |
| **컨텍스트 관리** | 자동 컴팩션 | 수동 청킹 | 자동 슬라이딩 |
| **가격 모델** | API 종량제 / Max 구독 | API 종량제 | 무료 티어 + API |
| **MCP 지원** | ✅ 네이티브 | ✅ (v0.104+) | ⚠️ 제한적 |
| **에이전트 팀** | ✅ subagent 패턴 | ✅ AGENTS.md | ❌ |
| **Skills/Rules** | CLAUDE.md + Skills | AGENTS.md + Skills | 설정 파일 |
| **Git 통합** | 내장 (커밋, PR) | GitHub 딥 통합 | 기본 수준 |
| **IDE 연동** | 터미널 독립 | 터미널 독립 | IDE 플러그인 별도 |

## 각 도구의 강점

### Claude Code — 시니어 개발자 느낌

```bash
# 대화형으로 복잡한 리팩토링 진행
claude

# 파이프로 자동화 스크립트에 연결
echo "이 함수를 분석해줘" | claude -p

# 멀티 에이전트로 병렬 작업
claude --agent refactor-agent
```

**이럴 때 선택하세요:**
- 대규모 코드베이스 리팩토링
- 여러 파일을 동시에 수정하는 작업
- 맥락이 중요한 아키텍처 설계
- 대화하면서 점진적으로 구체화하는 작업

### Codex CLI — 효율적인 실행자

```bash
# 원샷 실행 (빠른 코드 생성)
codex exec "JWT 인증 미들웨어를 만들어줘"

# stdin 파이프 (자동화에 적합)
echo "이 파일의 타입 에러를 수정해" | codex exec - --full-auto

# reasoning 활성화
# config.toml에서 model_reasoning_effort = "high"
```

**이럴 때 선택하세요:**
- 명확한 지시로 빠르게 코드 생성
- GitHub Actions/CI 파이프라인 연동
- 배치 처리나 자동화 스크립트
- 코딩 특화 작업 (5.3-codex 모델)

### Gemini CLI — 가성비 탐색기

```bash
# 무료 티어로 간단한 작업
gemini "이 에러 메시지 해석해줘"

# 긴 파일 분석 (2M 컨텍스트)
cat large-codebase.txt | gemini "구조를 분석해줘"
```

**이럴 때 선택하세요:**
- 비용을 최소화하고 싶을 때
- 매우 긴 파일/로그 분석
- 간단한 코드 생성이나 설명
- 프로젝트 계획 수립이나 문서 정리

## 실전 선택 가이드

| 상황 | 추천 도구 | 이유 |
|------|-----------|------|
| 레거시 코드 리팩토링 | Claude Code | 컨텍스트 이해력, 점진적 대화 |
| CI/CD 자동화 스크립트 | Codex CLI | GitHub 통합, 원샷 실행 |
| 긴 로그 파일 분석 | Gemini CLI | 2M 컨텍스트, 무료 티어 |
| PR 자동 리뷰 | Codex CLI | GitHub Actions 연동 |
| 아키텍처 설계 상담 | Claude Code | 추론 깊이, 대화형 |
| 빠른 코드 스니펫 생성 | Codex CLI | 속도, --full-auto |
| 비용 제한된 사이드 프로젝트 | Gemini CLI | 무료 쿼터 |
| 멀티 에이전트 병렬 작업 | Claude Code | subagent 패턴 |

## 벤치마크 요약 (2026 Q1)

| 벤치마크 | Claude Code | Codex CLI | Gemini CLI |
|----------|-------------|-----------|------------|
| SWE-bench Verified | 72.7% | 69.1% | 63.8% |
| Terminal-Bench | 68.2% | 71.5% | 58.4% |
| OSWorld-Verified | **74.1%** | 65.3% | 61.2% |
| HumanEval+ | 95.1% | **96.3%** | 93.7% |

> SWE-bench: 실제 GitHub 이슈 해결 능력. Terminal-Bench: 터미널 작업 자동화. OSWorld: OS 수준 태스크.

## 함께 사용하기 — 3도구 조합 패턴

```bash
# 1단계: Gemini로 계획 수립 (비용 절약)
gemini "이 프로젝트의 리팩토링 계획을 세워줘" > plan.md

# 2단계: Claude Code로 핵심 구현 (품질 중심)
claude  # plan.md 기반으로 대화하며 구현

# 3단계: Codex로 테스트 자동 생성 (속도 중심)
echo "src/ 디렉토리의 모든 함수에 대해 테스트를 생성해" | codex exec - --full-auto
```

## 설치 & 설정

| 도구 | 설치 | 설정 파일 |
|------|------|-----------|
| Claude Code | `npm install -g @anthropic-ai/claude-code` | `CLAUDE.md`, `~/.claude/settings.json` |
| Codex CLI | `npm install -g @openai/codex` | `~/.codex/config.toml` |
| Gemini CLI | `npm install -g @google/gemini-cli` | `~/.gemini/settings.json` |

## 흔한 실수 & 해결

| 실수 | 해결 |
|------|------|
| Claude Code에서 컨텍스트 초과 | `/clear`로 리셋, 필요한 파일만 명시적으로 지정 |
| Codex에서 모델 지정 안 함 | `config.toml`에 `model = "gpt-5.4"` 명시 |
| Gemini 무료 쿼터 소진 | 일일 한도 확인, API 키 유료 전환 검토 |
| 멀티 도구 사용 시 설정 충돌 | 각 도구의 설정 파일 경로 분리 확인 |
| MCP 서버 연결 실패 | Claude Code: `claude mcp list`로 상태 확인 |

---

**더 자세한 가이드:** [claude-code/playbooks](../claude-code/playbooks/)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
