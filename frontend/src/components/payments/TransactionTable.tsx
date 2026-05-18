"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Download } from "lucide-react";
import { PaymentMethodBadge } from "./PaymentMethodBadge";
import { PaymentStatusBadge } from "./PaymentStatusBadge";
import type { PaymentListItem } from "@/types/payment";

interface TransactionTableProps {
  payments: PaymentListItem[];
  isLoading?: boolean;
  currentPage?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
  onExport?: () => void;
}

export function TransactionTable({
  payments,
  isLoading,
  currentPage = 1,
  pageSize = 50,
  onPageChange,
  onExport,
}: TransactionTableProps) {
  if (isLoading) {
    return (
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Patient</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Method</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Description</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[...Array(10)].map((_, i) => (
              <TableRow key={i}>
                <TableCell>
                  <div className="h-4 w-24 animate-pulse bg-gray-200 rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-4 w-32 animate-pulse bg-gray-200 rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-4 w-20 animate-pulse bg-gray-200 rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-6 w-16 animate-pulse bg-gray-200 rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-6 w-16 animate-pulse bg-gray-200 rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-4 w-40 animate-pulse bg-gray-200 rounded" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  if (payments.length === 0) {
    return (
      <div className="border rounded-lg p-12 text-center">
        <p className="text-muted-foreground">No transactions found</p>
        <p className="text-sm text-muted-foreground mt-2">
          Try adjusting your filters or record a new payment
        </p>
      </div>
    );
  }

  const hasNextPage = payments.length === pageSize;
  const hasPreviousPage = currentPage > 1;

  return (
    <div className="space-y-4">
      {/* Export Button */}
      {onExport && (
        <div className="flex justify-end">
          <Button variant="outline" size="sm" onClick={onExport}>
            <Download className="mr-2 h-4 w-4" />
            Export to CSV
          </Button>
        </div>
      )}

      {/* Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Patient</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead>Method</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Description</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {payments.map((payment) => (
              <TableRow key={payment.id} className="cursor-pointer hover:bg-gray-50">
                <TableCell className="font-medium">
                  {new Date(payment.payment_date).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })}
                  <div className="text-xs text-muted-foreground">
                    {new Date(payment.created_at).toLocaleTimeString("en-US", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="font-medium">{payment.patient_name}</div>
                  {payment.patient_phone && (
                    <div className="text-xs text-muted-foreground">
                      {payment.patient_phone}
                    </div>
                  )}
                </TableCell>
                <TableCell className="text-right font-semibold">
                  {payment.currency} {payment.amount.toLocaleString()}
                </TableCell>
                <TableCell>
                  <PaymentMethodBadge method={payment.payment_method} />
                </TableCell>
                <TableCell>
                  <PaymentStatusBadge status={payment.status} />
                </TableCell>
                <TableCell className="max-w-xs truncate">
                  {payment.description || (
                    <span className="text-muted-foreground italic">No description</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {onPageChange && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Showing page {currentPage} ({payments.length} transactions)
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(currentPage - 1)}
              disabled={!hasPreviousPage}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(currentPage + 1)}
              disabled={!hasNextPage}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
