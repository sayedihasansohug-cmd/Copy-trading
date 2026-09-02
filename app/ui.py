HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOLANA MEME RADAR // PRO TERMINAL</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #06080e; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass-nav { background: rgba(10, 13, 22, 0.85); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.06); }
        .card-panel { background: #0c101a; border: 1px solid #172033; transition: all 0.25s ease; }
        .card-panel:hover { border-color: rgba(99, 102, 241, 0.4); transform: translateY(-2px); }
        .cyber-glow { box-shadow: 0 0 35px rgba(99, 102, 241, 0.12); }
        .badge-live { animation: pulseGlow 2s infinite; }
        @keyframes pulseGlow { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.95); } }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: #06080e; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
    </style>
</head>
<body class="text-slate-100 min-h-screen flex flex-col">

    <!-- Top Navigation -->
    <header class="glass-nav sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/25">
                    <i class="fa-solid fa-bolt text-lg"></i>
                </div>
                <div>
                    <h1 class="font-extrabold text-base sm:text-lg tracking-wider text-white flex items-center gap-2">
                        MEME RADAR <span class="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">PRO ENGINE</span>
                    </h1>
                    <p class="text-[11px] text-slate-400 mono">SOLANA VIRAL NARRATIVE DISCOVERY</p>
                </div>
            </div>

            <div class="flex items-center gap-3">
                <div class="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 badge-live"></span>
                    <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider" id="scanner-status">SCANNING ACTIVE</span>
                </div>
                <button onclick="toggleSound()" id="sound-btn" class="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition">
                    <i class="fa-solid fa-volume-high" id="sound-icon"></i>
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-6 flex-1 w-full pb-12">

        <!-- Metrics Row -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="card-panel p-5 rounded-2xl">
                <div class="flex justify-between items-center text-slate-400 text-xs">
                    <span class="font-semibold uppercase tracking-wider">TOTAL DISCOVERIES</span>
                    <i class="fa-solid fa-satellite-dish text-indigo-400"></i>
                </div>
                <div class="mt-2 text-2xl font-extrabold text-white mono" id="metric-total">0</div>
                <div class="mt-1 text-xs text-slate-500">Live tokens tracked</div>
            </div>

            <div class="card-panel p-5 rounded-2xl">
                <div class="flex justify-between items-center text-slate-400 text-xs">
                    <span class="font-semibold uppercase tracking-wider">TELEGRAM ALERTS</span>
                    <i class="fa-brands fa-telegram text-sky-400"></i>
                </div>
                <div class="mt-2 text-2xl font-extrabold text-sky-400 mono" id="metric-alerts">0</div>
                <div class="mt-1 text-xs text-slate-500">Direct notifications sent</div>
            </div>

            <div class="card-panel p-5 rounded-2xl">
                <div class="flex justify-between items-center text-slate-400 text-xs">
                    <span class="font-semibold uppercase tracking-wider">SCANNER INTERVAL</span>
                    <i class="fa-solid fa-stopwatch text-amber-400"></i>
                </div>
                <div class="mt-2 text-2xl font-extrabold text-amber-400 mono">10 SEC</div>
                <div class="mt-1 text-xs text-slate-500">Continuous background polling</div>
            </div>

            <div class="card-panel p-5 rounded-2xl">
                <div class="flex justify-between items-center text-slate-400 text-xs">
                    <span class="font-semibold uppercase tracking-wider">NETWORK SOURCING</span>
                    <i class="fa-solid fa-network-wired text-emerald-400"></i>
                </div>
                <div class="mt-2 text-2xl font-extrabold text-emerald-400 mono">X + DEX</div>
                <div class="mt-1 text-xs text-slate-500">DexScreener & Twitter attached</div>
            </div>
        </div>

        <!-- Main Feed & Terminal Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

            <!-- Discovered Tokens Stream (2 Cols) -->
            <div class="lg:col-span-2 space-y-4">
                <div class="flex justify-between items-center">
                    <h2 class="font-bold text-white text-sm sm:text-base flex items-center gap-2">
                        <i class="fa-solid fa-fire text-amber-400"></i> LIVE VIRAL MEME COIN STREAM
                    </h2>
                    <span class="text-xs text-slate-400 mono" id="stream-counter">0 Active Feeds</span>
                </div>

                <div id="tokens-grid" class="space-y-3">
                    <div class="text-center py-16 card-panel rounded-2xl border-dashed">
                        <i class="fa-solid fa-circle-notch fa-spin text-3xl text-indigo-500 mb-3"></i>
                        <p class="text-xs text-slate-400 font-medium">Listening for real-time viral narrative launches...</p>
                    </div>
                </div>
            </div>

            <!-- Terminal Logs (1 Col) -->
            <div class="space-y-4">
                <div class="flex justify-between items-center">
                    <h2 class="font-bold text-white text-sm sm:text-base flex items-center gap-2">
                        <i class="fa-solid fa-terminal text-indigo-400"></i> LIVE AGENT LOGS
                    </h2>
                    <span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 mono">REALTIME</span>
                </div>

                <div class="card-panel p-4 rounded-2xl h-[520px] flex flex-col">
                    <div id="terminal-logs" class="flex-1 overflow-y-auto space-y-2 text-xs mono text-slate-300 pr-1">
                        <!-- Populated via JS -->
                    </div>
                </div>
            </div>

        </div>

    </main>

    <script>
        let soundEnabled = true;
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

        function playChime() {
            if (!soundEnabled) return;
            try {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = "sine";
                osc.frequency.setValueAtTime(880, audioCtx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(1320, audioCtx.currentTime + 0.15);
                gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.15);
            } catch(e) {}
        }

        function toggleSound() {
            soundEnabled = !soundEnabled;
            document.getElementById('sound-icon').className = soundEnabled ? 'fa-solid fa-volume-high' : 'fa-solid fa-volume-xmark';
        }

        function copyCA(ca, btn) {
            navigator.clipboard.writeText(ca);
            const original = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-check text-emerald-400"></i> Copied!';
            setTimeout(() => { btn.innerHTML = original; }, 1800);
        }

        let previousCount = 0;

        async function pollData() {
            try {
                const res = await fetch('/api/stream');
                const data = await res.json();

                document.getElementById('metric-total').innerText = data.total_discovered;
                document.getElementById('metric-alerts').innerText = data.total_alerts;
                document.getElementById('stream-counter').innerText = `${data.tokens.length} Coins`;

                if (data.tokens.length > previousCount && previousCount > 0) {
                    playChime();
                }
                previousCount = data.tokens.length;

                // Render Tokens
                const grid = document.getElementById('tokens-grid');
                if (data.tokens.length === 0) {
                    grid.innerHTML = `
                        <div class="text-center py-16 card-panel rounded-2xl border-dashed">
                            <i class="fa-solid fa-radar text-3xl text-slate-600 mb-3"></i>
                            <p class="text-xs text-slate-400 font-medium">Scanning DexScreener & X for high-conviction narrative launches...</p>
                        </div>
                    `;
                } else {
                    grid.innerHTML = data.tokens.map(t => `
                        <div class="card-panel p-5 rounded-2xl space-y-4">
                            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                                <div class="flex items-center gap-3">
                                    <div class="w-11 h-11 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center font-extrabold text-white text-base">
                                        ${t.symbol.slice(0, 3)}
                                    </div>
                                    <div>
                                        <div class="flex items-center gap-2">
                                            <span class="font-bold text-white text-base">${t.name}</span>
                                            <span class="text-xs px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-400 font-bold mono">$${t.symbol}</span>
                                        </div>
                                        <div class="text-xs text-slate-400 mt-0.5 mono">Price: <span class="text-emerald-400 font-semibold">$${t.price_usd}</span></div>
                                    </div>
                                </div>

                                <div class="flex items-center gap-4 text-xs mono">
                                    <div><span class="text-slate-500">LIQ:</span> <span class="font-bold text-slate-200">$${Math.round(t.liquidity_usd).toLocaleString()}</span></div>
                                    <div><span class="text-slate-500">VOL:</span> <span class="font-bold text-slate-200">$${Math.round(t.volume_24h_usd).toLocaleString()}</span></div>
                                    <div><span class="text-slate-500">MCAP:</span> <span class="font-bold text-amber-400">$${Math.round(t.fdv_usd).toLocaleString()}</span></div>
                                </div>
                            </div>

                            <!-- Narrative -->
                            <div class="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300 italic">
                                "${t.description.slice(0, 180)}..."
                            </div>

                            <!-- CA Box & Links -->
                            <div class="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-slate-800/60">
                                <button onclick="copyCA('${t.mint}', this)" class="text-xs text-slate-400 mono px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 transition flex items-center gap-1.5">
                                    <i class="fa-regular fa-copy"></i> ${t.mint.slice(0, 6)}...${t.mint.slice(-6)}
                                </button>

                                <div class="flex flex-wrap items-center gap-2 text-xs font-bold">
                                    <a href="https://gmgn.ai/sol/token/${t.mint}" target="_blank" class="px-2.5 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition flex items-center gap-1">
                                        <i class="fa-solid fa-chart-simple"></i> GMGN
                                    </a>
                                    <a href="${t.dex_url}" target="_blank" class="px-2.5 py-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 hover:bg-cyan-500/20 transition flex items-center gap-1">
                                        <i class="fa-solid fa-chart-line"></i> DexScreener
                                    </a>
                                    <a href="https://pump.fun/${t.mint}" target="_blank" class="px-2.5 py-1.5 rounded-lg bg-pink-500/10 text-pink-400 border border-pink-500/20 hover:bg-pink-500/20 transition flex items-center gap-1">
                                        <i class="fa-solid fa-capsules"></i> Pump.fun
                                    </a>
                                    <a href="${t.twitter_url}" target="_blank" class="px-2.5 py-1.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20 hover:bg-sky-500/20 transition flex items-center gap-1">
                                        <i class="fa-brands fa-x-twitter"></i> Post
                                    </a>
                                </div>
                            </div>
                        </div>
                    `).join('');
                }

                // Render Logs
                const logsDiv = document.getElementById('terminal-logs');
                logsDiv.innerHTML = data.logs.map(l => `
                    <div class="flex gap-2">
                        <span class="text-slate-500">[${l.time}]</span>
                        <span class="${l.level === 'ALERT' ? 'text-emerald-400 font-bold' : (l.level === 'WARN' ? 'text-amber-400' : 'text-slate-300')}">${l.msg}</span>
                    </div>
                `).join('');

            } catch(e) {
                console.error("Polling error:", e);
            }
        }

        setInterval(pollData, 3000);
        pollData();
    </script>
</body>
</html>
"""
