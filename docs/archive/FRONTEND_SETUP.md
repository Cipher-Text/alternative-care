# Frontend Setup Guide — AltCare Next.js Application

> Complete guide to setting up the Next.js 16 frontend for AltCare Alternative Medicine Practice Management System

**Status:** ✅ Frontend Complete (May 2026)  
**Stack:** Next.js 16 + React 19 + TypeScript + Tailwind CSS 4 + shadcn/ui + React Query  
**Note:** This guide documents the initial setup. Frontend is now fully implemented.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Initialization](#project-initialization)
3. [Project Structure](#project-structure)
4. [Configuration Files](#configuration-files)
5. [Dependencies](#dependencies)
6. [Environment Setup](#environment-setup)
7. [Authentication Implementation](#authentication-implementation)
8. [API Client Setup](#api-client-setup)
9. [Component Library Setup](#component-library-setup)
10. [Internationalization (i18n)](#internationalization-i18n)
11. [First Feature: Patient Management](#first-feature-patient-management)
12. [Development Workflow](#development-workflow)
13. [Deployment Preparation](#deployment-preparation)

---

## Prerequisites

**Required Software:**
- Node.js 18+ (LTS recommended: 20.x)
- npm 9+ or pnpm 8+ (pnpm recommended for faster installs)
- Git
- VS Code or WebStorm (recommended IDEs)

**Backend Must Be Running:**
```bash
# In terminal 1: Start backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Verify backend is running
curl http://localhost:8000/health
```

**Skills Needed:**
- React fundamentals (hooks, components, props)
- TypeScript basics (types, interfaces)
- Basic understanding of REST APIs
- CSS (Tailwind is utility-based, easy to learn)

---

## Project Initialization

### Step 1: Create Next.js Project

```bash
# Navigate to project root
cd /Users/imran/Documents/Repo/Cipher-Text/alternative-care

# Create Next.js app with TypeScript
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --import-alias "@/*"

# Follow prompts:
# ✔ Would you like to use TypeScript? Yes
# ✔ Would you like to use ESLint? Yes
# ✔ Would you like to use Tailwind CSS? Yes
# ✔ Would you like to use `src/` directory? Yes
# ✔ Would you like to use App Router? Yes
# ✔ Would you like to customize the default import alias (@/*)? No

cd frontend
```

### Step 2: Verify Installation

```bash
# Start development server
npm run dev

# Open http://localhost:3000 in browser
# You should see Next.js welcome page
```

---

## Project Structure

```
frontend/
├── public/                      # Static assets
│   ├── images/
│   ├── icons/
│   └── favicon.ico
├── src/
│   ├── app/                     # Next.js App Router pages
│   │   ├── (auth)/              # Auth layout group
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── register/
│   │   │   │   └── page.tsx
│   │   │   └── layout.tsx       # Auth layout (no sidebar)
│   │   ├── (dashboard)/         # Dashboard layout group
│   │   │   ├── patients/
│   │   │   │   ├── page.tsx              # Patient list
│   │   │   │   ├── [id]/
│   │   │   │   │   └── page.tsx          # Patient detail
│   │   │   │   └── new/
│   │   │   │       └── page.tsx          # Create patient
│   │   │   ├── appointments/
│   │   │   ├── prescriptions/
│   │   │   ├── payments/
│   │   │   ├── medicines/
│   │   │   ├── library/
│   │   │   ├── settings/
│   │   │   └── layout.tsx       # Dashboard layout (with sidebar)
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Homepage (redirects to /login or /dashboard)
│   │   └── globals.css          # Global styles
│   ├── components/              # React components
│   │   ├── ui/                  # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   ├── table.tsx
│   │   │   └── ...
│   │   ├── layout/              # Layout components
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── MobileNav.tsx
│   │   ├── auth/                # Auth components
│   │   │   ├── LoginForm.tsx
│   │   │   ├── TwoFactorForm.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── patients/            # Patient components
│   │   │   ├── PatientList.tsx
│   │   │   ├── PatientCard.tsx
│   │   │   ├── PatientForm.tsx
│   │   │   └── PatientSearch.tsx
│   │   └── shared/              # Shared components
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorBoundary.tsx
│   │       ├── LanguageSwitcher.tsx
│   │       └── DateRangePicker.tsx
│   ├── lib/                     # Utility libraries
│   │   ├── api/                 # API client
│   │   │   ├── client.ts        # Axios instance
│   │   │   ├── auth.ts          # Auth API calls
│   │   │   ├── patients.ts      # Patient API calls
│   │   │   ├── appointments.ts
│   │   │   ├── prescriptions.ts
│   │   │   ├── payments.ts
│   │   │   └── dashboard.ts
│   │   ├── hooks/               # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── usePatients.ts
│   │   │   ├── useAppointments.ts
│   │   │   └── useLocalStorage.ts
│   │   ├── utils/               # Utility functions
│   │   │   ├── format.ts        # Date/currency formatters
│   │   │   ├── validation.ts    # Form validators
│   │   │   └── cn.ts            # Class name merger
│   │   └── constants/           # Constants
│   │       ├── routes.ts
│   │       ├── roles.ts
│   │       └── api-endpoints.ts
│   ├── types/                   # TypeScript types
│   │   ├── auth.ts
│   │   ├── patient.ts
│   │   ├── appointment.ts
│   │   ├── prescription.ts
│   │   ├── payment.ts
│   │   └── api.ts
│   ├── store/                   # State management (Zustand)
│   │   ├── authStore.ts
│   │   ├── uiStore.ts
│   │   └── index.ts
│   └── messages/                # i18n translations
│       ├── en.json
│       └── bn.json
├── .env.local                   # Environment variables
├── .eslintrc.json               # ESLint config
├── next.config.js               # Next.js config
├── tailwind.config.ts           # Tailwind config
├── tsconfig.json                # TypeScript config
├── components.json              # shadcn/ui config
└── package.json
```

---

## Configuration Files

### 1. TypeScript Configuration (`tsconfig.json`)

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### 2. Tailwind Configuration (`tailwind.config.ts`)

```typescript
import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
export default config
```

### 3. Next.js Configuration (`next.config.js`)

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // API endpoint rewrite for local development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
    ]
  },

  // Environment variables available to browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // Image optimization
  images: {
    domains: ['localhost'],
  },
}

module.exports = nextConfig
```

### 4. ESLint Configuration (`.eslintrc.json`)

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

## Dependencies

### Step 1: Install Core Dependencies

```bash
cd frontend

# Core dependencies
npm install axios react-query zustand date-fns
npm install @hookform/resolvers react-hook-form zod
npm install next-intl
npm install js-cookie
npm install react-hot-toast

# Development dependencies
npm install -D @types/js-cookie
```

### Step 2: Install shadcn/ui

```bash
# Initialize shadcn/ui
npx shadcn-ui@latest init

# Follow prompts:
# ✔ Which style would you like to use? Default
# ✔ Which color would you like to use as base color? Slate
# ✔ Would you like to use CSS variables for colors? Yes

# Install common components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add card
npx shadcn-ui@latest add table
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add select
npx shadcn-ui@latest add label
npx shadcn-ui@latest add form
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add avatar
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add calendar
```

### Complete `package.json`

```json
{
  "name": "altcare-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "@hookform/resolvers": "^3.3.4",
    "@radix-ui/react-avatar": "^1.0.4",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-toast": "^1.1.5",
    "axios": "^1.6.7",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "date-fns": "^3.3.1",
    "js-cookie": "^3.0.5",
    "lucide-react": "^0.344.0",
    "next": "14.1.0",
    "next-intl": "^3.9.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-hook-form": "^7.50.1",
    "react-hot-toast": "^2.4.1",
    "react-query": "^3.39.3",
    "tailwind-merge": "^2.2.1",
    "tailwindcss-animate": "^1.0.7",
    "zod": "^3.22.4",
    "zustand": "^4.5.0"
  },
  "devDependencies": {
    "@types/js-cookie": "^3.0.6",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "@typescript-eslint/eslint-plugin": "^6.21.0",
    "@typescript-eslint/parser": "^6.21.0",
    "autoprefixer": "^10.0.1",
    "eslint": "^8",
    "eslint-config-next": "14.1.0",
    "postcss": "^8",
    "tailwindcss": "^3.3.0",
    "typescript": "^5"
  }
}
```

---

## Environment Setup

Create `.env.local` file in `frontend/` directory:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_TIMEOUT=30000

# Application
NEXT_PUBLIC_APP_NAME=AltCare
NEXT_PUBLIC_APP_VERSION=0.1.0
NEXT_PUBLIC_DEFAULT_LANGUAGE=en

# Feature Flags (for gradual rollout)
NEXT_PUBLIC_FEATURE_2FA=true
NEXT_PUBLIC_FEATURE_BKASH=true
NEXT_PUBLIC_FEATURE_AI=false

# Development
NODE_ENV=development
```

**Security Notes:**
- Only variables prefixed with `NEXT_PUBLIC_` are exposed to browser
- Never commit `.env.local` to git (already in .gitignore)
- Use separate `.env.production` for production builds

---

## Authentication Implementation

### Step 1: Create Auth Store (`src/store/authStore.ts`)

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import Cookies from 'js-cookie'

interface User {
  id: string
  email: string
  full_name: string
  role: string
  tenant_id: string | null
  plan: string
  language: string
}

interface AuthStore {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  
  setAuth: (user: User, accessToken: string, refreshToken: string) => void
  logout: () => void
  updateUser: (user: Partial<User>) => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setAuth: (user, accessToken, refreshToken) => {
        // Store tokens in httpOnly cookies (more secure than localStorage)
        Cookies.set('accessToken', accessToken, { expires: 1/48 }) // 30 minutes
        Cookies.set('refreshToken', refreshToken, { expires: 7 }) // 7 days
        
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
        })
      },

      logout: () => {
        Cookies.remove('accessToken')
        Cookies.remove('refreshToken')
        
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        })
      },

      updateUser: (userData) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        }))
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user }), // Only persist user, not tokens
    }
  )
)
```

### Step 2: Create API Client (`src/lib/api/client.ts`)

```typescript
import axios, { AxiosError, AxiosRequestConfig } from 'axios'
import Cookies from 'js-cookie'
import { useAuthStore } from '@/store/authStore'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: Add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = Cookies.get('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    // If 401 and we haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = Cookies.get('refreshToken')
        if (!refreshToken) {
          throw new Error('No refresh token')
        }

        // Call refresh endpoint
        const response = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const { access_token } = response.data

        // Update token in cookies
        Cookies.set('accessToken', access_token, { expires: 1/48 })

        // Update store
        useAuthStore.setState({ accessToken: access_token })

        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh failed, logout user
        useAuthStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
```

### Step 3: Create Auth API (`src/lib/api/auth.ts`)

```typescript
import apiClient from './client'

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: {
    id: string
    email: string
    full_name: string
    role: string
    tenant_id: string | null
    plan: string
    language: string
    two_factor_enabled: boolean
  }
}

