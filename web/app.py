import sys
from flask import Flask, render_template_string

app = Flask(__name__)

# Capture command-line argument
# Example: python app.py myvalue
public_ip = sys.argv[1] if len(sys.argv) > 1 else "default_value"

@app.route("/")
def home():
    sites = [
        {"name": "VVP", "port": "8080"},
        {"name": "Grafana", "port": "8085"},
        {"name": "Redpanda", "port": "9090"},
        {"name": "Web Shell", "port": "4200"},
    ]

    # HTML template string with dynamic table and concatenated links
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Apache Flink Lab Day</title>
        <style>
            body { font-family: Arial, sans-serif; background: #fafafa; margin: 40px; }
            table { border-collapse: collapse; width: 50%; margin: auto; background: white; }
            th, td { border: 1px solid #ccc; padding: 10px; text-align: center; }
            th { background-color: #eee; }
            img { width: 300px; margin: 10px; }
            h1 { text-align: center; }
            h3 { text-align: center; }
        </style>
    </head>
    <body>
        <h1> Apache Flink Lab Day </h1>

        <div style="text-align:center;">
            <img src="https://raw.githubusercontent.com/campossalex/apacheflink-labday-1/refs/heads/master/web/ververica-logo_navy.png">
        </div>

        <h3> Lab Instructions: <a href="https://github.com/campossalex/apacheflink-labday-1/blob/master/instructions.MD" target="_blank">Open</a></h3>

        <h3> Access to components:</h3>

        <table>
            <tr>
                <th>Component</th>
                <th>URL</th>
            </tr>
            {% for site in sites %}
            <tr>
                <td>{{ site.name }}</td>
                <td><a href="{{ "http://" + public_ip + ":" + site.port }}" target="_blank">Open</a></td>
            </tr>
            {% endfor %}
        </table>

        <h3> Credentials:</h3>

        <table>
            <tr>
                <th>Component</th>
                <th>User</th>
                <th>Password</th>

            </tr>
            <tr>
                <td>Web Shell</td>
                <td>admin</td>
                <td>admin1</td>
            </tr>
            <tr>
                <td>Postgres</td>
                <td>root</td>
                <td>admin1</td>
            </tr>
        </table>
    </body>
    </html>
    """

    # Render page with the site data
    return render_template_string(html, sites=sites, public_ip=public_ip)


if __name__ == "__main__":
    print(f"Starting Flask app with arg_value = {public_ip}")
    app.run(host="0.0.0.0", port=80, debug=True)
