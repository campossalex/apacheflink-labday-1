<!---SECTION: Getting Familiar-->
Getting Familiar
===

The following tools and components were deployed to build the streaming application as part of this Lab Day:

- **Ververica**: access the Ververica Unified Streaming Data Platform web console to run Flink jobs.
- **Redpanda**: Redpanda Console will give access to the Kafka broker where the business events will come in.
- **Grafana**: access Grafana to design, build and publish a dashboard.

Additionally, you have access to two command line interfaces to run some commands.

> [!NOTE]
> Use the following credentials to connect to the Postgres database:
> - **User**: root
> - **Password**: admin1

> [!NOTE]
> You will need a **Session Cluster** to run SELECT statement.   
> If the session cluster is not running, you can start manually.  
> Go to Session Clusters, and then click on the `Start` button.  
> 
> ![0.png](screenshots/0.png)

<!---SECTION: Lab 1: Connecting with Data Sources-->
Lab 1: Connecting with Data Sources
===
In this first lab, you will learn how to create Dynamic Table to consume data from a Kafka topic and from a CSV file stored in Minio (s3).

### Step 1: Check the data in the Kafka topic:
Go to Redpanda tab to see the actual data arriving in the Kafka topic.

Navigate to the `Topics` option in the left-hand side menu, and then link on the topic `store.purchases` . This is where the purchases events are arriving in Kafka.  Choose one of the messages, and click on the arrow to expand the event details. You will be able to see the actual JSON data.

![1.png](screenshots/1.png)

This confirms purchase events are generated and published to the Kafka topic.

### Step 2: Create a Flink Table to consume purchase events:
Now it's time to create our first Dynamic Table. We are going to call this table `purchase_stream`to represent the purchases events generated in real-time.

Go to Ververica, then SQL Editor. To start a new draft, in the toolbar, click on New -> New Blank Draft.  
A new draft is ready to run all your the SQL statement you will need to develop this pipeline.

Copy and paste the following SQL statement in the SQL Editor. You can delete any default comments:

```sql,line-numbers,wrap
CREATE TABLE purchase_stream (
  transaction_time TIMESTAMP(3),
  transaction_id STRING,
  product_id STRING,
  price FLOAT,
  quantity INT,
  state STRING,
  is_member BOOLEAN,
  member_discount FLOAT,
  add_supplements BOOLEAN,
  supplement_price FLOAT,
  total_purchase FLOAT,
  WATERMARK FOR transaction_time AS transaction_time - INTERVAL '1' SECOND
) WITH (
    'connector'='kafka',
    'properties.bootstrap.servers'='host.minikube.internal:9092',
    'format'='json',
    'topic' = 'store.purchases',
    'properties.group.id' = 'flink-jobs',
    'scan.startup.mode' = 'earliest-offset',
    'properties.auto.offset.reset' = 'earliest'
);
```

Right-click on the statement, and then select `Run` to execute the SQL statement.  
In the bottom panel you will see the following message: **Query has been executed**. 

On the left-hand side of the SQL Editor, you will see the `Catalogs`. You will also be able to see the new created table on the Catalog (left side of the SQL Editor).

![2.png](screenshots/2.png)

Click on the `Reaload all metada` button to refresh the Catalog.

![3.png](screenshots/3.png)

Click on the `+` button to navigate in the Catalog tree. The `puchase_stream` table is now availabe.


### Step 3: Run a SELECT statement to print purchase events from the Kafka topic:

A good way to confirm the table creation works well, is running a SELECT query and see the actual data.   
Run the follow statement in the SQL Editor. You can reuse the same draft. Replace any previous query:

```sql,line-numbers,wrap
SELECT * FROM purchase_stream;
```

To debug SELECT statements, click on the `Debug` option in the SQL toolbar. 
Then confirm the query will execute in the default *Session Cluster**

![4.png](screenshots/4.png)

You will be able to see purchase events in the result grid, but now in a tabular format. Great! You have created your first Dynamic Table. Now let's create the table with the product reference data.

![5.png](screenshots/5.png)

