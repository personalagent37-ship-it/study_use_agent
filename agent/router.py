import re
from typing import NamedTuple
from .syllabus import UNIVERSAL_SUBJECTS, detect_subject_from_query

class StudyIntent(NamedTuple):
    raw_query: str
    cleaned_topic: str
    subject_name: str
    subject_code: str
    target_book: str
    selected_model: str
    understanding_briefing: str
    optimized_queries: list[str]
    use_gui_agent: bool = False
    gui_target: str = "auto"

# Backwards compatibility alias
FerozIntent = StudyIntent

# Supported OpenRouter Model Slugs
MODEL_SLUGS = {
    "gemini": "google/gemini-3.8-flash",
    "gemini-3.8": "google/gemini-3.8-flash",
    "gemini-3.7": "google/gemini-3.7-flash",
    "gemini-3.6": "google/gemini-3.6-flash",
    "gemini-3.1": "google/gemini-3.1-pro-preview",
    "gemini-2.5": "google/gemini-2.5-flash",
    "claude": "anthropic/claude-sonnet-4.6",
    "claude-sonnet-4.6": "anthropic/claude-sonnet-4.6",
    "claude-opus-4.6": "anthropic/claude-opus-4.6",
    "claude-3.5": "anthropic/claude-sonnet-5",
    "gpt-oss": "openai/gpt-oss-120b",
    "perplexity": "perplexity/sonar",
    "gpt": "openai/gpt-4o-mini",
    "nemotron": "nvidia/nemotron-3.5-lightning:free"
}

