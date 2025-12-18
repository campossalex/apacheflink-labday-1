import time
import pymysql
import sys

DB_PORT = 3306
DB_NAME = "registration_db"
DB_USER = "registration_user"
DB_PASSWORD = "registration_password"

# retry settings
MAX_RETRIES = 50
RETRY_DELAY = 10  # seconds


def insert_registration(lab_url, mysql_host):

    retries = 0
    while retries < MAX_RETRIES:
        try:
            conn = pymysql.connect(
                host=mysql_host,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor,
            )

            with conn.cursor() as cur:
                sql = """
                INSERT INTO registrations (name, surname, email, lab_url)
                VALUES (NULL, NULL, NULL, %s)
                """
                cur.execute(sql, (lab_url))

            conn.close()
            print("Lab registered successfully!")
            return True

        except pymysql.MySQLError as e:
            print(e)
            retries += 1
            if retries < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(1)
        
    lab_url = sys.argv[1]
    mysql_host = sys.argv[2]

    insert_registration(lab_url, mysql_host)