> [!WARNING]
> Make sure to stop the SELECT query. Click on the `stop` button located in the result grid.
> 
![6.png](screenshots/6.png)

### Step 4: Create a Flink Table to connect to the lookup data:

Now it's time to create our second Dynamic Table.   
We are going to call this table `product_lookup` to represent the information about each product of our coffe shop.   
This information is stored in a PgSQL table and we will use the postgres-cdc connector.

Right-click on the statement, and then select `Run` to execute the SQL statement.  

```sql,line-numbers,wrap
CREATE TABLE product_lookup (
  product_id string,
  category string,
  item string,
  size string,
  cogs string,
  price string,
  inventory_level string,
  contains_fruit string,
  contains_veggies string,
  contains_nuts string,
  contains_caffeine string,
  PRIMARY KEY (product_id) NOT ENFORCED
) WITH (
  'connector'                 = 'postgres-cdc',
  'hostname'                  = 'host.minikube.internal',
  'port'                      = '5432',
  'username'                  = 'cdc_user',
  'password'                  = 'admin1',
  'database-name'             = 'system',
  'schema-name'               = 'public',
  'table-name'                = 'product_lookup',
  'slot.name'                 = 'flink_cdc_slot',
  'decoding.plugin.name'      = 'pgoutput',
  'debezium.publication.name' = 'all_tables_pub'
);
```
In the bottom panel you will see the following message: **Query has been executed**.

In the Editor toolbar, click `Debug` to execute the SQL statement.  You will also be able to see the new created table on the Catalog (left side of the SQL Editor).

Again, let's confirm the table creation was successful.  
Run the follow statement in the SQL Editor to print the `product_lookup` table rows. Replace any previous query.

```sql,line-numbers,wrap
SELECT * FROM product_lookup;
```

You will be able to see the product information in a tabular format.  
Great! You have created the `product_lookup` table and now it's all set.

> [!WARNING]
> Make sure to stop the SELECT query. Click on the `stop` button located in the result grid.

<!---SECTION: Lab 2: Processing Data in Real-time -->

Lab 2: Processing Data in Real-time
===
In this second lab, you will learn how develop and run data enrichment and aggregations with Flink .

### Step 1: Enchich the purchase stream:

The first step we need to do is to enrich the purchase stream with the product details, so the see the actual product name instead of product id. To do that, we are going to a JOIN function and match `product_id` column from both tables.

Go to SQL Editor, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
SELECT
   transaction_time,
   item,
   category,
   quantity,
   total_purchase
FROM purchase_stream
JOIN product_lookup
ON purchase_stream.product_id = product_lookup.product_id
```
In the Editor toolbar, click `Debug` to execute the SQL statement.   
Observe now that the column `ìtem` displays the product name. Category is also part of `product_lookup` dataset.

> [!WARNING]
> Make sure to stop the SELECT query. Click on the `stop` button located in the result grid.

### Step 2: Run basic TUMBLE aggregation:

Now that data is enriched, we can do basic analytics. Let's start aggregating by the `item` attribute every 10 seconds. To do this, we will use the TUMBLE window function as you can see below.

Go to SQL Editor, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
SELECT
  item,
  SUM(total_purchase) AS sum_total_purchase,
  window_start AS purchase_window
FROM TABLE(
  TUMBLE(TABLE purchase_stream, DESCRIPTOR(transaction_time), INTERVAL '60' SECONDS)
) AS purchase_stream
JOIN product_lookup
  ON purchase_stream.product_id = product_lookup.product_id
GROUP BY
  window_start,
  window_end,
  item
```

In the Editor toolbar, click `Debug` to execute the SQL statement.   
Observe the different value of the column `purchase_window`. It is a TIMESTAMP column, increasing its value in 10-second intervals. This is exactly what we are looking for, aggregate the data in 10-seconds window.

> [!WARNING]
> Make sure to stop the SELECT query. Click on the `stop` button located in the result grid.

### Step 3: Run basic HOPPING aggregation:

Let's try a new Window function. **Hopping** also us to have a different window size and window slide. In this example, the query aggregates the sales of the last 60 seconds, reported every 10 seconds, only for the *Superfoods Smoothies*	produc category.

