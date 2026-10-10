-- Grants the least-privileged application role what it needs to run AltCare, so PostgreSQL
-- row-level security (migration 273747e56a3f) is enforced instead of bypassed by a superuser.
--
-- Run as the table-owner/superuser role, once per database, e.g.:
--   psql -d altcare_dev -v app_role=altcare -v owner_role=imran -f backend/scripts/grant_app_role.sql
-- The ALTER DEFAULT PRIVILEGES lines make tables created by future migrations accessible too.

GRANT USAGE ON SCHEMA public TO :"app_role";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :"app_role";
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO :"app_role";

ALTER DEFAULT PRIVILEGES FOR ROLE :"owner_role" IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"app_role";
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner_role" IN SCHEMA public
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO :"app_role";
