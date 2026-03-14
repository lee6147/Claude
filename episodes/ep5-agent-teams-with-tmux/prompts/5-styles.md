You are a UX Designer. Build the design system CSS for a SaaS analytics dashboard.

## Your file (create ONLY this one file):
- src/app/globals.css

## Requirements:

### 1. Tailwind import: `@import "tailwindcss";`

### 2. CSS custom properties (:root):
--background: #0F172A; --foreground: #F8FAFC;
--accent-cyan: #22D3EE; --accent-purple: #A78BFA;
--accent-green: #34D399; --accent-orange: #FB923C;
--text-dim: #94A3B8; --text-muted: #64748B;

### 3. Glass card (.glass-card):
Semi-transparent background, backdrop-blur, subtle border.
Hover: slight scale + glow effect.

### 4. Ambient background (.ambient-bg):
Two floating gradient orbs (cyan + purple) with slow drift animation.

### 5. Animations:
- fadeInUp (staggered grid items)
- shimmer (loading skeleton)
- Custom scrollbar (thin, transparent track)

### 6. Body defaults:
Dark background, light text, antialiased rendering.

Create the complete globals.css file now.
