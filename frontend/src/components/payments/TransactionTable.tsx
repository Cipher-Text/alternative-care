"use client";

import { useTranslations } from "next-intl";
import { useDateFormat } from "@/lib/i18n/date";
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
  const t = useTranslations("payTxUi");
  const { fmt } = useDateFormat();
  if (isLoading) {
    return (
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("colDate")}</TableHead>
              <TableHead>{t("colPatient")}</TableHead>
              <TableHead>{t("colAmount")}</TableHead>
              <TableHead>{t("colMethod")}</TableHead>
              <TableHead>{t("colStatus")}</TableHead>
              <TableHead>{t("colDescription")}</TableHead>
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
        <p className="text-muted-foreground">{t("emptyTitle")}</p>
        <p className="text-sm text-muted-foreground mt-2">
          {t("emptyHint")}
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
            {t("export")}
          </Button>
        </div>
      )}

      {/* Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("colDate")}</TableHead>
              <TableHead>{t("colPatient")}</TableHead>
              <TableHead className="text-right">{t("colAmount")}</TableHead>
              <TableHead>{t("colMethod")}</TableHead>
              <TableHead>{t("colStatus")}</TableHead>
              <TableHead>{t("colDescription")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {payments.map((payment) => (
              <TableRow key={payment.id} className="cursor-pointer hover:bg-gray-50">
                <TableCell className="font-medium">
                  {fmt(payment.payment_date, "MMM d, yyyy")}
                  <div className="text-xs text-muted-foreground">
                    {fmt(payment.created_at, "hh:mm a")}
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
                    <span className="text-muted-foreground italic">{t("noDescription")}</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {onPageChange && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm text-muted-foreground">
            {t("showingPage", { page: currentPage, count: payments.length })}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(currentPage - 1)}
              disabled={!hasPreviousPage}
            >
              <ChevronLeft className="h-4 w-4" />
              {t("previous")}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(currentPage + 1)}
              disabled={!hasNextPage}
            >
              {t("next")}
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
