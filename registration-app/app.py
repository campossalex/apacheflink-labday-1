import os
import pymysql
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-me")

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_NAME = os.environ.get("DB_NAME", "registration_db")
DB_USER = os.environ.get("DB_USER", "registration_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "registration_password")


def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

def get_one_null_email_record():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id 
                FROM registrations
                WHERE email IS NULL
                ORDER BY id ASC
                LIMIT 1;
            """)
            return cur.fetchone()
    finally:
        conn.close()

@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        surname = request.form.get("surname", "").strip()
        email = request.form.get("email", "").strip()
        company = request.form.get("company", "").strip()
        role = request.form.get("role", "").strip()

        if not name or not surname or not email:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("register"))

        row = get_one_null_email_record()

        if not row:
            flash("Sorry, no environments available!", "error")
            return redirect(url_for("register")) 
            
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE registrations 
                    SET name = %s, surname = %s, email = %s, company = %s, role = %s
                    WHERE email IS NULL
                    LIMIT 1;
                    """,
                    (name, surname, email, company, role),
                )

                cur.execute("""
                    SELECT lab_url
                    FROM registrations
                    WHERE email = %s
                    LIMIT 1;
                    """, (email,)
                )
                row = cur.fetchone()
                lab_url = "http://" + row["lab_url"]

            conn.close()
        except Exception as exc:
            app.logger.error("Error inserting registration: %s", exc)
            flash("Error saving registration. Please try again later.", "error")
            return redirect(url_for("register"))

        # Redirect to welcome page with name & username
        return render_template("welcome.html", name=name, lab_url=lab_url)

    return render_template("register.html")

@app.route("/registrations")
def list_registrations():
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM registrations ORDER BY created_at DESC")
            rows = cur.fetchall()
        conn.close()
    except Exception as exc:
        app.logger.error("Error fetching registrations: %s", exc)
        rows = []

    return render_template("registrations.html", registrations=rows)

@app.route("/welcome")
def welcome():
    name = request.args.get("name", "")
    username = request.args.get("username", "")
    if not name or not username:
        return redirect(url_for("register"))
    return render_template("welcome.html", name=name, username=username)


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 80)), debug=True)

