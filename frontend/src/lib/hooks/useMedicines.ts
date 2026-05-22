/**
 * Medicine React Query Hooks
 */

import { useMutation, useQuery, useQueryClient } from 'react-query';
import { medicinesApi } from '@/lib/api/medicines';
import type {
  MedicineCreate,
  MedicineUpdate,
  MedicineFilters,
  MedicineSearchParams,
  MedicineAliasCreate,
} from '@/types/medicine';

// List medicines
export function useMedicines(filters?: MedicineFilters) {
  return useQuery(
    ['medicines', filters],
    () => medicinesApi.list(filters),
    {
      staleTime: 60000, // 1 minute
    }
  );
}

// Get single medicine
export function useMedicine(id: number) {
  return useQuery(
    ['medicines', id],
    () => medicinesApi.get(id),
    {
      enabled: !!id,
      staleTime: 60000,
    }
  );
}

// Search medicines
export function useSearchMedicines(params: MedicineSearchParams) {
  return useQuery(
    ['medicines', 'search', params],
    () => medicinesApi.search(params),
    {
      enabled: params.q.length > 0,
      staleTime: 30000,
    }
  );
}

// Create medicine
export function useCreateMedicine() {
  const queryClient = useQueryClient();

  return useMutation(
    (payload: MedicineCreate) => medicinesApi.create(payload),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['medicines']);
      },
    }
  );
}

// Update medicine
export function useUpdateMedicine() {
  const queryClient = useQueryClient();

  return useMutation(
    ({ id, payload }: { id: number; payload: MedicineUpdate }) =>
      medicinesApi.update(id, payload),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['medicines']);
        queryClient.invalidateQueries(['medicines', data.id]);
      },
    }
  );
}

// Delete medicine
export function useDeleteMedicine() {
  const queryClient = useQueryClient();

  return useMutation(
    (id: number) => medicinesApi.delete(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['medicines']);
      },
    }
  );
}

// Get medicine aliases
export function useMedicineAliases(medicineId: number) {
  return useQuery(
    ['medicines', medicineId, 'aliases'],
    () => medicinesApi.listAliases(medicineId),
    {
      enabled: !!medicineId,
    }
  );
}

// Create medicine alias
export function useCreateMedicineAlias() {
  const queryClient = useQueryClient();

  return useMutation(
    ({ medicineId, payload }: { medicineId: number; payload: MedicineAliasCreate }) =>
      medicinesApi.createAlias(medicineId, payload),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['medicines', data.medicine_id, 'aliases']);
      },
    }
  );
}

// Delete medicine alias
export function useDeleteMedicineAlias() {
  const queryClient = useQueryClient();

  return useMutation(
    (aliasId: number) => medicinesApi.deleteAlias(aliasId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['medicines']);
      },
    }
  );
}
