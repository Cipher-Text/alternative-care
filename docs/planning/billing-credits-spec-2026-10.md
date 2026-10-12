# Billing, platform integrations and messaging credits — spec (draft)

Status: **decisions recorded 2026-10-12; plan values and several details still open.** Step 2 of §5
(platform providers from env + credit ledger + charged send routes) is built. Step 3 is built
with a fake gateway (§8) and real SSLCommerz and bKash gateways (§13, mock-tested, not yet run against a real sandbox). Seed plans and prices: §9. It extends `pricing-usage-onboarding-2026-10.md` (§2.3 subscription lifecycle)
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

## 9. Seed plans and the Bangladesh market analysis (2026-10-12)

Four plans: **Free, Plus, Pro, Enterprise**. Values live in `DEFAULT_PLANS` (`app/core/entitlements.py`) and
are seeded into the database by migration `d2a8e4b6f1c7` (prices only where none was set; descriptions only
where they still had the old built-in text). They are **hypotheses to validate, not measured willingness to
pay**, and every one is editable in the admin plan editor.

| | Free | Plus | Pro | Enterprise |
|---|---|---|---|---|
| Who | Solo doctor trying it | Working chamber / small clinic | Established clinic, several doctors | Hospitals, chains, institutions |
| Price per month (BDT) | 0 | **1,000** | **3,000** | custom ("contact us"; start around 15,000) |
| Price per year (BDT) | 0 | **10,000** (2 months free) | **30,000** (2 months free) | custom |
| Patients | 200 | unlimited | unlimited | unlimited |
| Doctors (seats) | 1 | 2 | 5 | unlimited |
| SMS / month | 0 | 300 | 1,000 | 5,000 |
| Email / month | 50 | 1,000 | 5,000 | 20,000 |
| Invoicing | no | yes | yes | yes |
| Public directory listing | no | yes | yes | yes |
| AI assistant (when built) | no | no | 200 queries | 1,000 queries |
| Facebook profile feature (AltCare page) | no | no | 1 per quarter | 3 per quarter (about 1 a month) |
| Patient phone verifications (OTP, AltCare pays the SMS) | 20 / month | 300 / month | 1,000 / month | 5,000 / month |

### What the market data says (and does not)
Searches on 2026-10-12 found **no published taka price list for clinic or chamber software in Bangladesh**,
and **no consultation-fee or practitioner-count data specific to homeopathy, Ayurveda or Unani**. What exists:

