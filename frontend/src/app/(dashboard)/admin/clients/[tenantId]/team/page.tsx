'use client'

import { use, useMemo } from 'react'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useCan } from '@/lib/auth/permissions'
import { useAdminClient } from '@/lib/hooks/useAdminClients'
import { clinicManagedByPlatform } from '@/lib/team/area'
import { TeamWorkspace } from '@/components/team/TeamWorkspace'

/** A clinic's staff and roles, managed by the platform on the clinic's behalf. Looking needs `tenants.read`, changing it
 * `clinic_roles.manage`. Clinics cannot do this themselves; they contact AltCare. */
export default function ClinicTeamPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = use(params)
  const { can } = useCan()
  const { data } = useAdminClient(tenantId)
  const area = useMemo(() => clinicManagedByPlatform(tenantId), [tenantId])
  const name = data?.tenant.clinic_name || data?.tenant.name

  return (
    <div className="space-y-4">
      <Button asChild variant="outline" size="sm">
        <Link href={`/admin/clients/${tenantId}`}>
          <ArrowLeft className="mr-2 h-4 w-4" aria-hidden="true" />
          {name ?? 'Back'}
        </Link>
      </Button>
      <TeamWorkspace area={area} canView={can('tenants.read')} canManage={can('clinic_roles.manage')} />
    </div>
  )
}
