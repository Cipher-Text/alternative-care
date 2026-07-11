/**
 * Generic CRUD hooks factory
 *
 * Creates standardized React Query hooks for any resource API.
 * Eliminates duplication across patient, medicine, symptom, prescription, etc.
 *
 * Usage:
 *   const patientHooks = createCrudHooks('patients', patientsApi);
 *   const { data } = patientHooks.useList();
 *   const { mutate } = patientHooks.useCreate();
 */

import { useMutation, useQuery, useQueryClient, UseQueryOptions } from 'react-query';
import type { AxiosError } from 'axios';

/**
 * Base CRUD API interface
 * Your API clients should implement these methods
 */
export interface CrudApi<T, CreateData = Partial<T>, UpdateData = Partial<T>, TList = T> {
  list?: (params?: any) => Promise<TList[]>;
  get?: (id: string | number) => Promise<T>;
  create?: (data: CreateData) => Promise<T>;
  update?: (id: string | number, data: UpdateData) => Promise<T>;
  delete?: (id: string | number) => Promise<void>;
}

/**
 * Configuration for CRUD hooks
 */
export interface CrudHooksConfig {
  /**
   * Custom key generator for React Query cache keys
   * Default: (resource, id?) => id ? [resource, id] : [resource]
   */
  keyGenerator?: (resource: string, id?: string | number, params?: any) => any[];

  /**
   * Whether to invalidate list queries on mutations
   * Default: true
   */
  invalidateListOnMutation?: boolean;

  /**
   * Whether to invalidate detail queries on update/delete
   * Default: true
   */
  invalidateDetailOnMutation?: boolean;
}

/**
 * Create standardized CRUD hooks for a resource
 *
 * @param resource - Resource name (e.g., 'patients', 'medicines')
 * @param api - API client implementing CrudApi interface
 * @param config - Optional configuration
 */
export function createCrudHooks<T, CreateData = Partial<T>, UpdateData = Partial<T>, TList = T>(
  resource: string,
  api: CrudApi<T, CreateData, UpdateData, TList>,
  config: CrudHooksConfig = {}
) {
  const {
    keyGenerator = (res: string, id?: string | number, params?: any) => {
      if (id !== undefined) return [res, id];
      if (params) return [res, params];
      return [res];
    },
    invalidateListOnMutation = true,
    invalidateDetailOnMutation = true,
  } = config;

  /**
   * Hook for listing resources
   *
   * @param params - Query parameters (search, filters, pagination)
   * @param options - React Query options
   */
  function useList<P = any>(params?: P, options?: Omit<UseQueryOptions<TList[], AxiosError>, 'queryKey' | 'queryFn'>) {
    return useQuery<TList[], AxiosError>({
      queryKey: keyGenerator(resource, undefined, params),
      queryFn: () => {
        if (!api.list) {
          throw new Error(`${resource} API does not implement list()`);
        }
        return api.list(params);
      },
      ...options,
    });
  }

  /**
   * Hook for getting a single resource
   *
   * @param id - Resource ID
   * @param options - React Query options
   */
  function useGet(
    id: string | number,
    options?: Omit<UseQueryOptions<T, AxiosError>, 'queryKey' | 'queryFn'>
  ) {
    return useQuery<T, AxiosError>({
      queryKey: keyGenerator(resource, id),
      queryFn: () => {
        if (!api.get) {
          throw new Error(`${resource} API does not implement get()`);
        }
        return api.get(id);
      },
      enabled: !!id && (options?.enabled ?? true),
      ...options,
    });
  }

  /**
   * Hook for creating a resource
   *
   * @param options - Mutation options
   */
  function useCreate(options?: {
    onSuccess?: (data: T) => void;
    onError?: (error: AxiosError) => void;
  }) {
    const queryClient = useQueryClient();

    return useMutation<T, AxiosError, CreateData>(
      (data: CreateData) => {
        if (!api.create) {
          throw new Error(`${resource} API does not implement create()`);
        }
        return api.create(data);
      },
      {
        onSuccess: (data: T) => {
          if (invalidateListOnMutation) {
            queryClient.invalidateQueries([resource]);
          }
          options?.onSuccess?.(data);
        },
        onError: options?.onError,
      }
    );
  }

  /**
   * Hook for updating a resource
   *
   * @param options - Mutation options
   */
  function useUpdate(options?: {
    onSuccess?: (data: T) => void;
    onError?: (error: AxiosError) => void;
  }) {
    const queryClient = useQueryClient();

    return useMutation<T, AxiosError, { id: string | number; data: UpdateData }>(
      ({ id, data }: { id: string | number; data: UpdateData }) => {
        if (!api.update) {
          throw new Error(`${resource} API does not implement update()`);
        }
        return api.update(id, data);
      },
      {
        onSuccess: (data: T, variables: { id: string | number; data: UpdateData }) => {
          if (invalidateListOnMutation) {
            queryClient.invalidateQueries([resource]);
          }
          if (invalidateDetailOnMutation) {
            queryClient.invalidateQueries(keyGenerator(resource, variables.id));
          }
          options?.onSuccess?.(data);
        },
        onError: options?.onError,
      }
    );
  }

  /**
   * Hook for deleting a resource
   *
   * @param options - Mutation options
   */
  function useDelete(options?: {
    onSuccess?: () => void;
    onError?: (error: AxiosError) => void;
  }) {
    const queryClient = useQueryClient();

    return useMutation<void, AxiosError, string | number>(
      (id: string | number) => {
        if (!api.delete) {
          throw new Error(`${resource} API does not implement delete()`);
        }
        return api.delete(id);
      },
      {
        onSuccess: (_: void, id: string | number) => {
          if (invalidateListOnMutation) {
            queryClient.invalidateQueries([resource]);
          }
          if (invalidateDetailOnMutation) {
            queryClient.invalidateQueries(keyGenerator(resource, id));
          }
          options?.onSuccess?.();
        },
        onError: options?.onError,
      }
    );
  }

  return {
    useList,
    useGet,
    useCreate,
    useUpdate,
    useDelete,
  };
}

/**
 * Example usage:
 *
 * // 1. Define your API client
 * const patientsApi: CrudApi<Patient, PatientCreateRequest, PatientUpdateRequest> = {
 *   list: (params) => apiClient.get('/patients', { params }).then(r => r.data),
 *   get: (id) => apiClient.get(`/patients/${id}`).then(r => r.data),
 *   create: (data) => apiClient.post('/patients', data).then(r => r.data),
 *   update: (id, data) => apiClient.patch(`/patients/${id}`, data).then(r => r.data),
 *   delete: (id) => apiClient.delete(`/patients/${id}`),
 * };
 *
 * // 2. Create hooks
 * const patientHooks = createCrudHooks('patients', patientsApi);
 *
 * // 3. Use in components
 * const { data: patients, isLoading } = patientHooks.useList({ search: 'John' });
 * const { data: patient } = patientHooks.useGet(patientId);
 * const { mutate: createPatient } = patientHooks.useCreate({
 *   onSuccess: () => toast.success('Patient created')
 * });
 * const { mutate: updatePatient } = patientHooks.useUpdate();
 * const { mutate: deletePatient } = patientHooks.useDelete();
 */
