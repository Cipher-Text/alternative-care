# Developer Quick Reference

Common patterns and utilities for AltCare development.

---

## React Query Setup

```typescript
// lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,   // 5 minutes
      gcTime: 10 * 60 * 1000,      // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

---

## Custom Hook Pattern

```typescript
// lib/hooks/usePatients.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function usePatients(search?: string) {
  return useQuery({
    queryKey: ['patients', search],
    queryFn: () => patientsApi.list({ search }),
  });
}

export function useCreatePatient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: patientsApi.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['patients'] }),
  });
}
```

---

## API Client (Axios)

```typescript
// lib/api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

// Attach auth token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      // trigger refresh or redirect to login
    }
    return Promise.reject(error);
  }
);
```

---

## Toast Notifications

```typescript
import { toast } from 'sonner';

toast.success('Patient added successfully!');
toast.error('Failed to save', { description: 'Check your connection' });

const id = toast.loading('Saving...');
toast.success('Saved!', { id });  // replaces the loading toast
```

---

## Class Name Utility

```typescript
// lib/utils/cn.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

---

## Date Formatting

```typescript
import { format, formatDistanceToNow } from 'date-fns';

export const formatDate = (date: string | Date) =>
  format(new Date(date), 'MMM dd, yyyy');

export const formatDateTime = (date: string | Date) =>
  format(new Date(date), 'MMM dd, yyyy h:mm a');

export const formatRelative = (date: string | Date) =>
  formatDistanceToNow(new Date(date), { addSuffix: true });
```

---

## Currency Formatting

```typescript
export const formatCurrency = (amount: number) =>
  `৳${amount.toLocaleString('en-IN')}`;

export const formatNumber = (value: number) => {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toString();
};
```

---

## i18n (next-intl)

```typescript
// In any Client Component:
import { useTranslations } from 'next-intl';

export function MyComponent() {
  const t = useTranslations('patient');
  return <h1>{t('add_new')}</h1>;
}
```

Messages live in `frontend/messages/en.json` and `frontend/messages/bn.json`. See [i18n guide](i18n.md) for full details.

---

## Error Boundary

```typescript
'use client';
import { Component, ReactNode } from 'react';

export class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error?: Error }
> {
  state = { hasError: false };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 text-center">
          <p className="text-sm text-gray-600 mb-4">{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false })}>
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

---

## E2E Test Pattern (Playwright)

```typescript
// tests/e2e/patients.spec.ts
import { test, expect } from '@playwright/test';

test('add a patient', async ({ page }) => {
  await page.goto('/patients/new');
  await page.fill('[name="name"]', 'Test Patient');
  await page.click('button:has-text("Save")');
  await expect(page).toHaveURL('/patients');
});
```

---

## Commands

```bash
# Backend
uvicorn app.main:app --reload
alembic upgrade head
pytest --cov=app
black backend/app && ruff check backend/app

# Frontend
npm run dev
npm run build
npx playwright test

# Infrastructure
docker compose up -d
cd backend && ./scripts/run_seed.sh

# Celery
celery -A app.core.celery:celery_app worker --loglevel=info
```
