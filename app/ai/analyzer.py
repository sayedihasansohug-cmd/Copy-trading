import json
import re
from typing import Dict, Any, List, Optional
import aiohttp
import google.generativeai as genai
from loguru import logger
from app.config import settings
from app.ai.prompts import ANALYSIS_SYSTEM_PROMPT

class AIAnalyzer:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY.strip().strip("'").strip('"')
        genai.configure(api_key=self.api_key)
        
        # Priority list of proven Gemini models
        self.default_models = [
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro",
            "gemini-2.0-flash",
            "gemini-pro"
        ]

    def _clean_json_string(self, text: str) -> str:
        """Strips markdown and sanitizes response string to pure JSON."""
        cleaned = text.strip()
        # Remove Markdown code blocks
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()
        
        # Find first '{' and last '}'
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end + 1]
            
        return cleaned

    def _fallback_regex_extraction(self, raw_text: str) -> Dict[str, Any]:
        """Emergency fallback: Extracts Solana CA & Ticker using Regex if JSON fails."""
        logger.warning("Attempting emergency regex narrative extraction...")
        
        # Match Base58 Solana Mint Address (32-44 base58 characters)
        sol_ca_pattern = r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b"
        # Match Token Tickers like $PEPE, $WIF, #DOGE
        ticker_pattern = r"[\$#]([A-Za-z0-9]{2,10})\b"

        ca_matches = re.findall(sol_ca_pattern, raw_text)
        ticker_matches = re.findall(ticker_pattern, raw_text)

        # Filter out common Solana system program addresses
        ignored_addresses = {
            "So11111111111111111111111111111111111111112",
            "11111111111111111111111111111111"
        }
        valid_cas = [addr for addr in ca_matches if addr not in ignored_addresses]

        detected_ca = valid_cas[0] if valid_cas else None
        detected_ticker = ticker_matches[0].upper() if ticker_matches else None

        has_target = bool(detected_ca or detected_ticker)

        return {
            "is_tradable_meme": has_target,
            "confidence_score": 80 if has_target else 0,
            "ticker": detected_ticker,
            "contract_address": detected_ca,
            "narrative_category": "Extracted via Regex Engine",
            "sentiment_summary": "Processed through emergency heuristic parser",
            "risk_factors": ["REGEX_HEURISTIC_PARSED"]
        }

    async def _call_gemini_rest_api(self, model_name: str, prompt: str) -> Optional[str]:
        """Direct REST fallback bypassing SDK bugs and version mismatches."""
        clean_model = model_name.replace("models/", "")
        endpoints = [
            f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={self.api_key}",
            f"https://generativelanguage.googleapis.com/v1/models/{clean_model}:generateContent?key={self.api_key}"
        ]

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 800
            }
        }

        async with aiohttp.ClientSession() as session:
            for url in endpoints:
                try:
                    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=8)) as response:
                        if response.status == 200:
                            data = await response.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                                if text:
                                    return text
                except Exception as e:
                    logger.debug(f"Direct REST call to {url} failed: {e}")
                    continue

        return None

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        prompt = (
            f"{ANALYSIS_SYSTEM_PROMPT}\n\n"
            f"Content to analyze:\n{text}\n\n"
            f"Return ONLY valid JSON format."
        )

        # Step 1: Discover dynamically available models from key
        models_to_try = []
        try:
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    models_to_try.append(m.name)
            if models_to_try:
                logger.info(f"Discovered active models on key: {models_to_try}")
        except Exception as e:
            logger.debug(f"Dynamic discovery skipped: {e}")

        # Add defaults
        for default_m in self.default_models:
            if default_m not in models_to_try:
                models_to_try.append(default_m)

        raw_response_text = ""

        # Step 2: Try SDK calls across available models
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = await model.generate_content_async(prompt)
                if response and response.text:
                    raw_response_text = response.text
                    logger.info(f"Successfully generated analysis via SDK ({model_name})")
                    break
            except Exception as sdk_err:
                logger.debug(f"SDK model {model_name} failed: {sdk_err}. Switching to REST...")
                
                # Step 3: Immediate REST API Fallback
                rest_result = await self._call_gemini_rest_api(model_name, prompt)
                if rest_result:
                    raw_response_text = rest_result
                    logger.info(f"Successfully generated analysis via direct REST ({model_name})")
                    break

        # Step 4: Parse JSON safely
        if raw_response_text:
            try:
                cleaned_json = self._clean_json_string(raw_response_text)
                parsed = json.loads(cleaned_json)
                return parsed
            except Exception as parse_err:
                logger.warning(f"JSON decode failed ({parse_err}). Falling back to heuristic regex...")
                return self._fallback_regex_extraction(raw_response_text)

        # Step 5: Final Emergency Fallback directly from raw social text
        logger.error("All AI API attempts failed. Extracting directly from raw input text.")
        return self._fallback_regex_extraction(text)
