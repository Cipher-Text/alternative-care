import type { User } from '@/types/auth'

export function getPostLoginPath(user: Pick<User, 'role' | 'tenant_id'>): string {
  if (user.tenant_id === null && (user.role === 'admin' || user.role === 'operator')) {
    return '/admin/dashboard'
  }

  return '/dashboard'
}
