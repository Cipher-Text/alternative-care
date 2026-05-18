"use client";

import { useState } from "react";
import { useForm, useFieldArray } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Trash2, Loader2 } from "lucide-react";
import type { InvoiceCreate, InvoiceItem } from "@/types/payment";

interface InvoiceFormProps {
  onSubmit: (data: InvoiceCreate) => Promise<void>;
  isLoading?: boolean;
  defaultValues?: Partial<InvoiceCreate>;
}

interface InvoiceFormData {
  patient_id: string;
  items: InvoiceItem[];
  notes?: string;
  issue_date: string;
  due_date?: string;
}

export function InvoiceForm({ onSubmit, isLoading, defaultValues }: InvoiceFormProps) {
  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<InvoiceFormData>({
    defaultValues: {
      patient_id: defaultValues?.patient_id || "",
      items: defaultValues?.items || [{ description: "", quantity: 1, unit_price: 0, total: 0 }],
      notes: defaultValues?.notes || "",
      issue_date: defaultValues?.issue_date || new Date().toISOString().split("T")[0],
      due_date: defaultValues?.due_date || "",
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "items",
  });

  const items = watch("items");

  // Calculate totals
  const subtotal = items.reduce((sum, item) => {
    const qty = Number(item.quantity) || 0;
    const price = Number(item.unit_price) || 0;
    return sum + qty * price;
  }, 0);

  const handleFormSubmit = async (data: InvoiceFormData) => {
    // Calculate totals for each item
    const itemsWithTotals = data.items.map((item) => ({
      ...item,
      quantity: Number(item.quantity),
      unit_price: Number(item.unit_price),
      total: Number(item.quantity) * Number(item.unit_price),
    }));

    const invoiceData: InvoiceCreate = {
      patient_id: data.patient_id,
      amount: subtotal,
      items: itemsWithTotals,
      notes: data.notes,
      issue_date: data.issue_date,
      due_date: data.due_date || undefined,
    };

    await onSubmit(invoiceData);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Basic Info */}
      <Card>
        <CardHeader>
          <CardTitle>Invoice Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Patient ID */}
            <div className="space-y-2">
              <Label htmlFor="patient_id">
                Patient ID <span className="text-red-500">*</span>
              </Label>
              <Input
                id="patient_id"
                {...register("patient_id", { required: "Patient ID is required" })}
                placeholder="Enter patient ID"
              />
              {errors.patient_id && (
                <p className="text-sm text-red-500">{errors.patient_id.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Patient search autocomplete coming soon
              </p>
            </div>

            {/* Issue Date */}
            <div className="space-y-2">
              <Label htmlFor="issue_date">Issue Date</Label>
              <Input id="issue_date" type="date" {...register("issue_date")} />
            </div>
          </div>

          {/* Due Date */}
          <div className="space-y-2">
            <Label htmlFor="due_date">Due Date (Optional)</Label>
            <Input id="due_date" type="date" {...register("due_date")} />
          </div>
        </CardContent>
      </Card>

      {/* Items */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Invoice Items</CardTitle>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                append({ description: "", quantity: 1, unit_price: 0, total: 0 })
              }
            >
              <Plus className="mr-2 h-4 w-4" />
              Add Item
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {fields.map((field, index) => {
              const qty = Number(items[index]?.quantity) || 0;
              const price = Number(items[index]?.unit_price) || 0;
              const itemTotal = qty * price;

              return (
                <div key={field.id} className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Item {index + 1}</span>
                    {fields.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => remove(index)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    )}
                  </div>

                  <div className="grid gap-3 md:grid-cols-4">
                    {/* Description */}
                    <div className="md:col-span-2 space-y-2">
                      <Label htmlFor={`items.${index}.description`}>Description *</Label>
                      <Input
                        {...register(`items.${index}.description`, {
                          required: "Description is required",
                        })}
                        placeholder="e.g., Consultation fee"
                      />
                      {errors.items?.[index]?.description && (
                        <p className="text-sm text-red-500">
                          {errors.items[index]?.description?.message}
                        </p>
                      )}
                    </div>

                    {/* Quantity */}
                    <div className="space-y-2">
                      <Label htmlFor={`items.${index}.quantity`}>Qty *</Label>
                      <Input
                        type="number"
                        min="1"
                        step="1"
                        {...register(`items.${index}.quantity`, {
                          required: "Quantity is required",
                          min: 1,
                        })}
                      />
                    </div>

                    {/* Unit Price */}
                    <div className="space-y-2">
                      <Label htmlFor={`items.${index}.unit_price`}>Price *</Label>
                      <Input
                        type="number"
                        min="0"
                        step="0.01"
                        {...register(`items.${index}.unit_price`, {
                          required: "Price is required",
                          min: 0,
                        })}
                      />
                    </div>
                  </div>

                  {/* Item Total */}
                  <div className="flex justify-end">
                    <span className="text-sm font-medium">
                      Total: ৳{itemTotal.toFixed(2)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Subtotal */}
          <div className="mt-6 pt-4 border-t">
            <div className="flex justify-end space-y-2">
              <div className="w-64 space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Subtotal:</span>
                  <span className="font-medium">৳{subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-lg font-bold pt-2 border-t">
                  <span>Total:</span>
                  <span>৳{subtotal.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notes */}
      <Card>
        <CardHeader>
          <CardTitle>Additional Notes</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            {...register("notes")}
            placeholder="Add any additional notes or payment terms..."
            rows={3}
          />
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-end gap-4">
        <Button type="button" variant="outline" disabled={isLoading}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading || subtotal === 0}>
          {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Create Invoice
        </Button>
      </div>
    </form>
  );
}
