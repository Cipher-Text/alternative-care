"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { useTranslations } from "next-intl";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreatePayment } from "@/lib/hooks/usePayments";
import { Loader2 } from "lucide-react";
import type { PaymentCreate, PaymentMethod } from "@/types/payment";

interface QuickPaymentModalProps {
  open: boolean;
  onClose: () => void;
  patientId?: string;
  patientName?: string;
}

interface PaymentFormData {
  patient_id: string;
  amount: number;
  payment_method: PaymentMethod;
  description?: string;
  payment_date: string;
}

export function QuickPaymentModal({
  open,
  onClose,
  patientId,
  patientName,
}: QuickPaymentModalProps) {
  const t = useTranslations("payFormUi");
  const tb = useTranslations("payBadgeUi");
  const createPayment = useCreatePayment();
  const [selectedPatient, setSelectedPatient] = useState(patientName || "");

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
  } = useForm<PaymentFormData>({
    defaultValues: {
      patient_id: patientId || "",
      payment_method: "cash",
      payment_date: new Date().toISOString().split("T")[0],
    },
  });

  const onSubmit = async (data: PaymentFormData) => {
    try {
      const paymentData: PaymentCreate = {
        patient_id: data.patient_id,
        amount: Number(data.amount),
        payment_method: data.payment_method,
        description: data.description,
        payment_date: data.payment_date,
      };

      await createPayment.mutateAsync(paymentData);
      toast.success(t("recordedOk", { amount: data.amount }));
      reset();
      onClose();
    } catch (error: any) {
      console.error("Failed to create payment:", error);
      toast.error(error?.response?.data?.detail || t("recordFail"));
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{t("modalTitle")}</DialogTitle>
          <DialogDescription>
            {t("modalDesc")}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Patient Selection - Simplified for now */}
          <div className="space-y-2">
            <Label htmlFor="patient_id">
              {t("patientId")} <span className="text-red-500">*</span>
            </Label>
            <Input
              id="patient_id"
              {...register("patient_id", { required: t("patientIdRequired") })}
              placeholder={t("patientIdPlaceholder")}
            />
            {errors.patient_id && (
              <p className="text-sm text-red-500">{errors.patient_id.message}</p>
            )}
            <p className="text-xs text-muted-foreground">
              {t("patientSearchNote")}
            </p>
          </div>

          {/* Amount */}
          <div className="space-y-2">
            <Label htmlFor="amount">
              {t("amountLabel")} <span className="text-red-500">*</span>
            </Label>
            <Input
              id="amount"
              type="number"
              step="0.01"
              min="0"
              {...register("amount", {
                required: t("amountRequired"),
                min: { value: 0, message: t("amountPositive") },
              })}
              placeholder="1000"
            />
            {errors.amount && (
              <p className="text-sm text-red-500">{errors.amount.message}</p>
            )}
          </div>

          {/* Payment Method */}
          <div className="space-y-2">
            <Label htmlFor="payment_method">{t("paymentMethod")}</Label>
            <Select
              defaultValue="cash"
              onValueChange={(value) =>
                setValue("payment_method", value as PaymentMethod)
              }
            >
              <SelectTrigger id="payment_method">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="cash">{tb("method.cash")}</SelectItem>
                <SelectItem value="bkash">{tb("method.bkash")}</SelectItem>
                <SelectItem value="nagad">{tb("method.nagad")}</SelectItem>
                <SelectItem value="rocket">{tb("method.rocket")}</SelectItem>
                <SelectItem value="card">{tb("method.card")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Payment Date */}
          <div className="space-y-2">
            <Label htmlFor="payment_date">{t("paymentDate")}</Label>
            <Input
              id="payment_date"
              type="date"
              {...register("payment_date")}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">{t("descriptionOptional")}</Label>
            <Textarea
              id="description"
              {...register("description")}
              placeholder={t("modalDescPlaceholder")}
              rows={2}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={createPayment.isLoading}
            >
              {t("cancel")}
            </Button>
            <Button type="submit" disabled={createPayment.isLoading}>
              {createPayment.isLoading && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              {t("recordPayment")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
