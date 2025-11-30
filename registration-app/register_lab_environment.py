import time
import pymysql
import sys

DB_HOST = "172.31.25.18"
DB_PORT = 3306
DB_NAME = "registration_db"
DB_USER = "registration_user"
DB_PASSWORD = "registration_password"

# retry settings
MAX_RETRIES = 10
RETRY_DELAY = 3  # seconds


def insert_registration(lab_url):

    retries = 0
    while retries < MAX_RETRIES:
        try:
            conn = pymysql.connect(
                host=DB_HOST,
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
            print("Record inserted successfully!")
            return True

        except pymysql.MySQLError as e:
            print(e)
            retries += 1
            if retries < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    lab_url = sys.argv[1]

    insert_registration(lab_url)
