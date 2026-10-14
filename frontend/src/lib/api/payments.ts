/**
 * Payment and Invoice API Client
 * Base path: /payments
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
} from '@/types/payment';

const BASE_PATH = '/payments';

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
   * Printable invoice PDF (rendered on demand by the server)
   * GET /api/v1/payments/invoices/{id}/pdf
   */
  downloadPdf: async (id: string): Promise<Blob> => {
    const response = await apiClient.get(`${BASE_PATH}/invoices/${id}/pdf`, { responseType: 'blob' });
    return response.data;
  },
};
