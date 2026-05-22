/**
 * Integration API Client
 * Handles all integration-related API calls
 */

import { apiClient } from './client';
import type {
  IntegrationProvider,
  IntegrationProviderListItem,
  TenantIntegration,
  TenantIntegrationCreate,
  TenantIntegrationListItem,
  TenantIntegrationUpdate,
  IntegrationTestRequest,
  IntegrationTestResponse,
  IntegrationLogListItem,
  SendSMSRequest,
  SendEmailRequest,
  SendOperationResponse,
  IntegrationFilters,
  LogFilters,
} from '@/types/integration';

// ===== Provider Catalog Endpoints =====

export const integrationsApi = {
  // List available integration providers
  listProviders: async (params?: {
    provider_type?: string;
    is_active?: boolean;
  }): Promise<IntegrationProviderListItem[]> => {
    const { data } = await apiClient.get('/integrations/providers', { params });
    return data;
  },

  // Get provider details
  getProvider: async (providerId: number): Promise<IntegrationProvider> => {
    const { data } = await apiClient.get(`/integrations/providers/${providerId}`);
    return data;
  },

  // ===== Tenant Integration Endpoints =====

  // List tenant's configured integrations
  listIntegrations: async (
    params?: IntegrationFilters
  ): Promise<TenantIntegrationListItem[]> => {
    const { data } = await apiClient.get('/integrations', { params });
    return data;
  },

  // Get integration details
  getIntegration: async (integrationId: number): Promise<TenantIntegration> => {
    const { data } = await apiClient.get(`/integrations/${integrationId}`);
    return data;
  },

  // Create tenant integration
  createIntegration: async (
    payload: TenantIntegrationCreate
  ): Promise<TenantIntegration> => {
    const { data } = await apiClient.post('/integrations', payload);
    return data;
  },

  // Update tenant integration
  updateIntegration: async (
    integrationId: number,
    payload: TenantIntegrationUpdate
  ): Promise<TenantIntegration> => {
    const { data } = await apiClient.patch(`/integrations/${integrationId}`, payload);
    return data;
  },

  // Delete tenant integration
  deleteIntegration: async (integrationId: number): Promise<void> => {
    await apiClient.delete(`/integrations/${integrationId}`);
  },

  // Set integration as primary
  setPrimaryIntegration: async (integrationId: number): Promise<TenantIntegration> => {
    const { data } = await apiClient.post(
      `/integrations/${integrationId}/set-primary`
    );
    return data;
  },

  // ===== Integration Testing =====

  // Test integration connection
  testIntegration: async (
    integrationId: number,
    payload: IntegrationTestRequest
  ): Promise<IntegrationTestResponse> => {
    const { data } = await apiClient.post(
      `/integrations/${integrationId}/test`,
      payload
    );
    return data;
  },

  // ===== Integration Logs =====

  // List integration transaction logs
  listLogs: async (params?: LogFilters): Promise<IntegrationLogListItem[]> => {
    const { data } = await apiClient.get('/integrations/logs', { params });
    return data;
  },

  // ===== Send Operations =====

  // Send SMS via configured provider
  sendSMS: async (payload: SendSMSRequest): Promise<SendOperationResponse> => {
    const { data } = await apiClient.post('/integrations/send/sms', payload);
    return data;
  },

  // Send email via configured provider
  sendEmail: async (payload: SendEmailRequest): Promise<SendOperationResponse> => {
    const { data } = await apiClient.post('/integrations/send/email', payload);
    return data;
  },
};
