# Developer Quick Reference
## Code Snippets & Common Patterns for Phase 1

Quick copy-paste examples for AltCare development.

---

## 🎨 Design Tokens (Tailwind Config)

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        // Primary (Green)
        primary: {
          50: '#E1F5EE',
          100: '#9FE1CB',
          200: '#5DCAA5',
          300: '#1D9E75',
          400: '#1D9E75',
          500: '#1D9E75', // Main
          600: '#0F6E56',
          700: '#0C5543',
          800: '#093C30',
          900: '#06231C',
        },
        // Secondary (Purple)
        secondary: {
          50: '#EEEDFE',
          100: '#CECBF6',
          200: '#AEA9EF',
          300: '#8E87E7',
          400: '#6B5FDB',
          500: '#534AB7', // Main
          600: '#423B92',
          700: '#322C6D',
          800: '#211E49',
          900: '#110F24',
        },
        // Info (Blue)
        info: {
          50: '#E6F1FB',
          100: '#B3D7F5',
          200: '#80BDEF',
          300: '#4DA3E9',
          400: '#378ADD',
          500: '#185FA5',
          600: '#134B84',
          700: '#0E3763',
          800: '#092342',
          900: '#041021',
        },
        // Warning (Amber)
        warning: {
          50: '#FAEEDA',
          100: '#F2D49F',
          200: '#FAC775',
          300: '#E6A93E',
          400: '#BA7517',
          500: '#854F0B',
          600: '#6A3F09',
          700: '#4F2F07',
          800: '#352005',
          900: '#1A1002',
        },
        // Error (Red)
        error: {
          50: '#FCEBEB',
          100: '#F5C3C2',
          200: '#EE9B9A',
          300: '#E77371',
          400: '#E24B4A',
          500: '#A32D2D',
          600: '#822424',
          700: '#621B1B',
          800: '#411212',
          900: '#210909',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'xs': '10px',
        'sm': '12px',
        'base': '13px',
        'md': '16px',
        'lg': '20px',
        'xl': '25px',
        '2xl': '31px',
      },
      spacing: {
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '5': '24px',
        '6': '32px',
        '8': '64px',
      },
      borderRadius: {
        'sm': '6px',
        'DEFAULT': '8px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        'full': '9999px',
      },
      boxShadow: {
        'sm': '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.02)',
        'DEFAULT': '0 4px 12px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.02)',
        'lg': '0 12px 24px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.02)',
      },
    },
  },
};
```

---

## 🧩 Common Component Patterns

### Button Variants
```tsx
// components/ui/Button.tsx
import { ButtonHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/utils/cn';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
  loading?: boolean;
}

const variants = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700',
  secondary: 'bg-secondary-600 text-white hover:bg-secondary-700',
  ghost: 'bg-gray-100 text-gray-700 hover:bg-gray-200',
  danger: 'bg-error-500 text-white hover:bg-error-600',
};

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-md',
};

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  loading = false,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'rounded-lg font-medium transition-colors duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <Spinner size={16} />
          Loading...
        </span>
      ) : (
        children
      )}
    </button>
  );
}

// Usage:
<Button variant="primary" size="md" onClick={handleSave}>
  Save Changes
</Button>
```

### Loading Skeleton
```tsx
// components/ui/Skeleton.tsx
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'animate-pulse bg-gray-200 rounded',
        className
      )}
    />
  );
}

// Usage:
<Skeleton className="h-4 w-32" />
<Skeleton className="h-10 w-full" />
<Skeleton className="h-64 w-full" />
```

### Toast Notifications
```tsx
// components/ui/Toast.tsx
import { toast } from 'sonner';

// Success toast
toast.success('Patient added successfully!', {
  description: 'Fatima Ahmed has been added to your records',
  duration: 3000,
});

// Error toast
toast.error('Failed to save prescription', {
  description: 'Please check your internet connection and try again',
  duration: 5000,
});

