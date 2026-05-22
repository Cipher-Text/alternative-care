/**
 * Integrations List Component
 * Displays all configured integrations with filters
 */

'use client';

import { useState } from 'react';
import {
  useIntegrations,
  useProviders,
  useDeleteIntegration,
  useSetPrimaryIntegration,
} from '@/lib/hooks/useIntegrations';
import { IntegrationCard } from './IntegrationCard';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Loader2, Plus } from 'lucide-react';
import type { ProviderType } from '@/types/integration';

interface IntegrationsListProps {
  onAdd: () => void;
  onEdit: (integrationId: number) => void;
  onTest: (integrationId: number) => void;
}

export function IntegrationsList({ onAdd, onEdit, onTest }: IntegrationsListProps) {
  const [activeTab, setActiveTab] = useState<'all' | ProviderType>('all');

  const { data: integrations, isLoading } = useIntegrations({
    is_active: true,
  });
  const { data: providers } = useProviders({ is_active: true });

  const deleteIntegration = useDeleteIntegration();
  const setPrimaryIntegration = useSetPrimaryIntegration();

  const handleDelete = async (integrationId: number) => {
    if (confirm('Are you sure you want to delete this integration?')) {
      try {
        await deleteIntegration.mutateAsync(integrationId);
      } catch (error) {
        console.error('Failed to delete integration:', error);
        alert('Failed to delete integration. Please try again.');
      }
    }
  };

  const handleSetPrimary = async (integrationId: number) => {
    try {
      await setPrimaryIntegration.mutateAsync(integrationId);
    } catch (error) {
      console.error('Failed to set primary integration:', error);
      alert('Failed to set primary integration. Please try again.');
    }
  };

  // Create provider lookup map
  const providerMap = new Map(providers?.map((p) => [p.id, p]) || []);

  // Enrich integrations with provider data
  const enrichedIntegrations = integrations?.map((integration) => ({
    ...integration,
    provider: providerMap.get(integration.provider_id),
  })) || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!enrichedIntegrations || enrichedIntegrations.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 mb-4">No integrations configured yet</p>
        <Button onClick={onAdd}>
          <Plus className="w-4 h-4 mr-2" />
          Add Integration
        </Button>
      </div>
    );
  }

  // Filter integrations by tab
  const filteredIntegrations =
    activeTab === 'all'
      ? enrichedIntegrations
      : enrichedIntegrations.filter((i) => i.provider?.provider_type === activeTab);

  // Count integrations by type
  const smsCount = enrichedIntegrations.filter((i) => i.provider?.provider_type === 'sms').length;
  const emailCount = enrichedIntegrations.filter((i) => i.provider?.provider_type === 'email').length;
  const paymentCount = enrichedIntegrations.filter((i) => i.provider?.provider_type === 'payment').length;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
          <TabsList>
            <TabsTrigger value="all">All ({enrichedIntegrations.length})</TabsTrigger>
            <TabsTrigger value="sms">SMS ({smsCount})</TabsTrigger>
            <TabsTrigger value="email">Email ({emailCount})</TabsTrigger>
            <TabsTrigger value="payment">Payment ({paymentCount})</TabsTrigger>
          </TabsList>
        </Tabs>

        <Button onClick={onAdd}>
          <Plus className="w-4 h-4 mr-2" />
          Add Integration
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredIntegrations.map((integration) => (
          <IntegrationCard
            key={integration.id}
            integration={integration}
            onEdit={onEdit}
            onTest={onTest}
            onSetPrimary={handleSetPrimary}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  );
}
