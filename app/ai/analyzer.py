import json
from typing import Dict, Any
from openai import AsyncOpenAI
from loguru import logger
from app.config import settings
from app.ai.prompts import ANALYSIS_SYSTEM_PROMPT

class AIAnalyzer:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this content:\n\n{text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {str(e)}")
            return {
                "is_tradable_meme": False,
                "confidence_score": 0,
                "ticker": None,
                "contract_address": None,
                "narrative_category": "Unknown",
                "sentiment_summary": "Analysis failed due to error",
                "risk_factors": ["LLM_ERROR"]
            }
