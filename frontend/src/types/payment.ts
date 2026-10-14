/**
 * Payment and Invoice TypeScript Types
 * Matches backend schemas from app/shared/schemas/payment.py
 */

export type PaymentMethod = 'cash' | 'bkash' | 'nagad' | 'rocket' | 'card';
export type PaymentStatus = 'paid' | 'pending' | 'failed' | 'refunded';
export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';

// ===== Payment Types =====

export interface Payment {
  id: string;
  tenant_id: string;
  patient_id: string;
  visit_id?: string;
  amount: number;
  currency: string;
  payment_method: PaymentMethod;
  status: PaymentStatus;
  payment_date: string; // ISO date string
  description?: string;
  transaction_id?: string;
  received_by: string;
  created_at: string;
  updated_at: string;
  deleted_at?: string;

  // Populated fields (from joins)
  patient_name?: string;
  patient_phone?: string;
  received_by_name?: string;
}

export interface PaymentCreate {
  patient_id: string;
  visit_id?: string;
  amount: number;
  payment_method: PaymentMethod;
  description?: string;
  payment_date?: string; // ISO date string, defaults to today
}

export interface PaymentListItem {
  id: string;
  patient_id: string;
  patient_name: string;
  patient_phone?: string;
  amount: number;
  currency: string;
  payment_method: PaymentMethod;
  status: PaymentStatus;
  payment_date: string;
  description?: string;
  created_at: string;
}

export interface PaymentSummary {
  total_payments: number;
  total_amount: number;
  paid_amount: number;
  pending_amount: number;
  cash_amount: number;
  bkash_amount: number;
  period_start?: string;
  period_end?: string;
}

// ===== Invoice Types =====

export interface InvoiceItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

/** An invoice is a document for one recorded payment; patient/amount/date/items come from it. */
export interface Invoice {
  id: string;
  tenant_id: string;
  payment_id: string;
  invoice_number: string;
  status: InvoiceStatus;
  due_date?: string | null; // ISO date string
  pdf_url?: string | null;
  created_at: string;
  updated_at?: string | null;

  // Derived from the invoiced payment
  patient_id?: string | null;
  patient_name?: string | null;
  patient_phone?: string | null;
  amount: number;
  currency: string;
  issue_date?: string | null;
  items: InvoiceItem[];
  notes?: string | null;
}

export interface InvoiceCreate {
  payment_id: string;
  due_date?: string; // ISO date string
}

export interface InvoiceUpdate {
  status?: InvoiceStatus;
  due_date?: string;
}

export interface InvoiceListItem {
  id: string;
  payment_id: string;
  patient_id?: string | null;
  patient_name?: string | null;
  invoice_number: string;
  amount: number;
  currency: string;
  status: InvoiceStatus;
  issue_date?: string | null;
  due_date?: string | null;
  created_at: string;
}

// ===== Filter Types =====

export interface PaymentFilters {
  patient_id?: string;
  visit_id?: string;
  payment_method?: PaymentMethod;
  status?: PaymentStatus;
  date_from?: string; // YYYY-MM-DD
  date_to?: string; // YYYY-MM-DD
  limit?: number;
  offset?: number;
}

export interface InvoiceFilters {
  patient_id?: string;
  status?: InvoiceStatus;
  date_from?: string; // YYYY-MM-DD
  date_to?: string; // YYYY-MM-DD
  limit?: number;
  offset?: number;
}

// ===== Chart/Display Types =====

export interface PaymentMethodBreakdown {
  method: PaymentMethod;
  count: number;
  amount: number;
  percentage: number;
}

export interface PaymentTrend {
  date: string; // YYYY-MM-DD
  amount: number;
  count: number;
}
