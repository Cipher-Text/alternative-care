# Billing, platform integrations and messaging credits — spec (draft)

Status: **decisions recorded 2026-10-12; plan values and several details still open.** Step 2 of §5
(platform providers from env + credit ledger + charged send routes) is built. Step 3 is built
against a **fake gateway only** (§8); SSLCommerz and bKash are not. It extends `pricing-usage-onboarding-2026-10.md` (§2.3 subscription lifecycle)
and `public-site-strategy-2026-10.md` (§6.3 listing benefit).

## 1. Decided

1. **Plan first, then payments.** Nothing is built until the plans (limits, prices) are settled.
2. **Integrations are platform-level, not per clinic.** Only platform admins operate third-party providers;
   clinics never enter provider credentials. SMS and email are sent through the platform's providers.
3. **Credentials and provider choice come from environment variables**, not database tables. The admin
   integrations page becomes a read-only status page (configured or not, provider balance, test send);
   it never shows a secret. Production refuses to start if a required key is missing. The old
   `tenant_integrations` credentials and their encryption key are retired, with a migration.
   Not secrets, still in the database and admin-editable: plan prices and allowances, top-up packs,
   clinic balances and the ledger, send and payment logs.
4. **Email provider: Resend** (already supported: `EMAIL_PROVIDER=resend`, `RESEND_API_KEY`,
   `EMAIL_FROM_ADDRESS`). Revisit Amazon SES at volume; it works through the existing generic SMTP option.
   Needs a sending domain with SPF, DKIM and DMARC, ideally a subdomain for system mail.
5. **Payment gateways: both SSLCommerz and bKash**, behind one provider interface. Sandbox credentials
   are supplied by the product owner; live keys are a separate deploy-time step.
6. **Billing model: prepaid periods (1 month / 1 year), manual renewal.** The plan activates automatically
   when the gateway confirms payment, runs to the paid-until date, reminders go out before expiry, and the
   existing expiry fallback moves the clinic to Free. No auto-recurring charges in v1.

7. **The clinic pays** (decided 2026-10-12). The subscription, the credit balance and every receipt belong
   to the clinic (tenant), not to an individual doctor. Consequences: seats (doctors in the clinic) are
   a plan limit the clinic buys; receipts and invoices are issued to the clinic name; only doctors can
   buy or renew (receptionists cannot); the payer's name and phone are recorded per order for support.

8. **Every limit, including Free's, is defined in the plan configuration** (admin plan editor and the
   `plan_entitlements` table), never hardcoded. Code defaults in `app/core/entitlements.py` only apply
   until an admin stores a value; the pricing page renders from the stored values. Enforcement already
   exists for patients, seats, SMS, invoicing, AI and the directory listing; new limits (monthly email,
   credit balances) follow the same mechanism.

## 2. Messaging credits (SMS and email)

- A clinic has a balance per channel made of (a) the **plan allowance**, granted monthly from the plan's
  `monthly_sms` / new `monthly_email` entitlement, and (b) **purchased credits** from top-up packs.
- Sends use the allowance first, then purchased credits. Every change is an append-only ledger row
  (grant, purchase, use, refund, adjustment, expiry) with the balance after it.
- A send reserves a credit atomically (row lock) so two sends cannot spend the last credit; a failed or
  bounced send refunds it.
- At zero the API returns a structured "buy credits" error that the UI turns into a purchase prompt.
- Top-up packs (name, channel, quantity, price) are admin-editable. They are paid through the same
  gateway checkout as subscriptions and credited only on a confirmed payment, exactly once even if the
  gateway notification repeats.
- Admin view: each provider's own balance with a low-balance alert, and credits sold against provider cost.

## 3. Payments scope

