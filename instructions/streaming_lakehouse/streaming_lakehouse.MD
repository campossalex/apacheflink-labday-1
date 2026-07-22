<!---SECTION: Getting Familiar-->
Real-Time to Lakehouse: Streaming Orders with Apache Fluss & Iceberg
===

In this hands-on workshop you will build a **Streaming Lakehouse** using **Apache Fluss** and **Apache Iceberg**. You'll ingest a real-time stream of e-commerce order events from Kafka, store it in Fluss tables, enrich it with product data replicated live from PostgreSQL via CDC, and transparently tier the result into Iceberg for long-term analytics — all with Flink SQL.

A data generator is already running and publishing synthetic order events as JSON to the Kafka topic `orders_log`. Each event represents an order moving through its lifecycle: `PLACED`, `PAID`, `SHIPPED`, `DELIVERED` (or, occasionally, `CANCELLED`). Your goal is to build the ingestion → state → enrichment pipeline, enable Fluss's native tiering to Iceberg, and then query the very same table both as a live, fresh stream and as a queryable historical Iceberg table — with no data movement or duplication for you to manage.

The following tools and components are available in this environment:

- **Ververica**: access the Ververica Unified Streaming Data Platform web console to write and run Flink SQL jobs.
- **Kafka**: inspect the `orders_log` topic the generator produces to.
- **Trino**: query Iceberg tables directly with plain SQL, completely independent of Flink.
- **Lakekeeper**: browse the Iceberg REST catalog to see the namespaces and tables Fluss tiers data into.
- **Grafana**: (optional, Lab 5) explore a near-real-time order revenue dashboard.

