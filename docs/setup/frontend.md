---
title: "Frontend Setup Guide"
type: "setup"
difficulty: "intermediate"
time: "30 minutes"
last_updated: "2026-05-29"
ai_summary: "Next.js 16 + TypeScript + Tailwind CSS + shadcn/ui frontend setup"
---

# Frontend Setup Guide

Complete guide to set up the AltCare Next.js 16 frontend with TypeScript, Tailwind CSS, and shadcn/ui.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Project Initialization](#project-initialization)
- [Install Dependencies](#install-dependencies)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Environment Setup](#environment-setup)
- [Start Development](#start-development)
- [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

**Required Software:**
- Node.js 18+ (LTS 20.x recommended)
- npm 9+ (this project uses npm/`package-lock.json`, not pnpm or yarn)
- Git
- VS Code or WebStorm (recommended IDEs)

**Check Versions:**
```bash
node --version   # Should be 18.x or 20.x
npm --version    # Should be 9.x or higher
git --version    # Any recent version
```

**Backend Must Be Running:**
```bash
# Start backend in separate terminal
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Verify
curl http://localhost:8000/health
```

---

> **Note:** This section describes how the frontend was originally scaffolded. To work on the existing repo, skip to [Install Dependencies](#install-dependencies) and just run `cd frontend && npm install` against the checked-in `package.json` — do not re-run `create-next-app`.

## 🚀 Project Initialization

### Step 1: Create Next.js Project

```bash
# Navigate to project root
cd alternative-care

# Create Next.js app with TypeScript
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --import-alias "@/*"
```

**Prompts (answer as shown):**
```
✔ Would you like to use TypeScript? Yes
✔ Would you like to use ESLint? Yes
✔ Would you like to use Tailwind CSS? Yes
✔ Would you like to use `src/` directory? Yes
✔ Would you like to use App Router? Yes
✔ Would you like to customize the default import alias (@/*)? No
```

---

### Step 2: Navigate to Frontend

```bash
cd frontend
```

---

## 📦 Install Dependencies

### Core Dependencies

```bash
# API & State Management
npm install axios
npm install react-query
npm install zustand
npm install date-fns

# Form Handling
npm install react-hook-form
npm install @hookform/resolvers
npm install zod

# UI & Utilities
npm install next-intl
npm install js-cookie
npm install react-hot-toast
npm install recharts
npm install lucide-react

# Development Dependencies
npm install -D @types/js-cookie
```

---

### shadcn/ui Components

```bash
# Initialize shadcn/ui
npx shadcn@latest init
```

**Prompts (answer as shown):**
```
✔ Which style would you like to use? Default
✔ Which color would you like to use as base color? Slate
✔ Would you like to use CSS variables for colors? Yes
```

**Install Common Components:**
```bash
npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add card
npx shadcn@latest add table
npx shadcn@latest add dialog
npx shadcn@latest add dropdown-menu
npx shadcn@latest add select
npx shadcn@latest add label
npx shadcn@latest add form
npx shadcn@latest add toast
npx shadcn@latest add avatar
npx shadcn@latest add badge
npx shadcn@latest add tabs
npx shadcn@latest add calendar
```

---

## ⚙️ Configuration

### 1. TypeScript Configuration (`tsconfig.json`)

**Already created by Next.js, verify paths:**
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

---

### 2. Next.js Configuration (`next.config.js`)

**Update to proxy API requests:**
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Proxy API requests to backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
    ]
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // Image optimization
  images: {
    domains: ['localhost'],
  },
}

export default nextConfig
```

---

### 3. Tailwind Configuration (`src/app/globals.css`)

**Tailwind CSS 4 does not use `tailwind.config.ts`** — theme and dark-mode variant are configured directly in CSS via `@import` and `@custom-variant`, with color tokens as CSS custom properties:
```css
@import "tailwindcss";
@custom-variant dark (&:where(.dark, .dark *));

:root {
  --background: 255 255 255;
  --foreground: 15 23 42;
  --primary: 79 70 229;
  /* ...remaining design tokens */
}
```
There is no `tailwind.config.ts` file in this project — do not create one; add new tokens as CSS variables in `globals.css` instead.

---

### 4. ESLint Configuration (`.eslintrc.json`)

**Update to add TypeScript rules:**
```json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "warn",
    "@typescript-eslint/no-explicit-any": "warn",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

---

## 📁 Project Structure

**Actual structure (as of this audit):**
```
frontend/
├── public/
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   └── login/
│   │   ├── (dashboard)/
│   │   │   ├── admin/          # clients, users, KPI dashboard
│   │   │   ├── appointments/
│   │   │   ├── dashboard/
│   │   │   ├── medicines/
│   │   │   ├── patients/
│   │   │   ├── payments/
│   │   │   ├── prescriptions/
│   │   │   ├── profile/
│   │   │   ├── settings/       # integrations
│   │   │   └── symptoms/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── providers.tsx
│   │   └── globals.css         # Tailwind v4 theme tokens (no tailwind.config.ts)
│   ├── components/
│   │   ├── ui/              # shadcn/ui components
│   │   ├── layout/          # Sidebar, Header
│   │   ├── auth/, doctor/, dashboard/, patients/, prescriptions/,
│   │   │   payments/, integrations/, medicines/, theme/, shared/
│   ├── lib/
│   │   ├── api/             # API clients (one per module)
│   │   ├── hooks/           # React Query hooks
│   │   └── utils/           # Utilities
│   ├── types/               # TypeScript interfaces
│   ├── store/                # Zustand stores (authStore.ts, themeStore.ts)
│   └── messages/            # i18n message files (next-intl wired up — cookie-based, login/header covered so far)
│       ├── en.json
│       └── bn.json
├── .env.local
├── next.config.js
└── package.json
```

---

## 🔐 Environment Setup

### Create `.env.local`

```bash
# Create environment file
cat > .env.local << 'EOF'
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_TIMEOUT=30000

# Application
NEXT_PUBLIC_APP_NAME=AltCare
NEXT_PUBLIC_APP_VERSION=0.1.0
NEXT_PUBLIC_DEFAULT_LANGUAGE=en

# Feature Flags
NEXT_PUBLIC_FEATURE_2FA=true
NEXT_PUBLIC_FEATURE_BKASH=true
NEXT_PUBLIC_FEATURE_AI=false

# Development
NODE_ENV=development
EOF
```

**Variables:**
- `NEXT_PUBLIC_API_URL`: Backend API base URL
- `NEXT_PUBLIC_API_TIMEOUT`: API request timeout in ms
- `NEXT_PUBLIC_APP_NAME`: Application name
- `NEXT_PUBLIC_APP_VERSION`: Version number
- `NEXT_PUBLIC_DEFAULT_LANGUAGE`: Default language (en|bn)
- `NEXT_PUBLIC_FEATURE_2FA`, `NEXT_PUBLIC_FEATURE_BKASH`, `NEXT_PUBLIC_FEATURE_AI`: Feature flags

---

## ▶️ Start Development

### Start Dev Server

```bash
npm run dev
```

**Server starts at:** http://localhost:3000

**Verify:**
- Should see Next.js welcome page
- No build errors in terminal
- Hot reload works (edit `src/app/page.tsx`)

---

### Build for Production

```bash
# Type check
./node_modules/.bin/tsc -p tsconfig.json --noEmit

# Lint
npm run lint

# Build
npm run build

# Start production server
npm start
```

---

## 🐛 Troubleshooting

### Port 3000 Already in Use

```bash
# Use different port
PORT=3001 npm run dev

# Or kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

---

### API Proxy Not Working

**Check `next.config.js` rewrites:**
```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8000/api/v1/:path*',
    },
  ]
}
```

**Test API connection:**
```bash
# In browser console
fetch('/api/health')
  .then(r => r.json())
  .then(console.log)

