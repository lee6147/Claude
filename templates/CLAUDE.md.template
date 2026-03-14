# [PROJECT_NAME]

## 프로젝트 개요

[한 줄 설명: 이 프로젝트가 무엇이고 누구를 위한 것인지]

## 기술 스택

- **Language:** [TypeScript / Python / Kotlin / Go]
- **Framework:** [Next.js / Spring Boot / FastAPI / ...]
- **Database:** [PostgreSQL / MongoDB / ...]
- **Infra:** [AWS / GCP / Vercel / ...]

## 아키텍처

```
[간단한 디렉토리 구조 또는 아키텍처 설명]
src/
├── api/          # API 라우트
├── components/   # UI 컴포넌트
├── lib/          # 유틸리티
└── types/        # 타입 정의
```

## 코딩 규칙

### 필수

- [예: 모든 함수에 JSDoc 주석 작성]
- [예: 에러 핸들링은 Result 패턴 사용]
- [예: 테스트 파일은 `__tests__/` 디렉토리에 배치]

### 금지

- [예: `any` 타입 사용 금지]
- [예: `console.log` 커밋 금지 — logger 사용]
- [예: 환경변수 직접 참조 금지 — config 모듈 사용]

## 명령어

```bash
# 개발
[npm run dev / ./gradlew bootRun / ...]

# 테스트
[npm test / ./gradlew test / ...]

# 빌드
[npm run build / ./gradlew build / ...]

# 린트
[npm run lint / ...]
```

## 환경변수

| 변수 | 설명 | 필수 |
|------|------|------|
| `DATABASE_URL` | DB 연결 문자열 | ✅ |
| `API_KEY` | 외부 API 키 | ✅ |

> ⚠️ `.env` 파일은 절대 커밋하지 않음

## Git 규칙

- 커밋 메시지: Conventional Commits (`feat:`, `fix:`, `chore:`)
- 브랜치: `feature/`, `fix/`, `chore/` 접두사
- main 직접 커밋 금지 — PR 필수
- `.claude/` 폴더는 `.gitignore`에 포함

## 작업 승인

### 자동 진행 (확인 불필요)

- 파일 읽기, 검색
- 테스트 실행
- 린트/포맷

### 확인 필요

- 파일 생성/수정/삭제
- 패키지 설치/삭제
- Git 커밋/푸시
- DB 변경

## 자주 하는 실수 방지

- [예: `prisma migrate dev`는 로컬에서만 실행]
- [예: API 응답에 민감 정보 포함 주의]
- [예: 타임존은 항상 UTC 기준]
