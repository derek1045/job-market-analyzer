-- Run as postgres superuser when job_market and job_analyzer already exist.
-- From project folder:
--   psql -U postgres -f fix_permissions.sql

\c job_market

ALTER DATABASE job_market OWNER TO job_analyzer;
ALTER SCHEMA public OWNER TO job_analyzer;
GRANT ALL ON SCHEMA public TO job_analyzer;
GRANT CREATE ON SCHEMA public TO job_analyzer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO job_analyzer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO job_analyzer;
