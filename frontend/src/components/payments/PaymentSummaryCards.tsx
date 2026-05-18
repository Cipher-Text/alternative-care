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
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 animate-pulse bg-gray-200 rounded" />
              <div className="h-4 w-4 animate-pulse bg-gray-200 rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-32 animate-pulse bg-gray-200 rounded mb-2" />
              <div className="h-3 w-20 animate-pulse bg-gray-200 rounded" />
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
      color: "text-blue-600",
    },
    {
      title: "Paid",
      value: `৳${summary.paid_amount.toLocaleString()}`,
      subtitle: `${((summary.paid_amount / summary.total_amount) * 100 || 0).toFixed(0)}% of total`,
      icon: CheckCircle,
      color: "text-green-600",
    },
    {
      title: "Pending",
      value: `৳${summary.pending_amount.toLocaleString()}`,
      subtitle: summary.pending_amount > 0 ? "Awaiting payment" : "All clear",
      icon: Clock,
      color: summary.pending_amount > 0 ? "text-orange-600" : "text-gray-600",
    },
    {
      title: "Cash Received",
      value: `৳${summary.cash_amount.toLocaleString()}`,
      subtitle: `${((summary.cash_amount / summary.total_amount) * 100 || 0).toFixed(0)}% cash`,
      icon: TrendingUp,
      color: "text-purple-600",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
              <Icon className={`h-4 w-4 ${card.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{card.value}</div>
              <p className="text-xs text-muted-foreground mt-1">{card.subtitle}</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
