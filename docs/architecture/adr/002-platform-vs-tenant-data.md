# ADR 002: Separate platform-global and tenant-owned data

- Status: Accepted
- Date: 2026-09-23

## Decision

Platform catalogs (future disciplines, conditions, herbs, references/evidence, canonical books, colleges, and articles) are global unless a documented ownership need says otherwise. Clinical records (patients, visits, appointments, prescriptions, payments, clinic configuration, tenant integrations, and tenant custom medicine/symptom records) remain tenant-owned. Tenant annotations such as reading progress and bookmarks remain user/tenant scoped.

## Current implementation

Medicine and symptom already use an `is_global` flag alongside `tenant_id`; preserve these tables and do not create duplicate catalogs. Important: ORM and initial migrations currently make `tenant_id` non-null, while global creation routes pass `None`. This is a code/schema mismatch; tenantless global records are not safely supported by the current schema. Most library records also inherit a non-null tenant FK, so they are not platform-global yet. Phase B must resolve medicine/symptom nullability and data ownership in additive migrations before asserting these are tenantless global catalogs. No schema conversion is part of this ADR's first phase.

## Isolation terminology

Current tenant isolation is **application-level row isolation** via explicit query predicates. PostgreSQL RLS is not enabled. Tenant-only endpoints must reject platform users without tenant context. Global data is exposed only on intentionally global catalog paths.

## Consequences

Future global models need an audited base without mandatory `tenant_id`; tenant models retain explicit scoping. Additive migrations and backfills must precede any ownership conversion.