> [!NOTE]
> If you prefer, download the Grafana template now:  
> Right click on this [link](https://raw.githubusercontent.com/campossalex/apacheflink-labday-1/refs/heads/master/instructions/streaming_lakehouse/assets/streaming_lakehouse_dashboard.json) and save the JSON file in your computer.

> [!NOTE]
> You will need a **Session Cluster** to run SELECT statement.   
> If the session cluster is not running, you can start manually.  
> Go to Session Clusters, and then click on the `Start` button.  
> 
> ![0.png](screenshots/0.png)

<!---SECTION: Lab 1: Fluss Catalog & Kafka Ingestion-->
Lab 1: Fluss Catalog & Kafka Ingestion
===

In this lab you will set up the Fluss catalog, create the Fluss table order events will land in, register the Kafka topic the generator is producing to, and run a simple job that carries events from one to the other.

### Step 1: Create the Fluss catalog

Fluss is Apache's native streaming lakehouse storage. Creating the catalog registers Fluss as a known catalog in Flink so you can create and query Fluss tables from SQL.

Go to the **Ververica** tab, then navigate to **SQL → SQL Scripts**. Copy and paste the following SQL statement into the SQL Editor:

```sql,line-numbers,wrap
CREATE CATALOG fluss WITH (
  'type'              = 'fluss',
  'bootstrap.servers' = 'coordinator-server-0.coordinator-server-hs.fluss.svc.cluster.local:9124'
);
```

Click `Run`.

> [!NOTE]
> The `fluss` catalog will appear in the Catalog panel on the left. All Fluss tables in this lab will live under `fluss.orders.*`.

### Step 2: Create the Fluss database and Log table

A Fluss **Log table** is an ordered, append-only store — every order event written to it is preserved forever and can be replayed from the beginning at any time. The `WATERMARK` declaration allows this table to drive time-based window operations later.

```sql,line-numbers,wrap
CREATE DATABASE IF NOT EXISTS fluss.orders;

CREATE TABLE IF NOT EXISTS fluss.orders.orders_log (
  `order_id`    STRING,
  `customer_id` STRING,
  `product_id`  STRING,
  `status`      STRING,
  `amount`      DECIMAL(10, 2),
  `event_time`  TIMESTAMP(3),
  WATERMARK FOR `event_time` AS `event_time` - INTERVAL '5' SECOND
) WITH (
  'bucket.num' = '3'
);
```

Click `Run`. You will see `orders_log` appear under `fluss → orders` in the Catalog panel — it's empty for now, since nothing is writing to it yet.

### Step 3: Create the Kafka source table

The generator doesn't write to Fluss directly — it publishes JSON events to the Kafka topic `orders_log`. Register that topic as a Flink table:

```sql,line-numbers,wrap
CREATE TABLE IF NOT EXISTS orders_log_kafka (
  `order_id`    STRING,
  `customer_id` STRING,
  `product_id`  STRING,
  `status`      STRING,
  `amount`      DECIMAL(10, 2),
  `event_time`  TIMESTAMP(3),
  WATERMARK FOR `event_time` AS `event_time` - INTERVAL '5' SECOND
) WITH (
  'connector'                    = 'kafka',
  'format'                       = 'json',
  'json.ignore-parse-errors'     = 'true',
  'properties.bootstrap.servers' = 'host.minikube.internal:9092',
  'properties.group.id'          = 'flink-streaming-lakehouse',
  'scan.startup.mode'            = 'earliest-offset',
  'topic'                        = 'orders_log'
);
```

Click `Run`. The generator emits `event_time` as `yyyy-MM-dd HH:mm:ss.SSS` (Python's `isoformat(" ", "milliseconds")` — the same approach `coffee_shop`'s Kafka generators use), which is the JSON format's default SQL timestamp shape. Flink parses it straight into `TIMESTAMP(3)` — no intermediate `STRING` column or `TO_TIMESTAMP()` conversion needed.

> [!NOTE]
> Open the **Kafka** tab if you'd like to see the raw JSON messages on the `orders_log` topic before they reach Flink.

### Step 4: Run the source → sink job

This is the "simple source → sink job" the rest of the workshop builds on: read every event from the Kafka topic, and insert it into the Fluss table.

```sql,line-numbers,wrap
INSERT INTO fluss.orders.orders_log
SELECT
  `order_id`,
  `customer_id`,
  `product_id`,
  `status`,
  `amount`,
  `event_time`
FROM orders_log_kafka;
```

Unlike the `CREATE TABLE` statements before it, this is a **long-running streaming job** — it needs to keep running for the rest of the workshop, so a plain `Run` (which ties it to your SQL Editor session) isn't enough. Instead, deploy it as its own job:

1. In the SQL Editor toolbar, click `Save As`. Name the draft `kafka-to-fluss` — a self-descriptive name makes it easy to find again in **Deployments** once you have several jobs running.
2. In the new draft tab, click `Deploy`, then `Confirm` to create a SQL Deployment from it.
3. Go to **Deployments** in the left-hand menu, find `kafka-to-fluss`, and click `Start` (with **Initial Mode** selected) to launch the job.

Leave it running for the rest of the workshop.

### Step 5: Confirm order events are landing in Fluss

```sql,line-numbers,wrap
SELECT * FROM fluss.orders.orders_log;
```

You will see order events appearing in real time, with `status` progressing through `PLACED` → `PAID` → `SHIPPED` → `DELIVERED` (some orders will show `CANCELLED` instead). To stop the query, click the `||` (pause) button above the result grid.

> [!NOTE]
> Unlike Kafka, the Fluss Log table retains data indefinitely. There is no retention window to worry about — this makes it a reliable long-term event store, and it's exactly what makes tiering to Iceberg in Lab 3 safe: nothing is lost in the handoff. Kafka is the ingestion buffer; Fluss is the durable, queryable copy.

<!---SECTION: Lab 2: Order State & Product Enrichment-->
Lab 2: Order State & Product Enrichment
===

In this lab you will maintain the current state of every order, replicate a product dimension live from PostgreSQL via CDC, and enrich the order stream with product details via a temporal lookup join — the same building blocks you'll tier into Iceberg in Lab 3.

### Step 6: Create the order_status PK table

A **Primary Key (PK) table** stores exactly one row per key — every write with the same key is an upsert. This gives you a live view of each order's current state without accumulating duplicates.

```sql,line-numbers,wrap
CREATE TABLE IF NOT EXISTS fluss.orders.order_status (
  `order_id`    STRING,
  `customer_id` STRING,
  `status`      STRING,
  `amount`      DECIMAL(10, 2),
  `last_update` TIMESTAMP(3),
  PRIMARY KEY (`order_id`) NOT ENFORCED
) WITH (
  'bucket.num' = '3'
);
```

Click `Run`.

### Step 7: Start the state aggregation job

This job reads from the Log table and writes to the PK table. As an order advances through `PLACED` → `DELIVERED`, its single row in this table is silently updated in place.

```sql,line-numbers,wrap
INSERT INTO fluss.orders.order_status
SELECT
  `order_id`,
  `customer_id`,
  `status`,
  `amount`,
  `event_time` AS `last_update`
FROM fluss.orders.orders_log;
```

This is another long-running job, so it needs the same treatment as Step 4: `Save As` a draft named `order-status-sync`, `Deploy` it, then `Start` it from **Deployments**.

### Step 8: Create the product_lookup Fluss PK table

PostgreSQL already has a `product_catalog` table, seeded by the environment setup with 500 realistic products (name, category, brand, price, cost, weight, rating, and more). Rather than re-typing that data into Fluss, you'll replicate it live via **Change Data Capture** — any insert or update in PostgreSQL will show up here automatically, with no re-run required.

Create the Fluss table with the exact same shape as PostgreSQL's `product_catalog`:

```sql,line-numbers,wrap
CREATE TABLE IF NOT EXISTS fluss.orders.product_lookup (
  `product_id`   STRING,
  `sku`          STRING,
  `product_name` STRING,
  `category`     STRING,
  `brand`        STRING,
  `unit_price`   DECIMAL(10, 2),
  `cost`         DECIMAL(10, 2),
  `weight_kg`    DECIMAL(6, 2),
  `in_stock`     BOOLEAN,
  `rating`       DECIMAL(2, 1),
  `created_at`   TIMESTAMP(3),
  PRIMARY KEY (`product_id`) NOT ENFORCED
) WITH (
  'bucket.num' = '3'
);
```

Click `Run`.

### Step 9: Create the postgres-cdc source table

The `postgres-cdc` connector snapshots the existing table on startup, then streams every subsequent change. The lab environment already configured PostgreSQL for this (a replication-enabled `cdc_user`, a publication, and a replication slot) — you just need to register the source table in Flink:

```sql,line-numbers,wrap
CREATE TABLE IF NOT EXISTS product_catalog_cdc (
  `product_id`   STRING,
  `sku`          STRING,
  `product_name` STRING,
  `category`     STRING,
  `brand`        STRING,
  `unit_price`   DECIMAL(10, 2),
  `cost`         DECIMAL(10, 2),
  `weight_kg`    DECIMAL(6, 2),
  `in_stock`     BOOLEAN,
  `rating`       DECIMAL(2, 1),
  `created_at`   TIMESTAMP(3),
  PRIMARY KEY (`product_id`) NOT ENFORCED
) WITH (
  'connector'                 = 'postgres-cdc',
  'hostname'                  = 'host.minikube.internal',
  'port'                      = '5432',
  'username'                  = 'cdc_user',
  'password'                  = 'admin1',
  'database-name'             = 'streaming_lakehouse',
  'schema-name'               = 'public',
  'table-name'                = 'product_catalog',
  'slot.name'                 = 'flink_cdc_lakehouse_slot',
  'decoding.plugin.name'      = 'pgoutput',
  'debezium.publication.name' = 'all_tables_pub'
);
```

Click `Run`.

> [!NOTE]
> This is the same `postgres-cdc` pattern used in `cc_fraud` (Lab 6) for dynamic per-card thresholds. There, a handful of rows changed occasionally; here, 500 rows are snapshotted once at startup and then kept in sync. The mechanism is identical either way.

### Step 10: Start the CDC → Fluss sync job

```sql,line-numbers,wrap
INSERT INTO fluss.orders.product_lookup
SELECT * FROM product_catalog_cdc;
```

This is a long-running job too: `Save As` a draft named `pgcdc-to-fluss`, `Deploy` it, then `Start` it from **Deployments** (same steps as Step 4). It first snapshots all 500 products, then keeps `product_lookup` in sync with any future change to PostgreSQL's `product_catalog`. Confirm it worked:

```sql,line-numbers,wrap
SELECT COUNT(*) FROM fluss.orders.product_lookup;
```

You should see `500`.

### Step 11: Create the orders_enriched Log table

This Log table will store every order event permanently, enriched with product metadata. It's the table you'll tier into Iceberg in the next lab — the single source of truth for both real-time and historical analytics.

```sql,line-numbers,wrap
CREATE TABLE IF NOT EXISTS fluss.orders.orders_enriched (
  `order_id`     STRING,
  `customer_id`  STRING,
  `product_id`   STRING,
  `product_name` STRING,
  `category`     STRING,
  `status`       STRING,
  `amount`       DECIMAL(10, 2),
  `unit_price`   DECIMAL(10, 2),
  `event_time`   TIMESTAMP(3),
  WATERMARK FOR `event_time` AS `event_time` - INTERVAL '5' SECOND
) WITH (
  'bucket.num' = '3'
);
```

Click `Run`.

### Step 12: Start the enrichment job

The `FOR SYSTEM_TIME AS OF t.proc_time` clause instructs Flink to look up each order's product from the `product_lookup` PK table at the moment the order event is processed.

```sql,line-numbers,wrap
INSERT INTO fluss.orders.orders_enriched
SELECT
  t.`order_id`,
  t.`customer_id`,
  t.`product_id`,
  p.`product_name`,
  p.`category`,
  t.`status`,
  t.`amount`,
  p.`unit_price`,
  t.`event_time`
FROM (
  SELECT *, PROCTIME() AS `proc_time`
  FROM fluss.orders.orders_log
) AS t
JOIN fluss.orders.product_lookup FOR SYSTEM_TIME AS OF t.`proc_time` AS p
  ON t.`product_id` = p.`product_id`;
```

This is a long-running job: `Save As` a draft named `product-enrichment`, `Deploy` it, then `Start` it from **Deployments** (same steps as Step 4). Once it's running, verify enriched events are flowing with a plain ad hoc query (`Run` is fine here — you're not deploying this one, just debugging):

