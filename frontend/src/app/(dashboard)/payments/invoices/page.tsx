"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useDateFormat } from "@/lib/i18n/date";
import { Pager, serverPage, usePager } from "@/components/shared/Pager";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, FileText, Eye } from "lucide-react";
import { useInvoices } from "@/lib/hooks/usePayments";
import { InvoiceStatusBadge } from "@/components/payments/InvoiceStatusBadge";
import type { InvoiceStatus } from "@/types/payment";

export default function InvoicesPage() {
  const t = useTranslations("payInvoiceUi");
  const tb = useTranslations("payBadgeUi");
  const { fmt } = useDateFormat();
  const [statusFilter, setStatusFilter] = useState<InvoiceStatus | "all">("all");

  const pager = usePager(undefined, [statusFilter]);

  // Status filter and paging run on the server; one extra row tells us a next page exists
  const { data, isLoading, isFetching } = useInvoices({
    status: statusFilter === "all" ? undefined : statusFilter,
    limit: pager.pageSize + 1,
    offset: pager.offset,
  });
  const { items: invoices, hasNext } = serverPage(data, pager.pageSize);

  return (
    <div className="flex-1 space-y-6 p-4 pt-4 sm:p-8 sm:pt-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-muted-foreground">{t("subtitle")}</p>
        </div>
        <Link href="/payments/invoices/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            {t("createInvoice")}
          </Button>
        </Link>
      </div>

      {/* Status Tabs */}
      <Tabs value={statusFilter} onValueChange={(v) => setStatusFilter(v as any)}>
        <TabsList>
          <TabsTrigger value="all">{t("tabAll")}</TabsTrigger>
          <TabsTrigger value="draft">{tb("invoiceStatus.draft")}</TabsTrigger>
          <TabsTrigger value="sent">{tb("invoiceStatus.sent")}</TabsTrigger>
          <TabsTrigger value="paid">{tb("invoiceStatus.paid")}</TabsTrigger>
          <TabsTrigger value="overdue">{tb("invoiceStatus.overdue")}</TabsTrigger>
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
                <h3 className="text-lg font-semibold mb-2">{t("emptyTitle")}</h3>
                <p className="text-muted-foreground mb-4">
                  {statusFilter === "all"
                    ? t("emptyAll")
                    : t(`emptyByStatus.${statusFilter}`)}
                </p>
                <Link href="/payments/invoices/new">
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    {t("createInvoice")}
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
                        <span className="text-muted-foreground">{t("amountLabel")}</span>
                        <span className="font-semibold">৳{invoice.amount.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">{t("issueDate")}</span>
                        <span>
                          {invoice.issue_date ? fmt(invoice.issue_date, "P") : "—"}
                        </span>
                      </div>
                      {invoice.due_date && (
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">{t("dueDate")}</span>
                          <span>
                            {fmt(invoice.due_date, "P")}
                          </span>
                        </div>
                      )}
                    </div>

                    <Link href={`/payments/invoices/${invoice.id}`}>
                      <Button variant="outline" size="sm" className="w-full">
                        <Eye className="mr-2 h-4 w-4" />
                        {t("viewDetails")}
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
          <Pager
            page={pager.page}
            pageSize={pager.pageSize}
            count={invoices.length}
            hasNext={hasNext}
            onPageChange={pager.setPage}
            isLoading={isFetching}
            noun="invoices"
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
