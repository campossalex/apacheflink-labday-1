#!/usr/bin/env bash

# install pip and python libs
python3 ververica-platform-playground/setup/get-pip.py
pip3 install faker kafka-python flask pymysql

# postgresql 14 install
sudo cp ververica-platform-playground/pgsql/pgdg.repo /etc/yum.repos.d/pgdg.repo
sudo yum makecache
sudo yum install postgresql14 postgresql14-server -y
sudo postgresql-14-setup initdb
printf '%s\n' >> "/var/lib/pgsql/14/data/pg_hba.conf" \
  'host     all     all     0.0.0.0/0     md5'
printf '%s\n' >> "/var/lib/pgsql/14/data/postgresql.conf" \
  "listen_addresses = '*'"
systemctl restart postgresql-14

sudo cp ververica-platform-playground/pgsql/pg_ddl.sql /pg_ddl.sql
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

cp mc /home/admin/mc
chmod +x /home/admin/mc
cp -Rv .mc /home/admin/.
chown -R admin:admin /home/admin/.mc

## Register Lab Env
MYSQL_HOST="$(cat regform-ip.txt)"
PUBLIC_DNS=$(curl --silent http://169.254.169.254/latest/meta-data/public-hostname)
python3 ververica-platform-playground/registration-app/register_lab_environment.py $PUBLIC_DNS $MYSQL_HOST

## Start Web App
screen -dmS web_app bash -c 'PUBLIC_DNS=$(curl --silent http://169.254.169.254/latest/meta-data/public-hostname); python3 ververica-platform-playground/web/app.py $PUBLIC_DNS'
