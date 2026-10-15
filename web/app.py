import sys
import os
from flask import Flask, render_template_string, send_from_directory

app = Flask(__name__)
WEB_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route("/assets/<path:filename>")
def serve_asset(filename):
    return send_from_directory(WEB_DIR, filename)

# Capture command-line argument
# Example: python app.py myvalue
public_ip = sys.argv[1] if len(sys.argv) > 1 else "default_value"

@app.route("/")
def home():
    sites = [
        {"name": "Ververica Platform", "port": "8080"},
        {"name": "Grafana", "port": "8085"},
        {"name": "Redpanda", "port": "9090"},
        {"name": "Web Shell", "port": "4200"},
    ]

    # HTML template string with dynamic table and concatenated links
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Apache Flink Lab Day &middot; Ververica</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            /* ---- Custom properties ---- */
            @property --border-angle {
                syntax: '<angle>';
                initial-value: 0deg;
                inherits: false;
            }

            :root {
                --bg-deep: #0a0624;
                --bg-base: #120A3D;
                --bg-surface: rgba(255,255,255,0.04);
                --bg-surface-hover: rgba(255,255,255,0.07);
                --teal: #05b89c;
                --teal-glow: rgba(5,184,156,0.25);
                --purple: #4e21e8;
                --purple-light: #7c5cf5;
                --purple-glow: rgba(78,33,232,0.3);
                --text: #ffffff;
                --text-muted: rgba(255,255,255,0.55);
                --text-dim: rgba(255,255,255,0.3);
                --border: rgba(255,255,255,0.07);
                --border-hover: rgba(78,33,232,0.5);
                --radius: 14px;
                --mono: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
            }

            *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

            body {
                font-family: 'Manrope', system-ui, sans-serif;
                background: var(--bg-deep);
                color: var(--text);
                min-height: 100vh;
                overflow-x: hidden;
            }

            /* ---- Dot grid background ---- */
            .dot-grid {
                position: fixed;
                inset: 0;
                z-index: 0;
                pointer-events: none;
                background-image: radial-gradient(rgba(255,255,255,0.04) 1px, transparent 1px);
                background-size: 32px 32px;
                mask-image: radial-gradient(ellipse 70% 60% at 50% 30%, black 20%, transparent 100%);
                -webkit-mask-image: radial-gradient(ellipse 70% 60% at 50% 30%, black 20%, transparent 100%);
            }

            /* ---- Ambient glow orbs ---- */
            .glow-orb {
                position: fixed;
                border-radius: 50%;
                filter: blur(100px);
                pointer-events: none;
                z-index: 0;
            }
            .glow-orb.purple {
                width: 600px; height: 600px;
                top: -15%; left: 40%;
                background: rgba(78,33,232,0.12);
                animation: orbFloat 20s ease-in-out infinite;
            }
            .glow-orb.teal {
                width: 400px; height: 400px;
                bottom: -10%; right: -5%;
                background: rgba(5,184,156,0.06);
                animation: orbFloat 25s ease-in-out infinite reverse;
            }

            @keyframes orbFloat {
                0%, 100% { transform: translate(0, 0) scale(1); }
                33% { transform: translate(30px, -20px) scale(1.05); }
                66% { transform: translate(-20px, 15px) scale(0.95); }
            }

            /* ---- Container ---- */
            .container {
                position: relative;
                z-index: 1;
                max-width: 920px;
                margin: 0 auto;
                padding: 36px 28px 72px;
            }

            /* ---- Staggered entrance animations ---- */
            @keyframes fadeUp {
                from { opacity: 0; transform: translateY(24px); }
                to   { opacity: 1; transform: translateY(0); }
            }

            .anim {
                opacity: 0;
                animation: fadeUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) forwards;
            }
            .anim-d1 { animation-delay: 0.08s; }
            .anim-d2 { animation-delay: 0.18s; }
            .anim-d3 { animation-delay: 0.28s; }
            .anim-d4 { animation-delay: 0.38s; }
            .anim-d5 { animation-delay: 0.50s; }
            .anim-d6 { animation-delay: 0.60s; }
            .anim-d7 { animation-delay: 0.72s; }
            .anim-d8 { animation-delay: 0.84s; }

            /* ---- Hero with animated gradient border ---- */
            .hero-wrap {
                position: relative;
                padding: 2px;
                border-radius: 20px;
                margin-bottom: 40px;
                background: conic-gradient(from var(--border-angle), var(--purple), var(--teal), var(--purple-light), var(--teal), var(--purple));
                animation: rotateBorder 6s linear infinite;
            }

            @keyframes rotateBorder {
                to { --border-angle: 360deg; }
            }

            .hero-wrap::before {
                content: '';
                position: absolute;
                inset: 0;
                border-radius: 20px;
                background: conic-gradient(from var(--border-angle), var(--purple), var(--teal), var(--purple-light), var(--teal), var(--purple));
                filter: blur(24px);
                opacity: 0.35;
                z-index: -1;
                animation: rotateBorder 6s linear infinite;
            }

            .hero {
                background: var(--bg-deep);
                border-radius: 18px;
                text-align: center;
                padding: 36px 36px 36px;
                position: relative;
                overflow: hidden;
            }

            .hero::before {
                content: '';
                position: absolute;
                inset: 0;
                background: radial-gradient(ellipse at 50% 0%, rgba(78,33,232,0.15) 0%, transparent 60%);
                pointer-events: none;
            }

            .hero .logo {
                position: relative;
                display: block;
                width: 220px;
                height: auto;
                margin: 0 auto 24px;
                filter: brightness(0) invert(1);
            }

            .hero h1 {
                position: relative;
                font-size: 2.5rem;
                font-weight: 800;
                letter-spacing: -0.03em;
                line-height: 1.15;
                margin-bottom: 14px;
                background: linear-gradient(135deg, #ffffff 60%, var(--teal) 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }

            .hero p {
                position: relative;
                font-size: 1.1rem;
                color: var(--text-muted);
                font-weight: 400;
                max-width: 440px;
                margin: 0 auto;
                line-height: 1.6;
            }

            /* ---- CTA button ---- */
            .cta-btn {
                position: relative;
                display: inline-flex;
                align-items: center;
                gap: 10px;
                margin-top: 28px;
                padding: 15px 36px;
                background: linear-gradient(135deg, var(--purple), var(--purple-light));
                color: var(--text);
                font-family: 'Manrope', sans-serif;
                font-size: 0.95rem;
                font-weight: 700;
                text-decoration: none;
                border-radius: 10px;
                border: none;
                transition: transform 0.3s cubic-bezier(0.22,1,0.36,1), box-shadow 0.3s ease;
                box-shadow: 0 4px 24px var(--purple-glow);
            }

            .cta-btn:hover {
                transform: translateY(-2px) scale(1.02);
                box-shadow: 0 8px 40px rgba(78,33,232,0.45);
            }

            .cta-btn svg {
                transition: transform 0.3s ease;
            }

            .cta-btn:hover svg {
                transform: translateX(3px);
            }

            /* ---- Section headings ---- */
            .section-label {
                font-size: 0.72rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.16em;
                color: var(--teal);
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .section-label::after {
                content: '';
                flex: 1;
                height: 1px;
                background: linear-gradient(90deg, var(--border), transparent);
            }

            /* ---- Component cards grid ---- */
            .cards {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                margin-bottom: 56px;
            }

            .card {
                background: var(--bg-surface);
                border: 1px solid var(--border);
                border-radius: var(--radius);
                padding: 28px 16px 24px;
                text-align: center;
                transition: all 0.35s cubic-bezier(0.22, 1, 0.36, 1);
                position: relative;
                overflow: hidden;
            }

            .card::before {
                content: '';
                position: absolute;
                inset: 0;
                background: radial-gradient(circle at 50% 0%, rgba(78,33,232,0.12), transparent 70%);
                opacity: 0;
                transition: opacity 0.35s ease;
            }

            .card:hover {
                transform: translateY(-6px);
                border-color: var(--border-hover);
                box-shadow: 0 12px 40px rgba(78,33,232,0.15), 0 0 0 1px rgba(78,33,232,0.1);
            }

            .card:hover::before {
                opacity: 1;
            }

            .card-icon {
                position: relative;
                width: 52px;
                height: 52px;
                margin: 0 auto 18px;
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .card-icon svg {
                width: 26px;
                height: 26px;
            }

            .card-icon.ververicaplatform { background: linear-gradient(135deg, #4e21e8, #7c5cf5); }
            .card-icon.grafana           { background: linear-gradient(135deg, #e6522c, #f5833f); }
            .card-icon.redpanda          { background: linear-gradient(135deg, #e2243b, #ff5c6c); }
            .card-icon.webshell          { background: linear-gradient(135deg, #05b89c, #21d4b5); }

            .card h3 {
                position: relative;
                font-size: 0.92rem;
                font-weight: 600;
                margin-bottom: 16px;
                line-height: 1.3;
            }

            .card-link {
                position: relative;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 8px 20px;
                font-family: 'Manrope', sans-serif;
                font-size: 0.8rem;
                font-weight: 600;
                color: var(--teal);
                text-decoration: none;
                border: 1.5px solid rgba(5,184,156,0.35);
                border-radius: 8px;
                transition: all 0.25s ease;
            }

            .card-link:hover {
                background: var(--teal);
                color: var(--bg-deep);
                border-color: var(--teal);
                box-shadow: 0 0 20px var(--teal-glow);
            }

            .card-link svg {
                width: 14px; height: 14px;
                transition: transform 0.25s ease;
            }

            .card-link:hover svg {
                transform: translateX(2px);
            }

            /* ---- Credentials card ---- */
            .cred-card {
                background: var(--bg-surface);
                border: 1px solid var(--border);
                border-radius: var(--radius);
                padding: 32px;
                margin-bottom: 56px;
                position: relative;
                overflow: hidden;
            }

            .cred-card::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(5,184,156,0.3), transparent);
            }

            .cred-table {
                width: 100%;
                border-collapse: collapse;
            }

            .cred-table th {
                text-align: left;
                font-size: 0.7rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                color: var(--text-dim);
                padding: 0 14px 14px;
                border-bottom: 1px solid var(--border);
            }

            .cred-table td {
                padding: 16px 14px;
                font-size: 0.92rem;
                border-bottom: 1px solid rgba(255,255,255,0.03);
            }

            .cred-table tr:last-child td {
                border-bottom: none;
            }

            .cred-table td:first-child {
                font-weight: 500;
            }

            .mono-wrap {
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }

            .mono {
                font-family: var(--mono);
                font-weight: 500;
                background: rgba(255,255,255,0.06);
                padding: 4px 10px;
                border-radius: 6px;
                font-size: 0.85rem;
                letter-spacing: 0.02em;
            }

            .copy-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 28px;
                height: 28px;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 6px;
                background: transparent;
                color: var(--text-dim);
                cursor: pointer;
                transition: all 0.2s ease;
                flex-shrink: 0;
            }

            .copy-btn:hover {
                background: rgba(255,255,255,0.06);
                color: var(--teal);
                border-color: rgba(5,184,156,0.3);
            }

            .copy-btn svg { width: 14px; height: 14px; }

            .copy-btn.copied {
                color: var(--teal);
                border-color: var(--teal);
                background: rgba(5,184,156,0.1);
            }

            /* ---- Toast notification ---- */
            .toast {
                position: fixed;
                bottom: 32px;
                left: 50%;
                transform: translateX(-50%) translateY(20px);
                background: var(--teal);
                color: var(--bg-deep);
                font-family: 'Manrope', sans-serif;
                font-size: 0.82rem;
                font-weight: 600;
                padding: 10px 20px;
                border-radius: 8px;
                opacity: 0;
                pointer-events: none;
                transition: all 0.35s cubic-bezier(0.22,1,0.36,1);
                z-index: 100;
                box-shadow: 0 8px 30px rgba(5,184,156,0.3);
            }

            .toast.show {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }

            /* ---- Footer ---- */
            .footer {
                text-align: center;
                color: var(--text-dim);
                font-size: 0.78rem;
                padding-top: 20px;
                border-top: 1px solid var(--border);
                letter-spacing: 0.04em;
            }

            /* ---- Responsive ---- */
            @media (max-width: 768px) {
                .container { padding: 36px 20px 56px; }
                .hero { padding: 40px 28px 36px; }
                .hero h1 { font-size: 2rem; }
                .hero .logo { width: 180px; }
                .cards { grid-template-columns: 1fr 1fr; gap: 12px; }
                .cred-card { padding: 24px 20px; }
            }

            @media (max-width: 480px) {
                .hero h1 { font-size: 1.6rem; }
                .hero p { font-size: 0.95rem; }
                .cards { grid-template-columns: 1fr; }
                .cred-table th:last-child,
                .cred-table td:last-child { display: none; }
            }
        </style>
    </head>
    <body>
        <!-- Background layers -->
        <div class="dot-grid"></div>
        <div class="glow-orb purple"></div>
        <div class="glow-orb teal"></div>

        <!-- Toast -->
        <div class="toast" id="toast">Copied to clipboard</div>

        <div class="container">
            <!-- Hero -->
            <div class="hero-wrap">
                <div class="hero anim anim-d1">
                    <img class="logo" src="/assets/ververica-logo_navy.png" onerror="this.onerror=null;this.src='https://raw.githubusercontent.com/campossalex/apacheflink-labday-1/refs/heads/master/web/ververica-logo_navy.png';" alt="Ververica">
                    <h1>Apache Flink Lab Day</h1>
                    <p>Your hands-on environment is ready. Open the lab instructions to get started.</p>
                    <a class="cta-btn" href="https://github.com/campossalex/apacheflink-labday-1/blob/master/instructions.MD" target="_blank">
                        Lab Instructions
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 10h10M11 6l4 4-4 4"/></svg>
                    </a>
                </div>
            </div>

            <!-- Components -->
            <div class="section-label anim anim-d3">Components</div>
            <div class="cards">
                {% for site in sites %}
                <div class="card anim anim-d{{ loop.index + 3 }}">
                    <div class="card-icon {{ site.name | lower | replace(' ', '') }}">
                        {% if site.name == 'Ververica Platform' %}
                        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/><circle cx="8" cy="6" r="1.5" fill="#fff" stroke="none"/><circle cx="14" cy="12" r="1.5" fill="#fff" stroke="none"/><circle cx="10" cy="18" r="1.5" fill="#fff" stroke="none"/></svg>
                        {% elif site.name == 'Grafana' %}
                        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><polyline points="7 14 10 10 13 13 17 8"/></svg>
                        {% elif site.name == 'Redpanda' %}
                        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4v16h16"/><path d="M4 16l4-4 4 2 4-6 4-2"/></svg>
                        {% elif site.name == 'Web Shell' %}
                        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><polyline points="8 10 11 13 8 16"/><line x1="14" y1="16" x2="17" y2="16"/></svg>
                        {% endif %}
                    </div>
                    <h3>{{ site.name }}</h3>
                    <a class="card-link" href="{{ "http://" + public_ip + ":" + site.port }}" target="_blank">
                        Open
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 8h8M9 5l3 3-3 3"/></svg>
                    </a>
                </div>
                {% endfor %}
            </div>

            <!-- Credentials -->
            <div class="section-label anim anim-d7">Credentials</div>
            <div class="cred-card anim anim-d8">
                <table class="cred-table">
                    <thead>
                        <tr>
                            <th>Component</th>
                            <th>User</th>
                            <th>Password</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Web Shell</td>
                            <td>
                                <span class="mono-wrap">
                                    <span class="mono">admin</span>
                                    <button class="copy-btn" onclick="copyText('admin', this)" title="Copy">
                                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M5 11H3.5A1.5 1.5 0 012 9.5v-7A1.5 1.5 0 013.5 1h7A1.5 1.5 0 0112 2.5V5"/></svg>
                                    </button>
                                </span>
                            </td>
                            <td>
                                <span class="mono-wrap">
                                    <span class="mono">admin1</span>
                                    <button class="copy-btn" onclick="copyText('admin1', this)" title="Copy">
                                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M5 11H3.5A1.5 1.5 0 012 9.5v-7A1.5 1.5 0 013.5 1h7A1.5 1.5 0 0112 2.5V5"/></svg>
                                    </button>
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td>Postgres</td>
                            <td>
                                <span class="mono-wrap">
                                    <span class="mono">root</span>
                                    <button class="copy-btn" onclick="copyText('root', this)" title="Copy">
                                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M5 11H3.5A1.5 1.5 0 012 9.5v-7A1.5 1.5 0 013.5 1h7A1.5 1.5 0 0112 2.5V5"/></svg>
                                    </button>
                                </span>
                            </td>
                            <td>
                                <span class="mono-wrap">
                                    <span class="mono">admin1</span>
                                    <button class="copy-btn" onclick="copyText('admin1', this)" title="Copy">
                                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M5 11H3.5A1.5 1.5 0 012 9.5v-7A1.5 1.5 0 013.5 1h7A1.5 1.5 0 0112 2.5V5"/></svg>
                                    </button>
                                </span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Footer -->
            <div class="footer anim anim-d8">Ververica &middot; Apache Flink Lab Day</div>
        </div>

        <script>
        function copyText(text, btn) {
            navigator.clipboard.writeText(text).then(function() {
                btn.classList.add('copied');
                btn.innerHTML = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3.5 8.5 6.5 11.5 12.5 4.5"/></svg>';

                var toast = document.getElementById('toast');
                toast.textContent = 'Copied "' + text + '"';
                toast.classList.add('show');

                setTimeout(function() {
                    toast.classList.remove('show');
                }, 1800);

                setTimeout(function() {
                    btn.classList.remove('copied');
                    btn.innerHTML = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M5 11H3.5A1.5 1.5 0 012 9.5v-7A1.5 1.5 0 013.5 1h7A1.5 1.5 0 0112 2.5V5"/></svg>';
                }, 2200);
            });
        }
        </script>
    </body>
    </html>
    """

    # Render page with the site data
    return render_template_string(html, sites=sites, public_ip=public_ip)


if __name__ == "__main__":
    print(f"Starting Flask app with arg_value = {public_ip}")
    app.run(host="0.0.0.0", port=80, debug=True)
