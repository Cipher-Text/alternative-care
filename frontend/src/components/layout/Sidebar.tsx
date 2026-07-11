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
  BookOpen,
  Settings,
  LayoutDashboard,
  Building2,
  UserCog,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

const doctorNavigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Patients', href: '/patients', icon: Users },
  { name: 'Appointments', href: '/appointments', icon: Calendar },
  { name: 'Prescriptions', href: '/prescriptions', icon: FileText },
  { name: 'Payments', href: '/payments', icon: CreditCard },
  { name: 'Medicines', href: '/medicines', icon: Pill },
  { name: 'Library', href: '/library', icon: BookOpen },
  { name: 'Settings', href: '/settings', icon: Settings },
]

const adminNavigation = [
  { name: 'Platform Dashboard', href: '/admin/dashboard', icon: LayoutDashboard },
  { name: 'Clients', href: '/admin/clients', icon: Building2 },
  { name: 'Users', href: '/admin/users', icon: UserCog },
]

export function Sidebar() {
  const pathname = usePathname()
  const user = useAuthStore((state) => state.user)

  // Platform admins see only admin nav — no patient/appointment/prescription items
  const items = user?.role === 'admin' ? adminNavigation : doctorNavigation

  return (
    <div className="hidden md:flex md:w-64 md:flex-col">
      <div className="flex flex-col flex-1 min-h-0 bg-white dark:bg-gradient-to-b dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 border-r border-gray-200 dark:border-slate-700 transition-colors">
        {/* Logo */}
        <div className="flex items-center h-16 flex-shrink-0 px-6 border-b border-gray-200 dark:border-slate-700">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">AltCare</h1>
        </div>

        {/* Navigation */}
        <div className="flex-1 flex flex-col overflow-y-auto">
          <nav className="flex-1 px-3 py-6 space-y-1">
            {items.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`)
              const Icon = item.icon

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200',
                    isActive
                      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/50'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700 hover:text-gray-900 dark:hover:text-white'
                  )}
                >
                  <Icon
                    className={cn(
                      'mr-3 h-5 w-5 flex-shrink-0',
                      isActive
                        ? 'text-white'
                        : 'text-gray-500 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white'
                    )}
                  />
                  {item.name}
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
    </div>
  )
}
