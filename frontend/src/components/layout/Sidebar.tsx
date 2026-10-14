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
  CalendarClock,
} from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useAuthStore } from '@/store/authStore'
import { useCan } from '@/lib/auth/permissions'

interface NavItem {
  key: string
  href: string
  icon: React.ElementType
  /** The user sees the item when they hold at least one of these permissions. No list: everyone signed in sees it. */
  any?: string[]
}

const doctorNavigation: NavItem[] = [
  { key: 'dashboard', href: '/dashboard', icon: Home, any: ['dashboard.view'] },
  { key: 'patients', href: '/patients', icon: Users, any: ['patients.read'] },
  { key: 'appointments', href: '/appointments', icon: Calendar, any: ['appointments.read'] },
  { key: 'appointmentRequests', href: '/appointment-requests', icon: CalendarClock, any: ['appointment_requests.manage'] },
  { key: 'prescriptions', href: '/prescriptions', icon: FileText, any: ['prescriptions.read'] },
  { key: 'payments', href: '/payments', icon: CreditCard, any: ['payments.read', 'invoices.read'] },
  { key: 'medicines', href: '/medicines', icon: Pill, any: ['medicines.read'] },
  { key: 'pharmacies', href: '/pharmacies', icon: Store },
  { key: 'symptoms', href: '/symptoms', icon: Stethoscope, any: ['symptoms.read'] },
  { key: 'articles', href: '/content', icon: Newspaper, any: ['content.author'] },
  { key: 'directory', href: '/directory', icon: BadgeCheck, any: ['directory.manage'] },
  { key: 'billing', href: '/billing', icon: Receipt, any: ['billing.manage'] },
  { key: 'facebookPromotion', href: '/marketing', icon: Megaphone, any: ['marketing.request'] },
  // The settings page leads to Messaging. Staff without clinic settings (the front desk) get a direct Messaging link instead.
  { key: 'settings', href: '/settings', icon: Settings, any: ['doctor_profile.manage'] },
  { key: 'messaging', href: '/settings/messaging', icon: MessageSquare, any: ['billing.view'] },
]

const adminNavigation: NavItem[] = [
  { key: 'platformDashboard', href: '/admin/dashboard', icon: LayoutDashboard, any: ['tenants.read'] },
  { key: 'clients', href: '/admin/clients', icon: Building2, any: ['tenants.read'] },
  { key: 'plansPricing', href: '/admin/plans', icon: Tags, any: ['plans.read'] },
  { key: 'adminBilling', href: '/admin/billing', icon: Receipt, any: ['billing.admin'] },
  { key: 'facebookPromotion', href: '/admin/marketing', icon: Megaphone, any: ['marketing.manage'] },
  { key: 'users', href: '/admin/users', icon: UserCog, any: ['users.read'] },
  { key: 'contactMessages', href: '/admin/contact', icon: Inbox, any: ['contact.manage'] },
  { key: 'articles', href: '/content', icon: Newspaper, any: ['content.manage', 'content.author'] },
  { key: 'institutions', href: '/admin/institutions', icon: GraduationCap },
  { key: 'pharmacies', href: '/admin/pharmacies', icon: Store },
  { key: 'medicines', href: '/admin/medicines', icon: Pill },
  { key: 'symptoms', href: '/admin/symptoms', icon: Stethoscope },
]

/** The nav items for the signed-in user (shared by the sidebar and the phone drawer): platform staff have no clinic,
 * so they get the admin menu; everyone else gets the clinic menu, each item shown only if they hold its permission. */
export function useNavItems() {
  const user = useAuthStore((state) => state.user)
  const { can, canAny } = useCan()
  const isPlatform = !user?.tenant_id

  return (isPlatform ? adminNavigation : doctorNavigation).filter((item) => {
    if (item.key === 'messaging') return can('billing.view') && !can('doctor_profile.manage')
    return !item.any || canAny(...item.any)
  })
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
