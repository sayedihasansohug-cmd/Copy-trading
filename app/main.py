import os
import time
import threading
import logging
from flask import Flask, render_template_string
from app.scanner import scan_tokens

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("solana-ai-bot")

app = Flask(__name__)

# Global state for dashboard
latest_scanned_tokens = []
last_scan_time = "Never"

def background_scanner_loop():
    global latest_scanned_tokens, last_scan_time
    while True:
        try:
            tokens = scan_tokens()
            latest_scanned_tokens = tokens
            last_scan_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        except Exception as exc:
            logger.error("Background loop error: %s", exc)
        time.sleep(30)

# Start background thread
scanner_thread = threading.Thread(target=background_scanner_loop, daemon=True)
scanner_thread.start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Solana AI Trading Bot</title>
    <meta http-equiv="refresh" content="15">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: auto; }
        .header { display: flex; justify-space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 15px; }
        .status-badge { background: #10b981; color: #000; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 14px; }
        .card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 20px; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 15px; }
        .card h3 { margin: 0 0 10px 0; color: #38bdf8; }
        .card p { margin: 5px 0; font-size: 14px; color: #cbd5e1; }
        .footer { margin-top: 30px; text-align: center; font-size: 12px; color: #64748b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🤖 Solana AI Trading Engine</h2>
            <span class="status-badge">SYSTEM ACTIVE</span>
        </div>
        <p><strong>Last Scan:</strong> {{ last_scan_time }}</p>

        <h3>Scanned Market Candidates ({{ tokens|length }})</h3>
        <div class="card-grid">
            {% for token in tokens %}
            <div class="card">
                <h3>${{ token.symbol }}</h3>
                <p><strong>Address:</strong> {{ token.token_address[:8] }}...{{ token.token_address[-6:] }}</p>
                <p><strong>Price:</strong> ${{ token.price }}</p>
                <p><strong>Liquidity:</strong> ${{ token.liquidity }}</p>
                <p><strong>24h Vol:</strong> ${{ token.volume24h }}</p>
            </div>
            {% else %}
            <div class="card"><p>Scanning market for new pairs...</p></div>
            {% endfor %}
        </div>
        
        <div class="footer">
            Powered by Gemini AI Engine & Solana Web3
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(
        HTML_TEMPLATE,
        tokens=latest_scanned_tokens,
        last_scan_time=last_scan_time
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
  
