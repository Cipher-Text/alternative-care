/**
 * Institution catalog React Query hooks
 */

import { createCrudHooks } from './useCrudFactory';
import { institutionsApi } from '@/lib/api/institutions';
import type {
  Institution,
  InstitutionListItem,
  InstitutionCreate,
  InstitutionUpdate,
  InstitutionFilters,
} from '@/types/institution';

const institutionCrudHooks = createCrudHooks<
  Institution,
  InstitutionCreate,
  InstitutionUpdate,
  InstitutionListItem
>('institutions', institutionsApi);

export const useInstitutions = institutionCrudHooks.useList<InstitutionFilters>;
export const useInstitution = institutionCrudHooks.useGet;
export const useCreateInstitution = institutionCrudHooks.useCreate;
export const useUpdateInstitution = institutionCrudHooks.useUpdate;
export const useDeleteInstitution = institutionCrudHooks.useDelete;