# Should return: {status: "healthy", ...}
```

---

### shadcn/ui Components Not Found

```bash
# Reinstall shadcn/ui
npx shadcn@latest init

# Add missing component
npx shadcn@latest add <component-name>
```

---

### TypeScript Errors

```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules
npm install

# Run type check
./node_modules/.bin/tsc -p tsconfig.json --noEmit
```

---

### Build Fails

```bash
# Clear cache
rm -rf .next

# Clean install
rm -rf node_modules package-lock.json
npm install

# Try build again
npm run build
```

---

### Next.js 16 Dynamic Route Params Warning

Next.js 16 passes App Router dynamic route `params` to client pages as a promise. Client components must unwrap it with React `use()` before reading values.

```tsx
'use client'

import { use } from 'react'

export default function DetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const recordId = parseInt(id, 10)

  return <div>{recordId}</div>
}
```

Do not access `params.id` directly in client pages.

---

### Hydration Error: `<p>` Cannot Contain `<div>`

The local `Badge` component renders a `div`. Avoid rendering it inside paragraph tags.

```tsx
// Correct
<div className="mt-1">
  <Badge>Active</Badge>
</div>
```

```tsx
// Incorrect
<p className="mt-1">
  <Badge>Active</Badge>
</p>
```

---

## 🎨 Verify Setup

### 1. Check API Connection

**Create test page: `src/app/test/page.tsx`**
```tsx
'use client'

