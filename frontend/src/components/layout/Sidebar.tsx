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
      <div className="flex flex-col flex-1 min-h-0 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 border-r border-slate-700">
        {/* Logo */}
        <div className="flex items-center h-16 flex-shrink-0 px-6 border-b border-slate-700">
          <h1 className="text-2xl font-bold text-white tracking-tight">AltCare</h1>
        </div>

        {/* Navigation */}
        <div className="flex-1 flex flex-col overflow-y-auto">
          <nav className="flex-1 px-3 py-6 space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200',
                    isActive
                      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/50'
                      : 'text-gray-300 hover:bg-slate-700 hover:text-white'
                  )}
                >
                  <Icon
                    className={cn(
                      'mr-3 h-5 w-5 flex-shrink-0',
                      isActive
                        ? 'text-white'
                        : 'text-gray-400 group-hover:text-white'
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
