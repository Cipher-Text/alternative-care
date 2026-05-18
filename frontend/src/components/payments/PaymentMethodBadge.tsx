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
      className: "bg-gray-100 text-gray-700",
    },
    bkash: {
      label: "bKash",
      icon: Smartphone,
      variant: "default" as const,
      className: "bg-pink-100 text-pink-700",
    },
    nagad: {
      label: "Nagad",
      icon: Smartphone,
      variant: "default" as const,
      className: "bg-orange-100 text-orange-700",
    },
    rocket: {
      label: "Rocket",
      icon: Smartphone,
      variant: "default" as const,
      className: "bg-purple-100 text-purple-700",
    },
    card: {
      label: "Card",
      icon: CreditCard,
      variant: "default" as const,
      className: "bg-blue-100 text-blue-700",
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
