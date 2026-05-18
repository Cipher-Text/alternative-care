/**
 * Payment and Invoice API Client
 * Base URL: /api/v1/payments
 */

import { apiClient } from './client';
import type {
  Payment,
  PaymentCreate,
  PaymentListItem,
  PaymentSummary,
  PaymentFilters,
  Invoice,
  InvoiceCreate,
  InvoiceUpdate,
  InvoiceListItem,
  InvoiceFilters,
  BkashPaymentCreate,
  BkashPaymentExecute,
  BkashPaymentResponse,
} from '@/types/payment';

const BASE_PATH = '/api/v1/payments';

// ===== Payment APIs =====

export const paymentsApi = {
  /**
   * Create a manual cash payment
   * POST /api/v1/payments
   */
  create: async (data: PaymentCreate): Promise<Payment> => {
    const response = await apiClient.post<Payment>(BASE_PATH, data);
    return response.data;
  },

  /**
   * List payments with filters and pagination
   * GET /api/v1/payments
   */
  list: async (filters?: PaymentFilters): Promise<PaymentListItem[]> => {
    const response = await apiClient.get<PaymentListItem[]>(BASE_PATH, {
      params: filters,
    });
    return response.data;
  },

  /**
   * Get payment summary statistics
   * GET /api/v1/payments/summary
   */
  getSummary: async (date_from?: string, date_to?: string): Promise<PaymentSummary> => {
    const response = await apiClient.get<PaymentSummary>(`${BASE_PATH}/summary`, {
      params: { date_from, date_to },
    });
    return response.data;
  },

  /**
   * Get payment by ID
   * GET /api/v1/payments/{id}
   */
  get: async (id: string): Promise<Payment> => {
    const response = await apiClient.get<Payment>(`${BASE_PATH}/${id}`);
    return response.data;
  },
};

// ===== bKash Payment APIs =====

export const bkashApi = {
  /**
   * Create bKash payment and get payment URL
   * POST /api/v1/payments/bkash/create
   */
  create: async (data: BkashPaymentCreate): Promise<BkashPaymentResponse> => {
    const response = await apiClient.post<BkashPaymentResponse>(
      `${BASE_PATH}/bkash/create`,
      data
    );
    return response.data;
  },

  /**
   * Execute bKash payment after user completes payment
   * POST /api/v1/payments/bkash/execute
   */
  execute: async (data: BkashPaymentExecute): Promise<Payment> => {
    const response = await apiClient.post<Payment>(`${BASE_PATH}/bkash/execute`, data);
    return response.data;
  },

  /**
   * Query bKash payment status
   * POST /api/v1/payments/bkash/query
   */
  query: async (paymentId: string): Promise<BkashPaymentResponse> => {
    const response = await apiClient.post<BkashPaymentResponse>(
      `${BASE_PATH}/bkash/query`,
      { payment_id: paymentId }
    );
    return response.data;
  },
};

// ===== Invoice APIs =====

export const invoicesApi = {
  /**
   * Create invoice
   * POST /api/v1/payments/invoices
   */
  create: async (data: InvoiceCreate): Promise<Invoice> => {
    const response = await apiClient.post<Invoice>(`${BASE_PATH}/invoices`, data);
    return response.data;
  },

  /**
   * List invoices with filters
   * GET /api/v1/payments/invoices
   */
  list: async (filters?: InvoiceFilters): Promise<InvoiceListItem[]> => {
    const response = await apiClient.get<InvoiceListItem[]>(`${BASE_PATH}/invoices`, {
      params: filters,
    });
    return response.data;
  },

  /**
   * Get invoice by ID
   * GET /api/v1/payments/invoices/{id}
   */
  get: async (id: string): Promise<Invoice> => {
    const response = await apiClient.get<Invoice>(`${BASE_PATH}/invoices/${id}`);
    return response.data;
  },

  /**
   * Update invoice (status, due date)
   * PATCH /api/v1/payments/invoices/{id}
   */
  update: async (id: string, data: InvoiceUpdate): Promise<Invoice> => {
    const response = await apiClient.patch<Invoice>(`${BASE_PATH}/invoices/${id}`, data);
    return response.data;
  },

  /**
   * Generate invoice PDF
   * POST /api/v1/payments/invoices/{id}/generate-pdf
   */
  generatePdf: async (id: string): Promise<{ pdf_url: string }> => {
    const response = await apiClient.post<{ pdf_url: string }>(
      `${BASE_PATH}/invoices/${id}/generate-pdf`
    );
    return response.data;
  },
};
