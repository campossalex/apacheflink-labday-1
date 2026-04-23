CREATE USER root WITH PASSWORD 'admin1';

CREATE DATABASE sales_report;

GRANT ALL PRIVILEGES ON DATABASE sales_report TO root;

\c sales_report;

CREATE TABLE purchase_report (dim_item VARCHAR(255), dim_category VARCHAR(255), dim_state VARCHAR(255), purchase_time TIMESTAMP, fact_count_transactions FLOAT, fact_sum_quantity FLOAT, fact_sum_price FLOAT, fact_sum_member_discount FLOAT, fact_sum_supplement_price FLOAT, fact_sum_total_purchase FLOAT, fact_avg_total_purchase FLOAT, PRIMARY KEY(dim_item, dim_category, dim_state, purchase_time));

CREATE INDEX idx_timestamp ON purchase_report (dim_item, dim_category, dim_state, purchase_time);

ALTER TABLE purchase_report OWNER TO root;
