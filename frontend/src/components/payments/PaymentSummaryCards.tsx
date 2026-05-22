"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DollarSign, CheckCircle, Clock, TrendingUp } from "lucide-react";
import type { PaymentSummary } from "@/types/payment";

interface PaymentSummaryCardsProps {
  summary: PaymentSummary;
  isLoading?: boolean;
}

export function PaymentSummaryCards({ summary, isLoading }: PaymentSummaryCardsProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 animate-pulse bg-gray-200 dark:bg-slate-700 rounded" />
              <div className="h-4 w-4 animate-pulse bg-gray-200 dark:bg-slate-700 rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-32 animate-pulse bg-gray-200 dark:bg-slate-700 rounded mb-2" />
              <div className="h-3 w-20 animate-pulse bg-gray-200 dark:bg-slate-700 rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: "Total Revenue",
      value: `৳${summary.total_amount.toLocaleString()}`,
      subtitle: `${summary.total_payments} payments`,
      icon: DollarSign,
      color: "text-blue-400",
      bgColor: "bg-blue-500/20 border-blue-500/30",
    },
    {
      title: "Paid",
      value: `৳${summary.paid_amount.toLocaleString()}`,
      subtitle: `${((summary.paid_amount / summary.total_amount) * 100 || 0).toFixed(0)}% of total`,
      icon: CheckCircle,
      color: "text-green-400",
      bgColor: "bg-green-500/20 border-green-500/30",
    },
    {
      title: "Pending",
      value: `৳${summary.pending_amount.toLocaleString()}`,
      subtitle: summary.pending_amount > 0 ? "Awaiting payment" : "All clear",
      icon: Clock,
      color: summary.pending_amount > 0 ? "text-orange-400" : "text-gray-400",
      bgColor: summary.pending_amount > 0 ? "bg-orange-500/20 border-orange-500/30" : "bg-gray-500/20 border-gray-500/30",
    },
    {
      title: "Cash Received",
      value: `৳${summary.cash_amount.toLocaleString()}`,
      subtitle: `${((summary.cash_amount / summary.total_amount) * 100 || 0).toFixed(0)}% cash`,
      icon: TrendingUp,
      color: "text-purple-400",
      bgColor: "bg-purple-500/20 border-purple-500/30",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card
            key={card.title}
            className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700 hover:shadow-lg dark:hover:shadow-xl dark:hover:shadow-indigo-500/10 transition-all duration-200"
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-300">
                {card.title}
              </CardTitle>
              <div className={`p-2 rounded-lg ${card.bgColor}`}>
                <Icon className={`h-4 w-4 ${card.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">{card.value}</div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{card.subtitle}</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
