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
> Please skip the license message you will see in the different components. This lab environment is for training purposes, so licenses are not required.

Lab 1: Connecting with Data Sources
===
In this first lab, you will learn how to create Dynamic Table to consume data from a Kafka topic and from a CSV file stored in Minio (s3).

### Step 1: Check the data in the Kafka topic:
Go to Redpanda tab to see the actual data arriving in the Kafka topic.

Navigate to the `Topics` option in the left-hand side menu, and then link on the topic `store.purchases` . This is where the purchases events are arriving in Kafka.  Choose one of the messages, and click on the arrow to expand the event details. You will be able to see the actual JSON data.

![1.png](https://github.com/campossalex/apacheflink-labday-1/blob/101cd07a146271c6124660d975e48ebc9ce9610c/web/screenshots/1.png)

This confirms purchase events are generated and published to the Kafka topic.

### Step 2: Create a Flink Table to consume purchase events:
Now it's time to create our first Dynamic Table. We are going to call this table `purchase_stream`to represent the purchases events generated in real-time.

Go to Ververica tab, then SQL -> SQL Scripts, copy and paste the following SQL statement in the SQL Editor:

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

In the Editor toolbar, click `Run` to execute the SQL statement.  You will also be able to see the new created table on the Catalog (left side of the SQL Editor).

### Step 3: Run a SELECT statement to print purchase events from the Kafka topic:

A good way to confirm the table creation works well, is running a SELECT query and see the actual data.  Run the follow statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
SELECT * FROM purchase_stream;
```
You will be able to see the purchase event, but now in a tabular format. Great! You have created your first Dynamic Table. Now let's create the table with the product reference data.

To stop the SELECT query, click on the pause `||` button located above the result grid.

### Step 4: Create a Flink Table to consume the file:

Now it's time to create our second Dynamic Table. We are going to call this table `master_product` to represent the information about each product of our coffe shop. This information is stoed in Minio (s3) in a CSV file. We will this data to enrich the purchase stream.

Go to Ververica tab, then SQL -> SQL Scripts, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
CREATE TABLE master_product (
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
  'connector' = 'filesystem',
  'path' = 's3://data/product',
  'format' = 'csv'
);
```
In the Editor toolbar, click `Run`to execute the SQL statement.  You will also be able to see the new created table on the Catalog (left side of the SQL Editor).

### Step 5: Run a SELECT statement to print master_product:

Again, let's confirm the table creation was successful.  Run the follow statement in the SQL Editor to print the `master_product` table rows. Replace any previous query.

```sql,line-numbers,wrap
SELECT * FROM master_product;
```

You will be able to see the product information, but now in a tabular format. Great! You have created the `master_product` table and now it's all set.

To stop the SELECT query, click on the pause `||` button located above the result grid.

### Optional:

If you are curious to see the CSV file that contains the product details, you can print its content using the Minio CLI tool. Run the following command in the CLI tab.

```bash,line-numbers,wrap
./mc cat vvpminio/data/product/products.csv
```

The command `cat` will read the file and print its content in the screen. It is a useful way to print file's content.

Lab 2: Processing Data in Real-time
===
In this second lab, you will learn how develop and run data enrichment and aggregations with Flink .

### Step 1: Enchich the purchase stream:

The first step we need to do is to enrich the purchase stream with the product details, so the see the actual product name instead of product id. To do that, we are going to a JOIN function and match `product_id` column from both tables.

Go to Ververica tab, then SQL -> SQL Scripts, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
SELECT
   transaction_time,
   item,
   category,
   quantity,
   total_purchase
FROM purchase_stream
JOIN master_product
ON purchase_stream.product_id = master_product.product_id
```
In the Editor toolbar, click `Run`to execute the SQL statement.  Observe now that the column ìtem` displays the product name. Category is also part of `master_product` dataset.

### Step 2: Run basic TUMBLE aggregation:

Now that data is enriched, we can do basic analytics. Let's start aggregating by the `item` attribute every 10 seconds. To do this, we will use the TUMBLE window function as you can see below.

Go to Ververica tab, then SQL -> SQL Scripts, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
SELECT
   item,
   SUM(total_purchase) AS sum_total_purchase,
   TUMBLE_START(transaction_time, INTERVAL '10' SECONDS) AS purchase_window
FROM purchase_stream
JOIN master_product
ON purchase_stream.product_id = master_product.product_id
GROUP BY
  TUMBLE(transaction_time, INTERVAL '10' SECONDS),
  item
```
In the Editor toolbar, click `Run`to execute the SQL statement.  Observe the different value of the column `purchase_window`. It is a TIMESTAMP column, increasing its value in 10-second intervals. This is exactly what we are looking for, aggregate the data in 10-seconds window.

### Step 3: Run basic HOPPING aggregation:

Let's try a new Window function. **Hopping** also us to have a different window size and window slide. In this example, the query aggregates the sales of the last 60 seconds, reported every 10 seconds, only for the *Superfoods Smoothies*	produc category.

Go to Ververica tab, then SQL -> SQL Scripts, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
SELECT
   item,
   SUM(total_purchase) AS sum_total_purchase,
   HOP_START(transaction_time, INTERVAL '10' SECONDS, INTERVAL '60' SECONDS) AS purchase_window
FROM purchase_stream
JOIN master_product
ON purchase_stream.product_id = master_product.product_id
WHERE category = 'Superfoods Smoothies'
GROUP BY
  HOP(transaction_time, INTERVAL '10' SECONDS, INTERVAL '60' SECONDS),
  item
```

In the Editor toolbar, click `Run`to execute the SQL statement.  Observe the different value of the column `purchase_window`. It is a TIMESTAMP column, increasing its value in 10-second intervals. This is exactly what we are looking for, aggregate the data in 10-seconds window.

### Step 4: Sales Report:

Finally, the business wants to see how the sales perform including information about the product, where the sales took place (state) and the relevant metrics to take decisions with a 30 seconds window.

Go to Ververica tab, then SQL -> SQL Scripts, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
SELECT
   item,
   category,
   state,
   COUNT(*) AS count_transactions,
   SUM(quantity) AS sum_quantity,
   SUM(purchase_stream.price) AS sum_price,
   SUM(member_discount) AS sum_member_discount,
   SUM(supplement_price) AS sum_supplement_price,
   SUM(total_purchase) AS sum_total_purchase,
   AVG(total_purchase) AS avg_total_purchase,
   TUMBLE_START(transaction_time, INTERVAL '30' SECONDS) AS purchase_window
FROM purchase_stream
JOIN master_product
ON purchase_stream.product_id = master_product.product_id
GROUP BY
  TUMBLE(transaction_time, INTERVAL '30' SECONDS),
  item,
	category,
	state
```

In the Editor toolbar, click `Run`to execute the SQL statement.  Observe the results.

Done! We have our data enriched and aggregated. Great job!

Lab 3: Sink Processed Data
===

### Step 1: Create a Catalog
Let's create our Catalog pointing to the Postgres database. When creating a Catalog in Flink, the creation process will scan the databases and tables the user configured in the connection has access and create the metadata. Once the CREATE CATALOG process is finished, developers can use the tables create for queries.

Go to Ververica tab, then SQL -> SQL Scripts, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
CREATE CATALOG dwh WITH (
  'type' = 'jdbc',
  'base-url' = 'jdbc:postgresql://host.minikube.internal:5432',
  'default-database' = 'sales_report',
  'username' = 'root',
  'password' = 'admin1'
)
```
In the Editor toolbar, click `Run`to execute the SQL statement.  Observe the *Schema Explorer* section will display the new Catalog as *dwh*.

### Step 2: Describe report table

The target table is called *purchase_report*.  Use the `+` buttons to navigate to the table: dwh -> sales_report -> purchase_report. Once you find it, right click on the table name and select the option *Describe* (see the image below).

![Screenshot 2025-08-25 at 02.18.55.png](https://github.com/campossalex/apacheflink-labday-1/blob/2ffd17afa410933e1423686731fdeacfd2dee47e/web/screenshots/Screenshot%25202025-08-25%2520at%252002.18.55.png)

*DESCRIBE* is a DDL function to list table's columns name and data type. In the SQL Editor, this informations will be displayed in the bottom. Scroll down to check this information (see image below).

![Screenshot 2025-08-25 at 02.20.03.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/4edaded6f97e8ef37e55303e6ff0c973/assets/Screenshot%202025-08-25%20at%2002.20.03.png)

Close the Describe column panel (the `x`icon in the image above).

### Step 3: Writing results to the table

Now that we confirmed the destination table we will sink the result data is created, it's time to deployed the job that will run our data enrichment and aggregation and store the results.

Go to Ververica tab, then SQL -> SQL Scripts, copy and paste the following SQL statement in the SQL Editor. Replace any previous query:

```sql,line-numbers,wrap
INSERT INTO dwh.sales_report.purchase_report
SELECT
   item,
   category,
   state,
   TUMBLE_START(transaction_time, INTERVAL '30' SECONDS),
   COUNT(quantity) ,
   SUM(quantity) AS sum_quantity,
   SUM(purchase_stream.price),
   SUM(member_discount),
   SUM(supplement_price),
   SUM(total_purchase),
   AVG(total_purchase)
FROM purchase_stream
JOIN master_product
ON purchase_stream.product_id = master_product.product_id
GROUP BY
  TUMBLE(transaction_time, INTERVAL '30' SECONDS),
  item,
	category,
	state
```
### Step 4: Deploying the Job

In the Editor toolbar, click on `Run` to execute the SQL statement.  At this moment, you will be asked to create a SQL Deployment. Click `OK` to start the deployment process.
![Screenshot 2025-08-26 at 00.27.36.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/d80fe809d19c6a1f7895a7278af6781d/assets/Screenshot%202025-08-26%20at%2000.27.36.png)

In the Create SQL Deployment, enter 'sales_aggregation_job' for  *Deployment Name* and select 'sql-editor' in *Deployment Target*.
![Screenshot 2025-08-26 at 00.29.10.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/7eaee7ffb7cd75530c101c0f0af4f28a/assets/Screenshot%202025-08-26%20at%2000.29.10.png)

When you select the 'sql-editor' target to run your job,  you are choosing a Session Cluster. Just confirm by clicking on `OK` button.
![Screenshot 2025-08-26 at 00.29.25.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/af2c5a4e1818e06558fe544976536eb3/assets/Screenshot%202025-08-26%20at%2000.29.25.png)

Confirm Parallelism is set '1' for our job and then click on `Create SQL Deployment`. The deployment will start and compute resource will be allocated to run the job:
![Screenshot 2025-08-26 at 00.30.06.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/5596b75448b670cea3277bf10797710a/assets/Screenshot%202025-08-26%20at%2000.30.06.png)

### Step 5: Deployment Job Status
Once the Deployment is triggered, the page will displayed the job status. Wait for a few minutes and the job will change to *Running* status (green):
![Screenshot 2025-08-26 at 00.30.50.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/9b70e3390b114471dcc18ba9a127229a/assets/Screenshot%202025-08-26%20at%2000.30.50.png)

Click on the *Events* tab to confirm the latest status is 'Transition to RUNNING completed':
![Screenshot 2025-08-26 at 00.32.12.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/366226be0b4a8b79015c3a8ca2b6763f/assets/Screenshot%202025-08-26%20at%2000.32.12.png)

Click on the *Overview* tab to observe the Job Graph, including the data sources, the job in the middle and the destination:

![Screenshot 2025-08-26 at 10.44.40.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/ea3dff210c72562967a7d66014939155/assets/Screenshot%202025-08-26%20at%2010.44.40.png)

### Step 6: Confirm data is sinking to Postgres
Let's run a simple SELECT to check data is landing in the Postgres table. Run the following command in the CLI tab to start a Postgres database connection. Introduce the password 'admin1':

```bash,line-numbers,wrap
psql -p 5432 -d sales_report -U root -W -h kubernetes-vm
```

Once the Postgres client connection is ready, copy and paste the following query:

```sql,line-numbers,wrap
SELECT count(*) FROM purchase_report;
```
And press ENTER to execute the SQL. This query will return the number (COUNT function) of records that are currently stored in the table.

![Screenshot 2025-08-26 at 10.45.41.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/3a9b4708d415931334a6bae49abf6c83/assets/Screenshot%202025-08-26%20at%2010.45.41.png)

We've got 1.081 records. You will see a different number of rows for your lab environment. All good, data is sinking to Postgres and your pipeline is running properly!


Lab 4: Build Real-Time Visualizations
===

### Step 1: Create a Data Source in Grafana
Go to Grafana tab, then click on the Grafana logo (top left-hand side) and go to Connections -> Add new connection:

![Screenshot 2025-08-26 at 10.55.45.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/518c753d0887f61950e3d42aa021768d/assets/Screenshot%202025-08-26%20at%2010.55.45.png)

Type 'Postgres' in the search bar to create a Postgres connection , then click on the Postgres logo:

![Screenshot 2025-08-26 at 10.57.19.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/3e7d7e4fa920f738b3df4487a56c3f52/assets/Screenshot%202025-08-26%20at%2010.57.19.png)

Once in the new Data source form, enter 'sales_dwh' in the Name field:

![Screenshot 2025-08-26 at 12.50.31.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/bfc72b4a299eead82fa1cd198d40b762/assets/Screenshot%202025-08-26%20at%2012.50.31.png)

In Connection section, add the following values:

- **Host URL**: host.minikube.internal:5432
- **Database name**: sales_report

In Authtentication, add the following values:

- **Username**: root
- **Password**: admin1

![Screenshot 2025-08-26 at 11.00.45.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/6d9dbeb4b7add3efa921e82ea2b67fc1/assets/Screenshot%202025-08-26%20at%2011.00.45.png)

- In **TLS/SSL Auth Details**, select Disabled.
-
- In **Additional Settings**, select Version 12.

![Screenshot 2025-08-26 at 10.59.57.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/c6cbd2fd474b1f18babce8a69533217c/assets/Screenshot%202025-08-26%20at%2010.59.57.png)

Now click on the `Save & Test` button to create the connection.

If process is correct, you will see a confirmation message:

![Screenshot 2025-08-26 at 11.00.56.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/aaa9e540c2f6c4258247c41ad6515557/assets/Screenshot%202025-08-26%20at%2011.00.56.png)

Now you are connect to create your first dashboard. Click on the 'build a dahsboard' link to start to create a new dashboard. If you are familiar with Grafana, you can use your creative to build a dashboard and graphs.

If not, you can import the dashboard we built for this use case.

### Step 2: Import a  Grafana template

First, download the JSON template that you will use.


Right click on this [link](https://raw.githubusercontent.com/campossalex/ververica-platform-playground/refs/heads/master/grafana-dashboard.json) and file the JSON file in your computer.

Click on the Grafana logo (top left-hand side) and select the option *Dashboards*.
![Screenshot 2025-08-26 at 21.43.10.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/f12008db88eb4ccfc565a738f21709d6/assets/Screenshot%202025-08-26%20at%2021.43.10.png)

Click on the `Create Dashboard` button.
![Screenshot 2025-08-26 at 21.43.28.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/fc14435a2b8b839b97d2dbddb60bb595/assets/Screenshot%202025-08-26%20at%2021.43.28.png)

Then click on the `Import Dashboard`  button to start a new import process.
![Screenshot 2025-08-26 at 21.44.14.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/1c04e0f142aca847971f408f8fb8d6ed/assets/Screenshot%202025-08-26%20at%2021.44.14.png)

Click on `Upload dashboard JSON file`. A window will open to select the JSON template file downloaded in your computer.
![Screenshot 2025-08-26 at 21.44.44.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/342369daac454e17baf4a8e3082f9a9d/assets/Screenshot%202025-08-26%20at%2021.44.44.png)

Once file is selected, a second page is opened to set the dashboard Name. Just click on the `Import` blue button.
![Screenshot 2025-08-26 at 21.45.22.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/189607b9f30fa9305e90aec041b12489/assets/Screenshot%202025-08-26%20at%2021.45.22.png)

Dashboard is imported successfuly, but graphs and data is not lodaded. You need now to link the dashboard with the data source created previously.
Located on the top right-side of the Dashboard panel, click on `Edit` button, then `Settings`.
![Screenshot 2025-08-26 at 21.46.44.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/0c0588c2fd8fd700512f4e92f3f460a2/assets/Screenshot%202025-08-26%20at%2021.46.44.png)

Once in the dashboard settings page, click on the *Variables* tab, then `+ New Variable` to create a new variable.
![Screenshot 2025-08-26 at 22.28.22.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/065e4247c7dbebdb0b6acd70b84d4d65/assets/Screenshot%202025-08-26%20at%2022.28.22.png)

A new variable form is displayed. Fill it up with the following information:

- **Variable type**: Data source
- **Name**: datasource (case sensitive)
- **Data Source type**: Postgres

![Screenshot 2025-08-26 at 21.47.31.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/e7cabda7878cb7b83243bf02ec498c16/assets/Screenshot%202025-08-26%20at%2021.47.31.png)

At the bottom of the form, confirm 'Preview of values' shows the data source name we set before, 'sales_dwh'. That means Grafana will be able to replace the variable placeholder by the datasource id.
![Screenshot 2025-08-26 at 21.47.53.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/2a2e8e7b6fe7295e82b2271ba4e13e92/assets/Screenshot%202025-08-26%20at%2021.47.53.png)

On the top right-side of the form, click on the `Save Dashboard` button to finish the configuration.
![Untitled 1.jpg](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/c4815918ff51c8582a53fcfbd64b569e/assets/Untitled%201.jpg)

Click on the `Save` blue button to finish the process.
![Screenshot 2025-08-26 at 21.48.18.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/06248f9432f3d402e6c413f644b7afb3/assets/Screenshot%202025-08-26%20at%2021.48.18.png)

Once the final step is closed, click on the `<- Back to Dashboard` button, located on the top right-side of the form.
![Untitled 2.jpg](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/06158585355e12d74f8dc31f7d35a5eb/assets/Untitled%202.jpg)

Now the Dashboard will load the data using the connection created to the Postgres database.
![Screenshot 2025-08-26 at 21.48.58.png](https://play.instruqt.com/assets/tracks/bqfnfdcejmah/dff55e3d5f0cca71e6f19ac3fe8d642f/assets/Screenshot%202025-08-26%20at%2021.48.58.png)

Congrats, you made it 👏 Now dashboard is loading data in real-time. The default time range is set to the last 30 minutes. Change the range and observe the new data that will be loaded.















