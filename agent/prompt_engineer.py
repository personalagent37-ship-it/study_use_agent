"""Human Professional Prompter Skill.

Crafts natural, high-impact, contextual prompts for web AI engines (Gemini, Claude, Perplexity)
like an expert human prompt engineer, taking into account user intent, requested depth,
and tone (e.g., 'in simple words', 'step-by-step', 'system architecture', 'deep dive').
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class HumanPromptEngineer:
    """Expert Human Prompter that analyzes user intent and synthesizes professional prompts."""

    @staticmethod
    def detect_tone_and_intent(raw_query: str) -> dict:
        """Detect the student's desired depth, tone, and cognitive focus."""
        q_lower = (raw_query or "").lower().strip()

        is_simple_words = bool(re.search(r"\b(in\s+simple\s+words?|simple|eli5|for\s+dummies|easy\s+to\s+understand|layman|basic|simply)\b", q_lower))
        is_step_by_step = bool(re.search(r"\b(step\s*by\s*step|how\s+it\s+works?|pipeline|workflow|mechanism|lifecycle)\b", q_lower))
        is_practical_chat = bool(re.search(r"\b(chat\s*bot|chat|conversational|real\s*world|production|implementation)\b", q_lower))
        is_deep_tech = bool(re.search(r"\b(deep\s*dive|in\s*depth|mathematical|derivation|algorithms?|formal|theory)\b", q_lower))
        is_comparison = bool(re.search(r"\b(vs|versus|difference\s+between|compare|comparison)\b", q_lower))
        is_diagram_requested = bool(re.search(r"\b(dia?gr[ae]m|d[ei]s[ei]?gn|archite[ck]t|flow\s*chart|sketch|blueprint|draw|schematic)\b", q_lower))

        return {
            "is_simple_words": is_simple_words,
            "is_step_by_step": is_step_by_step,
            "is_practical_chat": is_practical_chat,
            "is_deep_tech": is_deep_tech,
            "is_comparison": is_comparison,
            "is_diagram_requested": is_diagram_requested,
        }

    @staticmethod
    def clean_topic(raw_query: str) -> str:
        """Extract the clean subject/topic from a conversational query."""
        text = raw_query.strip()

        # Remove platform routing phrases and common typos (gemini/gemeni/claude/perplexity)
        text = re.sub(r"\b(use|using|on|from)\s+(gemini|gemeni|gemni|claude|clud|claud|perplexity|perpelexcity|perplexcity|google)(\s+ai)?(\s+web)?\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(and\s+)?(take|get|fetch)\s+(this\s+)?content\s+from\s+(gemini|gemeni|gemni|claude|clud|claud|perplexity|perpelexcity):?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(in\s+)?(gemini|gemeni|gemni|claude|clud|claud|perplexity|perpelexcity)\b", "", text, flags=re.IGNORECASE)

        # Remove conversational lead-ins
        text = re.sub(
            r"^(can\s+you\s+)?(please\s+)?(tell\s+me|explain|what\s+(is|are|does|was)|how\s+(does|do|to)|give\s+me(\s+notes\s+on)?|i\s+want(\s+to\s+know|\s+notes\s+on)?|make\s+(a\s+)?notes?\s+(on|about)?|prepare\s+(a\s+)?notes?\s+(on|about)?|write\s+(a\s+)?notes?\s+(on|about)?)\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

        # Remove trailing style instructions and typos for prompt extraction
        text = re.sub(r"\b(in\s+simple\s+words?|in\s+easy\s+language|point\s+to\s+point|step\s*by\s*step|i\s+wnat|i\s+want|plz|please)\b", "", text, flags=re.IGNORECASE)

        # Clean punctuation and extra spaces
        cleaned = re.sub(r"\s+", " ", text).strip().strip("?:;,. ")
        
        # Expand well-known acronyms for maximum clarity
        if re.search(r"\b(rag|ragg|rgae)\b", cleaned, re.IGNORECASE):
            cleaned = re.sub(r"\b(rag|ragg|rgae)\b", "RAG (Retrieval-Augmented Generation)", cleaned, flags=re.IGNORECASE)
            # Deduplicate if RAG is repeated multiple times
            if cleaned.count("RAG (Retrieval-Augmented Generation)") > 1:
                cleaned = "RAG (Retrieval-Augmented Generation) in Conversational Systems" if "chat" in cleaned.lower() else "RAG (Retrieval-Augmented Generation)"
        elif re.search(r"\b(cnn|cnns)\b", cleaned, re.IGNORECASE):
            cleaned = re.sub(r"\b(cnn|cnns)\b", "CNN (Convolutional Neural Networks)", cleaned, flags=re.IGNORECASE)
        elif re.search(r"\b(rnn|rnns)\b", cleaned, re.IGNORECASE):
            cleaned = re.sub(r"\b(rnn|rnns)\b", "RNN (Recurrent Neural Networks)", cleaned, flags=re.IGNORECASE)
        elif re.search(r"\b(llm|llms)\b", cleaned, re.IGNORECASE):
            cleaned = re.sub(r"\b(llm|llms)\b", "LLM (Large Language Models)", cleaned, flags=re.IGNORECASE)

        return cleaned if cleaned else raw_query.strip()

    @classmethod
    def craft_prompt(
        cls,
        topic: str,
        platform: str = "gemini",
        raw_query: Optional[str] = None
    ) -> str:
        """Synthesize an expert human-grade prompt tailored to the topic, user intent, and target platform."""
        full_query = raw_query or topic
        intent = cls.detect_tone_and_intent(full_query)
        clean_name = cls.clean_topic(full_query)
        platform_lower = (platform or "gemini").lower()

        # Determine persona based on topic
        persona = "world-class AI systems architect and educator"
        if any(w in clean_name.lower() for w in ["quantum", "physics", "laser", "optics"]):
            persona = "senior physicist and engineering educator"
        elif any(w in clean_name.lower() for w in ["database", "sql", "network", "operating system"]):
            persona = "principal software systems architect and educator"
        elif any(w in clean_name.lower() for w in ["math", "calculus", "matrix", "eigen"]):
            persona = "applied mathematician and educator"

        # Case 0: Diagram / System Design Intent (Highest priority if requested)
        if intent["is_diagram_requested"]:
            return cls._craft_system_design_diagram_prompt(clean_name, persona, platform_lower)

        # Case 1: Simple Words / ELI5 Intent
        if intent["is_simple_words"] or intent["is_practical_chat"]:
            return cls._craft_simple_words_prompt(clean_name, persona, platform_lower, intent)

        # Case 2: Deep Dive / Technical Architecture
        if intent["is_deep_tech"] or intent["is_step_by_step"]:
            return cls._craft_technical_deep_dive_prompt(clean_name, persona, platform_lower)

        # Case 3: Comparison / Contrast
        if intent["is_comparison"]:
            return cls._craft_comparison_prompt(clean_name, persona, platform_lower)

        # Case 4: Balanced High-Impact Universal Explanation
        return cls._craft_balanced_prompt(clean_name, persona, platform_lower)

    @classmethod
    def _craft_system_design_diagram_prompt(cls, topic: str, persona: str, platform: str) -> str:
        """Craft prompt for exact system design architecture, component flows, and technical tradeoffs."""
        return (
            f"Act as a {persona}. A student has explicitly requested the EXACT SYSTEM DESIGN & ARCHITECTURE FLOW for '{topic}'.\n\n"
            f"Please deliver an authoritative, point-by-point engineering architecture specification with:\n"
            f"1. 🏛️ Complete System Architecture & End-to-End Pipeline (Ingestion -> Transformation -> Storage/Index -> Retrieval/Compute -> Output).\n"
            f"2. 📦 Rigorous Component Breakdown: For every stage, specify exact data structures, models, dimensions, and latency profiles.\n"
            f"3. 📐 Technical Blueprint Specification (You MUST include the exact structured block below):\n"
            f"[SYSTEM_DESIGN:\n"
            f"Title: {topic} Architecture\n"
            f"Flow: <Component 1> -> <Component 2> -> <Component 3> -> ... -> <Output>\n"
            f"Nodes:\n"
            f"- <Node 1 Name> | <Role/Technology> | <Technical Parameter or Latency Note>\n"
            f"- <Node 2 Name> | <Role/Technology> | <Technical Parameter or Latency Note>\n"
            f"...\n"
            f"Callouts:\n"
            f"- <Critical bottleneck, failure mode, or latency factor>\n"
            f"- <Production best practice or optimization rule>\n"
            f"]\n\n"
            f"4. ⚖️ Production Trade-Offs & Scaling Bottlenecks (Throughput, Latency, Storage, Cost).\n"
            f"5. 🎯 Production Stack & Real-World Implementations (What modern systems actually run in production).\n\n"
            f"Write with precision, professional engineering depth, and zero superficial fluff."
        )

    @classmethod
    def _craft_simple_words_prompt(cls, topic: str, persona: str, platform: str, intent: dict) -> str:
        """Craft prompt for simple words, intuitive analogies, and conversational understanding."""
        chat_context = " especially how it powers modern conversational AI and chatbots" if intent.get("is_practical_chat") else ""

        if "gemini" in platform:
            return (
                f"Act as a {persona}. Explain '{topic}'{chat_context} in simple, crystal-clear words that anyone can grasp immediately.\n\n"
                f"Please structure your explanation with:\n"
                f"1. 💡 The Intuitive Mental Model (ELI5): Use a vivid, relatable real-world analogy (like an open-book exam or a library assistant) to explain what it is and why it exists.\n"
                f"2. 🏗️ How It Works in Simple Steps: Walk through the end-to-end flow from start to finish in plain English without confusing jargon.\n"
                f"3. ⚙️ The Core Pieces: Break down the 3 or 4 essential components and what each one actually does.\n"
                f"4. ⚖️ Why Traditional Systems Failed Without It: What exact problem does it solve?\n"
                f"5. 🎯 Practical Takeaways: 3 key bullet points summarizing everything neatly.\n\n"
                f"Write with clarity, energy, and zero unnecessary fluff."
            )
        elif "claude" in platform:
            return (
                f"Act as a {persona}. A student asked: 'What is {topic}{chat_context} in simple words?'\n\n"
                f"Provide a lucid, beginner-friendly explanation structured into:\n"
                f"- **Core Intuition (The Analogy)**: Connect the concept to a brilliant real-world metaphor.\n"
                f"- **Step-by-Step Mechanism**: Trace the operational flow clearly and chronologically.\n"
                f"- **Key Components**: Identify the foundational pillars.\n"
                f"- **Real-World Impact**: Show why this technique is transformative in today's technology.\n\n"
                f"Keep explanations vivid, direct, and accessible while preserving technical accuracy."
            )
        else: # Perplexity / Google / Combined
            return (
                f"Explain '{topic}'{chat_context} in simple words and intuitive language. "
                f"Provide: (1) A memorable real-world analogy explaining what it is, "
                f"(2) Step-by-step practical workflow, (3) Core architectural components, "
                f"(4) Comparison with traditional alternatives, and (5) Real-world use cases."
            )

    @classmethod
    def _craft_technical_deep_dive_prompt(cls, topic: str, persona: str, platform: str) -> str:
        """Craft prompt for in-depth engineering mechanics, equations, and architecture."""
        return (
            f"Act as a {persona}. Provide an authoritative, high-yield technical breakdown of '{topic}'.\n\n"
            f"Please structure as follows:\n"
            f"1. 📌 Exact Formal Definition & Theoretical Foundation.\n"
            f"2. ⚙️ Step-by-Step Algorithmic Mechanism / Architecture Flow.\n"
            f"3. 📐 Key Mathematical Formulations & Working Principles.\n"
            f"4. ⚖️ Trade-offs, Bottlenecks, and State-of-the-Art Solutions.\n"
            f"5. 🎯 Real-World Production Example with Architecture Diagram/Flow."
        )

    @classmethod
    def _craft_comparison_prompt(cls, topic: str, persona: str, platform: str) -> str:
        """Craft prompt for comparative analysis."""
        return (
            f"Act as a {persona}. Provide an insightful comparative breakdown of '{topic}'.\n\n"
            f"Please structure your analysis into:\n"
            f"1. 💡 High-Level Overview of each approach.\n"
            f"2. 📊 Comprehensive Comparison Table (Mechanisms, Latency, Complexity, Cost, Accuracy).\n"
            f"3. ⚖️ When to Choose Which (Decision Matrix & Trade-offs).\n"
            f"4. 🏗️ Hybrid or Modern Unified Paradigms.\n"
            f"5. 🎯 Key Takeaways."
        )

    @classmethod
    def _craft_balanced_prompt(cls, topic: str, persona: str, platform: str) -> str:
        """Craft a balanced, engaging, high-retention explanation for any topic."""
        return (
            f"Act as a {persona}. Explain '{topic}' thoroughly and engagingly.\n\n"
            f"Please structure your explanation as follows:\n"
            f"1. 💡 Core Concept & Intuition: Explain the fundamental idea using a clear analogy or real-world mental model.\n"
            f"2. ⚙️ How It Works: Provide the step-by-step mechanism or workflow.\n"
            f"3. 🏗️ Core Components / Elements: Detail the essential building blocks.\n"
            f"4. ⚖️ Key Comparison or Practical Advantages.\n"
            f"5. 🎯 Essential Takeaways & Real-World Applications."
        )
