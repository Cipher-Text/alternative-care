/**
 * React Query hooks for Payments and Invoices
 */

import { useQuery, useMutation, useQueryClient } from 'react-query';
import { paymentsApi, invoicesApi, bkashApi } from '@/lib/api/payments';
import type {
  PaymentCreate,
  PaymentFilters,
  InvoiceCreate,
  InvoiceUpdate,
  InvoiceFilters,
  BkashPaymentCreate,
  BkashPaymentExecute,
} from '@/types/payment';

// ===== Query Keys =====

export const paymentKeys = {
  all: ['payments'] as const,
  lists: () => [...paymentKeys.all, 'list'] as const,
  list: (filters?: PaymentFilters) => [...paymentKeys.lists(), filters] as const,
  details: () => [...paymentKeys.all, 'detail'] as const,
  detail: (id: string) => [...paymentKeys.details(), id] as const,
  summary: (date_from?: string, date_to?: string) =>
    [...paymentKeys.all, 'summary', date_from, date_to] as const,
};

export const invoiceKeys = {
  all: ['invoices'] as const,
  lists: () => [...invoiceKeys.all, 'list'] as const,
  list: (filters?: InvoiceFilters) => [...invoiceKeys.lists(), filters] as const,
  details: () => [...invoiceKeys.all, 'detail'] as const,
  detail: (id: string) => [...invoiceKeys.details(), id] as const,
};

// ===== Payment Hooks =====

/**
 * Get payment summary statistics
 */
export function usePaymentSummary(date_from?: string, date_to?: string) {
  return useQuery({
    queryKey: paymentKeys.summary(date_from, date_to),
    queryFn: () => paymentsApi.getSummary(date_from, date_to),
  });
}

/**
 * List payments with filters
 */
export function usePayments(filters?: PaymentFilters) {
  return useQuery({
    queryKey: paymentKeys.list(filters),
    queryFn: () => paymentsApi.list(filters),
  });
}

/**
 * Get payment by ID
 */
export function usePayment(id: string) {
  return useQuery({
    queryKey: paymentKeys.detail(id),
    queryFn: () => paymentsApi.get(id),
    enabled: !!id,
  });
}

/**
 * Create cash payment
 */
export function useCreatePayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PaymentCreate) => paymentsApi.create(data),
    onSuccess: () => {
      // Invalidate all payment queries
      queryClient.invalidateQueries({ queryKey: paymentKeys.all });
    },
  });
}

// ===== Invoice Hooks =====

/**
 * List invoices with filters
 */
export function useInvoices(filters?: InvoiceFilters) {
  return useQuery({
    queryKey: invoiceKeys.list(filters),
    queryFn: () => invoicesApi.list(filters),
  });
}

/**
 * Get invoice by ID
 */
export function useInvoice(id: string) {
  return useQuery({
    queryKey: invoiceKeys.detail(id),
    queryFn: () => invoicesApi.get(id),
    enabled: !!id,
  });
}

/**
 * Create invoice
 */
export function useCreateInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InvoiceCreate) => invoicesApi.create(data),
    onSuccess: () => {
      // Invalidate all invoice queries
      queryClient.invalidateQueries({ queryKey: invoiceKeys.all });
      // Also invalidate payment summary (invoice affects revenue)
      queryClient.invalidateQueries({ queryKey: paymentKeys.all });
    },
  });
}

/**
 * Update invoice (status, due date)
 */
export function useUpdateInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: InvoiceUpdate }) =>
      invoicesApi.update(id, data),
    onSuccess: (_, variables) => {
      // Invalidate specific invoice
      queryClient.invalidateQueries({ queryKey: invoiceKeys.detail(variables.id) });
      // Invalidate invoice lists
      queryClient.invalidateQueries({ queryKey: invoiceKeys.lists() });
      // Invalidate payment summary (status change affects revenue)
      queryClient.invalidateQueries({ queryKey: paymentKeys.all });
    },
  });
}

/**
 * Generate invoice PDF
 */
export function useGenerateInvoicePdf() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => invoicesApi.generatePdf(id),
    onSuccess: (_, id) => {
      // Invalidate specific invoice (to refresh pdf_url)
      queryClient.invalidateQueries({ queryKey: invoiceKeys.detail(id) });
    },
  });
}

// ===== bKash Hooks =====

/**
 * Create bKash payment
 */
export function useCreateBkashPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BkashPaymentCreate) => bkashApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: paymentKeys.all });
    },
  });
}

/**
 * Execute bKash payment
 */
export function useExecuteBkashPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BkashPaymentExecute) => bkashApi.execute(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: paymentKeys.all });
    },
  });
}

/**
 * Query bKash payment status
 */
export function useQueryBkashPayment(paymentId: string) {
  return useQuery({
    queryKey: ['bkash', 'payment', paymentId],
    queryFn: () => bkashApi.query(paymentId),
    enabled: !!paymentId,
    refetchInterval: 5000, // Poll every 5 seconds
  });
}
