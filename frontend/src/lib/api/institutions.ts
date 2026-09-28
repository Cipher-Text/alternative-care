/**
 * Institution catalog API client
 */

import { apiClient } from './client';
import type {
  Institution,
  InstitutionListItem,
  InstitutionCreate,
  InstitutionUpdate,
  InstitutionFilters,
} from '@/types/institution';

export const institutionsApi = {
  list: async (params?: InstitutionFilters): Promise<InstitutionListItem[]> => {
    const { data } = await apiClient.get('/institutions', { params });
    return data;
  },

  get: async (id: string | number): Promise<Institution> => {
    const { data } = await apiClient.get(`/institutions/${id}`);
    return data;
  },

  create: async (payload: InstitutionCreate): Promise<Institution> => {
    const { data } = await apiClient.post('/institutions', payload);
    return data;
  },

  update: async (id: string | number, payload: InstitutionUpdate): Promise<Institution> => {
    const { data } = await apiClient.patch(`/institutions/${id}`, payload);
    return data;
  },

  delete: async (id: string | number): Promise<void> => {
    await apiClient.delete(`/institutions/${id}`);
  },
};
