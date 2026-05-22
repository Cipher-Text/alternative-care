/**
 * Provider Card Component
 * Displays an integration provider with setup button
 */

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { IntegrationProviderListItem } from '@/types/integration';
import { CheckCircle2, Settings } from 'lucide-react';

interface ProviderCardProps {
  provider: IntegrationProviderListItem;
  configured?: boolean;
  onSetup: (providerId: number) => void;
  onManage?: (providerId: number) => void;
}

export function ProviderCard({
  provider,
  configured = false,
  onSetup,
  onManage,
}: ProviderCardProps) {
  const getProviderTypeColor = (type: string) => {
    switch (type) {
      case 'sms':
        return 'bg-blue-100 text-blue-800';
      case 'email':
        return 'bg-green-100 text-green-800';
      case 'payment':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {provider.logo_url ? (
            <img
              src={provider.logo_url}
              alt={provider.display_name}
              className="w-12 h-12 object-contain"
            />
          ) : (
            <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
              <span className="text-xl font-bold text-gray-500">
                {provider.display_name[0]}
              </span>
            </div>
          )}
          <div>
            <h3 className="font-semibold text-lg">{provider.display_name}</h3>
            <Badge className={getProviderTypeColor(provider.provider_type)}>
              {provider.provider_type.toUpperCase()}
            </Badge>
          </div>
        </div>
        {configured && (
          <div className="flex items-center gap-1 text-green-600">
            <CheckCircle2 className="w-5 h-5" />
            <span className="text-sm font-medium">Configured</span>
          </div>
        )}
      </div>

      <div className="mt-4 flex gap-2">
        {configured ? (
          <Button
            variant="outline"
            className="w-full"
            onClick={() => onManage?.(provider.id)}
          >
            <Settings className="w-4 h-4 mr-2" />
            Manage
          </Button>
        ) : (
          <Button className="w-full" onClick={() => onSetup(provider.id)}>
            Setup Integration
          </Button>
        )}
      </div>
    </Card>
  );
}
