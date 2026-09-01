import json
from typing import Dict, Any
import google.generativeai as genai
from loguru import logger
from app.config import settings
from app.ai.prompts import ANALYSIS_SYSTEM_PROMPT

class AIAnalyzer:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=ANALYSIS_SYSTEM_PROMPT,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        )

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        try:
            response = await self.model.generate_content_async(
                f"Analyze this content:\n\n{text}"
            )
            content = response.text
            return json.loads(content)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            return {
                "is_tradable_meme": False,
                "confidence_score": 0,
                "ticker": None,
                "contract_address": None,
                "narrative_category": "Unknown",
                "sentiment_summary": "Analysis failed due to error",
                "risk_factors": ["LLM_ERROR"]
            }