- **SMS cost (the main variable cost):** Alpha SMS publishes non-masking 0.31 to 0.40 BDT and masking 0.55 to
  0.64 BDT per SMS depending on the recharge tier ([pricing](https://sms.net.bd/Pricing)); another provider
  advertises from 0.24 BDT ([Automas](https://sms.automas.com.bd/)). Masking needs operator approval; Bangla
  text fits 70 characters per SMS segment versus 160 in English, so Bangla messages cost more.
- **Payment gateway fee:** one university payment page lists 1.4% via SSLCommerz and 1.15% for direct bKash
  ([BUBT](https://payment.bubt.edu.bd/)); an older news article gives 2% to 4% for mobile banking and a 15,000
  BDT SSLCommerz setup cost ([UNB](https://unb.com.bd/category/business/renowned-online-payment-gateways-in-bangladesh-for-domestic-international-transactions/74554)).
  Merchant-specific quotes will differ.
- **Local software benchmarks:** small-business cloud tools run roughly 1,000 to 5,000 BDT/month (an accounting
  tool from 4,500, [review](https://rakibhassan.eu/best-small-business-accounting-software-bangladesh/); global
  per-seat tools such as Odoo about 7.25 USD/user/month, roughly 880 BDT at the 121 BDT/USD rate that source
  used, [Odoo pricing](https://oec.sh/odoo-pricing/bangladesh)). A Bangladeshi prescription-software listing
  shows a one-time lifetime licence of 35,000 BDT ([bdstall](https://bdstall.com/details/prescription-writing-software-30583)),
  about 35 months of Plus. Hospital ERP is far higher: one Dhaka vendor lists a starting price of 150 USD/month
  (about 18,000 BDT, third-party listing, [SoftwareSuggest](https://www.softwaresuggest.com/global-mediklaud-bd)).
  Indian clinic SaaS lists around 2,999 INR/month, a rough upper benchmark for a multi-doctor clinic.
- **Doctor fees (affordability anchor):** opinion pieces cite urban specialist visits of 500 to 1,200 BDT
  ([Financial Express](https://thefinancialexpress.com.bd/views/consultation-fees-and-medical-test-charge)),
  while rural chambers can charge far less (a Dinajpur example at 40 BDT,
  [Daily Star](https://www.thedailystar.net/backpage/peoples-doctor-consultation-medicines-just-tk-40-1533295)).
  Alternative-medicine chambers are probably at the lower end; **not verified**.

### How the numbers were chosen
- **Plus at 1,000 BDT:** at the low end of the local small-business SaaS range, and about two to three
  paid consultations a month for a chamber charging 400 BDT. It is cheap enough for a solo practitioner to say
  yes, and it covers its own variable cost: 300 SMS at the worst-case 0.64 BDT is 192 BDT, 1,000 emails are
  about 50 BDT (assumed, unverified), the gateway fee up to 2.5% is 25 BDT, leaving roughly 730 BDT before
  VAT, hosting and support.
- **Pro at 3,000 BDT:** three times Plus for 2.5 times the doctors, 3 times the SMS and the AI assistant. Worst
  case cost: 1,000 SMS 640 + 5,000 emails 250 + AI 200 queries (assumed 2 to 5 BDT each, 400 to 1,000, the AI
  is not built so this is a guess) + gateway 75, about 1,370 to 1,970 BDT, leaving roughly 1,030 to 1,630.
- **Enterprise custom:** its allowances alone cost about 5,800 to 8,800 BDT a month at those assumptions, so it
  cannot be sold below roughly 15,000 BDT without losing money; that also sits near the 18,000 BDT hospital-ERP
  anchor. It is quoted per deal.
- **Free is trial-sized, not a permanent clinic:** 200 patients is about a month for a typical solo chamber;
  one doctor, no SMS (the largest cost and abuse risk), and no invoicing, which is the "I am running a
  business" upgrade moment. The directory listing is a Plus benefit (strategy §6.3).
- **Yearly price is 10 months** (about 17% off), which also reduces gateway fees and churn.
- **Seats count doctors**, not receptionists (the clinic pays; see §1.7).

### Not verified, to resolve before launch
- Whether VAT applies to subscriptions and whether prices are quoted inclusive. These figures ignore it;
  with 15% inclusive VAT, margins fall by roughly 130 BDT on Plus and 390 BDT on Pro. Confirm with an accountant.
- Real SMS and gateway terms from the providers you sign with, and Resend's actual per-email cost.
- AI cost per query, once the assistant exists.
- What homeopathy, Ayurveda and Unani practitioners earn and pay for software today. Run the 8 to 12
  interviews and Van Westendorp questions in `pricing-usage-onboarding-2026-10.md` §2.4 before treating
  1,000 and 3,000 as final; consider a founding-member price for the first clinics.
- Patient cap of 200 and doctor counts are product judgement, not data.
- **Stored values beat code defaults:** if an admin has already saved a plan in the plan editor, these new
  defaults do not apply to that plan (the migration only fills missing prices and unedited descriptions).

## 10. Facebook profile promotion (built 2026-10-13; Pro and Enterprise benefit)

A paid-plan benefit: AltCare features the doctor's public profile on the **AltCare Facebook page**.

- **Delivery is manual** (decided): there is no Facebook API integration. The doctor requests a feature, AltCare
  staff draft the post from the public profile, the doctor approves the exact text, staff publish it by hand
  on Facebook and paste the post link back. This avoids a Facebook app review and token management; it can be
  automated later behind the same workflow.
- **Consent rule, enforced on the server:** staff cannot mark a request posted unless the doctor approved the
  exact text (`approved_text` is frozen at approval and staff cannot redraft after it). The doctor can approve,
  ask for changes with a comment (it returns to staff), or cancel.
- **Quota:** new entitlement `quarterly_facebook_features` (period `quarterly`, per calendar quarter):
  Pro 1, Enterprise 3 (about one a month), Free and Plus off. Cancelled and rejected requests give the quota
  back. A clinic may have one open request at a time (also a partial unique index in the database).
- **Prerequisite:** the clinic's public directory profile must be live (listed, verified, approved, in plan,
  with a bio), because the post points at it.
- **Tables / API:** `facebook_feature_requests` (migration `e4c7a1d8b5f2`); doctor `/marketing/facebook...`
  (5 endpoints), admin queue `/admin/marketing/facebook...` (4 endpoints, admin only). Staff and doctors get
  best-effort emails at each step.
- **UI:** doctor page `/marketing`, admin queue `/admin/marketing`; the pricing page lists the benefit from the
  plan catalog automatically.
- **Gaps and risks:** staff time scales with the number of Pro and Enterprise clinics (1 hour per feature is a
  good planning figure; this is not in the price analysis yet, so check that 3,000 BDT still covers it); there
  is no post preview image, scheduling, or reporting of Facebook reach; posting is not verified (the link is
  trusted); the AltCare Facebook page itself, its audience and its posting policy need to exist and be owned by
  someone; health content on social media may carry regulatory and platform-policy limits that nobody has
  checked here.

## 11. Seed credit packs (2026-10-13)

Starting top-up packs for clinics that use up their plan's monthly allowance, seeded by migration
`f6b3e9a2c4d7` only when no packs exist (an admin who already created packs is not affected). All are
editable or retirable in Admin > Billing; past orders keep the price they sold at. Like the plan prices they are
**hypotheses**, not market-tested.

| Pack | Price (BDT) | Per message | Cost at provider* | Gross margin |
|---|---|---|---|---|
| 200 SMS | 250 | 1.25 | 128 | about 49% |
| 500 SMS | 550 | 1.10 | 320 | about 42% |
| 1,000 SMS | 1,000 | 1.00 | 640 | about 36% |
| 5,000 SMS | 4,500 | 0.90 | 3,200 | about 29% |
| 10,000 SMS | 8,000 | 0.80 | 6,400 | about 20% |
| 1,000 email | 150 | 0.15 | 50 | about 67% |
| 5,000 email | 600 | 0.12 | 250 | about 58% |
| 20,000 email | 2,000 | 0.10 | 1,000 | about 50% |

\* SMS cost uses the worst case from the market research, 0.64 BDT per masked SMS at the smallest recharge tier
([Alpha SMS](https://sms.net.bd/Pricing)); email cost uses an assumed 0.05 BDT each (unverified). Margins are
before the payment-gateway fee (about 1.4% to 2.5%), VAT, hosting and support.

Why these prices: a clinic cannot bring its own provider (integrations are platform-owned), so packs are priced
as a convenience at about 1.0 BDT per SMS for a typical top-up, falling to 0.8 BDT at 10,000. That is above what
a business pays a bulk provider directly (0.31 to 0.64 BDT), which is the price of not managing a provider
account, and it still undercuts the temptation to use one. The largest pack has the thinnest margin at the
worst-case cost; buying provider credit at a higher recharge tier (0.55 BDT or less) lifts it to about 31%.
Email is priced low and kept simple because its cost is tiny; the main aim is to stop emails from blocking a clinic.

Also check before launch: whether pack purchases are subject to VAT, whether unused credits may expire (open
decision 7 above; today they never expire), and the real provider cost per SMS once an account exists.

## 12. Public site additions (built 2026-10-13)

- **Contact:** public `/contact` page and form (topics: general, enterprise, billing, report a profile; consent
  required, hidden honeypot, 5 per hour per IP; at least an email or a phone). Messages are stored
  (`contact_messages`, migration `a7c4e1f9d2b8`), admins are emailed best-effort, and admins read and mark them
  handled at `/admin/contact`. Direct channels (email, WhatsApp, Facebook page) come from
  `NEXT_PUBLIC_CONTACT_EMAIL`, `NEXT_PUBLIC_WHATSAPP_NUMBER`, `NEXT_PUBLIC_FACEBOOK_URL` and are shown only when set.
  Wired into the header, footer, the verification page, practitioner profiles ("Report this profile") and
  Enterprise on the pricing page ("Talk to us").
- **Home page** is now server-rendered (real `h1` and sections in the HTML, Organization and WebSite structured
  data); the signed-in redirect is a small client component.
- **FAQ and billing** (`/faq`, with FAQPage structured data) and **Refund and cancellation policy**
  (`/refund-policy`), plus a "Paid plans and credits" section in the Terms.
- **Needs the owner before launch:** the refund terms are defaults, not decisions (no refund once a plan is
  active or credits are added, refund for duplicate or wrong charges, "we will fix it or refund you" when a
  charge does not add the plan, no refund timeline); the refund page shows a visible "working draft, pending
  legal review" line to remove once reviewed; the Terms wording (prepaid periods, price changes apply to future
  periods only, suspension for spam) needs review; all Bengali text needs a native reader; VAT is not mentioned
  anywhere; the FAQ says plans are paid for online at checkout, which is **not true until a real payment gateway
  exists** (only the fake test gateway is built), and promises expiry reminders, which need the Celery beat
  process running. Do not publish the FAQ and refund pages before those are real.
- **Still missing:** a contact email, WhatsApp number and Facebook page URL (set the three variables above); a
  separate Enterprise lead form (the contact form's Enterprise topic is the interim); canonical URLs and an
  indexable-404 fix; product screenshots; a patient-facing home door.

## 13. Real payment gateways: SSLCommerz and bKash (built 2026-10-13)

Two gateways behind the same interface as the fake one (`app/modules/billing/gateways/`): `sslcommerz.py` and
`bkash.py`. A method appears at checkout only when its credentials are set, so a blank environment shows none.
The checkout page flags **test mode** whenever a usable method is the fake gateway or a provider sandbox.

**How a payment is trusted (the important part).** Checkout creates a pending order and sends the browser to the
provider. The browser coming back, and the provider's own notification, only *identify* the order. Every callback
then asks the provider server to server what happened, and settles only from that answer, after checking the
amount, the currency and that the transaction is for this order's receipt number. A forged "success" for an unpaid
order, a wrong amount, or someone else's transaction changes nothing; settling is idempotent, so repeated or racing
callbacks and notifications cannot grant twice; a provider outage changes nothing and the return page keeps
checking, which also recovers a lost callback. (Tests cover each of these.)

- **SSLCommerz** (cards, bKash, Nagad, Rocket and other mobile banking on one page): session created with our
  receipt number as `tran_id`; browser returns to `/api/v1/billing/gateways/sslcommerz/{success|fail|cancel}`; its
  server calls `.../sslcommerz/ipn`; we query the transaction by `tran_id`, then confirm a valid one with the
  validation API (`val_id`) before reporting it paid.
- **bKash (direct, tokenized checkout):** token, create payment (our receipt number is the invoice number),
  browser returns to `/api/v1/billing/gateways/bkash/callback?paymentID=..&status=..`; only on `success` do we call
  Execute (which captures the money) and then trust bKash's response, falling back to a status query if Execute
  reports an error (for example a repeated callback). It is a separate client from the clinic-to-patient bKash
  service, so platform billing cannot be affected by that feature.

**Configuration** (`.env`, see `.env.example`): `BACKEND_PUBLIC_URL` (callbacks; https and public in production),
`SSLCOMMERZ_STORE_ID`, `SSLCOMMERZ_STORE_PASSWORD`, `SSLCOMMERZ_IS_SANDBOX`, `BKASH_APP_KEY`, `BKASH_APP_SECRET`,
`BKASH_USERNAME`, `BKASH_PASSWORD`, `BKASH_BASE_URL`, `BKASH_IS_SANDBOX`. **Production refuses to start** with a
sandbox flag or sandbox bKash URL while that gateway is configured, with a non-https `BACKEND_PUBLIC_URL`, or with
the fake gateway on.

**Trying it with sandbox accounts:** put the sandbox keys in `.env`, restart the backend, and buy a plan. The
browser returns work on localhost; SSLCommerz's server-to-server IPN cannot reach a laptop, so it is recovered by the
return page's check (use a tunnel such as ngrok and set `BACKEND_PUBLIC_URL` to test IPN itself). In the SSLCommerz
merchant panel also set the IPN listener URL to `<BACKEND_PUBLIC_URL>/api/v1/billing/gateways/sslcommerz/ipn`.

**Not verified, and why it matters:** both gateways were written from the providers' documented APIs and tested
against **mocked responses only**. Field names, status values and edge cases (for example bKash's status after
Execute, SSLCommerz's risk flags) must be confirmed against a real sandbox account before going live.

**Known gaps:** no refunds and no admin "mark paid" for a payment a provider took but could not confirm; an
SSLCommerz payment flagged high risk is still fulfilled (the risk level is stored on the order for review);
payer details sent to the provider use placeholders when a clinic has no phone or address; no provider fee is
tracked against orders (about 1.4% to 2.5%); order descriptions are English only; bKash's merchant agreement
(and any recurring or tokenized agreement) is not set up.
