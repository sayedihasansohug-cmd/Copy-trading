import asyncio
from solana.rpc.async_api import AsyncClient
from loguru import logger

class TransactionHelper:
    @staticmethod
    async def wait_for_confirmation(rpc_client: AsyncClient, tx_hash: str, max_retries: int = 15) -> bool:
        for attempt in range(max_retries):
            try:
                response = await rpc_client.get_signature_statuses([tx_hash])
                statuses = response.value
                if statuses and statuses[0] is not None:
                    status = statuses[0]
                    if status.err:
                        logger.error(f"Transaction {tx_hash} failed: {status.err}")
                        return False
                    if status.confirmation_status:
                        logger.info(f"Transaction {tx_hash} status: {status.confirmation_status}")
                        return True
            except Exception as e:
                logger.warning(f"Error checking status for {tx_hash}: {e}")
            await asyncio.sleep(2)
        return False
