#!/bin/bash
set -e
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
  CREATE SCHEMA memo;
  COMMIT;
EOSQL