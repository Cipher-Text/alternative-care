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
      className: "bg-green-100 text-green-700 border-green-200 dark:bg-green-500/20 dark:text-green-300 dark:border-green-500/30",
    },
    pending: {
      label: "Pending",
      icon: Clock,
      className: "bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-500/20 dark:text-yellow-300 dark:border-yellow-500/30",
    },
    failed: {
      label: "Failed",
      icon: XCircle,
      className: "bg-red-100 text-red-700 border-red-200 dark:bg-red-500/20 dark:text-red-300 dark:border-red-500/30",
    },
    refunded: {
      label: "Refunded",
      icon: RefreshCw,
      className: "bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-500/20 dark:text-gray-300 dark:border-gray-500/30",
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
