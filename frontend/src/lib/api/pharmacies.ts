/**
 * Pharmacy directory API client
 */

import { apiClient } from './client'
import type {
  Pharmacy,
  PharmacyFilters,
  PharmacyImportResult,
  PharmacyInput,
  PharmacyListItem,
  PharmacyUpdate,
} from '@/types/pharmacy'

export const pharmaciesApi = {
  list: async (params?: PharmacyFilters): Promise<PharmacyListItem[]> => {
    const { data } = await apiClient.get('/pharmacies', { params })
    return data
  },

  get: async (id: number): Promise<Pharmacy> => {
    const { data } = await apiClient.get(`/pharmacies/${id}`)
    return data
  },

  create: async (payload: PharmacyInput): Promise<Pharmacy> => {
    const { data } = await apiClient.post('/pharmacies', payload)
    return data
  },

  update: async (id: number, payload: PharmacyUpdate): Promise<Pharmacy> => {
    const { data } = await apiClient.patch(`/pharmacies/${id}`, payload)
    return data
  },

  deactivate: async (id: number): Promise<void> => {
    await apiClient.delete(`/pharmacies/${id}`)
  },

  importCsv: async (file: File): Promise<PharmacyImportResult> => {
    const form = new FormData()
    form.append('file', file)
    // Let the browser set the multipart boundary (the client defaults to JSON)
    const { data } = await apiClient.post('/pharmacies/import', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },
}
