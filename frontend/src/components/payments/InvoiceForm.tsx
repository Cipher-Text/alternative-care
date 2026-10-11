"use client";

import { useForm } from "react-hook-form";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { usePayments } from "@/lib/hooks/usePayments";
import type { InvoiceCreate } from "@/types/payment";

interface InvoiceFormProps {
  onSubmit: (data: InvoiceCreate) => Promise<void>;
  isLoading?: boolean;
  defaultValues?: Partial<InvoiceCreate>;
}

interface InvoiceFormData {
  payment_id: string;
  due_date?: string;
}

export function InvoiceForm({ onSubmit, isLoading, defaultValues }: InvoiceFormProps) {
  const t = useTranslations("payFormUi");
  const { data: payments, isLoading: paymentsLoading } = usePayments({ limit: 100 });
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<InvoiceFormData>({
    defaultValues: {
      payment_id: defaultValues?.payment_id || "",
      due_date: defaultValues?.due_date || "",
    },
  });

  const handleFormSubmit = async (data: InvoiceFormData) => {
    await onSubmit({ payment_id: data.payment_id, due_date: data.due_date || undefined });
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("invoiceInfo")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">{t("invoiceForPaymentNote")}</p>
          <div className="space-y-2">
            <Label htmlFor="payment_id">
              {t("paymentLabel")} <span className="text-red-500">*</span>
            </Label>
            <select
              id="payment_id"
              disabled={paymentsLoading}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              {...register("payment_id", { required: t("paymentRequired") })}
            >
              <option value="">{t("paymentPlaceholder")}</option>
              {(payments ?? []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.patient_name ?? p.patient_id.slice(0, 8)} — ৳{Number(p.amount).toLocaleString()} —{" "}
                  {p.payment_date}
                </option>
              ))}
            </select>
            {errors.payment_id && (
              <p className="text-sm text-red-500">{errors.payment_id.message}</p>
            )}
            {!paymentsLoading && (payments ?? []).length === 0 && (
              <p className="text-sm text-muted-foreground">{t("noPayments")}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="due_date">{t("dueDateOptional")}</Label>
            <Input id="due_date" type="date" {...register("due_date")} />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-4">
        <Button type="submit" disabled={isLoading}>
          {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {t("createInvoice")}
        </Button>
      </div>
    </form>
  );
}
