from app.market.token_data import get_token_data, passes_safety_filter
from app.ai.analyzer import analyze_signal
from app.trading.risk_manager import check_can_open_position, RiskCheckFailed
from app.trading.position_manager import open_position, close_position
from app.blockchain.transaction import buy_token, sell_token, SwapError
from app.database.database import get_session
from app.database.models import TradeLog


async def _log_trade(mint_address: str, side: str, amount_sol: float,
                      tx_signature: str | None, success: bool,
                      error_message: str | None = None, ai_reasoning: str | None = None):
    async with get_session() as session:
        session.add(TradeLog(
            mint_address=mint_address, side=side, amount_sol=amount_sol,
            tx_signature=tx_signature, success=success,
            error_message=error_message, ai_reasoning=ai_reasoning,
        ))


async def process_signal(signal: dict, sol_amount: float, notify=None) -> dict:
    mints = signal.get("possible_mints") or []
    if not mints:
        return {"status": "skipped", "reason": "no mint address in signal"}
    mint_address = mints[0]

    token_data = await get_token_data(mint_address)
    if not token_data:
        return {"status": "skipped", "reason": "no market data found"}

    passed, reason = passes_safety_filter(token_data)
    if not passed:
        return {"status": "skipped", "reason": f"safety filter: {reason}"}

    try:
        await check_can_open_position(mint_address, sol_amount)
    except RiskCheckFailed as e:
        return {"status": "skipped", "reason": f"risk check: {e}"}

    analysis = await analyze_signal(signal, token_data)
    if analysis["decision"] != "buy":
        return {"status": "skipped", "reason": f"ai: {analysis['reasoning']}", "analysis": analysis}

    if notify:
        await notify(f"🟢 Buying {token_data['symbol']} — {analysis['reasoning']} "
                      f"(confidence {analysis['confidence']}%)")
    try:
        tx_sig = await buy_token(mint_address, sol_amount)
    except SwapError as e:
        await _log_trade(mint_address, "buy", sol_amount, None, False, str(e))
        if notify:
            await notify(f"🔴 Buy failed for {token_data['symbol']}: {e}")
        return {"status": "error", "reason": str(e)}

    await _log_trade(mint_address, "buy", sol_amount, tx_sig, True, ai_reasoning=analysis["reasoning"])
    position = await open_position(
        mint_address=mint_address,
        entry_price=token_data["price_usd"],
        amount_tokens=sol_amount / token_data["price_usd"] if token_data["price_usd"] else 0,
        sol_invested=sol_amount,
        symbol=token_data["symbol"],
    )
    if notify:
        await notify(f"✅ Bought {token_data['symbol']} — tx: {tx_sig[:8]}... "
                      f"SL: {position.stop_loss_price:.6f} TP: {position.take_profit_price:.6f}")

    return {"status": "bought", "tx_signature": tx_sig, "position_id": position.id, "analysis": analysis}


async def exit_position(position, current_price: float, reason: str, notify=None):
    mint_address = position.token.mint_address
    try:
        token_amount_lamports = int(position.amount_tokens)
        tx_sig = await sell_token(mint_address, token_amount_lamports)
    except SwapError as e:
        await _log_trade(mint_address, "sell", position.sol_invested, None, False, str(e))
        if notify:
            await notify(f"🔴 Sell failed for position {position.id}: {e}")
        return

    await _log_trade(mint_address, "sell", position.sol_invested, tx_sig, True,
                      ai_reasoning=f"exit reason: {reason}")
    closed = await close_position(position.id, current_price)
    emoji = "🟢" if closed.realized_pnl_sol and closed.realized_pnl_sol > 0 else "🔴"
    if notify:
        await notify(f"{emoji} Closed position {position.id} ({reason}) — "
                      f"PnL: {closed.realized_pnl_sol:.4f} SOL — tx: {tx_sig[:8]}...")
