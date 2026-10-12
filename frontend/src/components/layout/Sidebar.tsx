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
  Newspaper,
  BadgeCheck,
  MessageSquare,
  Receipt,
  Megaphone,
  Inbox,
} from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useAuthStore } from '@/store/authStore'
import { useCan } from '@/lib/auth/permissions'

const doctorNavigation = [
  { key: 'dashboard', href: '/dashboard', icon: Home },
  { key: 'patients', href: '/patients', icon: Users },
  { key: 'appointments', href: '/appointments', icon: Calendar },
  { key: 'prescriptions', href: '/prescriptions', icon: FileText },
  { key: 'payments', href: '/payments', icon: CreditCard },
  { key: 'medicines', href: '/medicines', icon: Pill },
  { key: 'pharmacies', href: '/pharmacies', icon: Store },
  { key: 'symptoms', href: '/symptoms', icon: Stethoscope },
  { key: 'articles', href: '/content', icon: Newspaper },
  { key: 'directory', href: '/directory', icon: BadgeCheck },
  { key: 'billing', href: '/billing', icon: Receipt },
  { key: 'facebookPromotion', href: '/marketing', icon: Megaphone },
  { key: 'settings', href: '/settings', icon: Settings },
  // Doctors reach Messaging through Settings; receptionists have no Settings, so they get a direct link
  { key: 'messaging', href: '/settings/messaging', icon: MessageSquare },
]

const adminNavigation = [
  { key: 'platformDashboard', href: '/admin/dashboard', icon: LayoutDashboard },
  { key: 'clients', href: '/admin/clients', icon: Building2 },
  { key: 'plansPricing', href: '/admin/plans', icon: Tags },
  { key: 'adminBilling', href: '/admin/billing', icon: Receipt },
  { key: 'facebookPromotion', href: '/admin/marketing', icon: Megaphone },
  { key: 'users', href: '/admin/users', icon: UserCog },
  { key: 'contactMessages', href: '/admin/contact', icon: Inbox },
  { key: 'articles', href: '/content', icon: Newspaper },
  { key: 'institutions', href: '/admin/institutions', icon: GraduationCap },
  { key: 'pharmacies', href: '/admin/pharmacies', icon: Store },
  { key: 'medicines', href: '/admin/medicines', icon: Pill },
  { key: 'symptoms', href: '/admin/symptoms', icon: Stethoscope },
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
    ? // the content and billing APIs are admin only, so operators don't get those links
      adminNavigation.filter((item) => user.role === 'admin' || (item.href !== '/content' && item.href !== '/admin/billing' && item.href !== '/admin/marketing' && item.href !== '/admin/contact'))
    : doctorNavigation.filter(
        (item) =>
          (can.manageClinicSettings ? item.href !== '/settings/messaging' : item.href !== '/settings' && item.href !== '/billing') && // billing: doctors only
          
          (!can.isReceptionist || (item.href !== '/content' && item.href !== '/directory' && item.href !== '/marketing')) // articles, directory, Facebook promotion: no receptionists
      )
}

export function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname()
  const items = useNavItems()
  const t = useTranslations('nav')

  return (
    <nav className="flex-1 px-3 py-6 space-y-1" aria-label={t('mainNavigation')}>
      {items.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`)
        const Icon = item.icon

        return (
          <Link
            key={item.key}
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
            {t(item.key)}
          </Link>
        )
      })}
    </nav>
  )
}

export function Sidebar() {
  return (
    <div className="hidden md:flex md:w-64 md:flex-col print:hidden">
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