// Loading toast
const toastId = toast.loading('Saving prescription...');
// Later:
toast.success('Prescription saved!', { id: toastId });
```

---

## 🔌 API Integration Patterns

### React Query Setup
```tsx
// utils/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

### Custom Hooks
```tsx
// hooks/useOnboardingProgress.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/utils/api';

export function useOnboardingProgress(userId: string) {
  return useQuery({
    queryKey: ['onboarding', userId],
    queryFn: () => api.get(`/onboarding/progress/${userId}`),
  });
}

export function useDismissChecklist(userId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => api.post(`/onboarding/dismiss/${userId}`),
    onSuccess: () => {
      queryClient.invalidateQueries(['onboarding', userId]);
      toast.success('Checklist dismissed');
    },
    onError: () => {
      toast.error('Failed to dismiss checklist');
    },
  });
}

// Usage in component:
const { data, isLoading } = useOnboardingProgress(userId);
const { mutate: dismiss } = useDismissChecklist(userId);
```

### API Client (Axios)
```typescript
// utils/api.ts
import axios from 'axios';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors globally
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

---

## 📊 Analytics Tracking

### Track Event Helper
```typescript
// utils/analytics.ts
import mixpanel from 'mixpanel-browser';
import posthog from 'posthog-js';

// Initialize
if (typeof window !== 'undefined') {
  mixpanel.init(process.env.NEXT_PUBLIC_MIXPANEL_TOKEN!);
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_TOKEN!, {
    api_host: 'https://app.posthog.com',
  });
}

export const analytics = {
  track: (event: string, properties?: object) => {
    if (process.env.NODE_ENV === 'production') {
      mixpanel.track(event, properties);
      posthog.capture(event, properties);
    } else {
      console.log('📊 Analytics:', event, properties);
    }
  },
  
  identify: (userId: string, traits?: object) => {
    mixpanel.identify(userId);
    mixpanel.people.set(traits);
    posthog.identify(userId, traits);
  },
  
  page: (name: string) => {
    mixpanel.track_pageview({ page: name });
    posthog.capture('$pageview', { page: name });
  },
};

// Usage:
analytics.track('onboarding_step_completed', {
  step: 'first_patient',
  timestamp: new Date().toISOString(),
});
```

### Common Events
```typescript
// Track onboarding
analytics.track('onboarding_checklist_viewed', {
  step_count: 8,
  completed_count: 4,
});

// Track quick action
analytics.track('quick_action_used', {
  action: 'new_patient',
  trigger: 'button', // or 'keyboard'
});

// Track upgrade prompt
analytics.track('upgrade_prompt_shown', {
  trigger: 'patient_limit',
  plan: 'free',
  usage_percent: 90,
});

// Track conversion
analytics.track('upgrade_initiated', {
  from_plan: 'free',
  to_plan: 'plus',
  source: 'patient_limit_warning',
});
```

---

## 🧪 Testing Patterns

### Unit Test (Jest + React Testing Library)
```typescript
// __tests__/OnboardingChecklist.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/utils/queryClient';
import { OnboardingChecklist } from '@/components/dashboard/OnboardingChecklist';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

describe('OnboardingChecklist', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  it('renders with correct progress', async () => {
    render(<OnboardingChecklist userId="test-user" />, { wrapper });
    
    await waitFor(() => {
      expect(screen.getByText(/4\/8 completed/i)).toBeInTheDocument();
    });
  });

  it('dismisses when X clicked', async () => {
    render(<OnboardingChecklist userId="test-user" />, { wrapper });
    
    const dismissBtn = screen.getByLabelText('Dismiss checklist');
    fireEvent.click(dismissBtn);
    
    await waitFor(() => {
      expect(screen.queryByText(/Complete your setup/i)).not.toBeInTheDocument();
    });
  });
});
```

### E2E Test (Playwright)
```typescript
// e2e/onboarding.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Onboarding Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('completes onboarding step', async ({ page }) => {
    // Verify checklist is visible
    await expect(page.locator('text=Complete your setup')).toBeVisible();
    
    // Click "Continue Setup"
    await page.click('text=Continue Setup');
    
    // Verify navigation
    await expect(page).toHaveURL('/patients/new');
    
    // Add patient
    await page.fill('[name="patient_name"]', 'Test Patient');
    await page.click('button:has-text("Save")');
    
    // Go back to dashboard
    await page.goto('/dashboard');
    
    // Verify progress updated
    await expect(page.locator('text=5/8 completed')).toBeVisible();
  });

  test('dismisses checklist', async ({ page }) => {
    await page.click('[aria-label="Dismiss checklist"]');
    
    await expect(page.locator('text=Complete your setup')).not.toBeVisible();
  });
});
```

---

## 🎨 Animation Patterns

### Framer Motion Examples
```tsx
import { motion, AnimatePresence } from 'framer-motion';

