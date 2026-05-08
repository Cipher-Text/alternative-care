# AltCare Frontend

Next.js 16 frontend for multi-tenant alternative medicine practice management.

**Full Documentation:** See [../CLAUDE.md](../CLAUDE.md) for architecture, patterns, and detailed guides.

---

## Quick Start

```bash
# Install dependencies
npm install

# Start development server (requires backend on port 8000)
npm run dev
```

**Frontend:** http://localhost:3000  
**Backend API Required:** http://localhost:8000

---

## Project Structure

```
frontend/src/
├── app/                    # Next.js App Router
│   ├── (auth)/login/      # Authentication routes
│   ├── (dashboard)/       # Protected routes
│   │   ├── dashboard/     # Analytics dashboard
│   │   └── patients/      # Patient management
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── components/            # React components
│   ├── auth/             # LoginForm, TwoFactorForm
│   ├── dashboard/        # Charts, Stats
│   ├── patients/         # PatientCard, PatientForm
│   ├── layout/           # Header, Sidebar
│   └── ui/               # shadcn/ui components
├── lib/
│   ├── api/              # API clients (auth, patients, dashboard)
│   ├── hooks/            # React Query hooks
│   └── utils/            # Helper functions
└── stores/
    └── authStore.ts      # Zustand auth state
```

**Implemented:** Auth, Patients, Dashboard (44 source files)  
**Pending:** Doctor Profile, Appointments, Prescriptions, Payments, Integrations

---

## Tech Stack

- **Framework:** Next.js 16 (App Router), React 19
- **Language:** TypeScript
- **Styling:** Tailwind CSS 4
- **UI:** shadcn/ui (Radix UI primitives)
- **State:** Zustand (client), React Query (server)
- **Forms:** React Hook Form + Zod validation
- **API:** Axios with auth interceptors
- **i18n:** next-intl (English/Bengali)
- **Testing:** Playwright (E2E)

See [../CLAUDE.md § 3](../CLAUDE.md) for full stack details.

---

## Development

### Essential Commands

```bash
# Development
npm run dev              # Start dev server (port 3000)
npm run build            # Production build
npm start                # Start production server
npm run lint             # Lint code

# Testing
npx playwright test                 # Run E2E tests
npx playwright test --ui            # Interactive mode
npx playwright show-report          # View report

# Clean
rm -rf .next node_modules
npm install
```

### Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=AltCare
```

---

## Adding Features

**See [../CLAUDE.md § 5.3](../CLAUDE.md) for complete implementation guide:**

1. Create API client → `lib/api/<feature>.ts`
2. Create React Query hooks → `lib/hooks/use<Feature>.ts`
3. Create page component → `app/(dashboard)/<feature>/page.tsx`
4. Create TypeScript types → Match backend Pydantic schemas

**Example:**

```typescript
// 1. API Client
export const patientsApi = {
  list: async () => apiClient.get('/api/v1/patients'),
  create: async (data: PatientCreate) => apiClient.post('/api/v1/patients', data),
};

// 2. React Query Hook
export function usePatients() {
  return useQuery(['patients'], patientsApi.list);
}

// 3. Page Component
"use client";
export default function PatientsPage() {
  const { data, isLoading } = usePatients();
  if (isLoading) return <Skeleton />;
  return <PatientList patients={data} />;
}

// 4. TypeScript Types
export interface PatientCreate {
  name: string;
  phone: string;
  // ... match backend schema exactly
}
```

---

## Conventions

**See [../CLAUDE.md § 7](../CLAUDE.md) for full conventions.**

**Key Rules:**
1. **TypeScript everywhere** - no implicit `any`
2. **Match backend schemas** - TypeScript interfaces = Pydantic models
3. **Client components** - mark interactive with `"use client"`
4. **Error boundaries** - wrap features, show user-friendly errors
5. **Loading states** - always show skeletons/spinners
6. **Responsive design** - test 375px, 768px, 1440px
7. **Bilingual UI** - English/Bengali support
8. **Form validation** - Zod schemas matching backend
9. **Accessibility** - semantic HTML, ARIA, keyboard nav

---

## Key Files

- **app/layout.tsx** - Root layout with providers
- **lib/api/client.ts** - Axios client with auth interceptors
- **stores/authStore.ts** - Zustand auth state
- **components/ui/** - shadcn/ui component library
- **.env.local** - Environment variables
- **package.json** - Dependencies
- **../CLAUDE.md** - Main documentation

---

## Troubleshooting

**CORS errors:**
```bash
# Check backend .env: CORS_ORIGINS=["http://localhost:3000"]
```

**API connection refused:**
```bash
# Check .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000
# Ensure backend is running
```

**Port 3000 in use:**
```bash
lsof -ti:3000 | xargs kill -9
# Or: PORT=3001 npm run dev
```

**Module not found:**
```bash
rm -rf .next node_modules
npm install
npm run dev
```

**TypeScript errors:**
```bash
# Update types in src/types/ to match backend schemas
npm run build  # Check for type errors
```

See [../CLAUDE.md § 6](../CLAUDE.md) for more troubleshooting.

---

## API Documentation

**Backend API:** http://localhost:8000/docs (Swagger)

**Authentication Flow:**
```typescript
// 1. Login
const response = await authApi.login({ email, password });

// 2. If 2FA enabled
if (response.requires_2fa) {
  const tokens = await authApi.verify2FA({ user_id, code });
}

// 3. Store tokens
authStore.setTokens(tokens.access_token, tokens.refresh_token);

// 4. Redirect
router.push('/dashboard');
```

See [../CLAUDE.md § 4.6](../CLAUDE.md) for complete patterns.

---

## Learn More

- **Next.js 16:** https://nextjs.org/docs
- **Tailwind CSS:** https://tailwindcss.com/docs
- **shadcn/ui:** https://ui.shadcn.com
- **React Query:** https://tanstack.com/query
- **Playwright:** https://playwright.dev
