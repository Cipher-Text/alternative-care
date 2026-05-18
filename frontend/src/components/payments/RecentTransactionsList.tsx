"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { PaymentMethodBadge } from "./PaymentMethodBadge";
import { PaymentStatusBadge } from "./PaymentStatusBadge";
import type { PaymentListItem } from "@/types/payment";

interface RecentTransactionsListProps {
  payments: PaymentListItem[];
  isLoading?: boolean;
  limit?: number;
}

export function RecentTransactionsList({
  payments,
  isLoading,
  limit = 10,
}: RecentTransactionsListProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Transactions</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="space-y-2">
                  <div className="h-4 w-32 animate-pulse bg-gray-200 rounded" />
                  <div className="h-3 w-24 animate-pulse bg-gray-200 rounded" />
                </div>
                <div className="h-6 w-20 animate-pulse bg-gray-200 rounded" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const recentPayments = payments.slice(0, limit);

  if (recentPayments.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Transactions</CardTitle>
          <CardDescription>No transactions yet</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Transactions will appear here once you start recording payments.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Recent Transactions</CardTitle>
            <CardDescription>Latest {recentPayments.length} payments</CardDescription>
          </div>
          <Link href="/payments/transactions">
            <Button variant="ghost" size="sm">
              View All
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {recentPayments.map((payment) => (
            <div
              key={payment.id}
              className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium truncate">{payment.patient_name}</p>
                  <PaymentStatusBadge status={payment.status} />
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-xs text-muted-foreground">
                    {new Date(payment.payment_date).toLocaleDateString()}
                  </p>
                  <PaymentMethodBadge method={payment.payment_method} />
                  {payment.description && (
                    <p className="text-xs text-muted-foreground truncate">
                      {payment.description}
                    </p>
                  )}
                </div>
              </div>
              <div className="text-right ml-4">
                <p className="text-sm font-semibold">
                  {payment.currency} {payment.amount.toLocaleString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
