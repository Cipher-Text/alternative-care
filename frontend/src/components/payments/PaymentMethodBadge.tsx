import { Badge } from "@/components/ui/badge";
import { Banknote, CreditCard, Smartphone } from "lucide-react";
import type { PaymentMethod } from "@/types/payment";

interface PaymentMethodBadgeProps {
  method: PaymentMethod;
  className?: string;
}

export function PaymentMethodBadge({ method, className }: PaymentMethodBadgeProps) {
  const config = {
    cash: {
      label: "Cash",
      icon: Banknote,
      variant: "secondary" as const,
      className: "bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-500/20 dark:text-gray-300 dark:border-gray-500/30",
    },
    bkash: {
      label: "bKash",
      icon: Smartphone,
      variant: "default" as const,
      className: "bg-pink-100 text-pink-700 border-pink-200 dark:bg-pink-500/20 dark:text-pink-300 dark:border-pink-500/30",
    },
    nagad: {
      label: "Nagad",
      icon: Smartphone,
      variant: "default" as const,
      className: "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-500/20 dark:text-orange-300 dark:border-orange-500/30",
    },
    rocket: {
      label: "Rocket",
      icon: Smartphone,
      variant: "default" as const,
      className: "bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-500/20 dark:text-purple-300 dark:border-purple-500/30",
    },
    card: {
      label: "Card",
      icon: CreditCard,
      variant: "default" as const,
      className: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-500/20 dark:text-blue-300 dark:border-blue-500/30",
    },
  };

  const { label, icon: Icon, className: methodClassName } = config[method] || config.cash;

  return (
    <Badge variant="outline" className={`${methodClassName} ${className}`}>
      <Icon className="w-3 h-3 mr-1" />
      {label}
    </Badge>
  );
}
