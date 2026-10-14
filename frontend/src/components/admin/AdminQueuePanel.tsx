'use client'

import Link from 'next/link'
import { formatDistanceToNowStrict } from 'date-fns'
import {
  BadgeCheck,
  CalendarClock,
  CheckCircle2,
  Megaphone,
  Loader2,
  MessageSquare,
  TrendingDown,
  TrendingUp,
  UserCheck,
  Wallet,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAdminQueue } from '@/lib/hooks/useAdmin'
import type { AdminQueue, QueueTenant } from '@/types/admin'

const TOPIC: Record<string, string> = {
  general: 'General',
  enterprise: 'Enterprise plan',
  billing: 'Billing or refund',
  report_profile: 'Report a profile',
  other: 'Other',
}

const ago = (iso: string) => formatDistanceToNowStrict(new Date(iso), { addSuffix: true })
const taka = (value: string | number) => `৳${Number(value).toLocaleString()}`

/** What platform staff need to act on, across every clinic. Each card links to where the work is done. */
export function AdminQueuePanel({ enabled }: { enabled: boolean }) {
  const { data: q, isLoading, isError } = useAdminQueue(enabled)

  if (isLoading) {
    return (
      <div className="flex h-32 items-center justify-center" aria-busy="true">
        <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
      </div>
    )
  }
  if (isError || !q) return null // the KPI cards below still work without it

  return (
    <section aria-labelledby="queue-heading" className="space-y-4">
      <div>
        <h2 id="queue-heading" className="text-xl font-semibold text-gray-900 dark:text-white">Needs action</h2>
        <p className="text-sm text-muted-foreground">Open work across all clinics. Each card opens the page where it is done.</p>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
        <ApprovalsCard q={q} />
        <VerificationCard q={q} />
        <ContactCard q={q} />
        <MarketingCard q={q} />
        <RenewalsCard q={q} />
        <RevenueCard q={q} />
      </div>
    </section>
  )
}

function QueueCard({
  title,
  icon: Icon,
  count,
  href,
  action,
  children,
}: {
  title: string
  icon: React.ElementType
  count?: number
  href: string
  action: string
  children: React.ReactNode
}) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Icon className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          {title}
        </CardTitle>
        {count !== undefined && (
          <Badge className={count > 0 ? 'bg-amber-500 text-white hover:bg-amber-500' : ''} variant={count > 0 ? 'default' : 'outline'}>
            {count}
          </Badge>
        )}
      </CardHeader>
      <CardContent className="flex flex-1 flex-col justify-between gap-4">
        <div className="space-y-2 text-sm">{children}</div>
        <Button asChild variant="outline" size="sm" className="self-start">
          <Link href={href}>{action}</Link>
        </Button>
      </CardContent>
    </Card>
  )
}

const Clear = ({ text }: { text: string }) => (
  <p className="flex items-center gap-2 text-muted-foreground">
    <CheckCircle2 className="h-4 w-4 text-emerald-600" aria-hidden="true" />
    {text}
  </p>
)

function TenantRows({ rows, total }: { rows: QueueTenant[]; total: number }) {
  return (
    <>
      <ul className="space-y-2">
        {rows.map((t) => (
          <li key={t.tenant_id} className="flex flex-wrap items-baseline justify-between gap-x-3">
            <span className="min-w-0">
              <Link href={`/admin/clients/${t.tenant_id}`} className="font-medium hover:underline">{t.clinic_name}</Link>
              {t.doctor_name && <span className="block truncate text-muted-foreground">{t.doctor_name}</span>}
            </span>
            <span className="text-xs text-muted-foreground">{ago(t.since)}</span>
          </li>
        ))}
      </ul>
      {total > rows.length && <p className="text-xs text-muted-foreground">and {total - rows.length} more</p>}
    </>
  )
}

function ApprovalsCard({ q }: { q: AdminQueue }) {
  return (
    <QueueCard title="Clinic approvals" icon={UserCheck} count={q.pending_approvals_total} href="/admin/clients" action="Open clients">
      {q.pending_approvals_total === 0 ? <Clear text="No clinics are waiting for approval." /> : <TenantRows rows={q.pending_approvals} total={q.pending_approvals_total} />}
    </QueueCard>
  )
}

function VerificationCard({ q }: { q: AdminQueue }) {
  return (
    <QueueCard title="Directory verification" icon={BadgeCheck} count={q.verification_waiting_total} href="/admin/clients" action="Open clients">
      {q.verification_waiting_total === 0 ? (
        <Clear text="Every listed clinic is verified." />
      ) : (
        <>
          <p className="text-muted-foreground">Listed in the public directory, credentials not yet checked.</p>
          <TenantRows rows={q.verification_waiting} total={q.verification_waiting_total} />
        </>
      )}
    </QueueCard>
  )
}

