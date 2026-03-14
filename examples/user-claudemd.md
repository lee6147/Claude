# CLAUDE.md 예시: 사용자 전역 설정

> `~/.claude/CLAUDE.md`에 개인 선호도와 전역 규칙을 설정하는 템플릿

## 이 파일의 역할

`~/.claude/CLAUDE.md`는 **모든 프로젝트에 적용되는 개인 설정**이에요. 프로젝트별 `.claude/CLAUDE.md`와 별개로, 어떤 프로젝트를 열어도 항상 적용돼요.

```
~/.claude/CLAUDE.md          ← 전역 (이 파일)
my-project/.claude/CLAUDE.md ← 프로젝트별 (프로젝트에만 적용)
```

## 템플릿

```markdown
# CLAUDE.md (User Global)

## 기본 규칙

- 한국어로 응답해줘
- 코드 블록과 명령어는 영어 유지
- 불확실한 정보는 "불확실합니다"라고 명시해줘
- 과도한 칭찬이나 감정 표현 금지

## 코딩 스타일

- TypeScript 선호 (JavaScript보다)
- 함수형 패턴 선호 (class보다)
- 변수명: camelCase
- 파일명: kebab-case
- 들여쓰기: 2 spaces
- 세미콜론: 사용하지 않음

## Git 규칙

- 커밋 메시지: 영어, Conventional Commits
- 브랜치: feature/, fix/, chore/ 접두사
- main 직접 push 금지
- PR 생성 전 rebase 수행
- `.claude/` 폴더는 커밋하지 않음

## 자주 쓰는 도구

- Package Manager: pnpm
- Formatter: Biome (Prettier 대신)
- Linter: ESLint + Biome
- Test: Vitest
- E2E: Playwright

## 프로젝트 디렉토리

- 개인 프로젝트: ~/projects/
- 회사: ~/work/
- 사이드: ~/side-projects/

## 에이전트 사용 규칙

- 서브에이전트 모델: Haiku (비용 절감)
- 파일 탐색은 Glob/Grep 우선 (Agent 불필요)
- 복잡한 리서치만 Agent tool 사용
```

## 섹션별 설명

### 기본 규칙

AI의 응답 언어, 톤, 불확실성 처리 방식을 정의해요. Claude Code는 이 설정을 모든 대화에 적용해요.

### 코딩 스타일

선호하는 코드 스타일을 명시하면 AI가 해당 스타일로 코드를 생성해요. 팀 컨벤션과 다를 경우 프로젝트별 CLAUDE.md에서 오버라이드할 수 있어요.

### Git 규칙

커밋, 브랜치, PR 관련 규칙이에요. 이 규칙이 없으면 AI가 main에 직접 push하거나 불필요한 파일을 커밋할 수 있어요.

### 도구 설정

패키지 매니저, 포맷터 등을 명시하면 `npm install` 대신 `pnpm install`을 사용하는 식으로 자동 적용돼요.

## 프로젝트별 오버라이드

프로젝트 CLAUDE.md는 전역 설정을 **덮어쓸 수 있어요**:

```markdown
# my-project/CLAUDE.md

## 코딩 스타일
- 들여쓰기: 4 spaces (전역 설정 2 spaces를 오버라이드)
- 세미콜론: 사용

## 이 프로젝트 전용
- Django 5.x + Python 3.12
- ruff로 포맷팅 (Biome 대신)
- pytest로 테스트 (Vitest 대신)
```

## 고급: 모듈화 패턴

CLAUDE.md가 길어지면 외부 파일을 참조할 수 있어요:

```markdown
# CLAUDE.md

## 코딩 규칙
@./docs/coding-rules.md

## API 패턴
@./docs/api-patterns.md
```

> `@` 문법으로 별도 파일을 로딩해요. CLAUDE.md를 깔끔하게 유지하면서 상세 규칙은 분리할 수 있어요.

## 실전 팁

| 상황 | 권장 |
|------|------|
| 개인 프로젝트 | 전역 CLAUDE.md만으로 충분 |
| 팀 프로젝트 | 프로젝트 CLAUDE.md를 git에 커밋 |
| 오픈소스 | CLAUDE.md + CONTRIBUTING.md 병행 |
| 여러 언어 | 프로젝트별 CLAUDE.md에서 언어별 규칙 |

---

📬 매주 AI 코딩 팁을 받아보세요 → [maily.so/tenbuilder](https://maily.so/tenbuilder)
