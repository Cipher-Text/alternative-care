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
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Patients', href: '/patients', icon: Users },
  { name: 'Appointments', href: '/appointments', icon: Calendar },
  { name: 'Prescriptions', href: '/prescriptions', icon: FileText },
  { name: 'Payments', href: '/payments', icon: CreditCard },
  { name: 'Medicines', href: '/medicines', icon: Pill },
  { name: 'Library', href: '/library', icon: BookOpen },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="hidden md:flex md:w-64 md:flex-col">
      <div className="flex flex-col flex-1 min-h-0 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
        {/* Logo */}
        <div className="flex items-center h-16 flex-shrink-0 px-4 bg-indigo-600 dark:bg-indigo-800">
          <h1 className="text-xl font-bold text-white">AltCare</h1>
        </div>

        {/* Navigation */}
        <div className="flex-1 flex flex-col overflow-y-auto">
          <nav className="flex-1 px-2 py-4 space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                    isActive
                      ? 'bg-indigo-100 text-indigo-900 dark:bg-indigo-900 dark:text-indigo-100'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  )}
                >
                  <Icon
                    className={cn(
                      'mr-3 h-5 w-5 flex-shrink-0',
                      isActive
                        ? 'text-indigo-600 dark:text-indigo-400'
                        : 'text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300'
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
