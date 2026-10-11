import { useQuery, useMutation, useQueryClient } from 'react-query'
import { openPdf } from '@/lib/utils/pdf'
import { prescriptionsApi } from '@/lib/api/prescriptions'
import type {
  Prescription,
  PrescriptionCreateRequest,
  PrescriptionUpdateRequest,
  PrescriptionListParams,
  PrescriptionItemCreate,
} from '@/types/prescription'
import { toast } from 'react-hot-toast'

// List prescriptions
export function usePrescriptions(params?: PrescriptionListParams) {
  return useQuery(['prescriptions', params], () => prescriptionsApi.list(params), {
    staleTime: 30000, // 30 seconds
    keepPreviousData: true,
  })
}

// Get single prescription
export function usePrescription(id: string) {
  return useQuery(['prescription', id], () => prescriptionsApi.get(id), {
    enabled: !!id,
    staleTime: 30000,
  })
}

// Create prescription
export function useCreatePrescription() {
  const queryClient = useQueryClient()

  return useMutation(
    (data: PrescriptionCreateRequest) => prescriptionsApi.create(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('prescriptions')
        toast.success('Prescription created successfully')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to create prescription')
      },
    }
  )
}

// Update prescription
export function useUpdatePrescription() {
  const queryClient = useQueryClient()

  return useMutation(
    ({ id, data }: { id: string; data: PrescriptionUpdateRequest }) =>
      prescriptionsApi.update(id, data),
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries('prescriptions')
        queryClient.invalidateQueries(['prescription', variables.id])
        toast.success('Prescription updated successfully')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to update prescription')
      },
    }
  )
}

// Issue prescription (draft → issued)
export function useIssuePrescription() {
  const queryClient = useQueryClient()

  return useMutation(
    (id: string) => prescriptionsApi.issue(id),
    {
      onSuccess: (_, id) => {
        queryClient.invalidateQueries('prescriptions')
        queryClient.invalidateQueries(['prescription', id])
        toast.success('Prescription issued successfully')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to issue prescription')
      },
    }
  )
}

// Void prescription
export function useVoidPrescription() {
  const queryClient = useQueryClient()

  return useMutation(
    (id: string) => prescriptionsApi.void(id),
    {
      onSuccess: (_, id) => {
        queryClient.invalidateQueries('prescriptions')
        queryClient.invalidateQueries(['prescription', id])
        toast.success('Prescription voided successfully')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to void prescription')
      },
    }
  )
}

// View / print the prescription as a PDF (opens in a new tab)
export function useViewPrescriptionPdf() {
  return useMutation((id: string) =>
    openPdf(() => prescriptionsApi.downloadPdf(id), `prescription-${id.slice(0, 8)}.pdf`)
  )
}

// Add prescription item
export function useAddPrescriptionItem() {
  const queryClient = useQueryClient()

  return useMutation(
    ({ prescriptionId, data }: { prescriptionId: string; data: PrescriptionItemCreate }) =>
      prescriptionsApi.addItem(prescriptionId, data),
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries(['prescription', variables.prescriptionId])
        toast.success('Item added to prescription')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to add item')
      },
    }
  )
}

// Delete prescription item
export function useDeletePrescriptionItem() {
  const queryClient = useQueryClient()

  return useMutation(
    ({ prescriptionId, itemId }: { prescriptionId: string; itemId: number }) =>
      prescriptionsApi.deleteItem(prescriptionId, itemId),
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries(['prescription', variables.prescriptionId])
        toast.success('Item removed from prescription')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to remove item')
      },
    }
  )
}
