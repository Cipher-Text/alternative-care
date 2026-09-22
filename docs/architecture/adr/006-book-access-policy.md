# ADR 006: Make book access capabilities explicit

- Status: Proposed for Phase C
- Date: 2026-09-23

Represent book access with an explicit policy (PUBLIC_DOMAIN, LICENSED, METADATA_ONLY, INTERNAL_REFERENCE, RESTRICTED, UNKNOWN) and capabilities for metadata, search, snippets, full text, download, and RAG. Do not infer distribution rights from a generic `is_public` flag. Default unknown rights conservatively. Schema design and transition from the tenant-scoped legacy library require an additive migration.
