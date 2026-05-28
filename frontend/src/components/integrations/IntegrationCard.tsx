/**
 * Integration Card Component
 * Displays a configured integration with management actions
 */

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { getIntegrationLogoUrl } from '@/lib/integration-logos';
import type { TenantIntegrationListItem, IntegrationProviderListItem } from '@/types/integration';
import {
  CheckCircle2,
  XCircle,
  Star,
  MoreVertical,
  Settings,
  Trash2,
  TestTube,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

// Extended type that combines list item with provider data
type IntegrationCardData = TenantIntegrationListItem & {
  provider?: IntegrationProviderListItem;
};

interface IntegrationCardProps {
  integration: IntegrationCardData;
  onEdit: (integrationId: number) => void;
  onTest: (integrationId: number) => void;
  onSetPrimary: (integrationId: number) => void;
  onDelete: (integrationId: number) => void;
}

export function IntegrationCard({
  integration,
  onEdit,
  onTest,
  onSetPrimary,
  onDelete,
}: IntegrationCardProps) {
  const logoUrl = getIntegrationLogoUrl(integration.provider);

  const getStatusColor = (status: string | null) => {
    switch (status) {
      case 'success':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string | null) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4" />;
      case 'failed':
        return <XCircle className="w-4 h-4" />;
      default:
        return null;
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3 flex-1">
          {logoUrl && integration.provider && (
            <img
              src={logoUrl}
              alt={integration.provider.display_name}
              className="w-10 h-10 object-contain"
            />
          )}
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold">
                {integration.display_name || integration.provider?.display_name}
              </h3>
              {integration.is_primary && (
                <Badge variant="default" className="flex items-center gap-1">
                  <Star className="w-3 h-3" />
                  Primary
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline">
                {integration.provider?.provider_type.toUpperCase()}
              </Badge>
              <Badge variant={integration.is_active ? 'default' : 'secondary'}>
                {integration.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreVertical className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onEdit(integration.id)}>
              <Settings className="w-4 h-4 mr-2" />
              Edit Configuration
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onTest(integration.id)}>
              <TestTube className="w-4 h-4 mr-2" />
              Test Connection
            </DropdownMenuItem>
            {!integration.is_primary && (
              <DropdownMenuItem onClick={() => onSetPrimary(integration.id)}>
                <Star className="w-4 h-4 mr-2" />
                Set as Primary
              </DropdownMenuItem>
            )}
            <DropdownMenuItem
              onClick={() => onDelete(integration.id)}
              className="text-red-600"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Test Status */}
      {integration.test_status && (
        <div className="flex items-center gap-2 text-sm">
          <span className={getStatusColor(integration.test_status)}>
            {getStatusIcon(integration.test_status)}
          </span>
          <span className="text-gray-600">
            {integration.test_status === 'success' ? 'Test passed' : 'Test failed'}
          </span>
        </div>
      )}

      {/* Created At */}
      <div className="text-xs text-gray-500 mt-2">
        Created {formatDistanceToNow(new Date(integration.created_at), { addSuffix: true })}
      </div>
    </Card>
  );
}
