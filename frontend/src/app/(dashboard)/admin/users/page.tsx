'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  AlertCircle,
  Loader2,
  Search,
  ShieldAlert,
  UserCog,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useAdminUsers, useUpdateUser } from '@/lib/hooks/useAdmin'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { AdminUserItem, UserRole } from '@/types/admin'

const ROLES = ['admin', 'operator', 'doctor', 'receptionist'] as const

const roleColors: Record<string, string> = {
  admin: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  operator: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  doctor: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  receptionist: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function RoleBadge({ role }: { role: string }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${roleColors[role] ?? 'bg-gray-100 text-gray-800'}`}
    >
      {role}
    </span>
  )
}

function EditUserModal({
  user,
  onClose,
}: {
  user: AdminUserItem
  onClose: () => void
}) {
  const updateUser = useUpdateUser()
  const [role, setRole] = useState<UserRole>(user.role as UserRole)
  const [isActive, setIsActive] = useState<boolean>(user.is_active)

  const isPlatformUser = user.tenant_id === null
  const availableRoles: UserRole[] = isPlatformUser
    ? ['admin', 'operator']
    : ['doctor', 'receptionist']

  const handleSave = async () => {
    const changed: { role?: UserRole; is_active?: boolean } = {}
    if (role !== user.role) changed.role = role
    if (isActive !== user.is_active) changed.is_active = isActive

    if (Object.keys(changed).length === 0) {
      onClose()
      return
    }

    try {
      await updateUser.mutateAsync({ userId: user.id, data: changed })
      onClose()
    } catch {
      // error handled by hook (toast)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl p-6 w-full max-w-md space-y-6">
        <div>
          <h2 className="text-lg font-semibold">Edit User</h2>
          <p className="text-sm text-muted-foreground mt-1">{user.full_name} &middot; {user.email}</p>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Role</Label>
            <Select value={role} onValueChange={(v) => setRole(v as UserRole)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {availableRoles.map((r) => (
                  <SelectItem key={r} value={r} className="capitalize">
                    {r}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {role !== user.role && (
              <p className="text-xs text-amber-600 flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                Changing role will immediately invalidate the user&apos;s current session.
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label>Status</Label>
            <Select
              value={isActive ? 'active' : 'inactive'}
              onValueChange={(v) => setIsActive(v === 'active')}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <Button variant="outline" className="flex-1" onClick={onClose}>
            Cancel
          </Button>
          <Button
            className="flex-1"
            onClick={handleSave}
            disabled={updateUser.isLoading}
          >
            {updateUser.isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : null}
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  )
}

export default function AdminUsersPage() {
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  const isAdmin = user?.role === 'admin'

  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [editingUser, setEditingUser] = useState<AdminUserItem | null>(null)

  const { data, isLoading } = useAdminUsers(undefined, isAdmin)

  const filteredUsers = useMemo(() => {
    if (!data) return []
    let users = data.users

    if (roleFilter !== 'all') {
      users = users.filter((u) => u.role === roleFilter)
    }
    if (statusFilter !== 'all') {
      const active = statusFilter === 'active'
      users = users.filter((u) => u.is_active === active)
    }
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase()
      users = users.filter(
        (u) =>
          u.full_name.toLowerCase().includes(term) ||
          u.email.toLowerCase().includes(term) ||
          (u.tenant_name ?? '').toLowerCase().includes(term)
      )
    }
    return users
  }, [data, roleFilter, statusFilter, searchTerm])

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
              User management is available only to platform administrators.
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

  const summary = data?.summary

  return (
    <div className="space-y-6">
      {editingUser && (
        <EditUserModal user={editingUser} onClose={() => setEditingUser(null)} />
      )}

      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Users</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Role distribution across the platform. Click a role card to filter.
        </p>
      </div>

      {/* Role group cards */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {ROLES.map((r) => {
              const count = summary?.by_role[r] ?? 0
              const isSelected = roleFilter === r
              return (
                <button
                  key={r}
                  onClick={() => setRoleFilter(isSelected ? 'all' : r)}
                  className={`rounded-xl border p-4 text-left transition-all ${
                    isSelected
                      ? 'border-indigo-500 ring-2 ring-indigo-500 bg-indigo-50 dark:bg-indigo-950'
                      : 'hover:border-indigo-300 hover:bg-gray-50 dark:hover:bg-slate-800'
                  }`}
                >
                  <p className="text-3xl font-bold">{count}</p>
                  <RoleBadge role={r} />
                  <p className="text-xs text-muted-foreground mt-1">
                    {r === 'admin' || r === 'operator' ? 'Platform' : 'Tenant'}
                  </p>
                </button>
              )
            })}
          </div>

          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <UserCog className="h-5 w-5 text-indigo-500" />
                All Users
                {summary && (
                  <Badge variant="outline" className="ml-2">
                    {filteredUsers.length} of {summary.total}
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                Manage individual users — change role or activate/deactivate.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search by name, email, or clinic"
                    className="pl-9"
                  />
                </div>
                <Select value={roleFilter} onValueChange={setRoleFilter}>
                  <SelectTrigger className="w-[160px]">
                    <SelectValue placeholder="All roles" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All roles</SelectItem>
                    {ROLES.map((r) => (
                      <SelectItem key={r} value={r} className="capitalize">
                        {r}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="All status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All status</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {filteredUsers.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Clinic / Tenant</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Last Login</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUsers.map((u) => (
                      <TableRow key={u.id}>
                        <TableCell className="font-medium">{u.full_name}</TableCell>
                        <TableCell className="text-muted-foreground">{u.email}</TableCell>
                        <TableCell>
                          <RoleBadge role={u.role} />
                        </TableCell>
                        <TableCell>
                          {u.tenant_name ? (
                            <span className="text-sm">{u.tenant_name}</span>
                          ) : (
                            <span className="text-xs text-muted-foreground">Platform</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant={u.is_active ? 'default' : 'outline'}>
                            {u.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {formatDate(u.last_login_at)}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setEditingUser(u)}
                          >
                            Edit
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-12">
                  <UserCog className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold">No users found</h3>
                  <p className="text-muted-foreground mt-2">
                    Try adjusting your search or filters.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
