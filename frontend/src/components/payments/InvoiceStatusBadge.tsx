import { Badge } from "@/components/ui/badge";
import { FileText, Send, CheckCircle, AlertCircle, XCircle } from "lucide-react";
import type { InvoiceStatus } from "@/types/payment";

interface InvoiceStatusBadgeProps {
  status: InvoiceStatus;
  className?: string;
}

export function InvoiceStatusBadge({ status, className }: InvoiceStatusBadgeProps) {
  const config = {
    draft: {
      label: "Draft",
      icon: FileText,
      className: "bg-gray-100 text-gray-700",
    },
    sent: {
      label: "Sent",
      icon: Send,
      className: "bg-blue-100 text-blue-700",
    },
    paid: {
      label: "Paid",
      icon: CheckCircle,
      className: "bg-green-100 text-green-700",
    },
    overdue: {
      label: "Overdue",
      icon: AlertCircle,
      className: "bg-red-100 text-red-700",
    },
    cancelled: {
      label: "Cancelled",
      icon: XCircle,
      className: "bg-gray-100 text-gray-500",
    },
  };

  const { label, icon: Icon, className: statusClassName } = config[status] || config.draft;

  return (
    <Badge variant="outline" className={`${statusClassName} ${className}`}>
      <Icon className="w-3 h-3 mr-1" />
      {label}
    </Badge>
  );
}
