-- Run as postgres superuser:
--   psql -U postgres -f setup.sql
--
-- Or paste into SQL Shell (psql) after connecting as postgres.

CREATE DATABASE job_market;

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'job_analyzer') THEN
    CREATE USER job_analyzer WITH PASSWORD 'your_password';
  END IF;
END
$$;

ALTER DATABASE job_market OWNER TO job_analyzer;
GRANT ALL PRIVILEGES ON DATABASE job_market TO job_analyzer;

\c job_market

ALTER SCHEMA public OWNER TO job_analyzer;
GRANT ALL ON SCHEMA public TO job_analyzer;
GRANT CREATE ON SCHEMA public TO job_analyzer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO job_analyzer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO job_analyzer;
