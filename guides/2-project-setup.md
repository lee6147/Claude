# 가이드 02: 프로젝트 초기 설정

> CLAUDE.md부터 첫 커밋까지 — 새 프로젝트에 Claude Code를 세팅하는 전체 과정

## 소요 시간

10-15분

## 사전 준비

- Claude Code CLI 설치 완료 (`npm install -g @anthropic-ai/claude-code`)
- 프로젝트 레포지토리 존재

## Step 1: CLAUDE.md 생성

```bash
# 템플릿 복사
cp /path/to/CLAUDE.md.template ./CLAUDE.md

# 또는 직접 다운로드
curl -O https://raw.githubusercontent.com/tenbuilder/tenbuilder/main/claude-code/CLAUDE.md.template
mv CLAUDE.md.template CLAUDE.md
```

## Step 2: CLAUDE.md 커스터마이징

**필수 수정 항목:**

| 섹션 | 수정 내용 |
|------|----------|
| 프로젝트 개요 | 한 줄 설명 작성 |
| 기술 스택 | 실제 스택으로 교체 |
| 아키텍처 | 디렉토리 구조 반영 |
| 코딩 규칙 | 팀 컨벤션 반영 |
| 명령어 | 실제 스크립트 반영 |

**핵심 원칙:**

- **50-100줄 유지** — 길면 Claude가 무시합니다
- **구체적으로** — "좋은 코드 작성" ❌ → "함수는 20줄 이하" ✅
- **금지 사항 명시** — "하지 말 것"이 "해야 할 것"보다 효과적

## Step 3: .gitignore 확인

```bash
# .claude/ 폴더가 .gitignore에 있는지 확인
grep -q '.claude/' .gitignore || echo '.claude/' >> .gitignore
```

## Step 4: 첫 세션 시작

```bash
# 프로젝트 루트에서 실행
claude

# 첫 대화에서 확인
> "CLAUDE.md를 읽고 이 프로젝트의 기술 스택과 규칙을 요약해줘"
```

**정상 동작 확인:**
- [ ] 기술 스택을 정확히 인식
- [ ] 코딩 규칙을 따르는 코드 생성
- [ ] 금지 사항을 위반하지 않음

## Step 5: 점진적 개선

첫 세션 후 CLAUDE.md를 보완합니다:

```markdown
## 자주 하는 실수 방지

<!-- 실제 세션에서 발생한 문제를 추가 -->
- prisma generate 후 타입 재생성 필요
- Next.js 13+ App Router에서 "use client" 누락 주의
```

## 체크리스트

- [ ] CLAUDE.md 생성 및 커스터마이징
- [ ] .gitignore에 `.claude/` 추가
- [ ] 첫 세션에서 인식 확인
- [ ] 팀원과 CLAUDE.md 공유 (선택)

## 다음 단계

→ [03. 일일 AI 코딩 루틴](./03-daily-workflow.md)
