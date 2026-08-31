from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings
from app.blockchain.solana import solana_conn
from app.trading.risk_manager import get_open_position_count, get_today_realized_pnl

bot_state = {"paused": False}


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    open_positions = await get_open_position_count()
    today_pnl = await get_today_realized_pnl()
    balance = await solana_conn.get_sol_balance()
    state = "PAUSED ⏸️" if bot_state["paused"] else "RUNNING ▶️"
    await update.message.reply_text(
        f"Status: {state}\n"
        f"Wallet balance: {balance:.4f} SOL\n"
        f"Open positions: {open_positions}/{settings.max_open_positions}\n"
        f"Today's PnL: {today_pnl:.4f} SOL\n"
        f"Network: {settings.network}"
    )


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_state["paused"] = True
    await update.message.reply_text("Bot paused. No new trades will open.")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_state["paused"] = False
    await update.message.reply_text("Bot resumed.")


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = await solana_conn.get_sol_balance()
    await update.message.reply_text(f"Wallet balance: {balance:.4f} SOL ({settings.network})")


def build_telegram_app() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("balance", cmd_balance))
    return app


async def send_notification(app: Application, text: str):
    await app.bot.send_message(chat_id=settings.telegram_chat_id, text=text)
