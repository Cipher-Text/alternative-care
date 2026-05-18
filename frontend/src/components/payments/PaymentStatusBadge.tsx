import { Badge } from "@/components/ui/badge";
import { CheckCircle, Clock, XCircle, RefreshCw } from "lucide-react";
import type { PaymentStatus } from "@/types/payment";

interface PaymentStatusBadgeProps {
  status: PaymentStatus;
  className?: string;
}

export function PaymentStatusBadge({ status, className }: PaymentStatusBadgeProps) {
  const config = {
    paid: {
      label: "Paid",
      icon: CheckCircle,
      className: "bg-green-100 text-green-700",
    },
    pending: {
      label: "Pending",
      icon: Clock,
      className: "bg-yellow-100 text-yellow-700",
    },
    failed: {
      label: "Failed",
      icon: XCircle,
      className: "bg-red-100 text-red-700",
    },
    refunded: {
      label: "Refunded",
      icon: RefreshCw,
      className: "bg-gray-100 text-gray-700",
    },
  };

  const { label, icon: Icon, className: statusClassName } = config[status] || config.paid;

  return (
    <Badge variant="outline" className={`${statusClassName} ${className}`}>
      <Icon className="w-3 h-3 mr-1" />
      {label}
    </Badge>
  );
}
