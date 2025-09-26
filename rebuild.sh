#!/bin/bash -e
set -e

DATABASE_NAME=pg_mq_poc

psql -d $DATABASE_NAME -c "drop schema if exists mq cascade;"

# Execute in correct order
psql -f "./src/000_initialize.sql" -d $DATABASE_NAME --single-transaction
psql -f "./src/001_tables.sql" -d $DATABASE_NAME --single-transaction
psql -f "./src/001a_health_tables.sql" -d $DATABASE_NAME --single-transaction  
psql -f "./src/002_triggers.sql" -d $DATABASE_NAME --single-transaction
psql -f "./src/002a_health_triggers.sql" -d $DATABASE_NAME --single-transaction  
psql -f "./src/003_exchange_procedures.sql" -d $DATABASE_NAME --single-transaction
psql -f "./src/004_consumer_procedures.sql" -d $DATABASE_NAME --single-transaction
psql -f "./src/005_producer_procedures.sql" -d $DATABASE_NAME --single-transaction
psql -f "./src/007_health_functions.sql" -d $DATABASE_NAME --single-transaction  
psql -f "./src/008_monitoring_views.sql" -d $DATABASE_NAME --single-transaction  
psql -f "./src/006_example_data.sql" -d $DATABASE_NAME --single-transaction