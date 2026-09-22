# ADR 003: Build knowledge as shared, discipline-neutral catalogs

- Status: Proposed for Phase B
- Date: 2026-09-23

Use shared Discipline, Condition, Herb, Reference, and Evidence concepts. Relate records with association tables where many-to-many membership is valid. Keep conditions distinct from symptoms and herbs distinct from medicines. Reuse the current medicine/symptom global-vs-tenant design. Do not create discipline-specific table families.

No tables are created by this decision; schema and relationship details require a reviewed additive migration.
