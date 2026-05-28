'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Building2,
  CheckCircle,
  Loader2,
  ShieldAlert,
  UserPlus,
  Users,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useApproveTenant, usePendingTenants, useProvisionClient } from '@/lib/hooks/useAdminClients'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { AdminCreateTenantDoctorRequest, MedicalSystem, SubscriptionPlan } from '@/types/auth'

const medicalSystems: Array<{ value: MedicalSystem; label: string }> = [
  { value: 'homeopathy', label: 'Homeopathy' },
  { value: 'ayurveda', label: 'Ayurveda' },
  { value: 'unani', label: 'Unani' },
  { value: 'herbal', label: 'Herbal' },
]

const initialForm: AdminCreateTenantDoctorRequest = {
  email: '',
  password: '',
  full_name: '',
  phone: '',
  language: 'en',
  clinic_name: '',
  clinic_address: '',
  specializations: ['homeopathy'],
  license_number: '',
  tenant_name: '',
  plan: 'free',
  auto_approve: true,
}

function compactPayload(form: AdminCreateTenantDoctorRequest): AdminCreateTenantDoctorRequest {
  return {
    ...form,
    phone: form.phone?.trim() || null,
    clinic_name: form.clinic_name?.trim() || null,
    clinic_address: form.clinic_address?.trim() || null,
    license_number: form.license_number?.trim() || null,
    tenant_name: form.tenant_name?.trim() || null,
  }
}

