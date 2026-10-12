# Billing, platform integrations and messaging credits — spec (draft)

Status: **decisions recorded 2026-10-12; plan values and several details still open.** Nothing in this
document is built yet. It extends `pricing-usage-onboarding-2026-10.md` (§2.3 subscription lifecycle)
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
