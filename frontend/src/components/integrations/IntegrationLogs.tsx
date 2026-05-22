/**
 * Integration Logs Component
 * Displays audit trail of integration transactions
 */

'use client';

import { useState } from 'react';
import { useIntegrationLogs, useIntegrations } from '@/lib/hooks/useIntegrations';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Loader2, Search, RefreshCw } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { LogFilters } from '@/types/integration';

export function IntegrationLogs() {
  const [filters, setFilters] = useState<LogFilters>({
    limit: 50,
    offset: 0,
  });

  const [searchRecipient, setSearchRecipient] = useState('');

  const { data: logs, isLoading, refetch } = useIntegrationLogs(filters);
  const { data: integrations } = useIntegrations();

  const handleFilterChange = (key: keyof LogFilters, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value === 'all' ? undefined : value,
      offset: 0, // Reset pagination when filters change
    }));
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Implement search logic if needed
    refetch();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge className="bg-green-100 text-green-800">Success</Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">Failed</Badge>;
      case 'pending':
        return <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getTransactionTypeLabel = (type: string) => {
    switch (type) {
      case 'sms_sent':
        return 'SMS Sent';
      case 'email_sent':
        return 'Email Sent';
      case 'payment_initiated':
        return 'Payment Initiated';
      case 'payment_completed':
        return 'Payment Completed';
      case 'payment_failed':
        return 'Payment Failed';
      default:
        return type;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <Label htmlFor="integration">Integration</Label>
            <Select
              value={filters.integration_id?.toString() || 'all'}
              onValueChange={(value) =>
                handleFilterChange('integration_id', value === 'all' ? undefined : parseInt(value))
              }
            >
              <SelectTrigger id="integration">
                <SelectValue placeholder="All Integrations" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Integrations</SelectItem>
                {integrations?.map((integration) => (
                  <SelectItem key={integration.id} value={integration.id.toString()}>
                    {integration.display_name || `Integration #${integration.id}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="transaction_type">Transaction Type</Label>
            <Select
              value={filters.transaction_type || 'all'}
              onValueChange={(value) => handleFilterChange('transaction_type', value)}
            >
              <SelectTrigger id="transaction_type">
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="sms_sent">SMS Sent</SelectItem>
                <SelectItem value="email_sent">Email Sent</SelectItem>
                <SelectItem value="payment_initiated">Payment Initiated</SelectItem>
                <SelectItem value="payment_completed">Payment Completed</SelectItem>
                <SelectItem value="payment_failed">Payment Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="status">Status</Label>
            <Select
              value={filters.status || 'all'}
              onValueChange={(value) => handleFilterChange('status', value)}
            >
              <SelectTrigger id="status">
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="success">Success</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-end">
            <Button
              variant="outline"
              className="w-full"
              onClick={() => refetch()}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </Card>

      {/* Logs Table */}
      <Card>
        {!logs || logs.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No logs found</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Transaction Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Recipient</TableHead>
                <TableHead>Reference</TableHead>
                <TableHead>Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="font-medium">
                    {getTransactionTypeLabel(log.transaction_type)}
                  </TableCell>
                  <TableCell>{getStatusBadge(log.status)}</TableCell>
                  <TableCell>
                    {log.recipient ? (
                      <span className="font-mono text-sm">{log.recipient}</span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {log.external_reference ? (
                      <span className="font-mono text-xs">{log.external_reference}</span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-gray-600">
                    {formatDistanceToNow(new Date(log.created_at), {
                      addSuffix: true,
                    })}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      {/* Pagination */}
      {logs && logs.length >= (filters.limit || 50) && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            disabled={!filters.offset || filters.offset === 0}
            onClick={() =>
              setFilters((prev) => ({
                ...prev,
                offset: Math.max(0, (prev.offset || 0) - (prev.limit || 50)),
              }))
            }
          >
            Previous
          </Button>
          <Button
            variant="outline"
            onClick={() =>
              setFilters((prev) => ({
                ...prev,
                offset: (prev.offset || 0) + (prev.limit || 50),
              }))
            }
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