Go to SQL Editor, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
SELECT
   item,
   SUM(total_purchase) AS sum_total_purchase,
   window_start AS purchase_window
FROM TABLE(
  HOP(TABLE purchase_stream, DESCRIPTOR(transaction_time), INTERVAL '10' SECONDS, INTERVAL '60' SECONDS)
) AS purchase_stream
JOIN product_lookup
ON purchase_stream.product_id = product_lookup.product_id
WHERE category = 'Superfoods Smoothies'
GROUP BY
  window_start,
  window_end,
  item
```

In the Editor toolbar, click `Debug` to execute the SQL statement.    
Observe the different value of the column `purchase_window`. It is a TIMESTAMP column, increasing its value in 10-second intervals. This is exactly what we are looking for, aggregate the data in 10-seconds window.

> [!WARNING]
> Make sure to stop the SELECT query. Click on the `stop` button located in the result grid.


### Step 4: Sales Report:

Finally, the business wants to see how the sales perform including information about the product, where the sales took place (state) and the relevant metrics to take decisions with a 30 seconds window.

Go to SQL Editor, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
SELECT
   item,
   category,
   state,
   window_start,
   COUNT(quantity) ,
   SUM(quantity) AS sum_quantity,
   SUM(purchase_stream.price),
   SUM(member_discount),
   SUM(supplement_price),
   SUM(total_purchase),
   AVG(total_purchase)
FROM TABLE(
  TUMBLE(TABLE purchase_stream, DESCRIPTOR(transaction_time), INTERVAL '30' SECONDS)
) AS purchase_stream
JOIN product_lookup
ON purchase_stream.product_id = product_lookup.product_id
GROUP BY
  window_start,
  window_end,
  item,
  category,
  state
```

In the Editor toolbar, click `Debug` to execute the SQL statement.    

Done! We have our data enriched and aggregated. Great job!

> [!WARNING]
> Make sure to stop the SELECT query. Click on the `stop` button located in the result grid.

<!---SECTION: Lab 3: Sink Processed Data -->
Lab 3: Sink Processed Data
===

### Step 1: Create a Catalog
Let's create our Catalog pointing to the Postgres database. When creating a Catalog in Flink, the creation process will scan the databases and tables the user configured in the connection has access and create the metadata. Once the CREATE CATALOG process is finished, developers can use the tables create for queries.

Go to SQL Editor, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
CREATE CATALOG dwh WITH (
  'type'             = 'postgres',
  'base-url'         = 'jdbc:postgresql://host.minikube.internal:5432',
  'default-database' = 'sales_report',
  'username'         = 'root',
  'password'         = 'admin1'
)
```
In the Editor, select the CATALOG DDL, right-click and then click on `Run` option to execute the SQL statement.   
To see the new *dwh* Catalog, click on the refresh button in the Catalog.

### Step 2: Describe report table

The target table is called *purchase_report*.  Use the `+` buttons to navigate to the table: dwh -> sales_report -> purchase_report.   
Once you find it, right click on the table name (see the image below).

![7.png](screenshots/7.png)

Close the Table columns description panel (the `_` icon located beside the table name).

### Step 3: Writing results to the table

Now that we confirmed the destination table we will sink the result data is created, it's time to deployed the job that will run our data enrichment and aggregation and store the results.

Go to SQL Editor, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
INSERT INTO dwh.sales_report.purchase_report
SELECT
   item,
   category,
   state,
   window_start,
   COUNT(quantity) ,
   SUM(quantity) AS sum_quantity,
   SUM(purchase_stream.price),
   SUM(member_discount),
   SUM(supplement_price),
   SUM(total_purchase),
   AVG(total_purchase)
FROM TABLE(
  TUMBLE(TABLE purchase_stream, DESCRIPTOR(transaction_time), INTERVAL '30' SECONDS)
) AS purchase_stream
JOIN product_lookup
ON purchase_stream.product_id = product_lookup.product_id
GROUP BY
  window_start,
  window_end,
  item,
  category,
  state
```

In the Editor toolbar, click on `Save As`, to open a window to enter the draft name. 

