# ADR 005: Start search with PostgreSQL

- Status: Proposed
- Date: 2026-09-23

Implement metadata filtering and PostgreSQL full-text search first. Keep retrieval behind an Intelligence-owned search module. Add pgvector semantic retrieval and hybrid ranking only after corpus and citation requirements are established. Do not add Elasticsearch/OpenSearch or a separate vector database now.
