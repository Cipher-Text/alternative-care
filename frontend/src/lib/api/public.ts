/**
 * Public (unauthenticated) catalog API client — hits /api/v1/public/*,
 * the D4 router that never takes a CurrentUser dependency. Used by the
 * public marketing/directory site, never by the authenticated dashboard.
 */

import { apiClient } from './client';
import type {
  Medicine,
  MedicineListItem,
  MedicineSearchResult,
  MedicalSystem,
} from '@/types/medicine';
import type { Symptom, SymptomListItem, SymptomSearchResult } from '@/types/symptom';
import type { InstitutionListItem, Discipline, InstitutionType } from '@/types/institution';

export interface PublicMedicineFilters {
  system?: MedicalSystem;
  category?: string;
  limit?: number;
  offset?: number;
}

export interface PublicSymptomFilters {
  category?: string;
  limit?: number;
  offset?: number;
}

export interface PublicInstitutionFilters {
  discipline?: Discipline;
  institution_type?: InstitutionType;
  district_id?: number;
  limit?: number;
  offset?: number;
}

export const publicApi = {
  medicines: {
    list: async (params?: PublicMedicineFilters): Promise<MedicineListItem[]> => {
      const { data } = await apiClient.get('/public/medicines', { params });
      return data;
    },
    search: async (q: string, system?: MedicalSystem, limit = 20): Promise<MedicineSearchResult[]> => {
      const { data } = await apiClient.get('/public/medicines/search', {
        params: { q, system, limit },
      });
      return data;
    },
    get: async (id: number): Promise<Medicine> => {
      const { data } = await apiClient.get(`/public/medicines/${id}`);
      return data;
    },
  },

  symptoms: {
    list: async (params?: PublicSymptomFilters): Promise<SymptomListItem[]> => {
      const { data } = await apiClient.get('/public/symptoms', { params });
      return data;
    },
    search: async (q: string, category?: string, limit = 20): Promise<SymptomSearchResult[]> => {
      const { data } = await apiClient.get('/public/symptoms/search', {
        params: { q, category, limit },
      });
      return data;
    },
    get: async (id: number): Promise<Symptom> => {
      const { data } = await apiClient.get(`/public/symptoms/${id}`);
      return data;
    },
  },

  institutions: {
    list: async (params?: PublicInstitutionFilters): Promise<InstitutionListItem[]> => {
      const { data } = await apiClient.get('/public/institutions', { params });
      return data;
    },
    get: async (id: number): Promise<InstitutionListItem> => {
      const { data } = await apiClient.get(`/public/institutions/${id}`);
      return data;
    },
  },
};
