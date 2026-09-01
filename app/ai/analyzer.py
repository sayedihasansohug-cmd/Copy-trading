import json
import anthropic

from app.config import settings
from app.ai.prompts import ANALYSIS_SYSTEM_PROMPT, build_analysis_prompt

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


async def analyze_signal(signal: dict, token_data: dict) -> dict:
    prompt = build_analysis_prompt(signal, token_data)
    try:
        response = await client.messages.create(
            model=settings.ai_model,
            max_tokens=300,
            system=ANALYSIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(text)
    except (json.JSONDecodeError, anthropic.APIError, Exception) as e:
        return {
            "decision": "skip",
            "confidence": 0,
            "reasoning": f"analysis failed, defaulting to skip: {e}",
            "red_flags": ["ai_error"],
        }

    if result.get("confidence", 0) > 75:
        result["confidence"] = 75

    return result