```sql,line-numbers,wrap
SELECT * FROM fluss.orders.orders_enriched;
```

Stop the query with the `||` button once you see rows carrying `product_name` and `category`.

> [!WARNING]
> Don't simplify this to a plain `JOIN ... ON` without `FOR SYSTEM_TIME AS OF`. `product_lookup` is a PK (upsert) table, so a regular join against it produces a changelog stream that can include UPDATE/DELETE records — and `orders_enriched` is an append-only Log table, which can't accept them. Removing the temporal-join clause fails with: `Table sink 'fluss.orders.orders_enriched' doesn't support consuming update and delete changes`. The `FOR SYSTEM_TIME AS OF t.proc_time` clause is what makes this a point-in-time lookup (one output row per input row, insert-only) instead of a stateful two-sided join — it's required, not optional boilerplate.

> [!NOTE]
> This is the same `FOR SYSTEM_TIME AS OF proc_time` pattern used in `fluss_intro` (Lab 3). It's one of the most reusable patterns in Fluss: enrich a high-throughput stream from a PK table with O(1) point-read performance, no external cache required — regardless of whether that PK table was hand-seeded (`fluss_intro`) or CDC-replicated (here).

<!---SECTION: Lab 3: Enabling the Lakehouse — Tiering Fluss to Iceberg-->
Lab 3: Enabling the Lakehouse — Tiering Fluss to Iceberg
===

