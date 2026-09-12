import json
import logging
from openai import OpenAI
from pydantic import BaseModel, Field
from .prompts import INTENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class StudentIntent(BaseModel):
    is_study_request: bool = True
    topic: str = ""
    requested_formats: list[str] = Field(default_factory=lambda: ["pdf"])
    conversational_reply: str = ""

class IntentClassifier:
    """Classifies user messages and extracts academic topics and desired formats."""

    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

    def parse_message(self, message: str) -> StudentIntent:
        """Parse incoming WhatsApp message using LLM."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": message.strip()}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=250
            )
            raw_content = response.choices[0].message.content or "{}"
            data = json.loads(raw_content)

            # Ensure formats are lowercase and sanitized
            formats = [f.lower().strip() for f in data.get("requested_formats", ["pdf"]) if f.lower().strip() in ("pdf", "docx", "pptx")]
            if not formats and data.get("is_study_request", False):
                formats = ["pdf"]

            return StudentIntent(
                is_study_request=data.get("is_study_request", False),
                topic=data.get("topic", "").strip(),
                requested_formats=formats,
                conversational_reply=data.get("conversational_reply", "")
            )
        except Exception as e:
            logger.error(f"Failed to parse user intent: {e}")
            # Fallback heuristic
            lower = message.lower()
            formats = ["pdf"]
            if "ppt" in lower or "presentation" in lower or "slide" in lower:
                formats.append("pptx")
            if "doc" in lower or "word" in lower:
                formats.append("docx")

            return StudentIntent(
                is_study_request=True,
                topic=message.strip()[:100],
                requested_formats=formats,
                conversational_reply=""
            )
