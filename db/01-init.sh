#!/bin/bash
set -e
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
  CREATE SCHEMA IF NOT EXISTS "$SCHEMA_DB";
  ALTER ROLE "$POSTGRES_USER" SET search_path TO memo,public;
  COMMIT;
EOSQL