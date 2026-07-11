'use client'

import { useRouter } from 'next/navigation'
import {
  Building2,
  CheckCircle,
  Clock,
  Loader2,
  ShieldAlert,
  Stethoscope,
  Users,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useAdminDashboard } from '@/lib/hooks/useAdmin'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

function StatCard({
  title,
  value,
  description,
  icon: Icon,
  variant = 'default',
}: {
  title: string
  value: number
  description?: string
  icon: React.ElementType
  variant?: 'default' | 'warning' | 'success'
}) {
  const iconColor =
    variant === 'warning'
      ? 'text-amber-500'
      : variant === 'success'
        ? 'text-green-500'
        : 'text-indigo-500'

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold mt-1">{value.toLocaleString()}</p>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          <Icon className={`h-10 w-10 ${iconColor} opacity-80`} />
        </div>
      </CardContent>
    </Card>
  )
}

export default function AdminDashboardPage() {
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  const isAdmin = user?.role === 'admin'
  const { data, isLoading } = useAdminDashboard(isAdmin)

  if (!isAdmin) {
    return (
      <div className="flex min-h-[420px] items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-amber-600" />
              Admin Access Required
            </CardTitle>
            <CardDescription>
              The platform dashboard is available only to platform administrators.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={() => router.push('/dashboard')}>
              Go to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[420px]">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  const plans = data?.plans ?? { free: 0, plus: 0, pro: 0 }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Platform Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          System-wide metrics across all clinics and practitioners.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          title="Total Tenants"
          value={data?.total_tenants ?? 0}
          description="All registered clinics"
          icon={Building2}
        />
        <StatCard
          title="Active Tenants"
          value={data?.active_tenants ?? 0}
          description="Approved and active"
          icon={CheckCircle}
          variant="success"
        />
        <StatCard
          title="Pending Approvals"
          value={data?.pending_approvals ?? 0}
          description="Awaiting admin approval"
          icon={Clock}
          variant={data?.pending_approvals ? 'warning' : 'default'}
        />
        <StatCard
          title="Total Doctors"
          value={data?.total_doctors ?? 0}
          description="Across all clinics"
          icon={Stethoscope}
        />
        <StatCard
          title="Total Users"
          value={data?.total_users ?? 0}
          description="All roles combined"
          icon={Users}
        />
      </div>

      {/* Plan Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Plan Distribution</CardTitle>
          <CardDescription>
            How tenants are distributed across subscription plans.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            {(['free', 'plus', 'pro'] as const).map((plan) => (
              <div key={plan} className="flex items-center gap-3 p-4 rounded-lg border min-w-[140px]">
                <div className="flex-1">
                  <p className="text-2xl font-bold">{plans[plan]}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge
                      variant={plan === 'pro' ? 'default' : 'outline'}
                      className="capitalize"
                    >
                      {plan}
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Links */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card className="cursor-pointer hover:border-indigo-300 transition-colors" onClick={() => router.push('/admin/clients')}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <Building2 className="h-8 w-8 text-indigo-500" />
              <div>
                <p className="font-semibold">Manage Clients</p>
                <p className="text-sm text-muted-foreground">
                  Provision, approve, suspend, or change plans
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:border-indigo-300 transition-colors" onClick={() => router.push('/admin/users')}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <Users className="h-8 w-8 text-indigo-500" />
              <div>
                <p className="font-semibold">Role Distribution</p>
                <p className="text-sm text-muted-foreground">
                  View and manage users by role
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
