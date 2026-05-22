/**
 * Symptom React Query Hooks
 */

import { useMutation, useQuery, useQueryClient } from 'react-query';
import { symptomsApi } from '@/lib/api/symptoms';
import type {
  SymptomCreate,
  SymptomUpdate,
  SymptomFilters,
  SymptomSearchParams,
  SymptomAliasCreate,
} from '@/types/symptom';

// List symptoms
export function useSymptoms(filters?: SymptomFilters) {
  return useQuery(
    ['symptoms', filters],
    () => symptomsApi.list(filters),
    {
      staleTime: 60000, // 1 minute
    }
  );
}

// Get single symptom
export function useSymptom(id: number) {
  return useQuery(
    ['symptoms', id],
    () => symptomsApi.get(id),
    {
      enabled: !!id,
      staleTime: 60000,
    }
  );
}

// Search symptoms
export function useSearchSymptoms(params: SymptomSearchParams) {
  return useQuery(
    ['symptoms', 'search', params],
    () => symptomsApi.search(params),
    {
      enabled: params.q.length > 0,
      staleTime: 30000,
    }
  );
}

// Create symptom
export function useCreateSymptom() {
  const queryClient = useQueryClient();

  return useMutation(
    (payload: SymptomCreate) => symptomsApi.create(payload),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['symptoms']);
      },
    }
  );
}

// Update symptom
export function useUpdateSymptom() {
  const queryClient = useQueryClient();

  return useMutation(
    ({ id, payload }: { id: number; payload: SymptomUpdate }) =>
      symptomsApi.update(id, payload),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['symptoms']);
        queryClient.invalidateQueries(['symptoms', data.id]);
      },
    }
  );
}

// Delete symptom
export function useDeleteSymptom() {
  const queryClient = useQueryClient();

  return useMutation(
    (id: number) => symptomsApi.delete(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['symptoms']);
      },
    }
  );
}

// Get symptom aliases
export function useSymptomAliases(symptomId: number) {
  return useQuery(
    ['symptoms', symptomId, 'aliases'],
    () => symptomsApi.listAliases(symptomId),
    {
      enabled: !!symptomId,
    }
  );
}

// Create symptom alias
export function useCreateSymptomAlias() {
  const queryClient = useQueryClient();

  return useMutation(
    ({ symptomId, payload }: { symptomId: number; payload: SymptomAliasCreate }) =>
      symptomsApi.createAlias(symptomId, payload),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['symptoms', data.symptom_id, 'aliases']);
      },
    }
  );
}

// Delete symptom alias
export function useDeleteSymptomAlias() {
  const queryClient = useQueryClient();

  return useMutation(
    (aliasId: number) => symptomsApi.deleteAlias(aliasId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['symptoms']);
      },
    }
  );
}
