/**
 * Integration Provider and Tenant Integration Types
 * Matches backend schemas from app/shared/schemas/integration.py
 */

// ===== Integration Provider Types =====

export type ProviderType = 'sms' | 'email' | 'payment';

export interface ConfigSchemaField {
  type: 'string' | 'integer' | 'boolean';
  required: boolean;
  label: string;
  description: string;
  sensitive?: boolean;
  default?: string | number | boolean;
  max_length?: number;
}

export interface ConfigSchema {
  [key: string]: ConfigSchemaField;
}

export interface IntegrationProvider {
  id: number;
  name: string;
  display_name: string;
  provider_type: ProviderType;
  description: string | null;
  logo_url: string | null;
  config_schema: ConfigSchema | null;
  supported_countries: string[] | null;
  is_active: boolean;
  created_at: string;
}

export interface IntegrationProviderListItem {
  id: number;
  name: string;
  display_name: string;
  provider_type: ProviderType;
  logo_url: string | null;
  is_active: boolean;
}

// ===== Tenant Integration Types =====

export interface TenantIntegrationBase {
  provider_id: number;
  display_name: string | null;
  is_active: boolean;
}

export interface TenantIntegrationCreate extends TenantIntegrationBase {
  credentials: Record<string, any>;
}

export interface TenantIntegrationUpdate {
  display_name?: string | null;
  credentials?: Record<string, any>;
  is_active?: boolean;
}

export interface TenantIntegration extends TenantIntegrationBase {
  id: number;
  tenant_id: string;
  is_primary: boolean;
  last_tested_at: string | null;
  test_status: 'success' | 'failed' | null;
  created_at: string;
  updated_at: string | null;
  provider?: IntegrationProviderListItem | null;
}

export interface TenantIntegrationListItem {
  id: number;
  provider_id: number;
  display_name: string | null;
  is_primary: boolean;
  is_active: boolean;
  test_status: 'success' | 'failed' | null;
  created_at: string;
}

// ===== Integration Test Types =====

export interface IntegrationTestRequest {
  test_phone?: string | null;
  test_email?: string | null;
  test_amount?: number | null;
}

export interface IntegrationTestResponse {
  success: boolean;
  message: string;
  test_type: string;
  provider_name: string;
  details?: Record<string, any> | null;
  error?: string | null;
}

// ===== Integration Log Types =====

export interface IntegrationLog {
  id: number;
  tenant_id: string;
  tenant_integration_id: number;
  transaction_type: string;
  status: string;
  recipient: string | null;
  amount: number | null;
  currency: string | null;
  external_reference: string | null;
  error_message: string | null;
  response_status_code: number | null;
  created_at: string;
}

export interface IntegrationLogListItem {
  id: number;
  transaction_type: string;
  status: string;
  recipient: string | null;
  external_reference: string | null;
  created_at: string;
}

// ===== Send Operation Types =====

export interface SendSMSRequest {
  recipient: string;
  message: string;
  provider_id?: number | null;
}

export interface SendEmailRequest {
  recipient: string;
  subject: string;
  body_html?: string | null;
  body_text?: string | null;
  provider_id?: number | null;
}

export interface SendOperationResponse {
  success: boolean;
  message: string;
  transaction_id?: string | null;
  integration_log_id?: number | null;
  queued?: boolean;
}

// ===== UI Helper Types =====

export interface ProviderWithConfig extends IntegrationProvider {
  configured?: boolean;
  configuredIntegrationId?: number;
}

export interface IntegrationFilters {
  provider_type?: ProviderType | null;
  is_active?: boolean | null;
  is_primary?: boolean | null;
}

export interface LogFilters {
  integration_id?: number | null;
  transaction_type?: string | null;
  status?: string | null;
  limit?: number;
  offset?: number;
}
