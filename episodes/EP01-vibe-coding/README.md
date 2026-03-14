# EP01: 바이브 코딩 — 코드를 모르는 사람도 앱을 만드는 시대

> Andrej Karpathy가 제안한 "바이브 코딩" 개념을 실전으로 옮기는 핵심 코드와 프롬프트 모음

## 📺 영상

**[YouTube에서 보기](https://youtube.com/@ten-builder)**

## 이 에피소드에서 다루는 것

- 바이브 코딩이란 무엇인지, 왜 2025년 이후 주류가 되었는지
- 자연어로 앱을 만드는 실전 워크플로우
- Claude Code / Cursor / Replit을 사용한 바이브 코딩 비교
- 바이브 코딩의 한계와 실전에서 주의할 점

## 바이브 코딩이란?

2025년 2월 Andrej Karpathy가 트윗으로 소개한 개념이에요. 핵심은 간단해요:

> "코드를 직접 쓰지 않고, AI에게 자연어로 설명해서 소프트웨어를 만든다."

기존 개발이 "코드를 작성하는 것"이었다면, 바이브 코딩은 **"의도를 전달하는 것"**에 집중해요.

## 핵심 코드 & 설정

### Claude Code로 바이브 코딩 시작하기

```bash
# Claude Code 설치
npm install -g @anthropic-ai/claude-code

# 프로젝트 시작 — 코드를 직접 쓸 필요 없어요
cd my-project
claude

# 이제 자연어로 대화하면 됩니다
```

### CLAUDE.md 프로젝트 설정 예시

```markdown
# 프로젝트 컨텍스트

이 프로젝트는 할 일 관리 웹앱입니다.

## 기술 스택
- Frontend: React + TypeScript
- Backend: FastAPI
- DB: SQLite

## 규칙
- 컴포넌트는 함수형으로 작성
- API 응답은 항상 Pydantic 모델로 정의
- 테스트는 pytest로 작성
```

### Cursor에서 바이브 코딩하기

```
# Cursor Composer (Cmd+I)에서 사용하는 프롬프트 예시

"사용자 인증 기능을 추가해줘.
- 이메일/비밀번호 로그인
- JWT 토큰 발급
- 로그인 상태 유지는 localStorage 사용
- 로그아웃 버튼도 추가"
```

## 실전 프롬프트 모음

### 1단계: 프로젝트 초기 설정

```
React + TypeScript로 할 일 관리 앱을 만들어줘.
Tailwind CSS를 사용하고, 다크 모드를 지원해야 해.
할 일 추가, 완료 체크, 삭제 기능이 필요해.
```

### 2단계: 기능 확장

```
할 일에 우선순위(높음/중간/낮음)를 추가해줘.
우선순위별로 색상을 다르게 표시하고,
우선순위 순서로 정렬할 수 있게 해줘.
```

### 3단계: 코드 개선

```
현재 코드에서 반복되는 패턴을 찾아서
커스텀 훅으로 추출해줘. 상태 관리 로직이
컴포넌트에 직접 있으면 분리해줘.
```

## 바이브 코딩 vs 전통적 개발

| 항목 | 전통적 개발 | 바이브 코딩 |
|------|------------|------------|
| 입력 | 코드 작성 | 자연어 설명 |
| 디버깅 | 로그 분석 + 직접 수정 | 에러 메시지를 AI에 전달 |
| 학습 곡선 | 높음 (문법, 프레임워크) | 낮음 (의도 전달 능력) |
| 코드 품질 | 개발자 역량에 비례 | 프롬프트 품질에 비례 |
| 적합한 상황 | 대규모 프로덕션 | 프로토타입, MVP, 사이드 프로젝트 |

## 주의할 점

바이브 코딩이 편리하지만, 실전에서 주의해야 할 부분이 있어요:

1. **코드 리뷰는 필수** — AI가 생성한 코드도 반드시 검토해야 해요
2. **보안 취약점 확인** — 인증, 입력 검증 등은 직접 확인이 필요해요
3. **테스트 작성** — 바이브 코딩으로 만든 코드도 테스트가 있어야 안전해요
4. **프로젝트가 커지면 구조 설계가 중요** — 초기에 CLAUDE.md로 규칙을 잡아두면 좋아요

## 추천 도구 (2026년 기준)

| 도구 | 특징 | 가격 |
|------|------|------|
| Claude Code | CLI 기반, 대규모 코드베이스에 적합 | API 사용량 기반 |
| Cursor | IDE 통합, Composer로 멀티파일 편집 | $20/월 |
| Replit | 브라우저에서 바로 실행, 배포까지 원클릭 | 무료 ~ $25/월 |
| Lovable | UI 중심, 디자인→코드 변환에 특화 | $20/월 |

## 따라하기

### Step 1: Claude Code 설치

```bash
# Node.js 18+ 필요
npm install -g @anthropic-ai/claude-code

# API 키 설정
export ANTHROPIC_API_KEY="your-key"
```

### Step 2: 첫 프로젝트 만들기

```bash
mkdir vibe-coding-demo && cd vibe-coding-demo
claude

# Claude Code에서 입력:
# "React + Vite로 카운터 앱을 만들어줘. 
#  증가, 감소, 리셋 버튼이 있고 Tailwind CSS를 사용해."
```

### Step 3: 실행 및 확인

```bash
npm run dev
# http://localhost:5173 에서 확인
```

## 더 알아보기

- [Andrej Karpathy의 원본 트윗](https://x.com/karpathy/status/1886192184808149383)
- [Google Cloud — Vibe Coding 가이드](https://cloud.google.com/discover/what-is-vibe-coding)
- [Replit — How to Vibe Code](https://docs.replit.com/tutorials/how-to-vibe-code)
- [바이브 코딩 워크플로우 가이드](https://dev.to/wasp/a-structured-workflow-for-vibe-coding-full-stack-apps-352l)

---

**구독하기:** [@ten-builder](https://youtube.com/@ten-builder) | [뉴스레터](https://maily.so/tenbuilder)
