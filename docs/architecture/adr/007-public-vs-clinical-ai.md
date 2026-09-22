# ADR 007: Keep public knowledge retrieval separate from clinical AI

- Status: Proposed
- Date: 2026-09-23

Initial AI/RAG use is knowledge retrieval over books, sections, medicines, symptoms, conditions, herbs, articles, and references with source citations. Do not build diagnosis AI or include patient records in public retrieval. Any future clinical retrieval must be a separate tenant-scoped path with its own authorization and audit design. Preserve the existing `/api/v1/ai/query` contract while it remains a 501 stub.
