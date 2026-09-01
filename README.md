# AI Meme Trading Bot

Twitter/X viral-signal-driven Solana memecoin trading bot with AI filtering
and hard risk limits.

## ⚠️ Before you do anything

1. Use a dedicated wallet, not your main wallet. Fund it only with money
   you can afford to lose completely.
2. Start on `devnet` (NETWORK=devnet in .env). Test the full flow for
   several days before touching mainnet.
3. There is no such thing as a 100% accurate trading strategy. Expect
   losing trades — risk limits exist to keep any single loss small.
4. You need your own X (Twitter) API bearer token with filtered stream
   access (Basic tier or higher) — not included/provided.

## Setup

pip install -r requirements.txt
cp .env .env.local   # fill in real values

## Run

python -m app.main

Telegram commands: /status /pause /resume /balance
