import apiClient from './client'
import type {
  Prescription,
  PrescriptionListItem,
  PrescriptionCreateRequest,
  PrescriptionUpdateRequest,
  PrescriptionListParams,
  PrescriptionItemCreate,
  PrescriptionItem,
} from '@/types/prescription'

export const prescriptionsApi = {
  // List prescriptions with filters
  list: async (params?: PrescriptionListParams): Promise<PrescriptionListItem[]> => {
    const response = await apiClient.get('/prescriptions', { params })
    return response.data
  },

  // Get single prescription with items
  get: async (id: string): Promise<Prescription> => {
    const response = await apiClient.get(`/prescriptions/${id}`)
    return response.data
  },

  // Create prescription
  create: async (data: PrescriptionCreateRequest): Promise<Prescription> => {
    const response = await apiClient.post('/prescriptions', data)
    return response.data
  },

  // Update prescription (only drafts)
  update: async (id: string, data: PrescriptionUpdateRequest): Promise<Prescription> => {
    const response = await apiClient.patch(`/prescriptions/${id}`, data)
    return response.data
  },

  // Issue prescription (change status from draft to issued)
  issue: async (id: string): Promise<Prescription> => {
    const response = await apiClient.patch(`/prescriptions/${id}`, { status: 'issued' })
    return response.data
  },

  // Void prescription
  void: async (id: string): Promise<Prescription> => {
    const response = await apiClient.post(`/prescriptions/${id}/void`)
    return response.data
  },

  // Printable PDF (rendered on demand by the server)
  downloadPdf: async (id: string): Promise<Blob> => {
    const response = await apiClient.get(`/prescriptions/${id}/pdf`, { responseType: 'blob' })
    return response.data
  },

  // Add item to prescription
  addItem: async (prescriptionId: string, data: PrescriptionItemCreate): Promise<PrescriptionItem> => {
    const response = await apiClient.post(`/prescriptions/${prescriptionId}/items`, data)
    return response.data
  },

  // Delete item from prescription
  deleteItem: async (prescriptionId: string, itemId: number): Promise<void> => {
    await apiClient.delete(`/prescriptions/${prescriptionId}/items/${itemId}`)
  },
}
