import asyncio

from app.config import settings
from app.database.database import init_db
from app.market.scanner import TwitterListener
from app.trading.executor import process_signal, exit_position
from app.blockchain.wallet_monitor import monitor_loop
from app.telegram.bot import build_telegram_app, send_notification, bot_state

STREAM_RULES = [
    "(solana) (gem OR moon OR \"just launched\" OR 100x) -is:retweet lang:en",
]


async def signal_consumer(queue: asyncio.Queue, telegram_app):
    async def notify(text: str):
        await send_notification(telegram_app, text)

    while True:
        signal = await queue.get()
        if bot_state["paused"]:
            continue
        try:
            result = await process_signal(signal, settings.max_position_size_sol, notify=notify)
            print(f"[signal_consumer] {signal.get('cashtags')} -> {result['status']}: "
                  f"{result.get('reason', '')}")
        except Exception as e:
            print(f"[signal_consumer] unhandled error: {e}")


async def position_exit_callback(telegram_app):
    async def _cb(position, price, reason):
        async def notify(text: str):
            await send_notification(telegram_app, text)
        await exit_position(position, price, reason, notify=notify)
    return _cb


async def main():
    print(f"Starting bot on {settings.network} ...")
    if settings.is_mainnet:
        print("⚠️  MAINNET MODE — real funds will be used. Ctrl+C now if unsure.")

    await init_db()

    telegram_app = build_telegram_app()
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

    signal_queue: asyncio.Queue = asyncio.Queue()

    # listener = TwitterListener(bearer_token=settings.twitter_bearer_token, signal_queue=signal_queue)
    # await listener.setup_rules(STREAM_RULES)

    exit_cb = await position_exit_callback(telegram_app)

    tasks = [
        asyncio.create_task(signal_consumer(signal_queue, telegram_app)),
        asyncio.create_task(monitor_loop(exit_cb, interval_seconds=15)),
        # asyncio.create_task(listener.run()),
    ]

    await send_notification(telegram_app, f"🤖 Bot started on {settings.network}")

    try:
        await asyncio.gather(*tasks)
    finally:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
