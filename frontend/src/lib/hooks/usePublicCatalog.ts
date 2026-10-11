/**
 * React Query hooks over the public (unauthenticated) catalog API.
 * Used by the marketing/directory site — never by the dashboard.
 */

import { useQuery } from 'react-query';
import {
  publicApi,
  type PublicMedicineFilters,
  type PublicSymptomFilters,
  type PublicInstitutionFilters,
} from '@/lib/api/public';

export function usePublicMedicines(params?: PublicMedicineFilters) {
  return useQuery(['public', 'medicines', params], () => publicApi.medicines.list(params), {
    staleTime: 5 * 60 * 1000,
    keepPreviousData: true,
  });
}

export function usePublicMedicineSearch(q: string, system?: PublicMedicineFilters['system']) {
  return useQuery(
    ['public', 'medicines', 'search', q, system],
    () => publicApi.medicines.search(q, system, 100), // top 100 ranked; paged in the browser
    { enabled: q.trim().length > 0, staleTime: 60 * 1000 }
  );
}

export function usePublicSymptoms(params?: PublicSymptomFilters) {
  return useQuery(['public', 'symptoms', params], () => publicApi.symptoms.list(params), {
    staleTime: 5 * 60 * 1000,
    keepPreviousData: true,
  });
}

export function usePublicSymptomSearch(q: string, category?: string) {
  return useQuery(
    ['public', 'symptoms', 'search', q, category],
    () => publicApi.symptoms.search(q, category, 100), // top 100 ranked; paged in the browser
    { enabled: q.trim().length > 0, staleTime: 60 * 1000 }
  );
}

export function usePublicInstitutions(params?: PublicInstitutionFilters) {
  return useQuery(
    ['public', 'institutions', params],
    () => publicApi.institutions.list(params),
    { staleTime: 5 * 60 * 1000 }
  );
}
