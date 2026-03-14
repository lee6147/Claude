# Next.js + Claude Code 실전 예제

> Claude Code로 Next.js 프로젝트를 처음부터 구축하는 단계별 가이드

## 이 예제에서 배울 수 있는 것

- Next.js App Router 프로젝트를 Claude Code로 빠르게 셋업하는 방법
- CLAUDE.md 파일로 프로젝트 컨텍스트를 정확하게 전달하는 패턴
- AI와 함께 컴포넌트, API 라우트, 테스트를 단계적으로 만드는 워크플로우

## 프로젝트 구조

```
nextjs-claude-code/
├── CLAUDE.md              # Claude Code 프로젝트 설정
├── src/
│   ├── app/
│   │   ├── layout.tsx     # 루트 레이아웃
│   │   ├── page.tsx       # 메인 페이지
│   │   └── api/
│   │       └── posts/
│   │           └── route.ts  # API 라우트
│   ├── components/
│   │   ├── PostCard.tsx   # 포스트 카드 컴포넌트
│   │   └── PostList.tsx   # 포스트 목록
│   └── lib/
│       └── types.ts       # 타입 정의
├── __tests__/
│   └── PostCard.test.tsx  # 컴포넌트 테스트
├── package.json
└── tsconfig.json
```

## 시작하기

### Step 1: 프로젝트 생성

```bash
pnpm create next-app@latest my-app --typescript --tailwind --app --src-dir
cd my-app
```

### Step 2: CLAUDE.md 작성

프로젝트 루트에 `CLAUDE.md`를 만들어 Claude Code에 컨텍스트를 전달해요.

```markdown
# CLAUDE.md

## Project
- Next.js 15 (App Router) + TypeScript
- Tailwind CSS v4
- Package Manager: pnpm

## Rules
- 컴포넌트는 src/components/에 생성
- Server Component 기본, 필요할 때만 "use client"
- API 라우트는 src/app/api/에 Route Handler로 작성
- zod로 입력 검증

## Commands
- dev: pnpm dev
- build: pnpm build
- test: pnpm vitest
```

이 파일이 있으면 Claude Code가 프로젝트 구조와 규칙을 자동으로 이해해요.

### Step 3: Claude Code로 타입 정의

Claude Code에 다음과 같이 요청해요:

```
블로그 포스트 타입을 정의해줘. id, title, content, createdAt 필드가 필요해.
src/lib/types.ts에 만들어줘.
```

생성 결과:

```typescript
// src/lib/types.ts
export interface Post {
  id: string
  title: string
  content: string
  createdAt: Date
}

export interface CreatePostInput {
  title: string
  content: string
}
```

## 핵심 코드

### PostCard 컴포넌트

Claude Code에 "PostCard 컴포넌트를 만들어줘. Post 타입을 받아서 카드 형태로 렌더링" 이라고 요청하면:

```tsx
// src/components/PostCard.tsx
import { Post } from "@/lib/types"

interface PostCardProps {
  post: Post
}

export function PostCard({ post }: PostCardProps) {
  const formattedDate = new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(post.createdAt))

  return (
    <article className="rounded-lg border p-6 hover:shadow-md transition-shadow">
      <h2 className="text-xl font-semibold mb-2">{post.title}</h2>
      <p className="text-gray-600 mb-4 line-clamp-3">{post.content}</p>
      <time className="text-sm text-gray-400">{formattedDate}</time>
    </article>
  )
}
```

### API 라우트

```typescript
// src/app/api/posts/route.ts
import { NextResponse } from "next/server"
import { z } from "zod"

const createPostSchema = z.object({
  title: z.string().min(1).max(200),
  content: z.string().min(1),
})

// 임시 인메모리 저장소
const posts: Array<{ id: string; title: string; content: string; createdAt: Date }> = []

export async function GET() {
  return NextResponse.json(posts)
}

export async function POST(request: Request) {
  const body = await request.json()
  const parsed = createPostSchema.safeParse(body)

  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.flatten().fieldErrors },
      { status: 400 }
    )
  }

  const newPost = {
    id: crypto.randomUUID(),
    ...parsed.data,
    createdAt: new Date(),
  }

  posts.push(newPost)
  return NextResponse.json(newPost, { status: 201 })
}
```

## AI 사용 포인트

| 상황 | 프롬프트 예시 |
|------|-------------|
| 컴포넌트 생성 | `PostList 컴포넌트를 만들어줘. /api/posts에서 데이터를 가져와서 PostCard로 렌더링해줘` |
| 테스트 작성 | `PostCard 컴포넌트 테스트를 vitest로 작성해줘. 날짜 포맷팅이 맞는지 확인` |
| 에러 핸들링 | `API 라우트에 에러 핸들링 추가해줘. try-catch랑 적절한 HTTP 상태 코드로` |
| 리팩토링 | `PostList에서 데이터 fetching 로직을 커스텀 훅으로 분리해줘` |
| 스타일링 | `PostCard에 다크모드 지원 추가해줘. Tailwind dark: 클래스 사용` |

## 효과적인 Claude Code 사용 팁

### 1. 단계적으로 요청하기

한 번에 전체 앱을 만들어달라고 하는 것보다, 작은 단위로 나눠서 요청하면 결과가 좋아요.

```
❌ "블로그 앱 전체를 만들어줘"
✅ "Post 타입을 정의해줘" → "PostCard 컴포넌트를 만들어줘" → "API 라우트를 추가해줘"
```

### 2. 기존 코드 참조하기

새 코드를 만들 때 기존 파일을 참조하도록 알려주면 일관성이 유지돼요.

```
PostCard.tsx와 같은 스타일로 CommentCard 컴포넌트를 만들어줘
```

### 3. 테스트 먼저 요청하기

TDD 방식으로 테스트를 먼저 작성하게 하면 요구사항이 명확해져요.

```
PostCard가 title, content, 포맷된 날짜를 렌더링하는지 테스트를 먼저 작성해줘.
그다음에 테스트를 통과하는 컴포넌트를 만들어줘.
```

## 테스트 예제

```tsx
// __tests__/PostCard.test.tsx
import { render, screen } from "@testing-library/react"
import { PostCard } from "@/components/PostCard"

describe("PostCard", () => {
  const mockPost = {
    id: "1",
    title: "테스트 포스트",
    content: "이것은 테스트 콘텐츠입니다.",
    createdAt: new Date("2026-03-01"),
  }

  it("제목을 렌더링한다", () => {
    render(<PostCard post={mockPost} />)
    expect(screen.getByText("테스트 포스트")).toBeInTheDocument()
  })

  it("콘텐츠를 렌더링한다", () => {
    render(<PostCard post={mockPost} />)
    expect(screen.getByText("이것은 테스트 콘텐츠입니다.")).toBeInTheDocument()
  })

  it("한국어 날짜 포맷을 표시한다", () => {
    render(<PostCard post={mockPost} />)
    expect(screen.getByText("2026년 3월 1일")).toBeInTheDocument()
  })
})
```

---

**더 자세한 가이드:** [claude-code/playbooks](../../claude-code/playbooks/)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