import { useEffect, useState } from 'react'

export default function TestPage() {
  const [health, setHealth] = useState<any>(null)
  
  useEffect(() => {
    fetch('/api/health')
      .then(r => r.json())
      .then(setHealth)
  }, [])
  
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">API Connection Test</h1>
      <pre className="mt-4 p-4 bg-gray-100 rounded">
        {JSON.stringify(health, null, 2)}
      </pre>
    </div>
  )
}
```

**Visit:** http://localhost:3000/test

**Should see:** Health check JSON response

---

### 2. Check Tailwind CSS

**Update `src/app/page.tsx`:**
```tsx
export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <div className="bg-blue-500 text-white p-8 rounded-lg">
        <h1 className="text-4xl font-bold">Tailwind Works! 🎉</h1>
      </div>
    </main>
  )
}
```

**Should see:** Blue box with white text

---

### 3. Check shadcn/ui

**Create button test:**
```tsx
import { Button } from "@/components/ui/button"

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <Button>Click Me!</Button>
    </main>
  )
}
```

**Should see:** Styled button

---

## 📚 Next Steps

After setup:

1. **Build Authentication:**
   - Create login/register pages
   - Set up auth context
   - Implement JWT handling

2. **Create Dashboard Layout:**
   - Sidebar navigation
   - Header with user menu
   - Responsive design

3. **Implement First Feature:**
   - Patient management
   - Use API client
   - Create forms with react-hook-form

4. **Extend Internationalization Coverage** (infrastructure is wired up — `src/i18n/request.ts`, `NextIntlClientProvider` in `layout.tsx`, cookie-based locale, `LanguageSwitcher` in the header — but only the login card and header dropdown use `useTranslations` so far; see [i18n guide](../development/i18n.md)):
   - Add message keys for the next page/component you're translating
   - Replace its hardcoded strings with `useTranslations`
   - No middleware or URL routing needed — this app deliberately uses cookie-based locale, not `/en/`/`/bn/` URL prefixes

---

## 🤖 AI Quick Reference

**Q: How do I start frontend?**
→ `cd frontend && npm run dev`

**Q: How do I add shadcn/ui component?**
→ `npx shadcn@latest add <component-name>`

**Q: Where do I make API calls?**
→ Create client in `src/lib/api/`, use React Query hooks

**Q: How do I add a new page?**
→ Create `src/app/<path>/page.tsx`

**Q: Where are environment variables?**
→ `.env.local` (must start with `NEXT_PUBLIC_` for client-side)

---

**See Also:**
- [Backend Setup](backend.md) - Backend setup guide
- [API Reference](../api/README.md) - API documentation
- [Getting Started](../../GETTING_STARTED.md) - local setup flow

---

**Last Updated:** September 21, 2026  
**Difficulty:** Intermediate  
**Time Required:** 30 minutes ✅
