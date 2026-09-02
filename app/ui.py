HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>AXIOM // SOLANA MEME RADAR</title>
    
    <!-- PWA Mobile App Meta Tags -->
    <meta name="theme-color" content="#ff2a4d">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="MemeRadar">
    <link rel="manifest" href="/manifest.json">

    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=JetBrains+Mono:wght@400;600;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #050505; color: #ffffff; }
        .font-brand { font-family: 'Syne', sans-serif; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .red-glow { box-shadow: 0 0 30px rgba(255, 42, 77, 0.2); }
        .panel { background: #0c0c0c; border: 1px solid #1a1a1a; transition: all 0.2s ease; }
        .panel:hover { border-color: #ff2a4d; }
        .border-red-accent { border-color: #ff2a4d; }
        .bg-red-accent { background-color: #ff2a4d; }
        .text-red-accent { color: #ff2a4d; }
        .pulse-red { animation: pulseRed 2s infinite; }
        @keyframes pulseRed { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.3; transform: scale(0.9); } }
    </style>
</head>
<body class="min-h-screen flex flex-col antialiased selection:bg-red-600 selection:text-white">

    <!-- Top Header -->
    <header class="bg-[#0a0a0a]/90 backdrop-blur-xl border-b border-[#1f1f1f] sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-lg bg-red-600 flex items-center justify-center text-white shadow-lg shadow-red-600/30 font-extrabold text-xl">
                    <i class="fa-solid fa-gem"></i>
                </div>
                <div>
                    <h1 class="font-brand font-extrabold text-lg tracking-wider text-white flex items-center gap-2">
                        AXIOM <span class="text-xs px-2 py-0.5 rounded bg-red-600/20 text-red-500 border border-red-600/30 uppercase tracking-widest font-bold">RADAR PRO</span>
                    </h1>
                    <p class="text-[10px] text-neutral-400 mono">SOLANA VIRAL MEME SNIPER</p>
                </div>
            </div>

            <div class="flex items-center gap-3">
                <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#121212] border border-[#222]">
                    <span class="w-2.5 h-2.5 rounded-full bg-red-500 pulse-red"></span>
                    <span class="text-xs font-bold tracking-wider text-white uppercase mono" id="live-indicator">LIVE SCANNING</span>
                </div>
                <button onclick="installPWA()" id="install-btn" class="hidden px-3 py-1.5 rounded-lg bg-white text-black text-xs font-bold hover:bg-neutral-200 transition flex items-center gap-1">
                    <i class="fa-solid fa-download"></i> Install App
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-6 flex-1 w-full pb-12">

        <!-- Top Metrics Cards (Red/White/Black) -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="panel p-5 rounded-xl">
                <div class="flex justify-between items-center text-neutral-400 text-xs font-bold tracking-wider">
                    <span>DISCOVERED TOKENS</span>
                    <i class="fa-solid fa-fire text-red-500"></i>
                </div>
                <div class="mt-2 text-3xl font-extrabold text-white mono" id="metric-total">0</div>
                <div class="mt-1 text-xs text-neutral-500">Realtime meme narratives</div>
            </div>

            <div class="panel p-5 rounded-xl">
                <div class="flex justify-between items-center text-neutral-400 text-xs font-bold tracking-wider">
                    <span>TELEGRAM ALERTS</span>
                    <i class="fa-brands fa-telegram text-white"></i>
                </div>
                <div class="mt-2 text-3xl font-extrabold text-red-500 mono" id="metric-alerts">0</div>
                <div class="mt-1 text-xs text-neutral-500">Pushed to Telegram channel</div>
            </div>

            <div class="panel p-5 rounded-xl">
                <div class="flex justify-between items-center text-neutral-400 text-xs font-bold tracking-wider">
                    <span>AXIOM INTEGRATION</span>
                    <i class="fa-solid fa-bolt text-red-500"></i>
                </div>
                <div class="mt-2 text-3xl font-extrabold text-white mono">ACTIVE</div>
                <div class="mt-1 text-xs text-neutral-500">Axiom.trade + Trojan Links</div>
            </div>

            <div class="panel p-5 rounded-xl">
                <div class="flex justify-between items-center text-neutral-400 text-xs font-bold tracking-wider">
                    <span>SCAN CYCLE SPEED</span>
                    <i class="fa-solid fa-stopwatch text-white"></i>
                </div>
                <div class="mt-2 text-3xl font-extrabold text-white mono">10s</div>
                <div class="mt-1 text-xs text-neutral-500">24/7 continuous polling</div>
            </div>
        </div>

        <!-- Main Content Area -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

            <!-- Discovered Meme Coins Stream (2 Cols) -->
            <div class="lg:col-span-2 space-y-4">
                <div class="flex justify-between items-center">
                    <h2 class="font-brand font-bold text-lg text-white flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-red-600"></span> VIRAL TOKEN RADAR
                    </h2>
                    <span class="text-xs text-neutral-400 mono" id="stream-count">0 Tokens</span>
                </div>

                <div id="tokens-container" class="space-y-3">
                    <div class="text-center py-20 panel rounded-xl border-dashed">
                        <i class="fa-solid fa-circle-notch fa-spin text-3xl text-red-600 mb-3"></i>
                        <p class="text-xs text-neutral-400 font-mono">Listening for new Axiom & DexScreener launches...</p>
                    </div>
                </div>
            </div>

            <!-- Real-time Terminal Log (1 Col) -->
            <div class="space-y-4">
                <div class="flex justify-between items-center">
                    <h2 class="font-brand font-bold text-lg text-white flex items-center gap-2">
                        <i class="fa-solid fa-terminal text-red-500 text-sm"></i> SYSTEM LOGS
                    </h2>
                    <span class="text-[10px] px-2 py-0.5 rounded bg-neutral-900 border border-neutral-800 text-neutral-400 mono">STREAM</span>
                </div>

                <div class="panel p-4 rounded-xl h-[520px] flex flex-col">
                    <div id="terminal-logs" class="flex-1 overflow-y-auto space-y-2 text-xs mono text-neutral-300 pr-1"></div>
                </div>
            </div>

        </div>

    </main>

    <script>
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            const btn = document.getElementById('install-btn');
            if(btn) btn.classList.remove('hidden');
        });

        function installPWA() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then(() => { deferredPrompt = null; });
            }
        }

        function copyCA(ca, btn) {
            navigator.clipboard.writeText(ca);
            const orig = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-check text-red-500"></i> Copied';
            setTimeout(() => { btn.innerHTML = orig; }, 1800);
        }

        async function refreshFeed() {
            try {
                const res = await fetch('/api/stream');
                const data = await res.json();

                document.getElementById('metric-total').innerText = data.total_discovered;
                document.getElementById('metric-alerts').innerText = data.total_alerts;
                document.getElementById('stream-count').innerText = `${data.tokens.length} Active`;

                const container = document.getElementById('tokens-container');
                if (data.tokens.length === 0) {
                    container.innerHTML = `
                        <div class="text-center py-20 panel rounded-xl border-dashed">
                            <i class="fa-solid fa-radar text-3xl text-neutral-600 mb-3"></i>
                            <p class="text-xs text-neutral-400 font-mono">Monitoring DexScreener, Pump.fun & X for verified launches...</p>
                        </div>
                    `;
                } else {
                    container.innerHTML = data.tokens.map(t => `
                        <div class="panel p-5 rounded-xl space-y-4">
                            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                                <div class="flex items-center gap-3">
                                    <div class="w-12 h-12 rounded-lg bg-[#141414] border border-[#262626] flex items-center justify-center font-black text-white text-base overflow-hidden">
                                        ${t.image_url ? `<img src="${t.image_url}" class="w-full h-full object-cover">` : `$${t.symbol.slice(0,3)}`}
                                    </div>
                                    <div>
                                        <div class="flex items-center gap-2">
                                            <span class="font-extrabold text-white text-base">${t.name}</span>
                                            <span class="text-xs px-2 py-0.5 rounded bg-red-600/20 text-red-500 font-bold mono border border-red-600/30">$${t.symbol}</span>
                                        </div>
                                        <div class="text-xs text-neutral-400 mono mt-0.5">Price: <span class="text-white font-bold">$${t.price_usd}</span></div>
                                    </div>
                                </div>

                                <div class="flex items-center gap-3 text-xs mono bg-[#121212] px-3 py-2 rounded-lg border border-[#222]">
                                    <div><span class="text-neutral-500">LIQ:</span> <span class="font-bold text-white">$${Math.round(t.liquidity_usd).toLocaleString()}</span></div>
                                    <div><span class="text-neutral-500">VOL:</span> <span class="font-bold text-white">$${Math.round(t.volume_24h_usd).toLocaleString()}</span></div>
                                    <div><span class="text-neutral-500">MCAP:</span> <span class="font-bold text-red-500">$${Math.round(t.fdv_usd).toLocaleString()}</span></div>
                                </div>
                            </div>

                            <div class="p-3 rounded-lg bg-[#080808] border border-[#1a1a1a] text-xs text-neutral-300 italic">
                                "${t.description.slice(0, 180)}..."
                            </div>

                            <div class="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-[#1a1a1a]">
                                <button onclick="copyCA('${t.mint}', this)" class="text-xs text-neutral-300 mono px-3 py-1.5 rounded bg-[#141414] hover:bg-[#202020] border border-[#222] transition flex items-center gap-1.5">
                                    <i class="fa-regular fa-copy text-red-500"></i> ${t.mint.slice(0, 6)}...${t.mint.slice(-6)}
                                </button>

                                <div class="flex flex-wrap items-center gap-2 text-xs font-bold">
                                    <a href="https://axiom.trade/token/${t.mint}" target="_blank" class="px-3 py-1.5 rounded bg-red-600 text-white hover:bg-red-700 transition flex items-center gap-1">
                                        <i class="fa-solid fa-gem"></i> AXIOM
                                    </a>
                                    <a href="https://gmgn.ai/sol/token/${t.mint}" target="_blank" class="px-3 py-1.5 rounded bg-[#171717] text-white border border-[#2b2b2b] hover:border-red-600 transition flex items-center gap-1">
                                        <i class="fa-solid fa-chart-simple"></i> GMGN
                                    </a>
                                    <a href="${t.dex_url}" target="_blank" class="px-3 py-1.5 rounded bg-[#171717] text-white border border-[#2b2b2b] hover:border-white transition flex items-center gap-1">
                                        <i class="fa-solid fa-chart-line"></i> DEX
                                    </a>
                                    <a href="${t.twitter_url}" target="_blank" class="px-3 py-1.5 rounded bg-[#171717] text-white border border-[#2b2b2b] hover:border-sky-500 transition flex items-center gap-1">
                                        <i class="fa-brands fa-x-twitter"></i> X
                                    </a>
                                </div>
                            </div>
                        </div>
                    `).join('');
                }

                const logsContainer = document.getElementById('terminal-logs');
                logsContainer.innerHTML = data.logs.map(l => `
                    <div class="flex gap-2">
                        <span class="text-neutral-500">[${l.time}]</span>
                        <span class="${l.level === 'ALERT' ? 'text-red-500 font-bold' : (l.level === 'WARN' ? 'text-white' : 'text-neutral-300')}">${l.msg}</span>
                    </div>
                `).join('');

            } catch(e) {
                console.error("Poll error:", e);
            }
        }

        setInterval(refreshFeed, 3000);
        refreshFeed();
    </script>
</body>
</html>
"""
