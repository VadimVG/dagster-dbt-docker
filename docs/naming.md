# Naming conventions

Names are built from fixed parts, so they are easy to read and to search. Use only the values from the dictionaries below. To add a new value, add it here first.

## Dictionaries

**Layers:**

- `raw`: data dbt cannot reach directly (API, FTP). Loaded by dlt, after cleaning and validation
- `dbt_raw`: data dbt reaches directly
- `dbt_stage`: data prepared for the marts
- `dbt_mart`: data ready for use

**Steps before the `raw` layer:**

- `extracted`: data received from the source
- `cleaned`: data after cleaning

**Source types:**

- `api`
- `db`
- `ftp`
- `file`
- `s3`

**Storages:**

- `pg`: PostgreSQL
- `mssql`: Microsoft SQL Server
- `ch`: ClickHouse

**Refresh modes:**

- `inc`: incremental update
- `deep_inc`: incremental update over a longer period
- `full`: full reload

## Names

- Job and its folder: `<source>_<system>_<object>`
- Asset: `<step or schema>_<source>_<system>_<object>`
- Asset check: `validate_<asset>`
- Schedule: `<job>_<mode>_schedule`
- Sensor: `<job>_sensor`
- Table: `<layer>.<source>_<system>_<object>`

## Rules

- A job goes through all the steps, so its name has no layer.
- A job has no `_job` suffix. The name of the folder and the name of the job are the same.
- The refresh mode is not part of a job or asset name. A job has one set of assets, and the mode comes from the run config (`DagsterAssetRefreshConfig`). Each mode gets its own schedule.
- The technology (dbt, dlt, polars) is not part of a name. Set it in `kinds`, so it is visible in the UI. A tool can change, a table name should not.
- The storage is not part of a name if it is the main DWH (`pg`). Add it only for other storages: `raw_api_amazon_orders_ch`.
- A service job without a data source is named by its purpose: `verify_database_availability`.

## Example

Orders from the Amazon API in the domain `marketplace`:

- Job and folder: `domains/marketplace/api_amazon_orders/`, job `api_amazon_orders`
- Assets: `extracted_api_amazon_orders`, `cleaned_api_amazon_orders`, `raw_api_amazon_orders`
- Asset check: `validate_cleaned_api_amazon_orders`
- Schedules: `api_amazon_orders_inc_schedule`, `api_amazon_orders_full_schedule`
- Table: `raw.api_amazon_orders`
