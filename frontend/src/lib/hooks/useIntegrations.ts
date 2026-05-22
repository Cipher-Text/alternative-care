/**
 * Integration React Query Hooks
 * Custom hooks for integration-related data fetching and mutations
 */

import { useMutation, useQuery, useQueryClient } from 'react-query';
import { integrationsApi } from '@/lib/api/integrations';
import type {
  IntegrationFilters,
  LogFilters,
  TenantIntegrationCreate,
  TenantIntegrationUpdate,
  IntegrationTestRequest,
  SendSMSRequest,
  SendEmailRequest,
} from '@/types/integration';

// ===== Provider Hooks =====

/**
 * List available integration providers
 */
export function useProviders(params?: { provider_type?: string; is_active?: boolean }) {
  return useQuery(
    ['integrations', 'providers', params],
    () => integrationsApi.listProviders(params),
    {
      staleTime: 60000, // 1 minute
    }
  );
}

/**
 * Get provider details
 */
export function useProvider(providerId: number) {
  return useQuery(
    ['integrations', 'provider', providerId],
    () => integrationsApi.getProvider(providerId),
    {
      enabled: !!providerId,
      staleTime: 60000,
    }
  );
}

// ===== Tenant Integration Hooks =====

/**
 * List tenant's configured integrations
 */
export function useIntegrations(filters?: IntegrationFilters) {
  return useQuery(
    ['integrations', 'list', filters],
    () => integrationsApi.listIntegrations(filters),
    {
      staleTime: 30000,
    }
  );
}

/**
 * Get integration details
 */
export function useIntegration(integrationId: number) {
  return useQuery(
    ['integrations', integrationId],
    () => integrationsApi.getIntegration(integrationId),
    {
      enabled: !!integrationId,
      staleTime: 30000,
    }
  );
}

/**
 * Create tenant integration
 */
export function useCreateIntegration() {
  const queryClient = useQueryClient();

  return useMutation(
    (payload: TenantIntegrationCreate) => integrationsApi.createIntegration(payload),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['integrations', 'list']);
        queryClient.invalidateQueries(['integrations', 'providers']);
      },
    }
  );
}

/**
 * Update tenant integration
 */
export function useUpdateIntegration() {
  const queryClient = useQueryClient();

  return useMutation(
    ({ integrationId, payload }: { integrationId: number; payload: TenantIntegrationUpdate }) =>
      integrationsApi.updateIntegration(integrationId, payload),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['integrations', 'list']);
        queryClient.invalidateQueries(['integrations', data.id]);
      },
    }
  );
}

/**
 * Delete tenant integration
 */
export function useDeleteIntegration() {
  const queryClient = useQueryClient();

  return useMutation(
    (integrationId: number) => integrationsApi.deleteIntegration(integrationId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['integrations', 'list']);
        queryClient.invalidateQueries(['integrations', 'providers']);
      },
    }
  );
}

/**
 * Set integration as primary
 */
export function useSetPrimaryIntegration() {
  const queryClient = useQueryClient();

  return useMutation(
    (integrationId: number) => integrationsApi.setPrimaryIntegration(integrationId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['integrations', 'list']);
      },
    }
  );
}

// ===== Integration Testing Hook =====

/**
 * Test integration connection
 */
export function useTestIntegration() {
  const queryClient = useQueryClient();

  return useMutation(
    ({ integrationId, payload }: { integrationId: number; payload: IntegrationTestRequest }) =>
      integrationsApi.testIntegration(integrationId, payload),
    {
      onSuccess: (data, variables) => {
        queryClient.invalidateQueries(['integrations', variables.integrationId]);
      },
    }
  );
}

// ===== Integration Logs Hook =====

/**
 * List integration transaction logs
 */
export function useIntegrationLogs(filters?: LogFilters) {
  return useQuery(['integrations', 'logs', filters], () => integrationsApi.listLogs(filters), {
    staleTime: 10000, // 10 seconds
  });
}

// ===== Send Operation Hooks =====

/**
 * Send SMS via configured provider
 */
export function useSendSMS() {
  const queryClient = useQueryClient();

  return useMutation((payload: SendSMSRequest) => integrationsApi.sendSMS(payload), {
    onSuccess: () => {
      queryClient.invalidateQueries(['integrations', 'logs']);
    },
  });
}

/**
 * Send email via configured provider
 */
export function useSendEmail() {
  const queryClient = useQueryClient();

  return useMutation((payload: SendEmailRequest) => integrationsApi.sendEmail(payload), {
    onSuccess: () => {
      queryClient.invalidateQueries(['integrations', 'logs']);
    },
  });
}
