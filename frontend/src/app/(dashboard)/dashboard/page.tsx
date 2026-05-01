'use client'

import { useAuthStore } from '@/store/authStore'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back, {user?.full_name}!</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Total Patients</CardTitle>
            <CardDescription>All time</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">--</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Today's Appointments</CardTitle>
            <CardDescription>Scheduled</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">--</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>This Month Revenue</CardTitle>
            <CardDescription>Total collected</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">--</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pending Payments</CardTitle>
            <CardDescription>Outstanding</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">--</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>User Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <p className="text-sm text-muted-foreground">Email:</p>
            <p className="text-sm font-medium">{user?.email}</p>

            <p className="text-sm text-muted-foreground">Role:</p>
            <p className="text-sm font-medium capitalize">{user?.role}</p>

            <p className="text-sm text-muted-foreground">Plan:</p>
            <p className="text-sm font-medium capitalize">{user?.plan}</p>

            <p className="text-sm text-muted-foreground">Language:</p>
            <p className="text-sm font-medium uppercase">{user?.language}</p>

            <p className="text-sm text-muted-foreground">2FA:</p>
            <p className="text-sm font-medium">{user?.two_factor_enabled ? 'Enabled' : 'Disabled'}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
