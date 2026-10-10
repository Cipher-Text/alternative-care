'use client'

import { useState } from 'react'
import { Loader2, ShieldAlert } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useAdminPlans, usePlanAudit, useUpdatePlan } from '@/lib/hooks/usePlans'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { CatalogItem, PlanConfig, PlanUpdateRequest } from '@/types/plans'

interface EntitlementDraft {
  enabled: boolean
  unlimited: boolean
  limit: string
}

interface PlanDraft {
  name_en: string
  name_bn: string
  description_en: string
  description_bn: string
  price_monthly: string
  price_yearly: string
  is_public: boolean
  entitlements: Record<string, EntitlementDraft>
}

function toDraft(plan: PlanConfig): PlanDraft {
  return {
    name_en: plan.name_en,
    name_bn: plan.name_bn ?? '',
    description_en: plan.description_en ?? '',
    description_bn: plan.description_bn ?? '',
    price_monthly: plan.price_monthly ?? '',
    price_yearly: plan.price_yearly ?? '',
    is_public: plan.is_public,
    entitlements: Object.fromEntries(
      plan.entitlements.map((e) => [
        e.key,
        { enabled: e.enabled, unlimited: e.limit === null, limit: e.limit === null ? '' : String(e.limit) },
      ])
    ),
  }
}

function toRequest(plan: PlanConfig, draft: PlanDraft, catalog: CatalogItem[]): PlanUpdateRequest {
  return {
    name_en: draft.name_en.trim(),
    name_bn: draft.name_bn.trim() || null,
    description_en: draft.description_en.trim() || null,
    description_bn: draft.description_bn.trim() || null,
    price_monthly: draft.price_monthly.trim() || null,
    price_yearly: draft.price_yearly.trim() || null,
    currency: plan.currency,
    is_public: draft.is_public,
    entitlements: catalog.map((item) => {
      const d = draft.entitlements[item.key]
      if (item.kind === 'feature') return { key: item.key, enabled: d.enabled, limit: null }
      return {
        key: item.key,
        enabled: true,
        limit: d.unlimited ? null : Math.max(0, parseInt(d.limit || '0', 10) || 0),
      }
    }),
  }
}

