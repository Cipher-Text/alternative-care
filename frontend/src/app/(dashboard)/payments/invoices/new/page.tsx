"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { InvoiceForm } from "@/components/payments/InvoiceForm";
import { useCreateInvoice } from "@/lib/hooks/usePayments";
import type { InvoiceCreate } from "@/types/payment";

export default function NewInvoicePage() {
  const router = useRouter();
  const createInvoice = useCreateInvoice();

  const handleSubmit = async (data: InvoiceCreate) => {
    try {
      const invoice = await createInvoice.mutateAsync(data);
      // Navigate to invoice detail page
      router.push(`/payments/invoices/${invoice.id}`);
    } catch (error) {
      console.error("Failed to create invoice:", error);
      // TODO: Show error toast
    }
  };

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/payments/invoices">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Create Invoice</h2>
          <p className="text-muted-foreground">Create a new invoice for a patient</p>
        </div>
      </div>

      {/* Invoice Form */}
      <InvoiceForm onSubmit={handleSubmit} isLoading={createInvoice.isPending} />
    </div>
  );
}
