"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, FileText, Eye } from "lucide-react";
import { useInvoices } from "@/lib/hooks/usePayments";
import { InvoiceStatusBadge } from "@/components/payments/InvoiceStatusBadge";
import type { InvoiceStatus } from "@/types/payment";

export default function InvoicesPage() {
  const [statusFilter, setStatusFilter] = useState<InvoiceStatus | "all">("all");

  // Fetch invoices
  const { data: invoices = [], isLoading } = useInvoices({
    status: statusFilter === "all" ? undefined : statusFilter,
    limit: 100,
  });

  const statusCounts = {
    all: invoices.length,
    draft: invoices.filter((i) => i.status === "draft").length,
    sent: invoices.filter((i) => i.status === "sent").length,
    paid: invoices.filter((i) => i.status === "paid").length,
    overdue: invoices.filter((i) => i.status === "overdue").length,
  };

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Invoices</h2>
          <p className="text-muted-foreground">Create and manage patient invoices</p>
        </div>
        <Link href="/payments/invoices/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Invoice
          </Button>
        </Link>
      </div>

      {/* Status Tabs */}
      <Tabs value={statusFilter} onValueChange={(v) => setStatusFilter(v as any)}>
        <TabsList>
          <TabsTrigger value="all">All ({statusCounts.all})</TabsTrigger>
          <TabsTrigger value="draft">Draft ({statusCounts.draft})</TabsTrigger>
          <TabsTrigger value="sent">Sent ({statusCounts.sent})</TabsTrigger>
          <TabsTrigger value="paid">Paid ({statusCounts.paid})</TabsTrigger>
          <TabsTrigger value="overdue">Overdue ({statusCounts.overdue})</TabsTrigger>
        </TabsList>

        <TabsContent value={statusFilter} className="mt-6">
          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <Card key={i}>
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      <div className="h-6 w-32 animate-pulse bg-gray-200 rounded" />
                      <div className="h-4 w-24 animate-pulse bg-gray-200 rounded" />
                      <div className="h-8 w-20 animate-pulse bg-gray-200 rounded" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : invoices.length === 0 ? (
            <Card>
              <CardContent className="pt-12 pb-12 text-center">
                <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No invoices found</h3>
                <p className="text-muted-foreground mb-4">
                  {statusFilter === "all"
                    ? "Create your first invoice to get started"
                    : `No ${statusFilter} invoices`}
                </p>
                <Link href="/payments/invoices/new">
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Invoice
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {invoices.map((invoice) => (
                <Card key={invoice.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold">{invoice.invoice_number}</h3>
                        <p className="text-sm text-muted-foreground">
                          {invoice.patient_name}
                        </p>
                      </div>
                      <InvoiceStatusBadge status={invoice.status} />
                    </div>

                    <div className="space-y-2 mb-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Amount:</span>
                        <span className="font-semibold">৳{invoice.amount.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Issue Date:</span>
                        <span>
                          {new Date(invoice.issue_date).toLocaleDateString()}
                        </span>
                      </div>
                      {invoice.due_date && (
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Due Date:</span>
                          <span>
                            {new Date(invoice.due_date).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                    </div>

                    <Link href={`/payments/invoices/${invoice.id}`}>
                      <Button variant="outline" size="sm" className="w-full">
                        <Eye className="mr-2 h-4 w-4" />
                        View Details
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
