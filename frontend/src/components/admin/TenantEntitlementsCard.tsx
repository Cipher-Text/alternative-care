'use client'

import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import {
  useRemoveTenantOverride,
  useSetTenantOverride,
  useTenantEntitlements,
} from '@/lib/hooks/usePlans'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { TenantEntitlementItem } from '@/types/plans'

function limitText(item: TenantEntitlementItem): string {
  if (item.kind === 'feature') return item.enabled ? 'Included' : 'Not included'
  return item.limit === null ? 'Unlimited' : String(item.limit)
}

export function TenantEntitlementsCard({
  tenantId,
  canEdit,
}: {
  tenantId: string
  canEdit: boolean
}) {
  const { data, isLoading } = useTenantEntitlements(tenantId)
  const setOverride = useSetTenantOverride(tenantId)
  const removeOverride = useRemoveTenantOverride(tenantId)

  const [editing, setEditing] = useState<string | null>(null)
  const [enabled, setEnabled] = useState(true)
  const [unlimited, setUnlimited] = useState(false)
  const [limit, setLimit] = useState('')
  const [note, setNote] = useState('')

  const startEdit = (item: TenantEntitlementItem) => {
    setEditing(item.key)
    setEnabled(item.enabled)
    setUnlimited(item.limit === null)
    setLimit(item.limit === null ? '' : String(item.limit))
    setNote('')
  }

  const save = (item: TenantEntitlementItem) => {
    setOverride.mutate(
      {
        key: item.key,
        payload: {
          enabled: item.kind === 'feature' ? enabled : true,
          limit: item.kind === 'feature' || unlimited ? null : Math.max(0, parseInt(limit || '0', 10) || 0),
          note: note.trim() || null,
        },
      },
      { onSuccess: () => setEditing(null) }
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Plan limits &amp; usage</CardTitle>
        <CardDescription>
          Effective limits for this tenant
          {data ? ` (${data.plan} plan${data.expired ? ', expired — Free limits apply' : ''})` : ''}.
          An override replaces the plan value for this tenant only.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading || !data ? (
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Setting</TableHead>
                <TableHead>Limit</TableHead>
                <TableHead>Used</TableHead>
                <TableHead>Source</TableHead>
                {canEdit && <TableHead className="text-right">Actions</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.entitlements.map((item) => (
                <TableRow key={item.key}>
                  <TableCell className="text-sm">
                    {item.label_en}
                    {item.period === 'monthly' && (
                      <span className="ml-1 text-xs text-muted-foreground">(this month)</span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm">
                    {editing === item.key ? (
                      item.kind === 'feature' ? (
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={enabled}
                            onChange={(e) => setEnabled(e.target.checked)}
                          />
                          Included
                        </label>
                      ) : (
                        <div className="flex items-center gap-2">
                          <Input
                            type="number"
                            min={0}
                            className="w-24"
                            aria-label={`${item.label_en} override limit`}
                            value={unlimited ? '' : limit}
                            disabled={unlimited}
                            onChange={(e) => setLimit(e.target.value)}
                          />
                          <label className="flex items-center gap-1 text-xs">
                            <input
                              type="checkbox"
                              checked={unlimited}
                              onChange={(e) => setUnlimited(e.target.checked)}
                            />
                            Unlimited
                          </label>
                        </div>
                      )
                    ) : (
                      limitText(item)
                    )}
                  </TableCell>
                  <TableCell className="text-sm">{item.used ?? '—'}</TableCell>
                  <TableCell>
                    <Badge variant={item.source === 'override' ? 'default' : 'outline'}>
                      {item.source === 'override' ? 'Override' : 'Plan'}
                    </Badge>
                  </TableCell>
                  {canEdit && (
                    <TableCell className="text-right">
                      {editing === item.key ? (
                        <div className="flex flex-col items-end gap-2">
                          <Input
                            className="w-48"
                            placeholder="Note (e.g. founding member)"
                            value={note}
                            onChange={(e) => setNote(e.target.value)}
                          />
                          <div className="flex gap-2">
                            <Button size="sm" onClick={() => save(item)} disabled={setOverride.isLoading}>
                              Save
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => setEditing(null)}>
                              Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-end gap-2">
                          <Button size="sm" variant="outline" onClick={() => startEdit(item)}>
                            Override
                          </Button>
                          {item.source === 'override' && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => removeOverride.mutate(item.key)}
                              disabled={removeOverride.isLoading}
                            >
                              Reset
                            </Button>
                          )}
                        </div>
                      )}
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}
