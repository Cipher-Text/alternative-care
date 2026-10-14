'use client'

import { createContext, useContext } from 'react'
import { clinicTeamApi, createTeamApi, platformTeamApi, type TeamApi } from '@/lib/api/team'

/** Which team the page manages: a clinic's own staff and roles, or the platform's. The two share every component. */
export interface TeamArea {
  kind: 'clinic' | 'platform'
  /** Tells one area's cached data from another's (the platform can open any clinic's team) */
  key: string
  /** A clinic's team opened by the platform, which is the only side that can change it */
  byPlatform?: boolean
  api: TeamApi
}

export const clinicArea: TeamArea = { kind: 'clinic', key: 'clinic', api: clinicTeamApi }
export const platformArea: TeamArea = { kind: 'platform', key: 'platform', api: platformTeamApi }
export const clinicManagedByPlatform = (tenantId: string): TeamArea => ({
  kind: 'clinic',
  key: `clinic:${tenantId}`,
  byPlatform: true,
  api: createTeamApi(`/admin/tenants/${tenantId}/team`),
})

const TeamAreaContext = createContext<TeamArea>(clinicArea)

export const TeamAreaProvider = TeamAreaContext.Provider
export const useTeamArea = () => useContext(TeamAreaContext)