// Fade in/out
<AnimatePresence>
  {isVisible && (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
    >
      Content
    </motion.div>
  )}
</AnimatePresence>

// Slide in from bottom
<motion.div
  initial={{ y: 20, opacity: 0 }}
  animate={{ y: 0, opacity: 1 }}
  transition={{ duration: 0.3, ease: 'easeOut' }}
>
  Content
</motion.div>

// Scale button on press
<motion.button
  whileHover={{ scale: 1.02 }}
  whileTap={{ scale: 0.98 }}
  className="btn-primary"
>
  Click me
</motion.button>

// Count-up animation (for KPIs)
<motion.span
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: 0.5 }}
>
  {countUp(1284, 1000)}
</motion.span>

function countUp(target: number, duration: number) {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    let start = 0;
    const increment = target / (duration / 16);
    
    const timer = setInterval(() => {
      start += increment;
      if (start >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 16);
    
    return () => clearInterval(timer);
  }, [target, duration]);
  
  return count;
}
```

### CSS Animations
```css
/* Loading spinner */
@keyframes spin {
  to { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}

/* Pulse effect */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Bounce (for hints) */
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
.animate-bounce {
  animation: bounce 1s infinite;
}
```

---

## 🔐 Authentication Patterns

### Protected Route
```tsx
// components/ProtectedRoute.tsx
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login');
    }
  }, [status, router]);

  if (status === 'loading') {
    return <LoadingScreen />;
  }

  if (!session) {
    return null;
  }

  return <>{children}</>;
}

// Usage in page:
export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  );
}
```

### User Context
```tsx
// contexts/UserContext.tsx
import { createContext, useContext, ReactNode } from 'react';
import { useSession } from 'next-auth/react';

interface UserContextType {
  user: User | null;
  plan: 'free' | 'plus' | 'pro';
  isLoading: boolean;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const { data: session, status } = useSession();
  
  const value = {
    user: session?.user || null,
    plan: session?.user?.plan || 'free',
    isLoading: status === 'loading',
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within UserProvider');
  }
  return context;
}

// Usage:
const { user, plan } = useUser();
```

---

## 🌐 i18n Patterns (English/Bengali)

### next-intl Setup
```typescript
// i18n.ts
import { notFound } from 'next/navigation';
import { getRequestConfig } from 'next-intl/server';

const locales = ['en', 'bn'];

export default getRequestConfig(async ({ locale }) => {
  if (!locales.includes(locale as any)) notFound();

  return {
    messages: (await import(`./messages/${locale}.json`)).default
  };
});
```

### Translation Files
```json
// messages/en.json
{
  "onboarding": {
    "title": "Complete your setup",
    "progress": "{completed}/{total} completed",
    "steps": {
      "profile": "Profile created",
      "degrees": "Degrees verified",
      "patient": "First patient added"
    }
  },
  "buttons": {
    "continue": "Continue Setup",
    "dismiss": "Dismiss"
  }
}

