HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOLANA AI MEME SNIPER // PRO</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Space Grotesk', sans-serif; background-color: #07090e; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass { background: rgba(16, 20, 31, 0.7); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.07); }
        .glass-card { background: #0e121c; border: 1px solid #1a2233; }
        .neon-glow { box-shadow: 0 0 25px rgba(16, 185, 129, 0.15); }
        .pulse-dot { animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
    </style>
</head>
<body class="text-slate-200 min-h-screen pb-12">

    <!-- Header -->
    <header class="border-b border-slate-800/80 sticky top-0 z-50 glass">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-emerald-500/20">
                    <i class="fa-solid fa-brain"></i>
                </div>
                <div>
                    <h1 class="font-bold text-lg tracking-wider text-white flex items-center gap-2">
                        MEME SNIPER <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">AI PRO</span>
                    </h1>
                    <p class="text-xs text-slate-400 mono">SOLANA AGENT</p>
                </div>
            </div>

            <div class="flex items-center gap-4">
                <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 pulse-dot" id="status-indicator"></span>
                    <span class="text-xs font-semibold text-emerald-400" id="status-text">SCANNING</span>
                </div>
                <button onclick="toggleBot()" id="btn-toggle-bot" class="px-4 py-2 text-xs font-bold rounded-lg bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20 transition">
                    <i class="fa-solid fa-power-off mr-1"></i> PAUSE
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-6">

        <!-- Metric Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="glass-card p-5 rounded-2xl">
                <div class="flex justify-between items-start text-slate-400 text-xs">
                    <span>SOL BALANCE</span>
                    <i class="fa-solid fa-wallet text-emerald-400"></i>
                </div>
                <div class="mt-2 flex items-baseline gap-2">
                    <span class="text-2xl font-bold text-white mono" id="wallet-balance">-- SOL</span>
                </div>
                <div class="mt-1 text-xs text-slate-500 mono" id="wallet-address">Connecting...</div>
            </div>

            <div class="glass-card p-5 rounded-2xl">
                <div class="flex justify-between items-start text-slate-400 text-xs">
                    <span>ACTIVE TRADES</span>
                    <i class="fa-solid fa-coins text-indigo-400"></i>
                </div>
                <div class="mt-2 flex items-baseline gap-2">
                    <span class="text-2xl font-bold text-white mono" id="active-positions-count">0</span>
                    <span class="text-xs text-indigo-400 font-medium">Positions</span>
                </div>
                <div class="mt-1 text-xs text-slate-500">TP: +60% | SL: -20%</div>
            </div>

            <div class="glass-card p-5 rounded-2xl">
                <div class="flex justify-between items-start text-slate-400 text-xs">
                    <span>AI ENGINE</span>
                    <i class="fa-solid fa-bolt text-amber-400"></i>
                </div>
                <div class="mt-2 flex items-baseline gap-2">
                    <span class="text-2xl font-bold text-amber-400 mono">GEMINI 2.0</span>
                </div>
                <div class="mt-1 text-xs text-slate-400">X + DexScreener</div>
            </div>

            <div class="glass-card p-5 rounded-2xl">
                <div class="flex justify-between items-start text-slate-400 text-xs">
                    <span>SIZE PER TRADE</span>
                    <i class="fa-solid fa-shield-halved text-emerald-400"></i>
                </div>
                <div class="mt-2 flex items-baseline gap-2">
                    <span class="text-2xl font-bold text-white mono" id="trade-size-sol">0.05 SOL</span>
                </div>
                <div class="mt-1 text-xs text-emerald-400 font-medium">Auto-Risk Guard</div>
            </div>
        </div>

        <!-- Manual Signal Injector -->
        <div class="glass-card p-6 rounded-2xl neon-glow">
            <h2 class="text-base font-bold text-white flex items-center gap-2 mb-1">
                <i class="fa-solid fa-terminal text-emerald-400"></i> Manual Meme Scanner & Snipe
            </h2>
            <p class="text-xs text-slate-400 mb-4">Paste any viral tweet, meme hype or Solana CA to test AI & trade.</p>
            
            <div class="flex flex-col sm:flex-row gap-3">
                <input type="text" id="manual-input" placeholder="e.g. Everyone aping $PEPE! CA: 7EYnhQoR9YM3N7UoaKRoA44Uy8JeaencoqurzbR6gk5P" 
                       class="flex-1 bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-emerald-500 mono transition">
                <button onclick="injectSignal()" id="btn-inject" class="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-bold text-xs uppercase tracking-wider hover:opacity-95 transition flex items-center justify-center gap-2">
                    <i class="fa-solid fa-magnifying-glass"></i> Snipe Token
                </button>
            </div>
            <div id="inject-result" class="mt-3 text-xs hidden"></div>
        </div>

        <!-- Grid: Positions & Logs -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            <div class="lg:col-span-2 glass-card p-6 rounded-2xl space-y-4">
                <div class="flex justify-between items-center">
                    <h2 class="font-bold text-white text-sm flex items-center gap-2">
                        <i class="fa-solid fa-chart-line text-emerald-400"></i> ACTIVE POSITIONS
                    </h2>
                    <button onclick="fetchData()" class="text-xs text-slate-400 hover:text-white transition">
                        <i class="fa-solid fa-rotate-right mr-1"></i> Refresh
                    </button>
                </div>
                <div id="positions-container" class="space-y-3"></div>
            </div>

            <div class="glass-card p-6 rounded-2xl flex flex-col h-[400px]">
                <div class="flex justify-between items-center mb-3">
                    <h2 class="font-bold text-white text-sm flex items-center gap-2">
                        <i class="fa-solid fa-microchip text-indigo-400"></i> AGENT TERMINAL LOGS
                    </h2>
                    <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 mono">LIVE</span>
                </div>
                <div id="logs-container" class="flex-1 overflow-y-auto space-y-2 text-xs mono bg-slate-950/70 p-3 rounded-xl border border-slate-800/80"></div>
            </div>

        </div>

    </main>

    <script>
        async function fetchData() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                document.getElementById('wallet-balance').innerText = data.wallet_balance.toFixed(4) + ' SOL';
                document.getElementById('wallet-address').innerText = data.wallet_address.slice(0, 6) + '...' + data.wallet_address.slice(-6);
                document.getElementById('trade-size-sol').innerText = data.trade_size + ' SOL';
                document.getElementById('active-positions-count').innerText = data.positions.length;

                const indicator = document.getElementById('status-indicator');
                const statusText = document.getElementById('status-text');
                const toggleBtn = document.getElementById('btn-toggle-bot');

                if (data.bot_active) {
                    indicator.className = "w-2.5 h-2.5 rounded-full bg-emerald-400 pulse-dot";
                    statusText.className = "text-xs font-semibold text-emerald-400";
                    statusText.innerText = "SCANNING";
                    toggleBtn.innerHTML = '<i class="fa-solid fa-pause mr-1"></i> PAUSE';
                    toggleBtn.className = "px-4 py-2 text-xs font-bold rounded-lg bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20 transition";
                } else {
                    indicator.className = "w-2.5 h-2.5 rounded-full bg-amber-400";
                    statusText.className = "text-xs font-semibold text-amber-400";
                    statusText.innerText = "PAUSED";
                    toggleBtn.innerHTML = '<i class="fa-solid fa-play mr-1"></i> START';
                    toggleBtn.className = "px-4 py-2 text-xs font-bold rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20 transition";
                }

                const posContainer = document.getElementById('positions-container');
                if (data.positions.length === 0) {
                    posContainer.innerHTML = `<div class="text-center py-8 text-slate-500 text-xs">No active positions open. Scanner is monitoring.</div>`;
                } else {
                    posContainer.innerHTML = data.positions.map(p => `
                        <div class="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex justify-between items-center">
                            <div>
                                <div class="font-bold text-white">${p.symbol} <span class="text-xs text-emerald-400 mono ml-2">BUY: $${p.entry_price.toFixed(6)}</span></div>
                                <div class="text-xs text-slate-500 mono mt-1">CA: ${p.mint.slice(0, 8)}...${p.mint.slice(-6)}</div>
                            </div>
                            <button onclick="closePosition('${p.mint}')" class="px-3 py-1.5 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-bold hover:bg-red-500/30 transition">⚡ Sell</button>
                        </div>
                    `).join('');
                }

                const logsContainer = document.getElementById('logs-container');
                logsContainer.innerHTML = data.logs.map(l => `
                    <div class="flex gap-2">
                        <span class="text-slate-500">[${l.time}]</span>
                        <span class="${l.level === 'ERROR' ? 'text-red-400' : (l.level === 'SUCCESS' ? 'text-emerald-400' : 'text-slate-300')}">${l.msg}</span>
                    </div>
                `).join('');
            } catch (err) {
                console.error(err);
            }
        }

        async function toggleBot() {
            await fetch('/api/bot/toggle', { method: 'POST' });
            fetchData();
        }

        async function closePosition(mint) {
            if(!confirm("Sell this token now?")) return;
            const res = await fetch('/api/position/close', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mint })
            });
            const data = await res.json();
            alert(data.message);
            fetchData();
        }

        async function injectSignal() {
            const input = document.getElementById('manual-input');
            const resultBox = document.getElementById('inject-result');
            const btn = document.getElementById('btn-inject');
            const text = input.value.trim();
            if (!text) return;

            btn.disabled = true;
            btn.innerText = "Analyzing...";
            resultBox.className = "mt-3 text-xs block text-amber-400";
            resultBox.innerText = "Gemini AI is analyzing sentiment...";

            try {
                const res = await fetch('/api/scan/manual', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });
                const data = await res.json();
                resultBox.className = data.success ? "mt-3 text-xs block text-emerald-400 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20" : "mt-3 text-xs block text-red-400 p-3 rounded-lg bg-red-500/10 border border-red-500/20";
                resultBox.innerHTML = `<strong>Result:</strong> ${data.message}`;
                input.value = "";
                fetchData();
            } catch (err) {
                resultBox.innerText = err.message;
            } finally {
                btn.disabled = false;
                btn.innerText = "Snipe Token";
            }
        }

        setInterval(fetchData, 4000);
        fetchData();
    </script>
</body>
</html>
"""
