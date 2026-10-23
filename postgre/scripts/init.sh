#!/bin/sh
set -eu

psql --set=ON_ERROR_STOP=1 \
	--username "$POSTGRES_USER" \
	--dbname "$POSTGRES_DB" <<'SQL'
\getenv app_user APP_DB_USER
\getenv app_password APP_DB_PASSWORD
SELECT format(
		'CREATE ROLE %I WITH LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION',
		:'app_user',
		:'app_password'
)
WHERE NOT EXISTS (
		SELECT 1 FROM pg_roles WHERE rolname = :'app_user'
)
\gexec
SQL

psql --set=ON_ERROR_STOP=1 \
	--username "$POSTGRES_USER" \
	--dbname "$POSTGRES_DB" \
	--file /docker-entrypoint-sql/creation.sql

psql --set=ON_ERROR_STOP=1 \
	--username "$POSTGRES_USER" \
	--dbname "$POSTGRES_DB" <<'SQL'
\getenv app_user APP_DB_USER
GRANT CONNECT ON DATABASE leaderboard TO :"app_user";
GRANT USAGE ON SCHEMA public TO :"app_user";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :"app_user";
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO :"app_user";
SQL