Only AltCare's own revenue (subscriptions and top-ups) is collected through the platform merchant
accounts. Clinic-to-patient payments (today's per-clinic bKash flow) would make AltCare hold clinics'
money (settlement, refunds, possibly licensing) and are **not** part of this work. Needs a separate
decision and legal advice before anyone builds it.

## 4. Open decisions

| # | Question | Leaning |
|---|---|---|
| 1 | Free limit *values* (decided: they live in the plan config; the numbers are still to set, e.g. patient cap, invoicing) | cap patients, keep clinical loop free |
| 2 | Gating dimensions: patients, seats, SMS, email, invoicing, directory, AI | as proposed in `pricing-usage-onboarding` §2.2 |
| 3 | Prices (monthly, yearly) and founding-member price | derive from cost per active clinic |
| 4 | ~~Who pays~~ — **decided: the clinic** (see §1.7) | done |
| 5 | Email: allowance only, or top-ups too | allowance only (low cost) |
| 6 | Unused monthly allowance: expire or roll over | expire |
| 7 | Purchased credits: expire after N months or never | - |
| 8 | SMS sender identity (platform sender vs clinic name; check provider and regulator rules) | platform sender, clinic name in text |
| 9 | Clinics that already configured their own SMS/email provider: migrate, or let them keep it | - |
| 10 | Patient-payment collection (see §3) | out of scope for now |

## 5. Build order

1. Settle plan values (§4 items 1-4) and set them in the plan config. Enforcement of patients, seats,
   SMS, invoicing, AI and the directory already exists; add the monthly email limit and upgrade prompts
   (a clear "upgrade or buy credits" message instead of a bare 403).
2. Platform-only providers from env, the credit ledger, send routes charging credits, retire per-clinic
   integrations.
3. Payment orders, SSLCommerz and bKash checkout with idempotent confirmation, subscription activation,
   top-ups, receipts, expiry reminders.
4. Clinic billing page (plan, balance, usage, purchase history) and admin views (provider balances,
   revenue, credits sold).

## 6. Environment variables (to be added to `.env.example` when built)

Email (exists): `EMAIL_PROVIDER=resend`, `RESEND_API_KEY`, `EMAIL_FROM_ADDRESS`.
SMS: `SMS_PROVIDER`, provider keys. SSLCommerz: store id, store password, sandbox flag. bKash: existing
`BKASH_*`. Exact names are set when each piece is built.

## 7. Implementation notes (built 2026-10-12, branch `feat/platform-messaging-credits`)

- `credit_balances` / `credit_ledger` (migration `a4d9e2c7b6f1`); `usage_tracking.emails_sent`; new
  entitlement `monthly_email`; `integration_logs.tenant_integration_id` is now nullable (platform sends).
- `app/core/credits.py` `CreditService`: `spend` (allowance first, then a single conditional UPDATE on the
  purchased balance, so concurrent sends cannot overspend), `refund`, `grant`, `summary`, `ledger`.
  Allowance usage is measured in `usage_tracking`, not the ledger; only purchased credits are ledgered.
- `app/core/messaging.py`: platform SMS (`SMS_PROVIDER=bulksmsbd`, `BULKSMSBD_*`) and email
  (`EMAIL_PROVIDER`, e.g. Resend) from the environment; `messaging_status()` returns configured-or-not only.
- `/integrations/send/sms` and `/send/email` use the platform provider when it is configured (charged);
  otherwise they fall back to the clinic's own provider (legacy, until clinics are migrated).
  Failed sends are refunded by the Celery task; clinic emails carry the clinic as Reply-To.
- API: clinic `GET /billing/credits`, `GET /billing/credits/ledger`; admin `POST /admin/tenants/{id}/credits`
  (grant or remove, note required), `GET /admin/messaging/status`.
- **Known gaps:** the existing BulkSMSBD client is the repo's earlier generic implementation (its request
  format is marked "adjust based on actual API documentation") and has not been verified against the real
  provider; no provider-balance lookup or low-balance alert yet; no bounce handling; no checkout, so
  credits are added by an admin until Step 3; clinics' own provider integrations are not migrated or retired;
  the allowance check and its increment are not one atomic step (a burst of concurrent sends can overshoot
  the allowance by a few).

## 8. Checkout (built 2026-10-12 against a fake gateway, branch `feat/checkout-fake-gateway`)

- **Tables:** `billing_orders` (AltCare's own revenue; separate from the clinic-to-patient `payments`),
  `credit_packs` (admin-priced top-ups), `tenants.plan_reminder_stage` (migrations `b8e3f1a6c2d5`,
  `c5f2a7d9e1b3`).
- **Gateway interface** (`app/modules/billing/gateways/`): `create_checkout(order)` returns a redirect;
  `verify(order)` asks the gateway what happened. Only `FakeGateway` exists. SSLCommerz and bKash are
  two more classes behind the same interface plus their notification endpoints.
- **Fake gateway** is a test page where a tester picks success/failed/cancelled. It exists only when
  `PAYMENT_FAKE_GATEWAY_ENABLED=true`; **the app refuses to start in production with it on.**
- **Settling is the only place money becomes entitlement.** It runs under a row lock on the order, is
  idempotent (a repeated or racing notification cannot grant twice), and refuses to fulfil if the
  gateway's amount or currency differs from the order. The browser's return page is never trusted: it
  polls the order, and a pending order is re-checked with the gateway on every read.
- **Fulfilment:** subscription sets `tenants.plan` and `plan_expires_at` (renewing the same plan extends
  from the current expiry; a lapsed or new plan starts now; no proration when upgrading mid-period);
  a credit pack grants credits atomically with the order and records the receipt number in the ledger.
- **Rules computed by the server** (`assess`): subscribe / renew / upgrade allowed; a lower plan while a
  higher one is active, a plan that never expires, and a plan with no online price are refused.
  Only doctors can buy or see orders; orders are private to their clinic.
- **Housekeeping** (`app/modules/billing/maintenance.py`, Celery beat daily): expiry reminders at 7 and 1
  days (once per stage, reset on renewal) and expiry of pending orders older than 24h after a last
  gateway check. Needs a Celery worker **and beat** process in deployment.
- **Known gaps:** no real gateway; no gateway notification (IPN) endpoint yet (the fake needs none);
  no refunds or cancellation; no PDF receipt (a printable page only); no invoices with tax details; no
  proration; no admin manual "mark paid" for bank transfers; plan prices are still unset (the pricing
  and checkout pages show "contact us" until an admin saves prices in the plan editor); the order
  list does not filter by date.
