'use client'

import { useCan } from '@/lib/auth/permissions'
import { clinicArea } from '@/lib/team/area'
import { TeamWorkspace } from '@/components/team/TeamWorkspace'

/** A clinic's team, read only: staff, roles and the trail of changes. Needs `team.read`. Adding staff or changing roles is
 * done by AltCare (the platform), so a clinic that needs a change contacts AltCare. */
export default function TeamPage() {
  const { can } = useCan()
  return <TeamWorkspace area={clinicArea} canView={can('team.read')} canManage={false} />
}