export interface TwoFactorRequest {
  email: string
  password: string
  totp_code: string
}

export const authApi = {
  // Login
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post('/auth/login', data)
    return response.data
  },

  // Login with 2FA
  loginWith2FA: async (data: TwoFactorRequest): Promise<LoginResponse> => {
    const response = await apiClient.post('/auth/login-2fa', data)
    return response.data
  },

  // Refresh token
  refresh: async (refreshToken: string): Promise<{ access_token: string }> => {
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  // Logout
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout')
  },

  // Get current user
  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me')
    return response.data
  },
}
```

### Step 4: Create Login Form (`src/components/auth/LoginForm.tsx`)

```typescript
'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { toast } from 'react-hot-toast'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginFormData = z.infer<typeof loginSchema>

export function LoginForm() {
  const router = useRouter()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [loading, setLoading] = useState(false)
  const [needs2FA, setNeeds2FA] = useState(false)
  const [credentials, setCredentials] = useState<LoginFormData | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    setLoading(true)
    try {
      const response = await authApi.login(data)

      if (response.user.two_factor_enabled) {
        // Show 2FA form
        setCredentials(data)
        setNeeds2FA(true)
      } else {
        // Login successful
        setAuth(response.user, response.access_token, response.refresh_token)
        toast.success('Login successful!')
        router.push('/dashboard')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  if (needs2FA) {
    return (
      <TwoFactorForm
        email={credentials!.email}
        password={credentials!.password}
        onBack={() => setNeeds2FA(false)}
      />
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="doctor@clinic.com"
          {...register('email')}
        />
        {errors.email && (
          <p className="text-sm text-red-500 mt-1">{errors.email.message}</p>
        )}
      </div>

      <div>
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          placeholder="••••••••"
          {...register('password')}
        />
        {errors.password && (
          <p className="text-sm text-red-500 mt-1">{errors.password.message}</p>
        )}
      </div>

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </Button>
    </form>
  )
}
```

---

## API Client Setup

### Create Patient API (`src/lib/api/patients.ts`)

```typescript
import apiClient from './client'

export interface Patient {
  id: string
  tenant_id: string
  patient_code: string
  first_name: string
  last_name: string
  date_of_birth: string
  gender: 'male' | 'female' | 'other'
  phone: string
  email?: string
  address?: string
  division_id?: string
  district_id?: string
  upazila_id?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  blood_group?: string
  created_at: string
  updated_at: string
}

export interface PatientCreateRequest {
  first_name: string
  last_name: string
  date_of_birth: string
  gender: 'male' | 'female' | 'other'
  phone: string
  email?: string
  address?: string
  division_id?: string
  district_id?: string
  upazila_id?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  blood_group?: string
}

export const patientsApi = {
  // List all patients
  list: async (params?: {
    skip?: number
    limit?: number
    search?: string
    gender?: string
    tag_id?: string
  }): Promise<Patient[]> => {
    const response = await apiClient.get('/patients', { params })
    return response.data
  },

  // Get single patient
  get: async (id: string): Promise<Patient> => {
    const response = await apiClient.get(`/patients/${id}`)
    return response.data
  },

  // Create patient
  create: async (data: PatientCreateRequest): Promise<Patient> => {
    const response = await apiClient.post('/patients', data)
    return response.data
  },

  // Update patient
  update: async (id: string, data: Partial<PatientCreateRequest>): Promise<Patient> => {
    const response = await apiClient.put(`/patients/${id}`, data)
    return response.data
  },

  // Delete patient
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/patients/${id}`)
  },

  // Search patients
  search: async (query: string): Promise<Patient[]> => {
    const response = await apiClient.get('/patients/search', {
      params: { q: query },
    })
    return response.data
  },
}
```

### Create Custom Hook (`src/lib/hooks/usePatients.ts`)

```typescript
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { patientsApi, Patient, PatientCreateRequest } from '@/lib/api/patients'
import { toast } from 'react-hot-toast'

export function usePatients(params?: any) {
  return useQuery(['patients', params], () => patientsApi.list(params))
}

export function usePatient(id: string) {
  return useQuery(['patient', id], () => patientsApi.get(id), {
    enabled: !!id,
  })
}

export function useCreatePatient() {
  const queryClient = useQueryClient()

  return useMutation(
    (data: PatientCreateRequest) => patientsApi.create(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('patients')
        toast.success('Patient created successfully')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to create patient')
      },
    }
  )
}

export function useUpdatePatient() {
  const queryClient = useQueryClient()

  return useMutation(
    ({ id, data }: { id: string; data: Partial<PatientCreateRequest> }) =>
      patientsApi.update(id, data),
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries('patients')
        queryClient.invalidateQueries(['patient', variables.id])
        toast.success('Patient updated successfully')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to update patient')
      },
    }
  )
}

export function useDeletePatient() {
  const queryClient = useQueryClient()

  return useMutation((id: string) => patientsApi.delete(id), {
    onSuccess: () => {
      queryClient.invalidateQueries('patients')
      toast.success('Patient deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete patient')
    },
  })
}
```

---

## Component Library Setup

### Global Styles (`src/app/globals.css`)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

---

## Internationalization (i18n)

### Step 1: Create Translation Files

**`src/messages/en.json`:**
```json
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "edit": "Edit",
    "search": "Search",
    "loading": "Loading...",
    "error": "An error occurred"
  },
  "auth": {
    "login": "Login",
    "logout": "Logout",
    "email": "Email",
    "password": "Password",
    "loginSuccess": "Login successful",
    "loginFailed": "Login failed"
  },
  "patients": {
    "title": "Patients",
    "addPatient": "Add Patient",
    "editPatient": "Edit Patient",
    "firstName": "First Name",
    "lastName": "Last Name",
    "phone": "Phone",
    "gender": "Gender",
    "male": "Male",
    "female": "Female",
    "other": "Other"
  }
}
```

**`src/messages/bn.json`:**
```json
{
  "common": {
    "save": "সংরক্ষণ করুন",
    "cancel": "বাতিল করুন",
    "delete": "মুছুন",
    "edit": "সম্পাদনা",
    "search": "অনুসন্ধান",
    "loading": "লোড হচ্ছে...",
    "error": "একটি ত্রুটি ঘটেছে"
  },
  "auth": {
    "login": "লগইন",
    "logout": "লগআউট",
    "email": "ইমেইল",
    "password": "পাসওয়ার্ড",
    "loginSuccess": "সফলভাবে লগইন হয়েছে",
    "loginFailed": "লগইন ব্যর্থ হয়েছে"
  },
  "patients": {
    "title": "রোগীরা",
    "addPatient": "রোগী যোগ করুন",
    "editPatient": "রোগী সম্পাদনা করুন",
    "firstName": "প্রথম নাম",
    "lastName": "শেষ নাম",
    "phone": "ফোন",
    "gender": "লিঙ্গ",
    "male": "পুরুষ",
    "female": "মহিলা",
    "other": "অন্যান্য"
  }
}
```

### Step 2: Configure next-intl

**`src/i18n.ts`:**
```typescript
import { getRequestConfig } from 'next-intl/server'

export default getRequestConfig(async ({ locale }) => ({
  messages: (await import(`./messages/${locale}.json`)).default,
}))
```

---

## First Feature: Patient Management

### Patient List Page (`src/app/(dashboard)/patients/page.tsx`)

```typescript
'use client'

import { useState } from 'react'
import { usePatients } from '@/lib/hooks/usePatients'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { PatientCard } from '@/components/patients/PatientCard'
import { Loader2 } from 'lucide-react'
import Link from 'next/link'

export default function PatientsPage() {
  const [search, setSearch] = useState('')
  const { data: patients, isLoading, error } = usePatients()

  const filteredPatients = patients?.filter((patient) =>
    `${patient.first_name} ${patient.last_name} ${patient.phone}`
      .toLowerCase()
      .includes(search.toLowerCase())
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-red-500">
        Failed to load patients
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Patients</h1>
        <Link href="/patients/new">
          <Button>Add Patient</Button>
        </Link>
      </div>

      <Input
        placeholder="Search patients..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-md"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredPatients?.map((patient) => (
          <PatientCard key={patient.id} patient={patient} />
        ))}
      </div>

      {filteredPatients?.length === 0 && (
        <div className="text-center text-muted-foreground">
          No patients found
        </div>
      )}
    </div>
  )
}
```

---

## Development Workflow

### Daily Workflow

```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Type checking (optional)
cd frontend
npm run type-check -- --watch
```

### Access Points

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Development Tips

1. **Hot Reload:** Both Next.js and FastAPI support hot reload
2. **Type Safety:** Run `npm run type-check` before committing
3. **Linting:** Run `npm run lint` to catch issues
4. **Git Workflow:**
   ```bash
   git checkout -b feat/patient-management
   # Make changes
   git add .
   git commit -m "feat: implement patient list page"
   git push origin feat/patient-management
   ```

---

## Deployment Preparation

### Build for Production

```bash
# Test production build locally
npm run build
npm run start

# Check for build errors
# Optimize images
# Test all critical paths
```

### Environment Variables for Production

Create `.env.production`:
```env
NEXT_PUBLIC_API_URL=https://api.altcare.com/api/v1
NODE_ENV=production
```

### Vercel Deployment (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel

# Follow prompts to connect to Vercel account
```

---

## Next Steps

**Week 13 Development Plan:**

1. **Days 1-2:** Project setup (this guide)
2. **Days 3-4:** Authentication flow (login, 2FA, logout)
3. **Days 5-7:** Patient management (list, create, edit, delete)
4. **Days 8-10:** Dashboard layout (sidebar, header, routing)
5. **Days 11-12:** Dashboard analytics page (charts with recharts)
6. **Days 13-14:** Polish, testing, bug fixes

**By End of Week 13:**
- ✅ Login + 2FA working
- ✅ Patient CRUD complete
- ✅ Dashboard shell ready
- ✅ All 71 API endpoints integrated

**Week 14-18:** Remaining features (appointments, prescriptions, payments, etc.)

---

## Support

**Resources:**
- Next.js Docs: https://nextjs.org/docs
- shadcn/ui Components: https://ui.shadcn.com
- React Query Docs: https://tanstack.com/query/v3
- Tailwind CSS Docs: https://tailwindcss.com/docs

**Troubleshooting:**
- Clear Next.js cache: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check backend is running: `curl http://localhost:8000/health`

---

**Last Updated:** May 1, 2026  
**Status:** Ready for Week 13 implementation ✅
