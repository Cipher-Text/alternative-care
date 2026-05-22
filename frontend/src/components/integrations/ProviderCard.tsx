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
        return 'bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-300 dark:border dark:border-blue-500/30';
      case 'email':
        return 'bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-300 dark:border dark:border-green-500/30';
      case 'payment':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-500/20 dark:text-purple-300 dark:border dark:border-purple-500/30';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-500/20 dark:text-gray-300 dark:border dark:border-gray-500/30';
    }
  };

  return (
    <Card className="p-6 bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700 hover:shadow-lg dark:hover:shadow-indigo-500/10 transition-all duration-200">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {provider.logo_url ? (
            <img
              src={provider.logo_url}
              alt={provider.display_name}
              className="w-12 h-12 object-contain"
            />
          ) : (
            <div className="w-12 h-12 bg-gray-200 dark:bg-slate-700 rounded flex items-center justify-center">
              <span className="text-xl font-bold text-gray-500 dark:text-gray-400">
                {provider.display_name[0]}
              </span>
            </div>
          )}
          <div>
            <h3 className="font-semibold text-lg text-gray-900 dark:text-white">{provider.display_name}</h3>
            <Badge className={getProviderTypeColor(provider.provider_type)}>
              {provider.provider_type.toUpperCase()}
            </Badge>
          </div>
        </div>
        {configured && (
          <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
            <CheckCircle2 className="w-5 h-5" />
            <span className="text-sm font-medium">Configured</span>
          </div>
        )}
      </div>

      <div className="mt-4 flex gap-2">
        {configured ? (
          <Button
            variant="outline"
            className="w-full bg-white dark:bg-slate-700/50 border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700"
            onClick={() => onManage?.(provider.id)}
          >
            <Settings className="w-4 h-4 mr-2" />
            Manage
          </Button>
        ) : (
          <Button
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
            onClick={() => onSetup(provider.id)}
          >
            Setup Integration
          </Button>
        )}
      </div>
    </Card>
  );
}
