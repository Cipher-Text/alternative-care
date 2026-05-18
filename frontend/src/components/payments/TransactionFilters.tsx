"use client";

import { useState } from "react";
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
            <Label htmlFor="date_from">From Date</Label>
            <Input
              id="date_from"
              type="date"
              value={filters.date_from || ""}
              onChange={(e) => handleFilterChange("date_from", e.target.value)}
            />
          </div>

          {/* Date To */}
          <div className="space-y-2">
            <Label htmlFor="date_to">To Date</Label>
            <Input
              id="date_to"
              type="date"
              value={filters.date_to || ""}
              onChange={(e) => handleFilterChange("date_to", e.target.value)}
            />
          </div>

          {/* Payment Method */}
          <div className="space-y-2">
            <Label htmlFor="payment_method">Payment Method</Label>
            <Select
              value={filters.payment_method || "all"}
              onValueChange={(value) =>
                handleFilterChange("payment_method", value === "all" ? undefined : value)
              }
            >
              <SelectTrigger id="payment_method">
                <SelectValue placeholder="All methods" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All methods</SelectItem>
                <SelectItem value="cash">Cash</SelectItem>
                <SelectItem value="bkash">bKash</SelectItem>
                <SelectItem value="nagad">Nagad</SelectItem>
                <SelectItem value="rocket">Rocket</SelectItem>
                <SelectItem value="card">Card</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <Select
              value={filters.status || "all"}
              onValueChange={(value) =>
                handleFilterChange("status", value === "all" ? undefined : value)
              }
            >
              <SelectTrigger id="status">
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="paid">Paid</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="refunded">Refunded</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 mt-4">
          <Button onClick={handleApply} size="sm">
            <Search className="mr-2 h-4 w-4" />
            Apply Filters
          </Button>
          {hasActiveFilters && (
            <Button onClick={handleReset} variant="outline" size="sm">
              <X className="mr-2 h-4 w-4" />
              Clear
            </Button>
          )}
          {hasActiveFilters && (
            <span className="text-sm text-muted-foreground ml-2">
              {Object.keys(filters).filter(k => filters[k as keyof PaymentFilters]).length} filter(s) active
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
