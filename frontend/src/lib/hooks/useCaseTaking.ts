import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { caseTakingApi } from '@/lib/api/caseTaking'
import { errorMessage } from '@/lib/apiErrors'
import { useAuthStore } from '@/store/authStore'
import { useDoctorProfile } from '@/lib/hooks/useDoctor'
import type { CaseData } from '@/types/caseTaking'

/** Systems that have case-taking forms (the others are added as their fields are reviewed). */
export const CASE_SYSTEMS = ['homeopathy', 'ayurveda'] as const
export type CaseSystem = (typeof CASE_SYSTEMS)[number]

export const caseKeys = {
  definitions: (system: string) => ['case', 'definitions', system] as const,
  patient: (patientId: string, system: string) => ['case', 'patient', patientId, system] as const,
  visit: (visitId: string, system: string) => ['case', 'visit', visitId, system] as const,
}

/** The systems this clinic practises that have forms. Doctors only: it reads the doctor profile. */
export function useCaseSystems(): CaseSystem[] {
  const role = useAuthStore((s) => s.user?.role)
  const { data: profile } = useDoctorProfile({ enabled: role === 'doctor' })
  if (role !== 'doctor' || !profile) return []
  return CASE_SYSTEMS.filter((s) => profile.specializations.includes(s))
}

export function useCaseDefinitions(system: string) {
  return useQuery(caseKeys.definitions(system), () => caseTakingApi.definitions(system), { staleTime: Infinity })
}

export function usePatientCase(patientId: string, system: string) {
  return useQuery(caseKeys.patient(patientId, system), () => caseTakingApi.getPatient(patientId, system), { staleTime: 30000 })
}

export function useSavePatientCase(patientId: string, system: string) {
  const t = useTranslations('caseTakingUi.panel')
  const queryClient = useQueryClient()
  return useMutation((data: CaseData) => caseTakingApi.savePatient(patientId, system, data), {
    onSuccess: (record) => {
      queryClient.setQueryData(caseKeys.patient(patientId, system), record)
      toast.success(t('saved'))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('saveFailed')))
    },
  })
}

export function useVisitCase(visitId: string, system: string, enabled: boolean) {
  return useQuery(caseKeys.visit(visitId, system), () => caseTakingApi.getVisit(visitId, system), { enabled, staleTime: 30000 })
}

/** For the visit dialog: saves one system's answers once the visit exists. No toast: the visit's own one shows. */
export function useSaveVisitCase() {
  const queryClient = useQueryClient()
  return useMutation(({ visitId, system, data }: { visitId: string; system: string; data: CaseData }) =>
    caseTakingApi.saveVisit(visitId, system, data), {
    onSuccess: (record, vars) => {
      queryClient.setQueryData(caseKeys.visit(vars.visitId, vars.system), record)
    },
  })
}
