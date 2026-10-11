"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import toast from "react-hot-toast";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { InvoiceForm } from "@/components/payments/InvoiceForm";
import { useCreateInvoice } from "@/lib/hooks/usePayments";
import type { InvoiceCreate } from "@/types/payment";

export default function NewInvoicePage() {
  const router = useRouter();
  const t = useTranslations("payInvoiceUi");
  const createInvoice = useCreateInvoice();

  const handleSubmit = async (data: InvoiceCreate) => {
    try {
      const invoice = await createInvoice.mutateAsync(data);
      toast.success(t("createdOk"));
      // Navigate to invoice detail page
      router.push(`/payments/invoices/${invoice.id}`);
    } catch (error: any) {
      console.error("Failed to create invoice:", error);
      toast.error(error?.response?.data?.detail || t("createdFail"));
    }
  };

  return (
    <div className="flex-1 space-y-6 p-4 pt-4 sm:p-8 sm:pt-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
            <Link href="/payments/invoices" aria-label={t("back")}>
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t("newTitle")}</h1>
          <p className="text-muted-foreground">{t("newSubtitle")}</p>
        </div>
      </div>

      {/* Invoice Form */}
      <InvoiceForm onSubmit={handleSubmit} isLoading={createInvoice.isLoading} />
    </div>
  );
}