`orders_enriched` now carries the complete, enriched order stream. This is where the workshop's core idea comes in: Fluss can **continuously and automatically tier** any table's data into Apache Iceberg, in the open Parquet + manifest format, without you writing a single ingestion job.

### Step 13: Start the Datalake Tiering Service

Your lab environment already has a **Fluss Datalake Tiering Service** deployed as a draft — a long-running Flink job that reads Fluss log segments and primary-key snapshots and writes them out as native Iceberg data files and manifests into the Lakekeeper Iceberg REST catalog (backed by S3-compatible object storage).

Go to the **Ververica** tab → **Deployments** → **Drafts**, open `fluss-tiering-service-1`, and click **Start**. Leave it running for the rest of the workshop — it will pick up any table you enable tiering on in the next step.

> [!NOTE]
> This is one service, shared across every Fluss table in this environment. You don't deploy a new tiering job per table — you just tell an existing table to opt in.

### Step 14: Enable tiering on orders_enriched

Enabling tiering is a single `ALTER TABLE`:

```sql,line-numbers,wrap
ALTER TABLE fluss.orders.orders_enriched
SET ('table.datalake.enabled' = 'true', 'table.datalake.freshness' = '30s');
```

`table.datalake.freshness` controls how often the tiering service checkpoints new data into Iceberg — 30 seconds here, instead of waiting on the default interval, so you don't spend the workshop staring at an empty Iceberg table.

