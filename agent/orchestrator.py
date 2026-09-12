import logging
import re
from pathlib import Path
from datetime import datetime
from openai import OpenAI

from search.serper import SerperClient
from search.scraper import WebScraper
from generators.pdf_gen import generate_notes_pdf
from generators.docx_gen import generate_notes_docx
from generators.pptx_gen import generate_notes_pptx
from .router import AcademicRouter, StudyIntent, FerozRouter, FerozIntent
from .prompts import ACADEMIC_STUDY_NOTES_PROMPT, EXECUTIVE_SUMMARY_PROMPT

logger = logging.getLogger(__name__)

def sanitize_notes_output(raw_markdown: str, topic: str = "", subject: str = "", reference: str = "") -> str:
    """Sanitize LLM output to guarantee zero thinking preamble or syllabus debate leakage."""
    if not raw_markdown:
        return ""

    # 1. Strip reasoning blocks: <think>...</think>
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw_markdown, flags=re.IGNORECASE).strip()

    # 2. Look for real markdown title at start of line: ^# 📖
    # Find all line-start headers
    title_matches = list(re.finditer(r"(?m)^#\s*📖\s*([^\n]+)", cleaned))
    if title_matches:
        # Pick the one followed by Section 1 (or the last one)
        best_start = None
        for tm in reversed(title_matches):
            after_text = cleaned[tm.start():]
            if "## 1." in after_text or "1. 📌" in after_text:
                best_start = tm.start()
                break
        if best_start is None:
            best_start = title_matches[-1].start()
        cleaned = cleaned[best_start:].strip()
    else:
        # Fallback: look for line-start ## 1.
        sec1_match = re.search(r"(?m)^##\s*1\.", cleaned)
        if sec1_match:
            body = cleaned[sec1_match.start():].strip()
            cleaned = f"# 📖 {topic}\n**Subject**: {subject} | **Reference**: *{reference}*\n\n{body}"
        else:
            # Fallback to any # 📖 match
            match = re.search(r"#\s*📖", cleaned)
            if match:
                cleaned = cleaned[match.start():].strip()

    # 3. Clean any lingering planning commentary or code blocks
    cleaned = re.sub(r"^(Here'?s a thinking process:?|Analyze User Request:?|Key Point:?|Role:?|Task:?|Formatting Conventions:?|Deconstruct the Topic:?).*?\n", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```(?:markdown)?\s*\n", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n```\s*$", "", cleaned).strip()

    # 4. Guarantee markdown title header exists
    if not cleaned:
        cleaned = f"# 📖 {topic}\n**Subject**: {subject} | **Reference**: *{reference}*\n\n{raw_markdown.strip()}"
    elif not cleaned.startswith("#"):
        cleaned = f"# 📖 {topic}\n**Subject**: {subject} | **Reference**: *{reference}*\n\n{cleaned}"

    return cleaned.strip()

def sanitize_summary_output(raw_summary: str) -> str:
    """Strip any conversational chatter or thinking process from summary."""
    if not raw_summary:
        return ""

    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw_summary, flags=re.IGNORECASE).strip()

    # Extract bullet lines
    lines = [line.strip() for line in cleaned.split("\n") if line.strip().startswith(("-", "•", "*"))]
    clean_bullets = []
    meta_keywords = [
        "role:", "topic:", "constraints:", "critical instruction", "re-reading",
        "output only", "wait,", "there's a conflict", "no preamble", "must cover",
        "total response", "let me", "i should", "yes, the", "i will", "thinking process",
        "analyze user"
    ]
    for l in lines:
        lower = l.lower()
        if any(kw in lower for kw in meta_keywords):
            continue
        clean_bullets.append(l)

    if clean_bullets:
        if len(clean_bullets) > 4:
            clean_bullets = clean_bullets[-4:]
        return "\n".join(clean_bullets).strip()

    # Fallback if no bullets
    cleaned = re.sub(r"^(Alright team,?|Hello students,?|Feroz here!?|Hey everyone!?)[^\n]*\n*", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned

class TokenTracker:
    def __init__(self, quota_limit: int = 50000):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.call_count = 0
        self.quota_limit = quota_limit
        self.last_error = None
        self.is_over_limit = False
        self.history = []

    def record_usage(self, prompt_tokens: int, completion_tokens: int, total_tokens: int, model: str):
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += total_tokens
        self.call_count += 1
        if self.total_tokens >= self.quota_limit:
            self.is_over_limit = True
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        })

    def record_error(self, error_msg: str):
        self.last_error = error_msg
        if "402" in error_msg or "budget" in error_msg.lower() or "credit" in error_msg.lower() or "afford" in error_msg.lower():
            self.is_over_limit = True

    def reset(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.call_count = 0
        self.last_error = None
        self.is_over_limit = False
        self.history = []

    def to_dict(self) -> dict:
        pct = round((self.total_tokens / max(1, self.quota_limit)) * 100, 1)
        return {
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "quota_limit": self.quota_limit,
            "quota_percentage": min(100.0, pct),
            "remaining_tokens": max(0, self.quota_limit - self.total_tokens),
            "call_count": self.call_count,
            "is_over_limit": self.is_over_limit or (self.total_tokens >= self.quota_limit),
            "last_error": self.last_error,
            "status": "over_limit" if (self.is_over_limit or self.total_tokens >= self.quota_limit) else "healthy"
        }

class StudyAgentOrchestrator:
    """Universal Multi-Engine Academic Orchestrator with Authoritative Textbook Grounding."""

    def __init__(
        self,
        openrouter_api_key: str,
        serper_api_key: str,
        model: str = "openai/gpt-4o-mini",
        output_dir: str | Path = "./generated_notes"
    ):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key
        )
        self.default_model = model
        self.serper = SerperClient(api_key=serper_api_key)
        self.scraper = WebScraper()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tracker = TokenTracker(quota_limit=50000)

    def _create_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        max_tokens: int = 1500,
        retries: int = 2
    ):
        """Call OpenRouter with dynamic model routing, bounded tokens, and retry handling."""
        import time
        target_model = model or self.default_model
        current_tokens = max_tokens

        for attempt in range(retries + 1):
            try:
                logger.info(f"Dispatching query to AI Engine: '{target_model}' (tokens: {current_tokens})")
                resp = self.client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=current_tokens
                )
                if resp and resp.choices and not resp.choices[0].message.content and hasattr(resp.choices[0].message, "reasoning"):
                    resp.choices[0].message.content = resp.choices[0].message.reasoning

                if hasattr(resp, "usage") and resp.usage:
                    self.tracker.record_usage(
                        prompt_tokens=resp.usage.prompt_tokens or 0,
                        completion_tokens=resp.usage.completion_tokens or 0,
                        total_tokens=resp.usage.total_tokens or 0,
                        model=target_model
                    )
                return resp
            except Exception as e:
                err_str = str(e)
                logger.warning(f"Error on model {target_model} (attempt {attempt+1}/{retries+1}): {err_str}")
                self.tracker.record_error(err_str)

                # If model not found or rate-limited, fall back to gemini or gpt-4o-mini
                if ("404" in err_str or "429" in err_str) and attempt < retries:
                    if target_model != "google/gemini-2.5-flash":
                        logger.info("Falling back to google/gemini-2.5-flash...")
                        target_model = "google/gemini-2.5-flash"
                    else:
                        logger.info("Falling back to openai/gpt-4o-mini...")
                        target_model = "openai/gpt-4o-mini"
                    time.sleep(2)
                    continue

                if ("402" in err_str or "in_flight_budget" in err_str or "more credits" in err_str) and attempt < retries:
                    logger.warning("In-flight budget limit hit on OpenRouter. Adapting tokens...")
                    afford_match = re.search(r"can only afford (\d+)", err_str)
                    if afford_match:
                        affordable = int(afford_match.group(1))
                        if affordable >= 1200:
                            current_tokens = affordable - 10
                            logger.info(f"Dynamically adjusted tokens to {current_tokens}")
                            time.sleep(1)
                            continue

                    # If insufficient budget for current model, fall back to high-speed free engine
                    if target_model != "poolside/laguna-s-2.1:free":
                        logger.info("Falling back to poolside/laguna-s-2.1:free for unlimited budget...")
                        target_model = "poolside/laguna-s-2.1:free"
                    else:
                        logger.info("Falling back to nvidia/nemotron-3-ultra-550b-a55b:free...")
                        target_model = "nvidia/nemotron-3-ultra-550b-a55b:free"
                    current_tokens = min(current_tokens, 1500)
                    time.sleep(1)
                    continue

                raise

    def generate_study_package(
        self,
        query: str,
        gui_model: str = "openai/gpt-4o-mini",
        gui_subject: str = "",
        requested_formats: list[str] | None = None,
        use_gui_agent: bool = False,
        gui_target: str = "auto",
        headless: bool = False
    ) -> dict:
        """Run full research, authoritative textbook grounding, and note-styling pipeline."""
        if not requested_formats:
            requested_formats = ["handwritten", "pdf"]
        requested_formats = [f.lower().strip() for f in requested_formats]

        # 1. Academic Intent & Reference Resolution
        intent: StudyIntent = AcademicRouter.parse_student_query(query, gui_model, gui_subject)
        logger.info(f"Academic Intent Resolved: {intent.understanding_briefing}")

        # 2. Research & Academic Content Retrieval (GUI Agent or Serper Scraper)
        active_gui_agent = use_gui_agent or getattr(intent, "use_gui_agent", False)
        active_gui_target = gui_target if (gui_target and gui_target != "auto") else getattr(intent, "gui_target", "auto")
        web_context = ""
        sources_list = []
        search_results = []

        if active_gui_agent:
            logger.info(f"🤖 [GUI Browser Agent] Operating like a human on target: {active_gui_target.upper()} Web...")
            from .gui_agent import HumanGUIAgent
            try:
                gui_operator = HumanGUIAgent(headless=headless)
                gui_res = gui_operator.research_topic(target=active_gui_target, topic=intent.cleaned_topic)
                gui_operator.close()

                if gui_res.get("content"):
                    web_context = (
                        f"Primary Verified Source: {gui_res.get('source')}\n"
                        f"URL: {gui_res.get('url', '')}\n\n"
                        f"Content Extracted via Web Agent:\n{gui_res.get('content')}\n\n"
                        f"Authoritative Textbook Grounding: {intent.target_book}"
                    )
                    sources_list = gui_res.get("sources", [{"title": gui_res.get("source"), "link": gui_res.get("url", "#")}])
            except Exception as gui_err:
                logger.error(f"GUI Agent operation encountered error: {gui_err}. Falling back to standard research...")

        # Fallback to Serper & Scraper if web_context is still empty
        if not web_context:
            search_results = []
            for q in intent.optimized_queries[:2]:
                results = self.serper.search_educational_notes(q, num_results=3)
                search_results.extend(results)

            urls_to_scrape = [res["link"] for res in search_results if res.get("link")]
            scraped_pages = self.scraper.scrape_multiple(urls_to_scrape, max_total_chars=4000)

            context_parts = [
                f"Subject: {intent.subject_name}",
                f"Authoritative Reference: {intent.target_book}"
            ]
            for idx, res in enumerate(search_results[:4], 1):
                context_parts.append(f"Source [{idx}] {res.get('title')}: {res.get('snippet')}")
                sources_list.append({"title": res.get("title", ""), "link": res.get("link", "")})
            for page in scraped_pages[:3]:
                context_parts.append(f"Text from {page['url']}:\n{page['content']}")

            web_context = "\n\n".join(context_parts)

        # 3. Synthesize Handwritten Student Study Sheet
        logger.info(f"Synthesizing study sheet using {intent.selected_model}...")
        notes_prompt = ACADEMIC_STUDY_NOTES_PROMPT.format(
            subject=intent.subject_name,
            topic=intent.cleaned_topic,
            target_book=intent.target_book,
            web_context=web_context
        )

        notes_response = self._create_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert university professor and researcher. "
                        "Output ONLY the final markdown study sheet. "
                        "Strict rule: Absolutely NO preamble, NO meta-analysis, NO planning steps, and NO chain of thought. "
                        "Start immediately on line 1 with '# 📖 <Title>'."
                    )
                },
                {"role": "user", "content": notes_prompt}
            ],
            model=intent.selected_model,
            max_tokens=2500
        )
        raw_notes_markdown = notes_response.choices[0].message.content or ""
        # Strictly sanitize notes output to eliminate any thinking process or preambles
        full_notes_markdown = sanitize_notes_output(
            raw_notes_markdown,
            topic=intent.cleaned_topic,
            subject=intent.subject_name,
            reference=intent.target_book
        )

        # 4. Summary synthesis
        summary_prompt = EXECUTIVE_SUMMARY_PROMPT.format(
            topic=intent.cleaned_topic,
            notes_content=full_notes_markdown[:2500]
        )
        summary_response = self._create_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an academic summarizer. Output ONLY the final 3-4 bullet points. "
                        "Strict rule: Absolutely NO analysis of the prompt, NO preamble, and NO thinking process."
                    )
                },
                {"role": "user", "content": summary_prompt}
            ],
            model=intent.selected_model,
            max_tokens=400
        )
        raw_summary_text = summary_response.choices[0].message.content or f"Study notes for {intent.cleaned_topic}"
        summary_text = sanitize_summary_output(raw_summary_text)

        # 5. Compile Documents (PDF, PPTX, DOCX)
        safe_filename = re.sub(r"[^\w\-_\. ]", "_", intent.cleaned_topic).strip().replace(" ", "_")
        files = {}

        for fmt in requested_formats:
            try:
                if fmt == "pdf":
                    pdf_path = self.output_dir / f"{safe_filename}_Notes.pdf"
                    generate_notes_pdf(intent.cleaned_topic, full_notes_markdown, pdf_path)
                    files["pdf"] = f"/api/download/{pdf_path.name}"
                elif fmt == "docx":
                    docx_path = self.output_dir / f"{safe_filename}_Notes.docx"
                    generate_notes_docx(intent.cleaned_topic, full_notes_markdown, docx_path)
                    files["docx"] = f"/api/download/{docx_path.name}"
                elif fmt == "pptx":
                    pptx_path = self.output_dir / f"{safe_filename}_Slides.pptx"
                    generate_notes_pptx(intent.cleaned_topic, full_notes_markdown, pptx_path)
                    files["pptx"] = f"/api/download/{pptx_path.name}"
            except Exception as e:
                logger.error(f"Failed to compile {fmt}: {e}")

        # Aesthetic book leather color
        colors = ["#8B3A3A", "#2E5B88", "#2E6B4F", "#7A5229", "#5A3D68", "#C27D38", "#1F4E5B", "#9C4153"]
        book_color = colors[abs(hash(intent.cleaned_topic)) % len(colors)]

        return {
            "id": f"{safe_filename}_{int(datetime.now().timestamp())}",
            "topic": intent.cleaned_topic,
            "subject": intent.subject_name,
            "subject_code": intent.subject_code,
            "target_book": intent.target_book,
            "model_used": intent.selected_model,
            "briefing": intent.understanding_briefing,
            "notes_markdown": full_notes_markdown,
            "summary": summary_text,
            "sources": sources_list if sources_list else [{"title": r.get("title", ""), "link": r.get("link", ""), "snippet": r.get("snippet", "")} for r in search_results[:4]],
            "files": files,
            "color": book_color,
            "created_at": datetime.now().strftime("%B %d, %Y • %I:%M %p")
        }
