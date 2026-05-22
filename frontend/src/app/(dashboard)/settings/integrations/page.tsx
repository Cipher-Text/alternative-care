/**
 * Integrations Page
 * Main page for managing integrations
 */

'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ProviderList } from '@/components/integrations/ProviderList';
import { IntegrationsList } from '@/components/integrations/IntegrationsList';
import { IntegrationLogs } from '@/components/integrations/IntegrationLogs';
import { ConfigurationWizard } from '@/components/integrations/ConfigurationWizard';

export default function IntegrationsPage() {
  const [activeTab, setActiveTab] = useState('marketplace');
  const [wizardOpen, setWizardOpen] = useState(false);
  const [selectedProviderId, setSelectedProviderId] = useState<number | null>(null);
  const [selectedIntegrationId, setSelectedIntegrationId] = useState<number | null>(null);

  const handleSetup = (providerId: number) => {
    setSelectedProviderId(providerId);
    setSelectedIntegrationId(null);
    setWizardOpen(true);
  };

  const handleEdit = (integrationId: number) => {
    // TODO: Need to fetch provider_id for this integration
    // For now, we'll open the wizard with just the integration ID
    setSelectedIntegrationId(integrationId);
    setWizardOpen(true);
  };

  const handleTest = (integrationId: number) => {
    // Open wizard in test mode
    setSelectedIntegrationId(integrationId);
    setWizardOpen(true);
  };

  const handleWizardClose = () => {
    setWizardOpen(false);
    setSelectedProviderId(null);
    setSelectedIntegrationId(null);
  };

  const handleWizardSuccess = () => {
    // Switch to My Integrations tab after successful setup
    setActiveTab('my-integrations');
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Integrations</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Connect SMS, email, and payment providers to power your practice
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="marketplace">Provider Marketplace</TabsTrigger>
          <TabsTrigger value="my-integrations">My Integrations</TabsTrigger>
          <TabsTrigger value="logs">Activity Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="marketplace" className="mt-6">
          <ProviderList onSetup={handleSetup} onManage={handleEdit} />
        </TabsContent>

        <TabsContent value="my-integrations" className="mt-6">
          <IntegrationsList
            onAdd={() => setActiveTab('marketplace')}
            onEdit={handleEdit}
            onTest={handleTest}
          />
        </TabsContent>

        <TabsContent value="logs" className="mt-6">
          <IntegrationLogs />
        </TabsContent>
      </Tabs>

      {/* Configuration Wizard */}
      <ConfigurationWizard
        providerId={selectedProviderId}
        integrationId={selectedIntegrationId}
        open={wizardOpen}
        onClose={handleWizardClose}
        onSuccess={handleWizardSuccess}
      />
    </div>
  );
}
