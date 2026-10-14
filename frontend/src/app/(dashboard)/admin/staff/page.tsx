'use client'

import { useCan } from '@/lib/auth/permissions'
import { platformArea } from '@/lib/team/area'
import { TeamWorkspace } from '@/components/team/TeamWorkspace'

/** The platform's own team: staff, platform roles and the audit trail across the platform and every clinic.
 * Seeing it needs `users.read`, changing it `roles.manage_global`. */
export default function PlatformStaffPage() {
  const { can } = useCan()
  return <TeamWorkspace area={platformArea} canView={can('users.read')} canManage={can('roles.manage_global')} />
}
