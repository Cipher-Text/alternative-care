'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  Home,
  Users,
  Calendar,
  FileText,
  CreditCard,
  Pill,
  Settings,
  LayoutDashboard,
  Building2,
  UserCog,
  GraduationCap,
  Stethoscope,
  Store,
  Tags,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useCan } from '@/lib/auth/permissions'

const doctorNavigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Patients', href: '/patients', icon: Users },
  { name: 'Appointments', href: '/appointments', icon: Calendar },
  { name: 'Prescriptions', href: '/prescriptions', icon: FileText },
  { name: 'Payments', href: '/payments', icon: CreditCard },
  { name: 'Medicines', href: '/medicines', icon: Pill },
  { name: 'Pharmacies', href: '/pharmacies', icon: Store },
  { name: 'Symptoms', href: '/symptoms', icon: Stethoscope },
  { name: 'Settings', href: '/settings', icon: Settings },
]

const adminNavigation = [
  { name: 'Platform Dashboard', href: '/admin/dashboard', icon: LayoutDashboard },
  { name: 'Clients', href: '/admin/clients', icon: Building2 },
  { name: 'Plans & Pricing', href: '/admin/plans', icon: Tags },
  { name: 'Users', href: '/admin/users', icon: UserCog },
  { name: 'Institutions', href: '/admin/institutions', icon: GraduationCap },
  { name: 'Pharmacies', href: '/admin/pharmacies', icon: Store },
  { name: 'Medicines', href: '/admin/medicines', icon: Pill },
  { name: 'Symptoms', href: '/admin/symptoms', icon: Stethoscope },
]

/** The nav items for the signed-in user's role (shared by the sidebar and the phone drawer). */
export function useNavItems() {
  const user = useAuthStore((state) => state.user)
  const can = useCan()

  // Platform admins and operators (moderators) share the admin nav — no
  // patient/appointment/prescription items, since neither role has a
  // tenant. `operator` has no distinct endpoints yet (RBAC stub per
  // docs/architecture/roles-access.md), so it sees the same nav as admin
  // rather than a separate, currently-empty menu.
  return user?.role === 'admin' || user?.role === 'operator'
    ? adminNavigation
    : doctorNavigation.filter((item) => can.manageClinicSettings || item.href !== '/settings')
}

export function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname()
  const items = useNavItems()

  return (
    <nav className="flex-1 px-3 py-6 space-y-1" aria-label="Main">
      {items.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`)
        const Icon = item.icon

        return (
          <Link
            key={item.name}
            href={item.href}
            onClick={onNavigate}
            aria-current={isActive ? 'page' : undefined}
            className={cn(
              'group flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200',
              isActive
                ? 'bg-primary text-primary-foreground'
                : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white'
            )}
          >
            <Icon
              className={cn(
                'mr-3 h-5 w-5 flex-shrink-0',
                isActive
                  ? 'text-primary-foreground'
                  : 'text-slate-500 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white'
              )}
            />
            {item.name}
          </Link>
        )
      })}
    </nav>
  )
}

export function Sidebar() {
  return (
    <div className="hidden md:flex md:w-64 md:flex-col">
      <div className="flex flex-col flex-1 min-h-0 bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-700 transition-colors">
        {/* Logo (a div, not an h1: each page has exactly one h1 — its title) */}
        <div className="flex items-center h-16 flex-shrink-0 px-6 border-b border-gray-200 dark:border-slate-700">
          <span className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">AltCare</span>
        </div>

        <div className="flex-1 flex flex-col overflow-y-auto">
          <NavLinks />
        </div>
      </div>
    </div>
  )
}
