---
title: "Integrations API"
type: "api-reference"
module: "integrations"
version: "1.0.0"
last_updated: "2026-05-29"
ai_summary: "12 endpoints for provider catalog, tenant integration configs, testing, logs, and send operations"
endpoints: 12
authentication: "required"
---

# Integrations API

**Module:** Integrations  
**Endpoints:** 12  
**Base Path:** `/api/v1/integrations`

## Overview

This module manages:
- Integration provider catalog
- Tenant-specific provider configuration
- Primary provider selection
- Provider testing
- Integration logs
- Direct send operations (SMS/email)

## Provider Catalog

The seeded catalog currently contains 12 providers:
- SMS: Twilio, Banglalink SMS Gateway, Robi SMS Gateway, BulkSMSBD
- Email: SendGrid, Amazon SES, Generic SMTP
- Payment: bKash, Nagad, Rocket, SSLCommerz, Stripe

Provider `logo_url` values are stable local frontend asset paths such as `/integrations/twilio.svg`. The frontend also uses `frontend/src/lib/integration-logos.ts` as a compatibility fallback so existing seeded databases with null or old external URLs still display logos in `/settings/integrations`.

## Endpoints

1. `GET /api/v1/integrations/providers`
- List available integration providers

2. `GET /api/v1/integrations/providers/{provider_id}`
- Get provider details

3. `POST /api/v1/integrations/`
- Create tenant integration configuration

4. `GET /api/v1/integrations/`
- List tenant integrations

5. `GET /api/v1/integrations/{integration_id}`
- Get one tenant integration

6. `PATCH /api/v1/integrations/{integration_id}`
- Update tenant integration configuration

7. `DELETE /api/v1/integrations/{integration_id}`
- Delete tenant integration

8. `POST /api/v1/integrations/{integration_id}/set-primary`
- Set integration as primary for its type

9. `POST /api/v1/integrations/{integration_id}/test`
- Run integration test operation

10. `GET /api/v1/integrations/logs`
- List integration logs

11. `POST /api/v1/integrations/send/sms`
- Send SMS using configured provider

12. `POST /api/v1/integrations/send/email`
- Send email using configured provider

## Notes

- All endpoints require authentication and are tenant-scoped.
- Credentials are handled through backend encrypted storage patterns.
- `send/*` routes require usable tenant integration configuration.
