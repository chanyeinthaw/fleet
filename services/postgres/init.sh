#!/usr/bin/env bash
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
\getenv cpa2_password CPA2_DB_PASSWORD
CREATE USER cpa2 WITH PASSWORD :'cpa2_password';
CREATE DATABASE cpa2 OWNER cpa2;
SQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
\getenv cpa1_password CPA1_DB_PASSWORD
CREATE USER cpa1 WITH PASSWORD :'cpa1_password';
CREATE DATABASE cpa1 OWNER cpa1;
SQL