Click `Run`. Let's also tier the current-state PK table, to see that this works for upsert tables too, not just Log tables:

```sql,line-numbers,wrap
ALTER TABLE fluss.orders.order_status
SET ('table.datalake.enabled' = 'true', 'table.datalake.freshness' = '30s');
```

Click `Run`.

### Step 15: Verify the tiered data landed in Iceberg

Give the tiering service a minute or two to complete its first cycle, then check that Iceberg tables now exist. Go to the **Trino** tab and run:

```sql,line-numbers,wrap
SHOW TABLES FROM iceberg.warehouse;
```

You should see `orders_enriched` and `order_status` listed. You can also open the **Lakekeeper** tab to browse the same catalog visually — the warehouse, its namespace, and the tables Fluss just tiered.

> [!NOTE]
> If the tables don't appear yet, the tiering service may still be starting or waiting for its first checkpoint interval — wait another minute and re-run the query.

### Step 16: Why this matters

Once a table is tiered, its data exists twice — but for two different purposes, not as a wasteful copy:

- **Fluss** keeps the most recent data close, optimized for millisecond point lookups and low-latency streaming reads.
- **Iceberg** holds the full history in cheap, columnar object storage, queryable by any Iceberg-compatible engine — Trino, Spark, Dremio, or Flink itself — with no dependency on Fluss or Flink being up.

This is the "freshness + scale" promise of a streaming lakehouse: one pipeline, one table definition, two storage tiers working together automatically.

<!---SECTION: Lab 4: Querying the Lakehouse — Real-Time + Historical-->
Lab 4: Querying the Lakehouse — Real-Time + Historical
===

Now that `orders_enriched` is tiering into Iceberg, let's see what that actually unlocks: the same table, queried two different ways, for two different purposes.

### Step 17: Re-run the real-time query — this is now a union read

Go back to the **Ververica** SQL Editor and run the exact same query from Lab 2:

```sql,line-numbers,wrap
SELECT * FROM fluss.orders.orders_enriched;
```

You didn't change a thing, but under the hood something important happened: Flink now performs a **union read** — it transparently merges the freshest, not-yet-tiered rows still in Fluss with the already-tiered historical rows in Iceberg, and returns them as one seamless result. No query rewrite, no manual UNION, no awareness required from you that tiering is even happening.

### Step 18: Query the same table from Trino

Switch to the **Trino** tab and run:

```sql,line-numbers,wrap
SELECT * FROM iceberg.warehouse.orders_enriched LIMIT 20;
```

This is the same data — but Trino has no idea Fluss or Flink exist. It's reading plain Iceberg Parquet files and manifests through the Lakekeeper REST catalog. Any tool that speaks the Iceberg REST catalog protocol can read this table.

### Step 19: Run a historical analytics query

