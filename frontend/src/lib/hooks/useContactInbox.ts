import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { adminContactApi } from '@/lib/api/contact'
import { errorMessage } from '@/lib/apiErrors'

const KEY = ['admin', 'contact'] as const

export function useContactMessages(params: { status: 'new' | 'handled'; limit: number; offset: number }) {
  return useQuery([...KEY, params], () => adminContactApi.list(params), { keepPreviousData: true })
}

export function useSetContactStatus() {
  const t = useTranslations('publicContactUi.admin')
  const queryClient = useQueryClient()
  return useMutation(({ id, status }: { id: string; status: 'new' | 'handled' }) => adminContactApi.setStatus(id, status), {
    onSuccess: () => queryClient.invalidateQueries(KEY),
    onError: (error) => {
      toast.error(errorMessage(error, t('updateFailed')))
    },
  })
}
