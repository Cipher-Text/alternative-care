"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { usePayments } from "@/lib/hooks/usePayments";
import { TransactionFilters } from "@/components/payments/TransactionFilters";
import { TransactionTable } from "@/components/payments/TransactionTable";
import { QuickPaymentModal } from "@/components/payments/QuickPaymentModal";
import type { PaymentFilters } from "@/types/payment";

export default function TransactionsPage() {
  const [filters, setFilters] = useState<PaymentFilters>({ limit: 50, offset: 0 });
  const [currentPage, setCurrentPage] = useState(1);
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  const pageSize = 50;

  // Fetch payments with filters
  const { data: payments = [], isLoading } = usePayments(filters);

  const handleFilterApply = (newFilters: PaymentFilters) => {
    setFilters({ ...newFilters, limit: pageSize, offset: 0 });
    setCurrentPage(1);
  };

  const handleFilterReset = () => {
    setFilters({ limit: pageSize, offset: 0 });
    setCurrentPage(1);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    setFilters((prev) => ({
      ...prev,
      offset: (page - 1) * pageSize,
    }));
  };

  const handleExport = () => {
    // Convert payments to CSV
    if (payments.length === 0) return;

    const headers = ["Date", "Patient", "Amount", "Currency", "Method", "Status", "Description"];
    const rows = payments.map((p) => [
      p.payment_date,
      p.patient_name,
      p.amount.toString(),
      p.currency,
      p.payment_method,
      p.status,
      p.description || "",
    ]);

    const csvContent = [
      headers.join(","),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(",")),
    ].join("\n");

    // Download CSV
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `transactions-${new Date().toISOString().split("T")[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Transaction History</h2>
          <p className="text-muted-foreground">
            View and manage all payment transactions
          </p>
        </div>
        <Button onClick={() => setShowPaymentModal(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Record Payment
        </Button>
      </div>

      {/* Filters */}
      <TransactionFilters onFilter={handleFilterApply} onReset={handleFilterReset} />

      {/* Transaction Table */}
      <TransactionTable
        payments={payments}
        isLoading={isLoading}
        currentPage={currentPage}
        pageSize={pageSize}
        onPageChange={handlePageChange}
        onExport={handleExport}
      />

      {/* Quick Payment Modal */}
      <QuickPaymentModal
        open={showPaymentModal}
        onClose={() => setShowPaymentModal(false)}
      />
    </div>
  );
}