Because the tiered data lives in columnar Parquet, Trino can scan the *entire* order history cheaply — no need to replay the whole Fluss log through a Flink job to get an answer.

```sql,line-numbers,wrap
SELECT
  product_name,
  category,
  COUNT(*)      AS orders,
  SUM(amount)   AS revenue
FROM iceberg.warehouse.orders_enriched
WHERE status <> 'CANCELLED'
GROUP BY product_name, category
ORDER BY revenue DESC;
```

You'll see lifetime revenue per product, computed as a single batch scan.

### Step 20 (bonus): Time travel with Iceberg

Fluss gives you the current and recent past. Iceberg gives you something Fluss alone doesn't: **time travel** — the ability to query the table exactly as it looked at a previous snapshot. First, list the available snapshots:

```sql,line-numbers,wrap
SELECT snapshot_id, committed_at
FROM iceberg.warehouse."orders_enriched$snapshots"
ORDER BY committed_at DESC;
```

Copy a `snapshot_id` from earlier in the list (an older snapshot, before the most recent tiering cycle), substitute it below, and run:

```sql,line-numbers,wrap
SELECT COUNT(*) AS orders_at_that_point
FROM iceberg.warehouse.orders_enriched FOR VERSION AS OF 1234567890123456789;
```

You'll get the row count as it existed at that exact snapshot — a query Fluss's live tables cannot answer, because Fluss doesn't retain point-in-time snapshots the way Iceberg does.

<!---SECTION: Lab 5: Freshness Dashboard in Grafana (Optional)-->
Lab 5: Freshness Dashboard in Grafana (Optional)
===

> [!NOTE]
> This lab is a stretch goal. If you're short on time, skip straight to the wrap-up below — Labs 1 through 4 already deliver the complete streaming lakehouse pattern this workshop set out to teach.

### Step 21: Create a windowed revenue job

This job aggregates `orders_enriched` into 5-minute tumbling windows and writes the results to PostgreSQL, where Grafana can query them.

```sql,line-numbers,wrap
CREATE CATALOG lakehouse_pg WITH (
  'type'             = 'postgres',
  'base-url'         = 'jdbc:postgresql://host.minikube.internal:5432',
  'default-database' = 'streaming_lakehouse',
  'username'         = 'root',
  'password'         = 'admin1'
);

INSERT INTO lakehouse_pg.streaming_lakehouse.revenue_5m
SELECT
  window_start,
  window_end,
  `category`,
  COUNT(*)                    AS order_count,
  CAST(SUM(`amount`) AS DECIMAL(12, 2)) AS revenue
FROM TABLE(
  TUMBLE(TABLE fluss.orders.orders_enriched, DESCRIPTOR(`event_time`), INTERVAL '5' MINUTE)
)
WHERE `status` <> 'CANCELLED'
GROUP BY window_start, window_end, `category`;
```

Select just the `CREATE CATALOG` statement and click `Run` — it's a one-off metadata operation, not something you deploy.

The `INSERT INTO` statement below it is a long-running job, so it needs the same treatment as Step 4: select it, click `Save As`, and name the draft `revenue-analytics-sink`. Then `Deploy` it, and `Start` it from **Deployments**.

### Step 22: Import and explore the dashboard

Go to the **Grafana** tab → **Dashboards → Import**, upload `grafana/streaming_lakehouse_dashboard.json` from the lab repository, and select `lakehouse_dwh` as the data source when prompted.

The dashboard shows:

- **KPI row**: Total Orders, Total Revenue, and Categories Tracked in the selected time range.
- **Revenue Over Time by Category**: which product categories are trending right now.
- **Top Categories by Revenue**: a ranked view of your best performers.
- **Revenue by Category (Detail)**: a sortable table for drill-down.

Set the time range to **Last 30 minutes** to focus on the most recent activity.

Congrats, you made it! You have built a complete streaming lakehouse — from a Kafka-fed generator, through Log and PK table storage in Fluss, to CDC-driven enrichment, transparent tiering into Apache Iceberg, and real-time *and* historical queries against the very same table.
