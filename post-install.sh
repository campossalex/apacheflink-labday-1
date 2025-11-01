#!/usr/bin/env bash

# install pip and python libs
python3 ververica-platform-playground/get-pip.py
pip3 install faker kafka-python

# postgresql install
yum install postgresql postgresql-server -y
sudo postgresql-setup initdb
rm -rf /var/lib/pgsql/data/pg_hba.conf
cp ververica-platform-playground/pgsql/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf
printf '%s\n' >> "/var/lib/pgsql/data/postgresql.conf" \
  "listen_addresses = '*'"
systemctl restart postgresql

sudo cp ververica-platform-playground/pg_ddl.sql /pg_ddl.sql
sudo chown postgres:postgres /pg_ddl.sql
sudo -i -u postgres psql -a -w -f /pg_ddl.sql

# install redpanda
curl -1sLf 'https://dl.redpanda.com/nzc4ZYQK3WRGd9sy/redpanda/cfg/setup/bash.rpm.sh' | \
sudo -E bash && sudo yum install redpanda -y

rm -rf /etc/redpanda/redpanda.yaml
cp ververica-platform-playground/redpanda/redpanda.yaml /etc/redpanda/redpanda.yaml
systemctl start redpanda

sudo yum install redpanda-console -y
printf '%s\n' >> "/etc/redpanda/redpanda-console-config.yaml" \
  'server:' \
  '  listenAddress: "0.0.0.0"' \
  '  listenPort: 9090'
systemctl start redpanda-console

#product csv to minio
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
./mc alias set vvpminio http://localhost:9000 admin password --api S3v4
./mc mb vvpminio/data
./mc mb vvpminio/data/product
./mc od if=ververica-platform-playground/data/products.csv of=vvpminio/data/product/products.csv
