import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { tenantApi } from '@/lib/api/tenant'
import { errorMessage } from '@/lib/apiErrors'
import type { ClinicProfile } from '@/types/tenant'

const KEY = ['tenant', 'profile'] as const

export function useClinicProfile() {
  return useQuery(KEY, () => tenantApi.getProfile(), { staleTime: 60000 })
}

export function useUploadLogo() {
  const t = useTranslations('clinicLogoUi')
  const queryClient = useQueryClient()
  return useMutation((file: File) => tenantApi.uploadLogo(file), {
    onSuccess: (profile) => {
      queryClient.setQueryData(KEY, profile)
      queryClient.invalidateQueries('doctorProfile')
      toast.success(t('uploaded'))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('failed')))
    },
  })
}

export function useRemoveLogo() {
  const t = useTranslations('clinicLogoUi')
  const queryClient = useQueryClient()
  return useMutation<ClinicProfile, unknown, void>(() => tenantApi.removeLogo(), {
    onSuccess: (profile) => {
      queryClient.setQueryData(KEY, profile)
      toast.success(t('removed'))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('failed')))
    },
  })
}