![8.png](screenshots/8.png)

Introduce *sales-aggreation-job* to help to identify this script later.  

![9.png](screenshots/9.png)

### Step 4: Deploying the Job

Once you saved the SQL draft with the right name, a new editor tab will open.  
In the Editor toolbar, click on `Deploy` to start a Flink SQL deployment.  

![10.png](screenshots/10.png)

Noq you will be asked to create a SQL Deployment. Click `Confirm` to start the deployment process.

![11.png](screenshots/11.png)

The Deployment process is started.

![12.png](screenshots/12.png)


If successfully deployed, you will see a confirmation message.

![13.png](screenshots/13.png)

### Step 5: Start the job

The previous process just create a Deployment definition, but the job is not immediately started.  

Go to Deployments (left-hand side menu), the newly job created.  
Click on `Start` to go the the next step.

![14.png](screenshots/14.png)

Click on `Start` again with the *Iniital Mode* selected.

![15.png](screenshots/15.png)

In the Deployment list, you will see the deployment in the *Stating* state.

![16.png](screenshots/16.png)

After some seconds, the Deployment changes to *Running* state.   
Click on the Deployment name to review the details. 

![17.png](screenshots/17.png)

In the Deployment page, click on `Status` tab. 

![18.png](screenshots/18.png)

You will see all the different Flink operator that composes the pipeline.

Click on the *Lineage* tab to observe the Job Graph, including the data sources, the job in the middle and the destination:

![18.png](screenshots/19.png)

*Click on `Column Level` button to see the job Lienage but at column level. 

### Step 6: Confirm data is sinking to Postgres
Let's run a simple SELECT to check data is landing in the Postgres table. Run the following command in the CLI tab to start a Postgres database connection. Introduce the password 'admin1':

```bash,line-numbers,wrap
psql -p 5432 -d sales_report -U root -W -h host.minikube.internal
```

Once the Postgres client connection is ready, copy and paste the following query:

```sql,line-numbers,wrap
SELECT count(*) FROM purchase_report;
```
And press ENTER to execute the SQL. This query will return the number of records (COUNT function) currently stored in the table.

![20.png](screenshots/20.png)

```sql,line-numbers,wrap
SELECT * FROM purchase_report LIMIT 50;
```
And press ENTER to execute the SQL. This query will return 50 records.  
Type `q` to leave the result page.

We've got 1.081 records. You will see a different number of rows for your lab environment. All good, data is sinking to Postgres and your pipeline is running properly!

<!---SECTION: Lab 4: Build Real-Time Visualizations -->

Lab 4: Build Real-Time Visualizations
===

### Step 1: Check the Data Source in Grafana

Go to Grafana tab, then click on the Grafana logo (top left-hand side) and go to Connections -> Data Source.  
The connection to the *sales_report* Postgres databases is already pre-created for you.  

![21.png](screenshots/21.png)

Click on the *sales_dwh* connection to check the details.  
The Host URL and Database name are exactly the same we used to create the Postgres Catalog before.

![22.png](screenshots/22.png)

In the top right, click on the `Buid a dashboard` button to load the Grafana template for our use case.

### Step 2: Import a  Grafana template

First, download the JSON template that you will use.

Right click on this [link](https://raw.githubusercontent.com/campossalex/apacheflink-labday-1/refs/heads/master/grafana-dashboard.json) and save the JSON file in your computer.

Click on the `Create Dashboard` button.
![23.png](screenshots/23.png)

Click on `Upload dashboard JSON file`. A window will open to select the JSON template file downloaded in your computer.
![24.png](screenshots/24.png)

Once file is selected, a second page is opened to set the dashboard Name. Just click on the `Import` blue button.
![25.png](screenshots/25.png)

Now the Dashboard will load the data using the connection created to the Postgres database.
![26.png](screenshots/26.png)

In the top right menu, you can change the time selection.   
Also select `5s` in the drop menu in the `Refresh` button to automatically reload the dashboard data.  

Congrats, you made it 👏 Now dashboard is loading data in real-time. The default time range is set to the last 30 minutes. Change the range and observe the new data that will be loaded.
