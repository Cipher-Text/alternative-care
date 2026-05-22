/**
 * Symptom API Client
 */

import { apiClient } from './client';
import type {
  Symptom,
  SymptomListItem,
  SymptomCreate,
  SymptomUpdate,
  SymptomSearchResult,
  SymptomFilters,
  SymptomSearchParams,
  SymptomAlias,
  SymptomAliasCreate,
} from '@/types/symptom';

export const symptomsApi = {
  // List symptoms
  list: async (params?: SymptomFilters): Promise<SymptomListItem[]> => {
    const { data } = await apiClient.get('/symptoms', { params });
    return data;
  },

  // Get symptom by ID
  get: async (id: number): Promise<Symptom> => {
    const { data } = await apiClient.get(`/symptoms/${id}`);
    return data;
  },

  // Create symptom
  create: async (payload: SymptomCreate): Promise<Symptom> => {
    const { data } = await apiClient.post('/symptoms', payload);
    return data;
  },

  // Update symptom
  update: async (id: number, payload: SymptomUpdate): Promise<Symptom> => {
    const { data} = await apiClient.patch(`/symptoms/${id}`, payload);
    return data;
  },

  // Delete symptom
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/symptoms/${id}`);
  },

  // Search symptoms (autocomplete)
  search: async (params: SymptomSearchParams): Promise<SymptomSearchResult[]> => {
    const { data } = await apiClient.get('/symptoms/search', { params });
    return data;
  },

  // Symptom aliases
  createAlias: async (symptomId: number, payload: SymptomAliasCreate): Promise<SymptomAlias> => {
    const { data } = await apiClient.post(`/symptoms/${symptomId}/aliases`, payload);
    return data;
  },

  listAliases: async (symptomId: number): Promise<SymptomAlias[]> => {
    const { data } = await apiClient.get(`/symptoms/${symptomId}/aliases`);
    return data;
  },

  deleteAlias: async (aliasId: number): Promise<void> => {
    await apiClient.delete(`/symptoms/aliases/${aliasId}`);
  },
};
