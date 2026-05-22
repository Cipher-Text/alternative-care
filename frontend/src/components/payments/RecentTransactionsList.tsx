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
      <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
        <CardHeader>
          <CardTitle className="text-gray-900 dark:text-white">Recent Transactions</CardTitle>
          <CardDescription className="text-gray-600 dark:text-gray-400">Loading...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center justify-between p-3 border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900/50 rounded-lg">
                <div className="space-y-2">
                  <div className="h-4 w-32 animate-pulse bg-gray-200 dark:bg-slate-700 rounded" />
                  <div className="h-3 w-24 animate-pulse bg-gray-200 dark:bg-slate-700 rounded" />
                </div>
                <div className="h-6 w-20 animate-pulse bg-gray-200 dark:bg-slate-700 rounded" />
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
      <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
        <CardHeader>
          <CardTitle className="text-gray-900 dark:text-white">Recent Transactions</CardTitle>
          <CardDescription className="text-gray-600 dark:text-gray-400">No transactions yet</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Transactions will appear here once you start recording payments.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-gray-900 dark:text-white">Recent Transactions</CardTitle>
            <CardDescription className="text-gray-600 dark:text-gray-400">
              Latest {recentPayments.length} payments
            </CardDescription>
          </div>
          <Link href="/payments/transactions">
            <Button
              variant="ghost"
              size="sm"
              className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-700"
            >
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
              className="flex items-center justify-between p-3 border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900/50 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700/50 hover:border-indigo-300 dark:hover:border-indigo-600 transition-all duration-200"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium truncate text-gray-900 dark:text-white">
                    {payment.patient_name}
                  </p>
                  <PaymentStatusBadge status={payment.status} />
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {new Date(payment.payment_date).toLocaleDateString()}
                  </p>
                  <PaymentMethodBadge method={payment.payment_method} />
                  {payment.description && (
                    <p className="text-xs text-gray-500 dark:text-gray-500 truncate">
                      {payment.description}
                    </p>
                  )}
                </div>
              </div>
              <div className="text-right ml-4">
                <p className="text-sm font-semibold text-indigo-400">
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
