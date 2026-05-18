"use client";

import { use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, FileText, Send, CheckCircle } from "lucide-react";
import { useInvoice, useUpdateInvoice, useGenerateInvoicePdf } from "@/lib/hooks/usePayments";
import { InvoiceStatusBadge } from "@/components/payments/InvoiceStatusBadge";

interface InvoiceDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function InvoiceDetailPage({ params }: InvoiceDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();

  const { data: invoice, isLoading } = useInvoice(id);
  const updateInvoice = useUpdateInvoice();
  const generatePdf = useGenerateInvoicePdf();

  const handleStatusUpdate = async (status: "sent" | "paid" | "cancelled") => {
    try {
      await updateInvoice.mutateAsync({ id, data: { status } });
      const statusMessages = {
        sent: "Invoice sent successfully",
        paid: "Invoice marked as paid",
        cancelled: "Invoice cancelled",
      };
      toast.success(statusMessages[status]);
    } catch (error: any) {
      console.error("Failed to update invoice:", error);
      toast.error(error?.response?.data?.detail || "Failed to update invoice status");
    }
  };

  const handleGeneratePdf = async () => {
    try {
      const result = await generatePdf.mutateAsync(id);
      // Open PDF in new tab
      if (result.pdf_url) {
        window.open(result.pdf_url, "_blank");
        toast.success("PDF generated successfully");
      }
    } catch (error: any) {
      console.error("Failed to generate PDF:", error);
      toast.error(error?.response?.data?.detail || "Failed to generate PDF");
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 space-y-6 p-8 pt-6">
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
      <div className="flex-1 p-8 pt-6">
        <Card>
          <CardContent className="pt-12 pb-12 text-center">
            <h3 className="text-lg font-semibold mb-2">Invoice not found</h3>
            <Link href="/payments/invoices">
              <Button variant="outline" className="mt-4">
                Back to Invoices
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/payments/invoices">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-3xl font-bold tracking-tight">{invoice.invoice_number}</h2>
              <InvoiceStatusBadge status={invoice.status} />
            </div>
            <p className="text-muted-foreground">{invoice.patient_name}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleGeneratePdf} disabled={generatePdf.isLoading}>
            <FileText className="mr-2 h-4 w-4" />
            {generatePdf.isLoading ? "Generating..." : "Generate PDF"}
          </Button>

          {invoice.status === "draft" && (
            <Button onClick={() => handleStatusUpdate("sent")} disabled={updateInvoice.isLoading}>
              <Send className="mr-2 h-4 w-4" />
              Send Invoice
            </Button>
          )}

          {invoice.status === "sent" && (
            <Button onClick={() => handleStatusUpdate("paid")} disabled={updateInvoice.isLoading}>
              <CheckCircle className="mr-2 h-4 w-4" />
              Mark as Paid
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Invoice Details */}
        <Card>
          <CardHeader>
            <CardTitle>Invoice Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Patient:</span>
              <span className="font-medium">{invoice.patient_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Issue Date:</span>
              <span>{new Date(invoice.issue_date).toLocaleDateString()}</span>
            </div>
            {invoice.due_date && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Due Date:</span>
                <span>{new Date(invoice.due_date).toLocaleDateString()}</span>
              </div>
            )}
            <div className="flex justify-between pt-3 border-t">
              <span className="text-muted-foreground">Status:</span>
              <InvoiceStatusBadge status={invoice.status} />
            </div>
          </CardContent>
        </Card>

        {/* Amount */}
        <Card>
          <CardHeader>
            <CardTitle>Amount</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">৳{invoice.amount.toLocaleString()}</div>
            <p className="text-sm text-muted-foreground mt-1">
              {invoice.items.length} item{invoice.items.length !== 1 ? "s" : ""}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Items */}
      <Card>
        <CardHeader>
          <CardTitle>Invoice Items</CardTitle>
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
              <span>Total:</span>
              <span>৳{invoice.amount.toFixed(2)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notes */}
      {invoice.notes && (
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground whitespace-pre-wrap">{invoice.notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
