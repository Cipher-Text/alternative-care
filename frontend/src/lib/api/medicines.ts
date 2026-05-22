/**
 * Medicine API Client
 */

import { apiClient } from './client';
import type {
  Medicine,
  MedicineListItem,
  MedicineCreate,
  MedicineUpdate,
  MedicineSearchResult,
  MedicineFilters,
  MedicineSearchParams,
  MedicineAlias,
  MedicineAliasCreate,
} from '@/types/medicine';

export const medicinesApi = {
  // List medicines
  list: async (params?: MedicineFilters): Promise<MedicineListItem[]> => {
    const { data } = await apiClient.get('/medicines', { params });
    return data;
  },

  // Get medicine by ID
  get: async (id: number): Promise<Medicine> => {
    const { data } = await apiClient.get(`/medicines/${id}`);
    return data;
  },

  // Create medicine
  create: async (payload: MedicineCreate): Promise<Medicine> => {
    const { data } = await apiClient.post('/medicines', payload);
    return data;
  },

  // Update medicine
  update: async (id: number, payload: MedicineUpdate): Promise<Medicine> => {
    const { data } = await apiClient.patch(`/medicines/${id}`, payload);
    return data;
  },

  // Delete medicine
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/medicines/${id}`);
  },

  // Search medicines (autocomplete)
  search: async (params: MedicineSearchParams): Promise<MedicineSearchResult[]> => {
    const { data } = await apiClient.get('/medicines/search', { params });
    return data;
  },

  // Medicine aliases
  createAlias: async (medicineId: number, payload: MedicineAliasCreate): Promise<MedicineAlias> => {
    const { data } = await apiClient.post(`/medicines/${medicineId}/aliases`, payload);
    return data;
  },

  listAliases: async (medicineId: number): Promise<MedicineAlias[]> => {
    const { data } = await apiClient.get(`/medicines/${medicineId}/aliases`);
    return data;
  },

  deleteAlias: async (aliasId: number): Promise<void> => {
    await apiClient.delete(`/medicines/aliases/${aliasId}`);
  },
};
