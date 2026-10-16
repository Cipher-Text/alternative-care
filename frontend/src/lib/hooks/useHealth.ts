import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { healthApi } from '@/lib/api/health'
import { patientsApi } from '@/lib/api/patients'
import { errorMessage } from '@/lib/apiErrors'
import type { HealthProfileInput, VisitInput } from '@/types/health'

export const healthKeys = {
  options: ['health', 'options'] as const,
  profile: (patientId: string) => ['health', 'profile', patientId] as const,
  visits: (patientId: string) => ['health', 'visits', patientId] as const,
}

/** The closed lists never change while the app is open. */
export function useHealthOptions() {
  return useQuery(healthKeys.options, () => healthApi.options(), { staleTime: Infinity })
}

export function useHealthProfile(patientId: string | undefined) {
  return useQuery(healthKeys.profile(patientId ?? ''), () => healthApi.getProfile(patientId as string), {
    enabled: Boolean(patientId),
    staleTime: 30000,
  })
}

export function useSaveHealthProfile(patientId: string) {
  const t = useTranslations('healthUi.profile')
  const queryClient = useQueryClient()
  return useMutation((data: HealthProfileInput) => healthApi.saveProfile(patientId, data), {
    onSuccess: (profile) => {
      queryClient.setQueryData(healthKeys.profile(patientId), profile)
      toast.success(t('saved'))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('saveFailed')))
    },
  })
}

/** One visit in full, for the consultation screen. */
export function useVisit(visitId: string) {
  return useQuery(['health', 'visit', visitId], () => healthApi.visit(visitId), { enabled: Boolean(visitId), staleTime: 30000 })
}

export function useVisits(patientId: string | undefined) {
  return useQuery(healthKeys.visits(patientId ?? ''), () => healthApi.visits(patientId as string), {
    enabled: Boolean(patientId),
    staleTime: 30000,
  })
}

export function useCreateVisit(patientId: string) {
  const t = useTranslations('healthUi.visits')
  const queryClient = useQueryClient()
  return useMutation((data: VisitInput) => healthApi.createVisit(data), {
    onSuccess: () => {
      queryClient.invalidateQueries(healthKeys.visits(patientId))
      toast.success(t('saved'))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('saveFailed')))
    },
  })
}

/** Finish a visit: marks it completed, which also completes the appointment it was started from. */
export function useFinishVisit(patientId: string) {
  const t = useTranslations('healthUi.visits')
  const queryClient = useQueryClient()
  return useMutation((visitId: string) => healthApi.updateVisit(visitId, { status: 'completed' }), {
    onSuccess: () => {
      queryClient.invalidateQueries(healthKeys.visits(patientId))
      queryClient.invalidateQueries('appointments')
      queryClient.invalidateQueries(['dashboard'])
      toast.success(t('finished'))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('saveFailed')))
    },
  })
}

/** Add a diagnosis to a patient's history. */
export function useAddDiagnosis(patientId: string) {
  const t = useTranslations('patientDiagnosisUi')
  const queryClient = useQueryClient()
  return useMutation((data: { description: string; icd_code?: string; diagnosed_at: string }) => patientsApi.addDiagnosis(patientId, data), {
    onSuccess: () => {
      queryClient.invalidateQueries(['patient', patientId, 'diagnoses'])
      toast.success(t('saved'))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('failed')))
    },
  })
}