// messages/bn.json
{
  "onboarding": {
    "title": "আপনার সেটআপ সম্পূর্ণ করুন",
    "progress": "{completed}/{total} সম্পন্ন",
    "steps": {
      "profile": "প্রোফাইল তৈরি হয়েছে",
      "degrees": "ডিগ্রি যাচাই হয়েছে",
      "patient": "প্রথম রোগী যোগ করা হয়েছে"
    }
  },
  "buttons": {
    "continue": "সেটআপ চালিয়ে যান",
    "dismiss": "বাতিল করুন"
  }
}
```

### Usage in Component
```tsx
import { useTranslations } from 'next-intl';

export function OnboardingChecklist() {
  const t = useTranslations('onboarding');

  return (
    <div>
      <h3>{t('title')}</h3>
      <p>{t('progress', { completed: 4, total: 8 })}</p>
      <ul>
        <li>{t('steps.profile')}</li>
        <li>{t('steps.degrees')}</li>
        <li>{t('steps.patient')}</li>
      </ul>
    </div>
  );
}
```

---

## 🔧 Utility Functions

### Class Name Merger
```typescript
// utils/cn.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Usage:
<div className={cn(
  'base-styles',
  isActive && 'active-styles',
  className
)} />
```

### Date Formatting
```typescript
// utils/date.ts
import { format, formatDistanceToNow } from 'date-fns';

export const formatDate = (date: Date | string) => {
  return format(new Date(date), 'MMM dd, yyyy');
};

export const formatDateTime = (date: Date | string) => {
  return format(new Date(date), 'MMM dd, yyyy h:mm a');
};

export const formatRelative = (date: Date | string) => {
  return formatDistanceToNow(new Date(date), { addSuffix: true });
};

// Usage:
formatDate('2026-04-21') // "Apr 21, 2026"
formatRelative('2026-04-21T10:00:00') // "2 hours ago"
```

### Number Formatting
```typescript
// utils/format.ts
export const formatCurrency = (amount: number, currency = 'BDT') => {
  if (currency === 'BDT') {
    return `৳${amount.toLocaleString('en-IN')}`;
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
};

export const formatPercent = (value: number) => {
  return `${Math.round(value)}%`;
};

export const formatNumber = (value: number) => {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toString();
};

// Usage:
formatCurrency(1799) // "৳1,799"
formatPercent(0.856) // "86%"
formatNumber(12500) // "12.5K"
```

---

## 🐛 Debugging Tips

### React Query DevTools
```tsx
// app/layout.tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <ReactQueryDevtools initialIsOpen={false} />
      </body>
    </html>
  );
}
```

### Error Boundary
```tsx
// components/ErrorBoundary.tsx
import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  state = { hasError: false, error: undefined };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error boundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 text-center">
          <h2 className="text-lg font-semibold mb-2">Something went wrong</h2>
          <p className="text-sm text-gray-600 mb-4">
            {this.state.error?.message}
          </p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="btn-primary"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Console Helpers
```typescript
// Development-only logging
if (process.env.NODE_ENV === 'development') {
  console.log('🐛 Debug:', data);
  console.table(users);
  console.time('API Call');
  // ... code ...
  console.timeEnd('API Call');
}
```

---

## 📦 Package.json Scripts

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "format": "prettier --write \"**/*.{ts,tsx,js,jsx,json,md}\"",
    "test": "jest --watch",
    "test:ci": "jest --ci --coverage --watchAll=false",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "type-check": "tsc --noEmit",
    "analyze": "ANALYZE=true next build"
  }
}
```

---

## 🚀 Deployment Checklist

### Pre-Deploy
- [ ] Run `npm run lint` (no errors)
- [ ] Run `npm run type-check` (no errors)
- [ ] Run `npm run test:ci` (all tests pass)
- [ ] Run `npm run build` (builds successfully)
- [ ] Test on staging
- [ ] Review environment variables
- [ ] Check API rate limits
- [ ] Backup database

### Post-Deploy
- [ ] Smoke test critical paths
- [ ] Check error logs (Sentry)
- [ ] Monitor API performance
- [ ] Verify analytics tracking
- [ ] Test on mobile devices
- [ ] Update changelog
- [ ] Notify team

---

*Quick reference • Keep nearby while coding*  
*Last updated: 2026-04-21*
