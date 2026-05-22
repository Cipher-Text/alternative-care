/**
 * Provider List Component
 * Lists all available providers with filters
 */

'use client';

import { useState } from 'react';
import { useProviders, useIntegrations } from '@/lib/hooks/useIntegrations';
import { ProviderCard } from './ProviderCard';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2 } from 'lucide-react';
import type { ProviderType } from '@/types/integration';

interface ProviderListProps {
  onSetup: (providerId: number) => void;
  onManage?: (providerId: number) => void;
}

export function ProviderList({ onSetup, onManage }: ProviderListProps) {
  const [activeTab, setActiveTab] = useState<'all' | ProviderType>('all');

  const { data: providers, isLoading: loadingProviders } = useProviders({
    is_active: true,
  });

  const { data: integrations } = useIntegrations();

  if (loadingProviders) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600 dark:text-indigo-400" />
      </div>
    );
  }

  if (!providers || providers.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 dark:text-gray-400">No providers available</p>
      </div>
    );
  }

  // Create a map of configured provider IDs
  const configuredProviderIds = new Set(
    integrations?.map((integration) => integration.provider_id) || []
  );

  // Filter providers by tab
  const filteredProviders =
    activeTab === 'all'
      ? providers
      : providers.filter((p) => p.provider_type === activeTab);

  // Count providers by type
  const smsCount = providers.filter((p) => p.provider_type === 'sms').length;
  const emailCount = providers.filter((p) => p.provider_type === 'email').length;
  const paymentCount = providers.filter((p) => p.provider_type === 'payment').length;

  return (
    <div>
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
        <TabsList className="mb-6">
          <TabsTrigger value="all">All ({providers.length})</TabsTrigger>
          <TabsTrigger value="sms">SMS ({smsCount})</TabsTrigger>
          <TabsTrigger value="email">Email ({emailCount})</TabsTrigger>
          <TabsTrigger value="payment">Payment ({paymentCount})</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProviders.map((provider) => (
              <ProviderCard
                key={provider.id}
                provider={provider}
                configured={configuredProviderIds.has(provider.id)}
                onSetup={onSetup}
                onManage={onManage}
              />
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
