You are a Frontend Architect. Build the root layout and navigation for a SaaS analytics dashboard.

## Your files (create ONLY these — do not touch any other files):

### src/app/layout.tsx
Root layout with Inter font. Dark theme (#0F172A background).

### src/app/page.tsx
"use client". useState for active tab. 4 tabs: dashboard, analytics, settings, help.
Dashboard tab: TopBar + 4 KPI cards in a grid + 2 charts side by side.

### src/components/Sidebar.tsx
240px sidebar. Brand logo at top. 4 nav items with active state highlight.
User avatar and plan badge at bottom.

### src/components/TopBar.tsx
Search input + notification bell + user menu.

## Tech stack: Next.js 15 + React 19 + Tailwind CSS 4

Create all files now, in order: layout.tsx → page.tsx → Sidebar.tsx → TopBar.tsx.
