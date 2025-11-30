#!/usr/bin/env bash
set -euo pipefail

# ===== CONFIG (override via env vars if you want) =====
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-rootpassword}"   # root pass we'll set if empty
MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"

DB_NAME="${DB_NAME:-registration_db}"
DB_USER="${DB_USER:-registration_user}"
DB_PASSWORD="${DB_PASSWORD:-registration_password}"

FLASK_SECRET_KEY="${FLASK_SECRET_KEY:-super-secret-key}"
# =====================================================

echo "==> Updating apt and installing MySQL + Python tools..."
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  mysql-server \
  python3-venv \
  python3-pip \
  build-essential \
  libmysqlclient-dev

echo "==> Securing MySQL and setting root password (basic non-interactive setup)..."

# Configure MySQL root user password & auth method on Ubuntu (local root)
sudo mysql <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${MYSQL_ROOT_PASSWORD}';
FLUSH PRIVILEGES;
EOF

# Allow MySQL to listen on all interfaces
MYSQL_CONF="/etc/mysql/mysql.conf.d/mysqld.cnf"
if [ -f "$MYSQL_CONF" ]; then
  echo "==> Updating bind-address in $MYSQL_CONF to 0.0.0.0 ..."
  sudo sed -i "s/^bind-address\s*=.*/bind-address = 0.0.0.0/" "$MYSQL_CONF" || true
fi

echo "==> Restarting MySQL..."
sudo systemctl restart mysql

echo "==> Creating database and user (with external access) in MySQL..."

MYSQL_ROOT_FLAGS="-h ${MYSQL_HOST} -P ${MYSQL_PORT} -u root -p${MYSQL_ROOT_PASSWORD}"

# Create DB
mysql ${MYSQL_ROOT_FLAGS} <<EOF
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF

# Create user that can connect from anywhere
mysql ${MYSQL_ROOT_FLAGS} <<EOF
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;
EOF

# Create registrations table
mysql -h "${MYSQL_HOST}" -P "${MYSQL_PORT}" -u "${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" <<EOF
CREATE TABLE IF NOT EXISTS registrations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100 NULL,
  surname VARCHAR(100) NULL,
  email VARCHAR(255) NULL,
  lab_url VARCHAR(255) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF

echo "==> MySQL DB, user, and table configured."

echo "==> Creating Python virtualenv and installing requirements..."
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Compute server IP for JDBC URL
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "${SERVER_IP}" ]; then
  SERVER_IP="${MYSQL_HOST}"
fi

echo "=========================================================="
echo " MySQL is ready. JDBC URL for external connections:"
echo
echo "   jdbc:mysql://${SERVER_IP}:${MYSQL_PORT}/${DB_NAME}"
echo "   user: ${DB_USER}"
echo "   password: ${DB_PASSWORD}"
echo
echo "NOTE: Make sure any cloud firewall / security group also"
echo "      allows inbound TCP ${MYSQL_PORT} from your clients."
echo "=========================================================="

echo "==> Exporting env vars and starting Flask app..."

export DB_HOST="${MYSQL_HOST}"
export DB_PORT="${MYSQL_PORT}"
export DB_NAME="${DB_NAME}"
export DB_USER="${DB_USER}"
export DB_PASSWORD="${DB_PASSWORD}"
export FLASK_SECRET_KEY="${FLASK_SECRET_KEY}"

python app.py