function PlanEditor({
  plan,
  catalog,
  readOnly,
}: {
  plan: PlanConfig
  catalog: CatalogItem[]
  readOnly: boolean
}) {
  const [draft, setDraft] = useState<PlanDraft>(() => toDraft(plan))
  const update = useUpdatePlan()
  const dirty = JSON.stringify(draft) !== JSON.stringify(toDraft(plan))

  const setField = <K extends keyof PlanDraft>(key: K, value: PlanDraft[K]) =>
    setDraft((d) => ({ ...d, [key]: value }))
  const setEntitlement = (key: string, patch: Partial<EntitlementDraft>) =>
    setDraft((d) => ({
      ...d,
      entitlements: { ...d.entitlements, [key]: { ...d.entitlements[key], ...patch } },
    }))

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-xl">{plan.name_en}</CardTitle>
          <Badge variant="outline">
            {plan.tenant_count} tenant{plan.tenant_count === 1 ? '' : 's'}
          </Badge>
        </div>
        <CardDescription className="font-mono text-xs">{plan.key}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor={`${plan.key}-name`}>Name (English)</Label>
          <Input
            id={`${plan.key}-name`}
            value={draft.name_en}
            disabled={readOnly}
            onChange={(e) => setField('name_en', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${plan.key}-name-bn`}>Name (Bengali)</Label>
          <Input
            id={`${plan.key}-name-bn`}
            value={draft.name_bn}
            disabled={readOnly}
            onChange={(e) => setField('name_bn', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${plan.key}-desc`}>Tagline (English)</Label>
          <Textarea
            id={`${plan.key}-desc`}
            rows={2}
            value={draft.description_en}
            disabled={readOnly}
            onChange={(e) => setField('description_en', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${plan.key}-desc-bn`}>Tagline (Bengali)</Label>
          <Textarea
            id={`${plan.key}-desc-bn`}
            rows={2}
            value={draft.description_bn}
            disabled={readOnly}
            onChange={(e) => setField('description_bn', e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor={`${plan.key}-pm`}>Monthly ({plan.currency})</Label>
            <Input
              id={`${plan.key}-pm`}
              inputMode="decimal"
              placeholder="Contact us"
              value={draft.price_monthly}
              disabled={readOnly}
              onChange={(e) => setField('price_monthly', e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor={`${plan.key}-py`}>Yearly ({plan.currency})</Label>
            <Input
              id={`${plan.key}-py`}
              inputMode="decimal"
              placeholder="Contact us"
              value={draft.price_yearly}
              disabled={readOnly}
              onChange={(e) => setField('price_yearly', e.target.value)}
            />
          </div>
        </div>
        <p className="-mt-3 text-xs text-muted-foreground">
          Leave a price empty to show &quot;Contact us&quot; on the public pricing page.
        </p>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={draft.is_public}
            disabled={readOnly}
            onChange={(e) => setField('is_public', e.target.checked)}
          />
          Show on the public pricing page
        </label>

        <div className="space-y-3 border-t pt-4">
          <p className="text-sm font-medium">Limits &amp; features</p>
          {catalog.map((item) => {
            const d = draft.entitlements[item.key]
            return (
              <div key={item.key} className="space-y-1">
                <Label className="text-sm">{item.label_en}</Label>
                {item.kind === 'feature' ? (
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={d.enabled}
                      disabled={readOnly}
                      onChange={(e) => setEntitlement(item.key, { enabled: e.target.checked })}
                    />
                    Included
                  </label>
                ) : (
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <Input
                      type="number"
                      min={0}
                      aria-label={`${item.label_en} limit`}
                      className="w-28"
                      value={d.unlimited ? '' : d.limit}
                      placeholder={d.unlimited ? '∞' : '0'}
                      disabled={readOnly || d.unlimited}
                      onChange={(e) => setEntitlement(item.key, { limit: e.target.value })}
                    />
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={d.unlimited}
                        disabled={readOnly}
                        onChange={(e) => setEntitlement(item.key, { unlimited: e.target.checked })}
                      />
                      Unlimited
                    </label>
                    <span className="w-full text-xs text-muted-foreground">{item.unit_en}</span>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {!readOnly && (
          <Button
            className="w-full"
            disabled={!dirty || update.isLoading}
            onClick={() => update.mutate({ key: plan.key, payload: toRequest(plan, draft, catalog) })}
          >
            {update.isLoading ? 'Saving...' : dirty ? 'Save changes' : 'No changes'}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

function describe(entry: { old_value: string | null; new_value: string | null }) {
  const show = (v: string | null) => (v === null || v === '' ? '—' : v)
  return `${show(entry.old_value)} → ${show(entry.new_value)}`
}

export default function AdminPlansPage() {
  const user = useAuthStore((state) => state.user)
  const isAdmin = user?.role === 'admin'
  const { data, isLoading } = useAdminPlans()
  const { data: audit } = usePlanAudit()

  if (user && user.role !== 'admin' && user.role !== 'operator') {
    return (
      <Card>
        <CardContent className="flex items-center gap-3 p-6">
          <ShieldAlert className="h-5 w-5 text-red-500" />
          Platform admin access required.
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Plans &amp; Pricing</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Configure what each plan costs and allows. Changes apply immediately to every tenant on
          the plan and to the public pricing page. A tenant is never blocked from data it already
          has; limits apply to creating new records.
        </p>
        {!isAdmin && (
          <p className="mt-2 text-sm text-amber-600">Read-only: only platform admins can edit plans.</p>
        )}
      </div>

      {isLoading || !data ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          {data.plans.map((plan) => (
            <PlanEditor
              // Remount with fresh draft state whenever the saved plan changes.
              key={`${plan.key}-${JSON.stringify(plan)}`}
              plan={plan}
              catalog={data.catalog}
              readOnly={!isAdmin}
            />
          ))}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Change history</CardTitle>
          <CardDescription>Who changed what, most recent first.</CardDescription>
        </CardHeader>
        <CardContent>
          {!audit || audit.length === 0 ? (
            <p className="text-sm text-muted-foreground">No changes yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>When</TableHead>
                  <TableHead>Scope</TableHead>
                  <TableHead>Setting</TableHead>
                  <TableHead>Change</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {audit.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="whitespace-nowrap text-xs">
                      {new Date(entry.changed_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-xs">
                      {entry.plan_key
                        ? `Plan: ${entry.plan_key}`
                        : `Tenant: ${entry.tenant_id?.slice(0, 8)}…`}
                    </TableCell>
                    <TableCell className="text-xs">
                      {[entry.entitlement_key, entry.field].filter(Boolean).join(' · ')}
                    </TableCell>
                    <TableCell className="font-mono text-xs">{describe(entry)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
