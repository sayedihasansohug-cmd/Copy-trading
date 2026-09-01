import json
from typing import Dict, Any
import google.generativeai as genai
from loguru import logger
from app.config import settings
from app.ai.prompts import ANALYSIS_SYSTEM_PROMPT

class AIAnalyzer:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Compatible model list with fallbacks
        self.model_candidates = [
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro",
            "gemini-pro"
        ]

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        prompt = (
            f"{ANALYSIS_SYSTEM_PROMPT}\n\n"
            f"Analyze this content and output valid JSON ONLY:\n{text}"
        )

        for model_name in self.model_candidates:
            try:
                model = genai.GenerativeModel(model_name)
                response = await model.generate_content_async(prompt)
                raw_text = response.text.strip()

                # Clean markdown backticks if returned
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]

                data = json.loads(raw_text.strip())
                logger.info(f"Successfully analyzed via model: {model_name}")
                return data

            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}. Trying fallback...")
                continue

        logger.error("All Gemini model attempts failed.")
        return {
            "is_tradable_meme": False,
            "confidence_score": 0,
            "ticker": None,
            "contract_address": None,
            "narrative_category": "Unknown",
            "sentiment_summary": "Analysis failed",
            "risk_factors": ["LLM_ERROR"]
        }
