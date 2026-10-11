"use client";

import { use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useDateFormat } from "@/lib/i18n/date";
import toast from "react-hot-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, FileText, Send, CheckCircle } from "lucide-react";
import { useInvoice, useUpdateInvoice, useViewInvoicePdf } from "@/lib/hooks/usePayments";
import { InvoiceStatusBadge } from "@/components/payments/InvoiceStatusBadge";

interface InvoiceDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function InvoiceDetailPage({ params }: InvoiceDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const t = useTranslations("payInvoiceUi");
  const { fmt } = useDateFormat();

  const { data: invoice, isLoading } = useInvoice(id);
  const updateInvoice = useUpdateInvoice();
  const viewPdf = useViewInvoicePdf();

  const handleStatusUpdate = async (status: "sent" | "paid" | "cancelled") => {
    try {
      await updateInvoice.mutateAsync({ id, data: { status } });
      const statusMessages = {
        sent: t("sentOk"),
        paid: t("paidOk"),
        cancelled: t("cancelledOk"),
      };
      toast.success(statusMessages[status]);
    } catch (error: any) {
      console.error("Failed to update invoice:", error);
      toast.error(error?.response?.data?.detail || t("updateFail"));
    }
  };

  const handleViewPdf = async () => {
    await viewPdf.mutateAsync(id);
  };

  if (isLoading) {
    return (
      <div className="flex-1 space-y-6 p-4 pt-4 sm:p-8 sm:pt-6">
        <div className="h-8 w-64 animate-pulse bg-gray-200 rounded" />
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-4 w-full animate-pulse bg-gray-200 rounded" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="flex-1 p-4 pt-4 sm:p-8 sm:pt-6">
        <Card>
          <CardContent className="pt-12 pb-12 text-center">
            <h3 className="text-lg font-semibold mb-2">{t("notFound")}</h3>
            <Link href="/payments/invoices">
              <Button variant="outline" className="mt-4">
                {t("backToInvoices")}
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-6 p-4 pt-4 sm:p-8 sm:pt-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/payments/invoices" aria-label={t("back")}>
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight">{invoice.invoice_number}</h1>
              <InvoiceStatusBadge status={invoice.status} />
            </div>
            <p className="text-muted-foreground">{invoice.patient_name}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleViewPdf} disabled={viewPdf.isLoading}>
            <FileText className="mr-2 h-4 w-4" />
            {viewPdf.isLoading ? t("preparing") : t("viewPrintPdf")}
          </Button>

          {invoice.status === "draft" && (
            <Button onClick={() => handleStatusUpdate("sent")} disabled={updateInvoice.isLoading}>
              <Send className="mr-2 h-4 w-4" />
              {t("sendInvoice")}
            </Button>
          )}

          {invoice.status === "sent" && (
            <Button onClick={() => handleStatusUpdate("paid")} disabled={updateInvoice.isLoading}>
              <CheckCircle className="mr-2 h-4 w-4" />
              {t("markPaid")}
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Invoice Details */}
        <Card>
          <CardHeader>
            <CardTitle>{t("detailsTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t("patient")}</span>
              <span className="font-medium">{invoice.patient_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t("issueDate")}</span>
              <span>{fmt(invoice.issue_date, "P")}</span>
            </div>
            {invoice.due_date && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">{t("dueDate")}</span>
                <span>{fmt(invoice.due_date, "P")}</span>
              </div>
            )}
            <div className="flex justify-between pt-3 border-t">
              <span className="text-muted-foreground">{t("status")}</span>
              <InvoiceStatusBadge status={invoice.status} />
            </div>
          </CardContent>
        </Card>

        {/* Amount */}
        <Card>
          <CardHeader>
            <CardTitle>{t("amountTitle")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">৳{invoice.amount.toLocaleString()}</div>
            <p className="text-sm text-muted-foreground mt-1">
              {t("itemCount", { count: invoice.items.length })}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Items */}
      <Card>
        <CardHeader>
          <CardTitle>{t("itemsTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {invoice.items.map((item, index) => (
              <div key={index} className="flex justify-between items-center py-2 border-b last:border-0">
                <div className="flex-1">
                  <p className="font-medium">{item.description}</p>
                  <p className="text-sm text-muted-foreground">
                    {item.quantity} × ৳{item.unit_price.toFixed(2)}
                  </p>
                </div>
                <span className="font-semibold">৳{item.total.toFixed(2)}</span>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t">
            <div className="flex justify-between text-lg font-bold">
              <span>{t("total")}</span>
              <span>৳{invoice.amount.toFixed(2)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notes */}
      {invoice.notes && (
        <Card>
          <CardHeader>
            <CardTitle>{t("notes")}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground whitespace-pre-wrap">{invoice.notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
