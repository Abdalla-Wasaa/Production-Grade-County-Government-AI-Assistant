#!/bin/bash
set -eu
# Fresh PGDATA only. Never echo credentials, interpolate SQL in shell, or use -x.
export COUNTY_INIT_MIGRATION_PASSWORD="$(cat /run/secrets/migration_password)"
export COUNTY_INIT_RUNTIME_PASSWORD="$(cat /run/secrets/runtime_password)"
# Prevent a failed role statement from echoing password literals in server logs.
export PGOPTIONS='-c log_statement=none -c log_min_error_statement=panic -c log_error_verbosity=terse'
if ! psql --no-psqlrc --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1 >/dev/null 2>&1 <<'SQL'
\getenv migration_password COUNTY_INIT_MIGRATION_PASSWORD
\getenv runtime_password COUNTY_INIT_RUNTIME_PASSWORD
CREATE ROLE county_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD :'migration_password';
CREATE ROLE county_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD :'runtime_password';
ALTER DATABASE county_local OWNER TO county_migrator;
REVOKE ALL ON DATABASE county_local FROM PUBLIC;
GRANT CONNECT ON DATABASE county_local TO county_runtime;
ALTER SCHEMA public OWNER TO county_migrator;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO county_runtime;
SQL
then
  echo "Fresh database provisioning failed; preserve the volume and review initialization." >&2
  exit 1
fi
unset COUNTY_INIT_MIGRATION_PASSWORD COUNTY_INIT_RUNTIME_PASSWORD PGOPTIONS
