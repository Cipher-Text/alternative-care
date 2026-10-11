/**
 * React Query hooks over the public (unauthenticated) API.
 * Used by the marketing site — never by the dashboard.
 */

import { useQuery } from 'react-query';
import { publicApi, type PublicInstitutionFilters } from '@/lib/api/public';

export function usePublicStats() {
  return useQuery(['public', 'stats'], () => publicApi.stats(), { staleTime: 5 * 60 * 1000 });
}

export function usePublicInstitutions(params?: PublicInstitutionFilters) {
  return useQuery(
    ['public', 'institutions', params],
    () => publicApi.institutions.list(params),
    { staleTime: 5 * 60 * 1000 }
  );
}
