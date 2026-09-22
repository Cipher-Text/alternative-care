# ADR 001: Keep AltCare as a modular monolith

- Status: Accepted
- Date: 2026-09-23

## Decision

Keep one Next.js frontend, one FastAPI backend, one PostgreSQL database, Redis, MinIO, and Celery/background workers in the same backend repository. Organize ownership by Platform, Practice, Knowledge, Content, and Intelligence domains without extracting microservices or replacing working route/module names.

## Context

The repository already has established practice-management modules and one active FastAPI app. Splitting services would add deployment and data-boundary complexity without being required for the product expansion.

## Consequences

Modules own routes and business logic; shared infrastructure/models remain centralized where appropriate. Admin remains integrated. Public knowledge and clinical tenant data must have explicitly separate access paths.
