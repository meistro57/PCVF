""" Prompt generator module """

import json
import time
from typing import List, Dict, Any
from core.segmenter import Segment
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, RETRY_LLM

def generate_prompts(segments: List[Segment], global_style: str, negative_style: str, retry=int(RETRY_LLM)) -> Dict[str, Any]:
    import openai

    client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

    system_prompt = f"""You are generating stable-diffusion prompts for video segments.
Rules:
- Incorporate the provided GLOBAL_STYLE into each prompt: "{global_style}"
- Never include text/typography in the image. Avoid words, logos, watermarks.
- Negative prompt must discourage blur, artifacts, and unwanted text: "{negative_style}"
- Caption must be 6–12 words, human-hook style, not copied transcript.
Return strict JSON with the shape:
{{"results": [{{"segment_index": <int>, "prompt": "<positive prompt>", "negative_prompt": "<negative or global default>", "caption": "<short hook>"}}, ...]}}"""

    user_prompt = f"Segments:\n" + '\n'.join(f"{s.index}: {s.text}" for s in segments)

    for attempt in range(retry + 1):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            if attempt == retry:
                raise
            time.sleep((2 ** attempt))

    raise ValueError("LLM failed after retries")