function ContactCard({ q }: { q: AdminQueue }) {
  const { contact } = q
  return (
    <QueueCard title="Contact messages" icon={MessageSquare} count={contact.new} href="/admin/contact" action="Open messages">
      {contact.new === 0 ? (
        <Clear text="No new messages." />
      ) : (
        <>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(contact.by_topic).map(([topic, n]) => (
              <Badge key={topic} variant="outline">{TOPIC[topic] ?? topic}: {n}</Badge>
            ))}
          </div>
          <ul className="space-y-1">
            {contact.latest.map((m) => (
              <li key={m.id} className="flex justify-between gap-3">
                <span className="truncate">{m.name}</span>
                <span className="shrink-0 text-xs text-muted-foreground">{ago(m.created_at)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </QueueCard>
  )
}

function MarketingCard({ q }: { q: AdminQueue }) {
  const m = q.marketing
  const total = m.needs_draft + m.ready_to_post
  const rows: [string, number, string][] = [
    ['Needs a draft', m.needs_draft, 'You write the post'],
    ['Waiting for the doctor', m.waiting_for_doctor, 'Nothing for you to do yet'],
    ['Ready to post', m.ready_to_post, 'Post it, then paste the link'],
  ]
  return (
    <QueueCard title="Facebook promotion" icon={Megaphone} count={total} href="/admin/marketing" action="Open requests">
      {m.needs_draft + m.waiting_for_doctor + m.ready_to_post === 0 ? (
        <Clear text="No open requests." />
      ) : (
        <ul className="space-y-1.5">
          {rows.map(([label, n, hint]) => (
            <li key={label} className="flex items-baseline justify-between gap-3">
              <span>{label}<span className="block text-xs text-muted-foreground">{hint}</span></span>
              <span className="text-lg font-semibold tabular-nums">{n}</span>
            </li>
          ))}
        </ul>
      )}
    </QueueCard>
  )
}

function RenewalsCard({ q }: { q: AdminQueue }) {
  return (
    <QueueCard title="Plan renewals" icon={CalendarClock} count={q.plans_expiring_total} href="/admin/clients" action="Open clients">
      {q.plans_expiring_total === 0 && q.recently_expired === 0 ? (
        <Clear text="No paid plan ends in the next 14 days." />
      ) : (
        <>
          <ul className="space-y-2">
            {q.plans_expiring.map((p) => (
              <li key={p.tenant_id} className="flex flex-wrap items-baseline justify-between gap-x-3">
                <span className="min-w-0">
                  <Link href={`/admin/clients/${p.tenant_id}`} className="font-medium hover:underline">{p.clinic_name}</Link>
                  <span className="ml-2 text-xs capitalize text-muted-foreground">{p.plan}</span>
                </span>
                <span className={p.days_left <= 3 ? 'font-medium text-amber-700 dark:text-amber-300' : 'text-muted-foreground'}>
                  {p.days_left === 0 ? 'ends today' : `${p.days_left} ${p.days_left === 1 ? 'day' : 'days'} left`}
                </span>
              </li>
            ))}
          </ul>
          {q.plans_expiring_total > q.plans_expiring.length && <p className="text-xs text-muted-foreground">and {q.plans_expiring_total - q.plans_expiring.length} more</p>}
          {q.recently_expired > 0 && <p className="text-xs text-muted-foreground">{q.recently_expired} paid {q.recently_expired === 1 ? 'plan' : 'plans'} ended in the last 7 days.</p>}
        </>
      )}
    </QueueCard>
  )
}

function RevenueCard({ q }: { q: AdminQueue }) {
  const r = q.revenue
  const now = Number(r.this_month)
  const before = Number(r.last_month)
  const up = now >= before
  const problems = r.failed_last_7_days + r.abandoned_checkouts
  return (
    <QueueCard title="Billing" icon={Wallet} count={problems} href="/admin/billing" action="Open billing">
      <div>
        <p className="text-xs text-muted-foreground">Paid this month</p>
        <p className="text-2xl font-bold tabular-nums">{taka(r.this_month)}</p>
        <p className="flex items-center gap-1 text-xs text-muted-foreground">
          {up ? <TrendingUp className="h-3.5 w-3.5 text-emerald-600" aria-hidden="true" /> : <TrendingDown className="h-3.5 w-3.5 text-amber-600" aria-hidden="true" />}
          {taka(r.last_month)} last month · {r.paid_orders_this_month} {r.paid_orders_this_month === 1 ? 'payment' : 'payments'} this month
        </p>
      </div>
      {problems === 0 ? (
        <Clear text="No failed or abandoned checkouts this week." />
      ) : (
        <p className="text-amber-700 dark:text-amber-300">
          Last 7 days: {r.failed_last_7_days} failed, {r.abandoned_checkouts} abandoned.
        </p>
      )}
    </QueueCard>
  )
}

