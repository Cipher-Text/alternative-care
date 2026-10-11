"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Search, X } from "lucide-react";
import type { PaymentFilters } from "@/types/payment";

interface TransactionFiltersProps {
  onFilter: (filters: PaymentFilters) => void;
  onReset: () => void;
}

export function TransactionFilters({ onFilter, onReset }: TransactionFiltersProps) {
  const t = useTranslations("payTxUi");
  const tb = useTranslations("payBadgeUi");
  const [filters, setFilters] = useState<PaymentFilters>({});

  const handleFilterChange = (key: keyof PaymentFilters, value: any) => {
    const newFilters = { ...filters, [key]: value || undefined };
    setFilters(newFilters);
  };

  const handleApply = () => {
    onFilter(filters);
  };

  const handleReset = () => {
    setFilters({});
    onReset();
  };

  const hasActiveFilters = Object.keys(filters).some(
    (key) => filters[key as keyof PaymentFilters] !== undefined
  );

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {/* Date From */}
          <div className="space-y-2">
            <Label htmlFor="date_from">{t("fromDate")}</Label>
            <Input
              id="date_from"
              type="date"
              value={filters.date_from || ""}
              onChange={(e) => handleFilterChange("date_from", e.target.value)}
            />
          </div>

          {/* Date To */}
          <div className="space-y-2">
            <Label htmlFor="date_to">{t("toDate")}</Label>
            <Input
              id="date_to"
              type="date"
              value={filters.date_to || ""}
              onChange={(e) => handleFilterChange("date_to", e.target.value)}
            />
          </div>

          {/* Payment Method */}
          <div className="space-y-2">
            <Label htmlFor="payment_method">{t("paymentMethod")}</Label>
            <Select
              value={filters.payment_method || "all"}
              onValueChange={(value) =>
                handleFilterChange("payment_method", value === "all" ? undefined : value)
              }
            >
              <SelectTrigger id="payment_method">
                <SelectValue placeholder={t("allMethods")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("allMethods")}</SelectItem>
                <SelectItem value="cash">{tb("method.cash")}</SelectItem>
                <SelectItem value="bkash">{tb("method.bkash")}</SelectItem>
                <SelectItem value="nagad">{tb("method.nagad")}</SelectItem>
                <SelectItem value="rocket">{tb("method.rocket")}</SelectItem>
                <SelectItem value="card">{tb("method.card")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <Label htmlFor="status">{t("status")}</Label>
            <Select
              value={filters.status || "all"}
              onValueChange={(value) =>
                handleFilterChange("status", value === "all" ? undefined : value)
              }
            >
              <SelectTrigger id="status">
                <SelectValue placeholder={t("allStatuses")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("allStatuses")}</SelectItem>
                <SelectItem value="paid">{tb("paymentStatus.paid")}</SelectItem>
                <SelectItem value="pending">{tb("paymentStatus.pending")}</SelectItem>
                <SelectItem value="failed">{tb("paymentStatus.failed")}</SelectItem>
                <SelectItem value="refunded">{tb("paymentStatus.refunded")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 mt-4">
          <Button onClick={handleApply} size="sm">
            <Search className="mr-2 h-4 w-4" />
            {t("applyFilters")}
          </Button>
          {hasActiveFilters && (
            <Button onClick={handleReset} variant="outline" size="sm">
              <X className="mr-2 h-4 w-4" />
              {t("clear")}
            </Button>
          )}
          {hasActiveFilters && (
            <span className="text-sm text-muted-foreground ml-2">
              {t("filtersActive", { count: Object.keys(filters).filter(k => filters[k as keyof PaymentFilters]).length })}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
