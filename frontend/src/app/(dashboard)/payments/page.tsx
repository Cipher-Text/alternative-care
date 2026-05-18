"use client";

import { Button } from "@/components/ui/button";
import { Plus, FileText } from "lucide-react";
import Link from "next/link";
import { usePaymentSummary, usePayments } from "@/lib/hooks/usePayments";
import { PaymentSummaryCards } from "@/components/payments/PaymentSummaryCards";
import { RecentTransactionsList } from "@/components/payments/RecentTransactionsList";

export default function PaymentsPage() {
  // Fetch payment summary (default: all time)
  const { data: summary, isLoading: summaryLoading } = usePaymentSummary();

  // Fetch recent payments (limit 10, ordered by date desc)
  const { data: payments = [], isLoading: paymentsLoading } = usePayments({
    limit: 10,
    offset: 0,
  });

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Payments & Billing</h2>
          <p className="text-muted-foreground">
            Manage payments, invoices, and financial records
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/payments/invoices/new">
            <Button variant="outline">
              <FileText className="mr-2 h-4 w-4" />
              Create Invoice
            </Button>
          </Link>
          <Link href="/payments/transactions">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Record Payment
            </Button>
          </Link>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <PaymentSummaryCards summary={summary} isLoading={summaryLoading} />
      )}

      {/* Quick Navigation */}
      <div className="grid gap-4 md:grid-cols-3">
        <Link href="/payments/transactions">
          <div className="border rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer">
            <h3 className="font-semibold mb-1">Transaction History</h3>
            <p className="text-sm text-muted-foreground">
              View all payments and filter by date, method, or status
            </p>
          </div>
        </Link>
        <Link href="/payments/invoices">
          <div className="border rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer">
            <h3 className="font-semibold mb-1">Invoices</h3>
            <p className="text-sm text-muted-foreground">
              Create and manage invoices for patients
            </p>
          </div>
        </Link>
        <div className="border rounded-lg p-4 bg-gray-50">
          <h3 className="font-semibold mb-1 text-gray-500">Reports (Coming Soon)</h3>
          <p className="text-sm text-muted-foreground">
            Generate financial reports and analytics
          </p>
        </div>
      </div>

      {/* Recent Transactions */}
      <RecentTransactionsList payments={payments} isLoading={paymentsLoading} limit={10} />

      {/* Payment Method Breakdown (Placeholder) */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="border rounded-lg p-6">
          <h3 className="font-semibold mb-4">Payment Methods</h3>
          {summary && !summaryLoading && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Cash</span>
                <span className="text-sm font-medium">
                  ৳{summary.cash_amount.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">bKash</span>
                <span className="text-sm font-medium">
                  ৳{summary.bkash_amount.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between pt-2 border-t">
                <span className="text-sm font-semibold">Total</span>
                <span className="text-sm font-semibold">
                  ৳{summary.total_amount.toLocaleString()}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="border rounded-lg p-6">
          <h3 className="font-semibold mb-4">Quick Stats</h3>
          {summary && !summaryLoading && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Total Transactions</span>
                <span className="text-sm font-medium">{summary.total_payments}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Average Transaction</span>
                <span className="text-sm font-medium">
                  ৳{summary.total_payments > 0
                    ? Math.round(summary.total_amount / summary.total_payments).toLocaleString()
                    : 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Collection Rate</span>
                <span className="text-sm font-medium">
                  {summary.total_amount > 0
                    ? ((summary.paid_amount / summary.total_amount) * 100).toFixed(1)
                    : 0}%
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