export default function AdminClientsPage() {
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  const [form, setForm] = useState<AdminCreateTenantDoctorRequest>(initialForm)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const isAdmin = user?.role === 'admin'

  const pendingTenants = usePendingTenants(isAdmin)
  const provisionClient = useProvisionClient()
  const approveTenant = useApproveTenant()

  const selectedSystems = useMemo(
    () => new Set(form.specializations),
    [form.specializations]
  )

  const validateForm = () => {
    const nextErrors: Record<string, string> = {}

    if (!form.full_name.trim()) nextErrors.full_name = 'Doctor name is required'
    if (!form.email.trim()) nextErrors.email = 'Email is required'
    if (!form.password.trim()) nextErrors.password = 'Password is required'
    if (form.password && form.password.length < 8) {
      nextErrors.password = 'Password must be at least 8 characters'
    }
    if (form.specializations.length === 0) {
      nextErrors.specializations = 'Select at least one medical system'
    }

    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const updateForm = <K extends keyof AdminCreateTenantDoctorRequest>(
    key: K,
    value: AdminCreateTenantDoctorRequest[K]
  ) => {
    setForm((current) => ({ ...current, [key]: value }))
  }

  const toggleSystem = (system: MedicalSystem) => {
    setForm((current) => {
      const exists = current.specializations.includes(system)
      const specializations = exists
        ? current.specializations.filter((item) => item !== system)
        : [...current.specializations, system]

      return { ...current, specializations }
    })
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!validateForm()) return

    const result = await provisionClient.mutateAsync(compactPayload(form))
    setForm(initialForm)
    setErrors({})

    if (result.requires_approval) {
      pendingTenants.refetch()
    }
  }

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
              Client provisioning is available only to platform administrators.
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Admin Clients</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Provision clinic tenants, create primary doctors, and approve registrations.
        </p>
      </div>

      <Tabs defaultValue="provision">
        <TabsList>
          <TabsTrigger value="provision">
            <UserPlus className="h-4 w-4 mr-2" />
            Provision Client
          </TabsTrigger>
          <TabsTrigger value="pending">
            <Users className="h-4 w-4 mr-2" />
            Pending Tenants
          </TabsTrigger>
        </TabsList>

        <TabsContent value="provision" className="mt-6">
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Tenant and Primary Doctor</CardTitle>
                  <CardDescription>
                    Creates an isolated tenant and the first doctor account in one operation.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-8">
                  <section className="space-y-4">
                    <div className="flex items-center gap-2">
                      <UserPlus className="h-5 w-5 text-indigo-600" />
                      <h2 className="text-lg font-semibold">Doctor Account</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="full_name">Full Name *</Label>
                        <Input
                          id="full_name"
                          value={form.full_name}
                          onChange={(event) => updateForm('full_name', event.target.value)}
                          placeholder="Dr. Example"
                        />
                        {errors.full_name && <p className="text-sm text-red-500">{errors.full_name}</p>}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="email">Email *</Label>
                        <Input
                          id="email"
                          type="email"
                          value={form.email}
                          onChange={(event) => updateForm('email', event.target.value)}
                          placeholder="doctor@example.com"
                        />
                        {errors.email && <p className="text-sm text-red-500">{errors.email}</p>}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="password">Initial Password *</Label>
                        <Input
                          id="password"
                          type="password"
                          value={form.password}
                          onChange={(event) => updateForm('password', event.target.value)}
                          placeholder="Doctor@1234"
                        />
                        {errors.password && <p className="text-sm text-red-500">{errors.password}</p>}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="phone">Phone</Label>
                        <Input
                          id="phone"
                          value={form.phone || ''}
                          onChange={(event) => updateForm('phone', event.target.value)}
                          placeholder="01700000000"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Language</Label>
                        <Select
                          value={form.language}
                          onValueChange={(value) => updateForm('language', value as 'en' | 'bn')}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="en">English</SelectItem>
                            <SelectItem value="bn">Bengali</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="license_number">License Number</Label>
                        <Input
                          id="license_number"
                          value={form.license_number || ''}
                          onChange={(event) => updateForm('license_number', event.target.value)}
                          placeholder="BMDC-123"
                        />
                      </div>
                    </div>
                  </section>

                  <section className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-5 w-5 text-indigo-600" />
                      <h2 className="text-lg font-semibold">Clinic Tenant</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="tenant_name">Tenant Name</Label>
                        <Input
                          id="tenant_name"
                          value={form.tenant_name || ''}
                          onChange={(event) => updateForm('tenant_name', event.target.value)}
                          placeholder="Defaults to doctor name"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="clinic_name">Clinic Name</Label>
                        <Input
                          id="clinic_name"
                          value={form.clinic_name || ''}
                          onChange={(event) => updateForm('clinic_name', event.target.value)}
                          placeholder="Example Clinic"
                        />
                      </div>

                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor="clinic_address">Clinic Address</Label>
                        <Textarea
                          id="clinic_address"
                          value={form.clinic_address || ''}
                          onChange={(event) => updateForm('clinic_address', event.target.value)}
                          placeholder="Clinic address"
                          rows={3}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Plan</Label>
                        <Select
                          value={form.plan}
                          onValueChange={(value) => updateForm('plan', value as SubscriptionPlan)}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="free">Free</SelectItem>
                            <SelectItem value="plus">Plus</SelectItem>
                            <SelectItem value="pro">Pro</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label>Approval</Label>
                        <Select
                          value={form.auto_approve ? 'yes' : 'no'}
                          onValueChange={(value) => updateForm('auto_approve', value === 'yes')}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="yes">Auto approve</SelectItem>
                            <SelectItem value="no">Create as pending</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Medical Systems *</Label>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                        {medicalSystems.map((system) => (
                          <Button
                            key={system.value}
                            type="button"
                            variant={selectedSystems.has(system.value) ? 'default' : 'outline'}
                            onClick={() => toggleSystem(system.value)}
                            className="justify-center"
                          >
                            {system.label}
                          </Button>
                        ))}
                      </div>
                      {errors.specializations && (
                        <p className="text-sm text-red-500">{errors.specializations}</p>
                      )}
                    </div>
                  </section>
                </CardContent>
              </Card>

              <Card className="h-fit">
                <CardHeader>
                  <CardTitle>Provisioning Summary</CardTitle>
                  <CardDescription>
                    The doctor will belong to the new tenant. Platform admins remain outside tenant scope.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between gap-4">
                      <span className="text-muted-foreground">Tenant</span>
                      <span className="font-medium text-right">
                        {form.tenant_name || form.clinic_name || form.full_name || 'Not set'}
                      </span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-muted-foreground">Doctor</span>
                      <span className="font-medium text-right">{form.full_name || 'Not set'}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-muted-foreground">Plan</span>
                      <Badge variant="outline" className="capitalize">{form.plan}</Badge>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-muted-foreground">Status</span>
                      <Badge variant={form.auto_approve ? 'default' : 'outline'}>
                        {form.auto_approve ? 'Approved' : 'Pending'}
                      </Badge>
                    </div>
                  </div>

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={provisionClient.isLoading}
                  >
                    {provisionClient.isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Creating Client
                      </>
                    ) : (
                      <>
                        <UserPlus className="h-4 w-4 mr-2" />
                        Create Tenant and Doctor
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </div>
          </form>
        </TabsContent>

        <TabsContent value="pending" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Pending Tenant Approvals</CardTitle>
              <CardDescription>
                Self-registered doctor tenants cannot log in until a platform admin approves them.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {pendingTenants.isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
                </div>
              ) : pendingTenants.data && pendingTenants.data.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tenant</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Plan</TableHead>
                      <TableHead>Systems</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingTenants.data.map((tenant) => (
                      <TableRow key={tenant.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{tenant.name}</p>
                            {tenant.clinic_name && (
                              <p className="text-sm text-muted-foreground">{tenant.clinic_name}</p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{tenant.email}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">{tenant.plan}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {tenant.specializations.map((system) => (
                              <Badge key={system} variant="outline" className="capitalize">
                                {system}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">Pending</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            onClick={() => approveTenant.mutate(tenant.id)}
                            disabled={approveTenant.isLoading}
                          >
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Approve
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-12">
                  <CheckCircle className="h-12 w-12 mx-auto text-green-600 mb-4" />
                  <h3 className="text-lg font-semibold">No pending tenants</h3>
                  <p className="text-muted-foreground mt-2">
                    New self-registrations will appear here for platform approval.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
