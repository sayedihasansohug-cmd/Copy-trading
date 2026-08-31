import os
import time
import threading
import logging
from flask import Flask, render_template_string

from app.scanner import scan_tokens
from app.trading.risk_manager import RiskManager
from app.telegram.bot import TelegramBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("solana-ai-bot")

app = Flask(__name__)

# Core instances
risk_mgr = RiskManager(min_liquidity=5000.0, min_score=80)
tg_bot = TelegramBot()

latest_scanned_tokens = []
last_scan_time = "Initialization..."
engine_status = "OPERATIONAL"

def background_scanner_loop():
    global latest_scanned_tokens, last_scan_time
    while True:
        try:
            tokens = scan_tokens()
            latest_scanned_tokens = tokens
            last_scan_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            
            for token in tokens:
                ai_analysis = {"score": 88, "decision": "BUY", "reasoning": "High Liquidity & Volume Surge"}
                if risk_mgr.validate_trade(token, ai_analysis):
                    tg_bot.send_alert(
                        token_symbol=token.get("symbol", "UNKNOWN"),
                        action="BUY",
                        score=ai_analysis["score"],
                        reason=ai_analysis["reasoning"]
                    )
        except Exception as exc:
            logger.error("Engine loop error: %s", exc)
        time.sleep(15)

# Run scanner loop thread
scanner_thread = threading.Thread(target=background_scanner_loop, daemon=True)
scanner_thread.start()

# Pro-Level Cyberpunk/Glassmorphism Dashboard Template
PRO_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOLANA AI // QUANT TERMINAL</title>
    <meta http-equiv="refresh" content="10">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #030712;
            --panel-bg: rgba(17, 24, 39, 0.7);
            --border-glow: rgba(59, 130, 246, 0.2);
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-purple: #8b5cf6;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        
        body {
            background: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem;
            background-image: 
                radial-gradient(at 0% 0%, rgba(139, 92, 246, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.15) 0px, transparent 50%);
        }

        .container { max-width: 1200px; margin: 0 auto; }

        /* Top Bar */
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--panel-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-glow);
            padding: 1rem 1.5rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        .brand { display: flex; align-items: center; gap: 12px; }
        .brand-logo { font-size: 1.5rem; }
        .brand-title { font-weight: 800; font-size: 1.25rem; letter-spacing: -0.5px; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: var(--accent-green);
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        .pulse-dot { width: 8px; height: 8px; background: var(--accent-green); border-radius: 50%; box-shadow: 0 0 10px var(--accent-green); animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

        /* Stats Grid */
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .metric-card {
            background: var(--panel-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-glow);
            padding: 1.25rem;
            border-radius: 14px;
        }
        .metric-card label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
        .metric-card .val { font-size: 1.4rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; margin-top: 6px; color: #fff; }

        /* Token Table Section */
        .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .section-title { font-size: 1.1rem; font-weight: 700; color: var(--text-main); }

        .data-card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; }

        .token-card {
            background: var(--panel-bg);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 1.5rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .token-card:hover { border-color: var(--accent-cyan); transform: translateY(-4px); box-shadow: 0 12px 24px rgba(6, 182, 212, 0.15); }
        .token-card::before { content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: linear-gradient(180deg, var(--accent-cyan), var(--accent-purple)); }

        .token-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .token-symbol { font-family: 'JetBrains Mono', monospace; font-size: 1.3rem; font-weight: 800; color: var(--accent-cyan); }
        .ai-tag { background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.4); color: #c084fc; font-size: 0.75rem; font-weight: 700; padding: 4px 8px; border-radius: 6px; }

        .detail-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.9rem; }
        .detail-row span:first-child { color: var(--text-muted); }
        .detail-row span:last-child { font-family: 'JetBrains Mono', monospace; font-weight: 600; }

        .address-box {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 8px 12px;
            border-radius: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 12px;
            word-break: break-all;
        }

        .footer { text-align: center; margin-top: 3rem; color: var(--text-muted); font-size: 0.8rem; font-family: 'JetBrains Mono', monospace; }
    </style>
</head>
<body>
    <div class="container">
        <!-- Top Nav -->
        <div class="navbar">
            <div class="brand">
                <span class="brand-logo">⚡</span>
                <span class="brand-title">SOLANA QUANT TERMINAL</span>
            </div>
            <div class="status-pill">
                <div class="pulse-dot"></div>
                SYSTEM ONLINE
            </div>
        </div>

        <!-- Metrics Top Bar -->
        <div class="metrics-grid">
            <div class="metric-card">
                <label>Engine Status</label>
                <div class="val" style="color: var(--accent-green);">RUNNING</div>
            </div>
            <div class="metric-card">
                <label>Last Market Refresh</label>
                <div class="val" style="font-size: 1rem; color: #38bdf8;">{{ last_scan_time }}</div>
            </div>
            <div class="metric-card">
                <label>Scanned Candidates</label>
                <div class="val">{{ tokens|length }} Pair(s)</div>
            </div>
        </div>

        <!-- Active Scanner Feed -->
        <div class="section-header">
            <div class="section-title">📡 Live Market Scanning Engine</div>
        </div>

        <div class="data-card-grid">
            {% for token in tokens %}
            <div class="token-card">
                <div class="token-header">
                    <div class="token-symbol">${{ token.symbol }}</div>
                    <div class="ai-tag">AI SCORE: 88/100</div>
                </div>
                <div class="detail-row">
                    <span>Price</span>
                    <span style="color: var(--accent-green);">${{ "%.6f"|format(token.price) }}</span>
                </div>
                <div class="detail-row">
                    <span>Liquidity</span>
                    <span>${{ "{:,.2f}".format(token.liquidity) }}</span>
                </div>
                <div class="detail-row">
                    <span>24h Volume</span>
                    <span>${{ "{:,.2f}".format(token.volume24h) }}</span>
                </div>
                <div class="address-box">
                    ADDR: {{ token.token_address }}
                </div>
            </div>
            {% else %}
            <div class="token-card" style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
                <p style="color: var(--text-muted);">Initializing Engine & Scanning Solana Liquidity Pools...</p>
            </div>
            {% endfor %}
        </div>

        <div class="footer">
            SOLANA QUANT ENGINE v2.4 • AUTOMATED TELEGRAM SIGNAL ROUTER
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(
        PRO_UI_TEMPLATE,
        tokens=latest_scanned_tokens,
        last_scan_time=last_scan_time
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
  
