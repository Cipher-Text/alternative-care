'use client'

import { use } from 'react'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft,
  Building2,
  CalendarClock,
  CheckCircle,
  Loader2,
  Mail,
  Phone,
  ShieldAlert,
  Stethoscope,
  User,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useAdminClient } from '@/lib/hooks/useAdminClients'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

function formatDate(value: string | null) {
  if (!value) return 'Not available'
  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export default function AdminClientDetailPage({
  params,
}: {
  params: Promise<{ tenantId: string }>
}) {
  const { tenantId } = use(params)
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  const isAdmin = user?.role === 'admin'
  const { data, isLoading, error } = useAdminClient(tenantId, isAdmin)

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
              Client details are available only to platform administrators.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={() => router.push('/dashboard')}>
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <Button variant="outline" size="sm" onClick={() => router.push('/admin/clients')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Card>
          <CardHeader>
            <CardTitle>Client not found</CardTitle>
            <CardDescription>
              The client may have been removed or you may not have access.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  const { tenant, doctors } = data

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={() => router.push('/admin/clients')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div className="min-w-0">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            {tenant.clinic_name || tenant.name}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Clinic tenant and doctor account details
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-indigo-600" />
              Clinic / Tenant
            </CardTitle>
            <CardDescription>
              Platform-level tenant record used for multi-tenant isolation.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <p className="text-sm text-muted-foreground">Tenant Name</p>
              <p className="font-medium">{tenant.name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Clinic Name</p>
              <p className="font-medium">{tenant.clinic_name || 'Not provided'}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Email</p>
              <p className="font-medium">{tenant.email}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Plan</p>
              <Badge variant="outline" className="capitalize">{tenant.plan}</Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Approval</p>
              <Badge variant={tenant.is_approved ? 'default' : 'outline'}>
                {tenant.is_approved ? 'Approved' : 'Pending'}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Verification</p>
              <Badge variant={tenant.is_verified ? 'default' : 'outline'}>
                {tenant.is_verified ? 'Verified' : 'Unverified'}
              </Badge>
            </div>
            <div className="md:col-span-2">
              <p className="text-sm text-muted-foreground">Specializations</p>
              <div className="flex flex-wrap gap-2 mt-1">
                {tenant.specializations.map((system) => (
                  <Badge key={system} variant="outline" className="capitalize">
                    {system}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarClock className="h-5 w-5 text-indigo-600" />
              Lifecycle
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">Created</p>
              <p className="font-medium">{formatDate(data.created_at)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Updated</p>
              <p className="font-medium">{formatDate(data.updated_at)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Approved</p>
              <p className="font-medium">{formatDate(data.approved_at)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Approved By</p>
              <p className="font-medium">{data.approved_by || 'Not available'}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Stethoscope className="h-5 w-5 text-indigo-600" />
            Doctors
          </CardTitle>
          <CardDescription>
            Doctor users attached to this tenant.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {doctors.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Doctor</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {doctors.map((doctor) => (
                  <TableRow key={doctor.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="h-9 w-9 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
                          <User className="h-4 w-4 text-indigo-600 dark:text-indigo-300" />
                        </div>
                        <div>
                          <p className="font-medium">{doctor.full_name}</p>
                          <p className="text-sm text-muted-foreground capitalize">{doctor.role}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <p className="flex items-center gap-2 text-sm">
                          <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                          {doctor.email}
                        </p>
                        {doctor.phone && (
                          <p className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Phone className="h-3.5 w-3.5" />
                            {doctor.phone}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-2">
                        <Badge variant={doctor.is_active ? 'default' : 'outline'}>
                          {doctor.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                        {doctor.is_email_verified && (
                          <Badge variant="outline">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Email verified
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{formatDate(doctor.last_login_at)}</TableCell>
                    <TableCell>{formatDate(doctor.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12">
              <User className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold">No doctors found</h3>
              <p className="text-muted-foreground mt-2">
                This tenant does not currently have doctor users attached.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
