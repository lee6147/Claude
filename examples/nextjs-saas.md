# CLAUDE.md 예시: Next.js SaaS

> Next.js 15 + Supabase + Stripe 기반 SaaS 프로젝트용 CLAUDE.md 템플릿

## 프로젝트 개요

```markdown
# CLAUDE.md

## Project
- Next.js 15 (App Router) + TypeScript
- Supabase (Auth, Database, Storage)
- Stripe (결제)
- Tailwind CSS + shadcn/ui
- Package Manager: pnpm
```

## 기술 스택 규칙

### 데이터베이스 (Supabase)

```markdown
## Database Rules
- Always use Row Level Security (RLS) — no exceptions
- Select explicit columns, never SELECT *
- Use Supabase types from `database.types.ts`
- Migrations go in `supabase/migrations/`

## Auth Pattern
- Server: `createServerClient(cookies)`
- Client: `createBrowserClient()`
- Middleware: `updateSession()` in middleware.ts
- Never expose service_role key in client code
```

### 서버 액션 패턴

```typescript
// app/actions/create-project.ts
"use server"

import { z } from "zod"
import { createServerClient } from "@/lib/supabase/server"
import { revalidatePath } from "next/cache"

const schema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().optional(),
})

export async function createProject(formData: FormData) {
  const parsed = schema.safeParse({
    name: formData.get("name"),
    description: formData.get("description"),
  })

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors }
  }

  const supabase = await createServerClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return { error: "Unauthorized" }
  }

  const { error } = await supabase
    .from("projects")
    .insert({ ...parsed.data, user_id: user.id })

  if (error) {
    return { error: error.message }
  }

  revalidatePath("/dashboard")
  return { success: true }
}
```

> **핵심 패턴:** Zod 검증 → Auth 확인 → DB 조작 → revalidatePath

### 결제 (Stripe)

```markdown
## Billing Rules
- Webhook handler: `app/api/webhooks/stripe/route.ts`
- Always verify webhook signature
- Sync subscription status to Supabase `subscriptions` table
- Price IDs in environment variables, never hardcoded
```

## 디렉토리 구조

```markdown
## File Structure
app/
├── (auth)/           # Auth routes (login, signup)
├── (dashboard)/      # Protected routes
│   ├── layout.tsx    # Auth guard
│   └── settings/
├── api/
│   └── webhooks/     # Stripe, Supabase webhooks
├── actions/          # Server Actions
└── layout.tsx        # Root layout

lib/
├── supabase/
│   ├── server.ts     # Server client factory
│   ├── client.ts     # Browser client factory
│   └── middleware.ts  # Session refresh
├── stripe.ts         # Stripe client
└── utils.ts          # Shared utilities

components/
├── ui/               # shadcn/ui components
├── forms/            # Form components
└── layout/           # Layout components
```

## 코딩 컨벤션

```markdown
## Conventions
- Use Server Components by default
- "use client" only when needed (interactivity, hooks)
- Error handling: Server Actions return { error } | { success }
- Loading: Suspense + loading.tsx per route
- Environment: .env.local for secrets (never commit)

## Commands
- `pnpm dev` — development server
- `pnpm build` — production build
- `pnpm test` — run tests
- `pnpm db:migrate` — apply migrations
- `pnpm db:types` — regenerate Supabase types
```

## 보안 체크리스트

```markdown
## Security
- [ ] RLS enabled on all tables
- [ ] Server Actions validate input with Zod
- [ ] Stripe webhooks verify signature
- [ ] No secrets in client-side code
- [ ] middleware.ts protects dashboard routes
```

## 실전 팁

| 상황 | 패턴 |
|------|------|
| 데이터 패칭 | Server Component에서 직접 Supabase 호출 |
| 폼 제출 | Server Action + `useFormState` |
| 실시간 데이터 | Supabase Realtime subscription (Client Component) |
| 파일 업로드 | Supabase Storage + presigned URL |
| 캐시 무효화 | `revalidatePath()` 또는 `revalidateTag()` |

> 이 템플릿을 프로젝트 루트의 `CLAUDE.md`에 복사하고, 프로젝트 이름/테이블명을 수정해서 사용하세요.

---

📬 매주 AI 코딩 팁을 받아보세요 → [maily.so/tenbuilder](https://maily.so/tenbuilder)