class AcademicRouter:
    """Universal Academic Query Clarifier, Model Router, and Reference Mapper."""

    @staticmethod
    def parse_student_query(raw_prompt: str, gui_model: str = "google/gemini-3.8-flash", gui_subject: str = "") -> StudyIntent:
        prompt_lower = raw_prompt.lower().strip()
        clean_text = raw_prompt

        # 1. Detect GUI Browser Agent command in chat
        use_gui = False
        gui_target = "auto"

        if any(kw in prompt_lower for kw in ["from claude", "claude ai", "claude web", "use claude"]):
            use_gui = True
            gui_target = "claude"
            clean_text = re.sub(r"\b(and\s+)?(take|get|fetch)\s+(this\s+)?content\s+from\s+claude(\s+ai)?:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
            clean_text = re.sub(r"\b(use\s+)?claude(\s+ai)?(\s+web)?(\s+to)?\b", "", clean_text, flags=re.IGNORECASE).strip()
            clean_text = re.sub(r"\b(from|on)\s+claude(\s+ai)?\b", "", clean_text, flags=re.IGNORECASE).strip()
        elif any(kw in prompt_lower for kw in ["from gemini", "gemini web", "use gemini"]):
            use_gui = True
            gui_target = "gemini"
            clean_text = re.sub(r"\b(and\s+)?(take|get|fetch)\s+(this\s+)?content\s+from\s+gemini(\s+ai)?:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
            clean_text = re.sub(r"\b(use\s+)?gemini(\s+ai)?(\s+web)?(\s+to)?\b", "", clean_text, flags=re.IGNORECASE).strip()
            clean_text = re.sub(r"\b(from|on)\s+gemini\b", "", clean_text, flags=re.IGNORECASE).strip()
        elif any(kw in prompt_lower for kw in ["from perplexity", "perplexity web", "use perplexity"]):
            use_gui = True
            gui_target = "perplexity"
            clean_text = re.sub(r"\b(and\s+)?(take|get|fetch)\s+(this\s+)?content\s+from\s+perplexity:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
            clean_text = re.sub(r"\b(use\s+)?perplexity(\s+ai)?(\s+web)?(\s+to)?\b", "", clean_text, flags=re.IGNORECASE).strip()
            clean_text = re.sub(r"\b(from|on)\s+perplexity\b", "", clean_text, flags=re.IGNORECASE).strip()
        elif any(kw in prompt_lower for kw in ["gui agent", "browser agent", "browse google", "search on google", "use google"]):
            use_gui = True
            gui_target = "google" if "google" in prompt_lower else "perplexity"
            clean_text = re.sub(r"\b(gui agent|browser agent|use browser|browse google|search on google|use google(\s+search)?)\b", "", clean_text, flags=re.IGNORECASE).strip()

        # 2. Detect explicit model command in chat
        chosen_model = gui_model

        # Check specific models first
        if "gemini 3.8" in prompt_lower or "gemini-3.8" in prompt_lower:
            chosen_model = MODEL_SLUGS["gemini-3.8"]
            clean_text = re.sub(r"\b(use|using)?\s*gemini[- ]?3\.8:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
        elif "gemini 3.7" in prompt_lower or "gemini-3.7" in prompt_lower:
            chosen_model = MODEL_SLUGS["gemini-3.7"]
            clean_text = re.sub(r"\b(use|using)?\s*gemini[- ]?3\.7:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
        elif "gemini 3.6" in prompt_lower or "gemini-3.6" in prompt_lower:
            chosen_model = MODEL_SLUGS["gemini-3.6"]
            clean_text = re.sub(r"\b(use|using)?\s*gemini[- ]?3\.6:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
        elif "gemini 3.1" in prompt_lower or "gemini-3.1" in prompt_lower:
            chosen_model = MODEL_SLUGS["gemini-3.1"]
            clean_text = re.sub(r"\b(use|using)?\s*gemini[- ]?3\.1:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
        elif "claude opus" in prompt_lower or "opus 4.6" in prompt_lower:
            chosen_model = MODEL_SLUGS["claude-opus-4.6"]
            clean_text = re.sub(r"\b(use|using)?\s*claude[- ]?opus[- ]?(4\.6)?:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
        elif "claude sonnet" in prompt_lower or "sonnet 4.6" in prompt_lower:
            chosen_model = MODEL_SLUGS["claude-sonnet-4.6"]
            clean_text = re.sub(r"\b(use|using)?\s*claude[- ]?sonnet[- ]?(4\.6)?:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
        elif "gpt-oss" in prompt_lower or "gpt oss" in prompt_lower:
            chosen_model = MODEL_SLUGS["gpt-oss"]
            clean_text = re.sub(r"\b(use|using)?\s*gpt[- ]?oss[- ]?(120b)?:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
        elif "use gemini" in prompt_lower or "using gemini" in prompt_lower or prompt_lower.startswith("gemini:"):
            chosen_model = MODEL_SLUGS["gemini"]
            clean_text = re.sub(r"\b(use|using)?\s*gemini:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
        elif "use claude" in prompt_lower or "using claude" in prompt_lower or prompt_lower.startswith("claude:"):
            chosen_model = MODEL_SLUGS["claude"]
            clean_text = re.sub(r"\b(use|using)?\s*claude:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
        elif "use perplexity" in prompt_lower or "using perplexity" in prompt_lower or prompt_lower.startswith("perplexity:"):
            chosen_model = MODEL_SLUGS["perplexity"]
            clean_text = re.sub(r"\b(use|using)?\s*perplexity:?\s*", "", clean_text, flags=re.IGNORECASE).strip()
        elif "use gpt" in prompt_lower or "using gpt" in prompt_lower or prompt_lower.startswith("gpt:"):
            chosen_model = MODEL_SLUGS["gpt"]
            clean_text = re.sub(r"\b(use|using)?\s*gpt(-4o|-4o-mini)?:?\s*", "", clean_text, flags=re.IGNORECASE).strip()

        # Clean conversational filler: "i want to notes on", "give me notes about", "what is", "explain"
        clean_topic = re.sub(
            r"^(i\s+(want|wnat)\s+(to\s+)?(notes|make\s+notes|notes\s+on)?|give\s+me\s+notes\s+on|make\s+notes\s+on|can\s+you\s+give\s+me\s+notes\s+on|notes\s+on|explain|what\s+(is|are|does|was)|how\s+(does|do|to)|tell\s+me\s+about|define)\s*",
            "",
            clean_text,
            flags=re.IGNORECASE
        ).strip()

        # Clean prompt instructions from user like "i want the point to point notes and easy to understand"
        clean_topic = re.sub(r"\bi\s+(want|wnat)\s+the\s+point\s+to\s+point\s+notes.*$", "", clean_topic, flags=re.IGNORECASE).strip()
        clean_topic = re.sub(r"\beasy\s+to\s+(undertand|understand).*$", "", clean_topic, flags=re.IGNORECASE).strip()
        clean_topic = re.sub(r"\bpoint\s+to\s+point\s+notes.*$", "", clean_topic, flags=re.IGNORECASE).strip()
        clean_topic = re.sub(r"\bfor\s+(exam|semester|revision).*$", "", clean_topic, flags=re.IGNORECASE).strip()

        # Fix common spelling typos & canonical casings
        clean_topic = re.sub(r"\bopen\s*cv\b", "OpenCV", clean_topic, flags=re.IGNORECASE)
        clean_topic = re.sub(r"\benginearing\b", "Engineering", clean_topic, flags=re.IGNORECASE)
        clean_topic = re.sub(r"\bphysic\b", "Physics", clean_topic, flags=re.IGNORECASE)
        clean_topic = re.sub(r"\bmats\b", "Mathematics", clean_topic, flags=re.IGNORECASE)
        clean_topic = re.sub(r"\bmathes\b", "Mathematics", clean_topic, flags=re.IGNORECASE)
        clean_topic = re.sub(r"\bdrowing\b", "Drawing", clean_topic, flags=re.IGNORECASE)

        # 2. Universal Subject & Reference Resolution
        subject_info = None
        if gui_subject and gui_subject in UNIVERSAL_SUBJECTS and gui_subject != "AUTO":
            subject_code = gui_subject
            subject_info = UNIVERSAL_SUBJECTS[gui_subject]
        elif gui_subject and gui_subject != "AUTO" and len(gui_subject.strip()) > 1:
            # Custom subject entered by student
            subject_code = "CUSTOM"
            custom_name = gui_subject.strip()
            subject_info = {
                "name": custom_name,
                "primary_book": f"Standard Academic Literature for {custom_name}",
                "standard_textbooks": [f"Standard University Reference Textbooks in {custom_name}"]
            }
        else:
            # Automatic detection from query content
            detected_code, detected_info = detect_subject_from_query(prompt_lower + " " + clean_topic)
            subject_code = detected_code
            subject_info = detected_info

        subject_name = subject_info["name"]
        target_book = subject_info.get("primary_book", "Authoritative Academic Reference")

        # Strip subject mention from topic if redundant
        clean_topic = re.sub(rf"\b({subject_code}|{subject_name})\b", "", clean_topic, flags=re.IGNORECASE).strip()
        clean_topic = re.sub(r"^(subject|topic|\d+)\s*", "", clean_topic, flags=re.IGNORECASE).strip()
        if not clean_topic:
            clean_topic = f"{subject_name} Core Concepts & Key Derivations"

        # Preserve canonical casing for technical terms
        words = clean_topic.split()
        capitalized_words = []
        acronyms = {"opencv": "OpenCV", "rag": "RAG", "llm": "LLM", "ai": "AI", "ml": "ML", "dsa": "DSA", "kvl": "KVL", "kcl": "KCL", "bjt": "BJT", "fet": "FET", "mosfet": "MOSFET", "cad": "CAD"}
        for w in words:
            low = w.lower()
            if low in acronyms:
                capitalized_words.append(acronyms[low])
            elif len(w) > 1 and (w.isupper() or any(c.isupper() for c in w[1:])):
                capitalized_words.append(w)
            else:
                capitalized_words.append(w.capitalize())
        final_topic = " ".join(capitalized_words)

        # Model friendly name
        model_name = chosen_model.split("/")[-1].upper()

        # 3. Create Professional Academic Briefing
        if use_gui:
            briefing = (
                f"🤖 **Human GUI Browser Agent**: Operating **{gui_target.upper()} Web** | "
                f"Topic: **{final_topic}** | Reference: *{target_book}*"
            )
        else:
            briefing = (
                f"🎯 **Academic Focus**: **{subject_name}** | Topic: **{final_topic}** | "
                f"Reference: *{target_book}* | Engine: **{model_name}**"
            )

        # 4. Generate Authoritative Search Queries
        queries = [
            f'"{final_topic}" "{target_book}" lecture notes formulas',
            f'"{final_topic}" {subject_name} university study sheet explanation',
            f'"{final_topic}" comprehensive academic guide filetype:pdf'
        ]

        return StudyIntent(
            raw_query=raw_prompt,
            cleaned_topic=final_topic,
            subject_name=subject_name,
            subject_code=subject_code,
            target_book=target_book,
            selected_model=chosen_model,
            understanding_briefing=briefing,
            optimized_queries=queries,
            use_gui_agent=use_gui,
            gui_target=gui_target
        )

# Backwards compatibility alias
FerozRouter = AcademicRouter

