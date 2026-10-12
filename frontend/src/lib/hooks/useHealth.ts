import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { healthApi } from '@/lib/api/health'
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

export function useVisits(patientId: string) {
  return useQuery(healthKeys.visits(patientId), () => healthApi.visits(patientId), { staleTime: 30000 })
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
