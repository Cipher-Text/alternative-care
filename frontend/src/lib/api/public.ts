/**
 * Public (unauthenticated) catalog API client — hits /api/v1/public/*,
 * the D4 router that never takes a CurrentUser dependency. Used by the
 * public marketing/directory site, never by the authenticated dashboard.
 */

import { apiClient } from './client';
import type { InstitutionListItem, Discipline, InstitutionType } from '@/types/institution';

export interface PublicInstitutionFilters {
  discipline?: Discipline;
  institution_type?: InstitutionType;
  district_id?: number;
  limit?: number;
  offset?: number;
}

export interface PublicStats {
  medicines: number;
  symptoms: number;
  institutions: number;
  clinics: number;
  practitioners: number;
}

export const publicApi = {
  /** Headline counts only — the medicine/symptom catalogs themselves are not public. */
  stats: async (): Promise<PublicStats> => {
    const { data } = await apiClient.get('/public/stats');
    return data;
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
