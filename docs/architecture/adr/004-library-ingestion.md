# ADR 004: Make library ingestion asynchronous and idempotent

- Status: Proposed for Phase C
- Date: 2026-09-23

Ingest normalized JSON and, later, PDF/EPUB through backend services and Celery jobs. Store binaries in MinIO, metadata/content in PostgreSQL, and track source/content checksums so retries and reprocessing do not duplicate books or sections. HTTP routes enqueue work rather than parse large files synchronously. OCR is an adapter/extension point, not a new OCR implementation in this phase.

The current repository has library models and Celery configuration but no MinIO client or book-ingestion tasks.
