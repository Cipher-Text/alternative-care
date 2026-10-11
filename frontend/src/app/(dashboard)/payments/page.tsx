"use client";

import { useTranslations } from 'next-intl'
import { Button } from "@/components/ui/button";
import { Plus, FileText } from "lucide-react";
import Link from "next/link";
import { usePaymentSummary, usePayments } from "@/lib/hooks/usePayments";
import { PaymentSummaryCards } from "@/components/payments/PaymentSummaryCards";
import { RecentTransactionsList } from "@/components/payments/RecentTransactionsList";

export default function PaymentsPage() {
  const tp = useTranslations('pages')
  const t = useTranslations('payUi')
  const tm = useTranslations('payBadgeUi')
  // Fetch payment summary (default: all time)
  const { data: summary, isLoading: summaryLoading } = usePaymentSummary();

  // Fetch recent payments (limit 10, ordered by date desc)
  const { data: payments = [], isLoading: paymentsLoading } = usePayments({
    limit: 10,
    offset: 0,
  });

  return (
    <div className="flex-1 space-y-6 p-4 pt-4 sm:p-8 sm:pt-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">{tp('paymentsTitle')}</h1>
          <p className="text-gray-600 dark:text-gray-400">
            {tp('paymentsSubtitle')}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Link href="/payments/invoices/new">
            <Button
              variant="outline"
              className="bg-white dark:bg-slate-700/50 border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-200 hover:bg-blue-50 dark:hover:bg-blue-600 hover:text-blue-700 dark:hover:text-white hover:border-blue-300 dark:hover:border-blue-600"
            >
              <FileText className="mr-2 h-4 w-4" />
              {t('createInvoice')}
            </Button>
          </Link>
          <Link href="/payments/transactions">
            <Button className="bg-primary hover:bg-slate-950 dark:hover:bg-emerald-800 text-white shadow-lg shadow-slate-900/10">
              <Plus className="mr-2 h-4 w-4" />
              {t('recordPayment')}
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
          <div className="border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 rounded-lg p-4 hover:bg-emerald-50 dark:hover:bg-primary/20 hover:border-emerald-300 dark:hover:border-emerald-600 transition-all duration-200 cursor-pointer group">
            <h3 className="font-semibold mb-1 text-gray-900 dark:text-white group-hover:text-emerald-700 dark:group-hover:text-emerald-300">
              {t('txHistoryTitle')}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300">
              {t('txHistoryDesc')}
            </p>
          </div>
        </Link>
        <Link href="/payments/invoices">
          <div className="border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 rounded-lg p-4 hover:bg-blue-50 dark:hover:bg-blue-600/20 hover:border-blue-300 dark:hover:border-blue-600 transition-all duration-200 cursor-pointer group">
            <h3 className="font-semibold mb-1 text-gray-900 dark:text-white group-hover:text-blue-700 dark:group-hover:text-blue-300">
              {t('invoicesTitle')}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300">
              {t('invoicesDesc')}
            </p>
          </div>
        </Link>
        <div className="border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800/30 rounded-lg p-4">
          <h3 className="font-semibold mb-1 text-gray-600 dark:text-gray-500">
            {t('reportsTitle')}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-500">
            {t('reportsDesc')}
          </p>
        </div>
      </div>

      {/* Recent Transactions */}
      <RecentTransactionsList payments={payments} isLoading={paymentsLoading} limit={10} />

      {/* Payment Method Breakdown (Placeholder) */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 rounded-lg p-6">
          <h3 className="font-semibold mb-4 text-gray-900 dark:text-white">{t('paymentMethods')}</h3>
          {summary && !summaryLoading && (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="text-sm text-gray-600 dark:text-gray-400">{tm('method.cash')}</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  ৳{summary.cash_amount.toLocaleString()}
                </span>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="text-sm text-gray-600 dark:text-gray-400">{tm('method.bkash')}</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  ৳{summary.bkash_amount.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-gray-200 dark:border-slate-700">
                <span className="text-sm font-semibold text-gray-900 dark:text-white">{t('total')}</span>
                <span className="text-sm font-semibold text-emerald-400">
                  ৳{summary.total_amount.toLocaleString()}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 rounded-lg p-6">
          <h3 className="font-semibold mb-4 text-gray-900 dark:text-white">{t('quickStats')}</h3>
          {summary && !summaryLoading && (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="text-sm text-gray-600 dark:text-gray-400">{t('totalTransactions')}</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">{summary.total_payments}</span>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="text-sm text-gray-600 dark:text-gray-400">{t('averageTransaction')}</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  ৳{summary.total_payments > 0
                    ? Math.round(summary.total_amount / summary.total_payments).toLocaleString()
                    : 0}
                </span>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="text-sm text-gray-400">{t('collectionRate')}</span>
                <span className="text-sm font-medium text-green-400">
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
