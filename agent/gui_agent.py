"""
Human-like GUI Browser Agent for Alexandria Studio.
Operates web AI interfaces (Perplexity, Claude AI, Gemini, Google) like a human operator
to research and retrieve authoritative academic content.
"""

import os
import time
import logging
import random
from pathlib import Path
from typing import Optional, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

DEFAULT_CHROMEDRIVER_PATH = "/home/talha/.wdm/drivers/chromedriver/linux64/152.0.7977.82/chromedriver-linux64/chromedriver"
DEFAULT_PROFILE_DIR = Path(__file__).resolve().parent.parent / ".gui_agent_profile"

class HumanGUIAgent:
    """Autonomous Web Operator that interacts with web platforms like a human student."""

    def __init__(
        self,
        headless: bool = False,
        profile_dir: Optional[Path] = None,
        chromedriver_path: str = DEFAULT_CHROMEDRIVER_PATH,
        display: str = ":0"
    ):
        self.headless = headless
        self.profile_dir = profile_dir or DEFAULT_PROFILE_DIR
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.chromedriver_path = chromedriver_path
        self.display = display
        self.driver: Optional[webdriver.Chrome] = None

    def _ensure_display(self):
        if not self.headless and "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = self.display

    def _clean_stale_locks(self):
        """Remove Chrome Singleton lock symlinks that cause startup stalls."""
        for name in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
            try:
                link = self.profile_dir / name
                if link.is_symlink() or link.exists():
                    link.unlink(missing_ok=True)
            except Exception:
                pass

    def get_driver(self) -> webdriver.Chrome:
        """Create or return existing Chrome session."""
        if self.driver:
            try:
                _ = self.driver.title
                return self.driver
            except Exception:
                self.close()

        self._ensure_display()
        self._clean_stale_locks()
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        
        options.add_argument(f"--user-data-dir={str(self.profile_dir)}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7977.82 Safari/537.36"
        )

        service = Service(self.chromedriver_path)
        logger.info(f"Launching Human GUI Agent Chrome (headless={self.headless}, profile={self.profile_dir})...")
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(35)

        # Stealth: mask navigator.webdriver
        try:
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                    """
                }
            )
        except Exception:
            pass

        return self.driver

    def insert_full_prompt(self, element, text: str):
        """Insert the complete multi-line prompt in ONE GO without triggering premature submits on newlines."""
        try:
            # Atomic JavaScript insertion for rich-textareas (Gemini & Claude)
            self.driver.execute_script("""
                const el = arguments[0];
                const text = arguments[1];
                el.focus();
                // Select all inside contenteditable
                const sel = window.getSelection();
                const range = document.createRange();
                range.selectNodeContents(el);
                sel.removeAllRanges();
                sel.addRange(range);
                // Insert text atomically
                const ok = document.execCommand('insertText', false, text);
                if (!ok) {
                    el.innerText = text;
                }
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            """, element, text)
            time.sleep(0.6)
        except Exception as js_err:
            logger.warning(f"JS prompt insertion fallback: {js_err}")
            # Fallback: type lines with Shift+Enter so Enter never submits prematurely
            lines = text.split("\n")
            for idx, line in enumerate(lines):
                if line:
                    element.send_keys(line)
                if idx < len(lines) - 1:
                    element.send_keys(Keys.SHIFT, Keys.ENTER)
                time.sleep(0.02)

    def human_typing(self, element, text: str, delay_range: tuple = (0.02, 0.06)):
        """Simulate human-like keystroke intervals."""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(*delay_range))

    # --------------------------------------------------------------------------
    # 1. PERPLEXITY WEB OPERATOR (Instant, No Login Needed)
    # --------------------------------------------------------------------------
    def research_perplexity(self, query: str) -> Dict[str, Any]:
        """Perform web-grounded research on Perplexity AI web interface."""
        driver = self.get_driver()
        clean_q = query.replace(" ", "+")
        url = f"https://www.perplexity.ai/search?q={clean_q}"
        logger.info(f"[GUI Agent • Perplexity] Navigating to {url}...")
        driver.get(url)

        time.sleep(4)
        extracted_text = ""
        sources = []

        try:
            # Check for Cloudflare Turnstile / verification
            body_text = driver.find_element(By.TAG_NAME, "body").text
            if "security verification" in body_text.lower() or "just a moment..." in driver.title.lower():
                logger.info("[GUI Agent • Perplexity] Cloudflare verification detected. Waiting 5s...")
                time.sleep(5)
                body_text = driver.find_element(By.TAG_NAME, "body").text
                if "security verification" in body_text.lower() or "just a moment..." in driver.title.lower():
                    logger.warning("[GUI Agent • Perplexity] Cloudflare challenge active. Seamlessly retrieving via Google Search...")
                    return self.research_google(query)

            answer_elements = driver.find_elements(By.CSS_SELECTOR, "div.prose, [data-testid='answer'], div[class*='answer']")
            if answer_elements:
                for el in answer_elements:
                    txt = el.text.strip()
                    if len(txt) > len(extracted_text):
                        extracted_text = txt

            if not extracted_text:
                lines = [l.strip() for l in body_text.split("\n") if l.strip()]
                if "Answer" in lines:
                    idx = lines.index("Answer")
                    extracted_text = "\n\n".join(lines[idx+1:idx+25])
                else:
                    extracted_text = "\n\n".join(lines[:30])

            links = driver.find_elements(By.CSS_SELECTOR, "a[href^='http']")
            for a in links[:6]:
                href = a.get_attribute("href")
                if href and not any(skip in href for skip in ["perplexity.ai", "google", "login"]):
                    title = a.text.strip() or "Academic Reference"
                    sources.append({"title": title, "link": href})

            logger.info(f"[GUI Agent • Perplexity] Extracted {len(extracted_text)} chars of grounded research.")
            return {
                "source": "Perplexity AI Web (Human GUI Agent)",
                "success": bool(extracted_text),
                "content": extracted_text,
                "sources": sources,
                "url": url
            }
        except Exception as e:
            logger.error(f"[GUI Agent • Perplexity] Extraction error: {e}")
            return {
                "source": "Perplexity AI Web",
                "success": False,
                "content": "",
                "error": str(e)
            }

    # --------------------------------------------------------------------------
    # 2. CLAUDE AI WEB OPERATOR
    # --------------------------------------------------------------------------
    def research_claude(self, prompt: str) -> Dict[str, Any]:
        """Interact with Claude AI web interface (claude.ai/new)."""
        driver = self.get_driver()
        url = "https://claude.ai/new"
        logger.info(f"[GUI Agent • Claude AI] Navigating to {url}...")
        driver.get(url)
        time.sleep(3)

        current_url = driver.current_url
        if "login" in current_url:
            logger.warning("[GUI Agent • Claude AI] Session not logged in. Waiting for user login...")
            return {
                "source": "Claude AI Web",
                "success": False,
                "needs_login": True,
                "message": "Claude AI requires a one-time login. Please log in in the opened Chrome window.",
                "url": current_url
            }

        try:
            wait = WebDriverWait(driver, 10)
            input_box = wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div[contenteditable='true'], fieldset div[contenteditable='true'], textarea"
                ))
            )
            input_box.click()
            time.sleep(0.5)

            self.insert_full_prompt(input_box, prompt)
            time.sleep(1.0)

            send_btns = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Send'], button[class*='send']")
            if send_btns and send_btns[0].is_enabled():
                send_btns[0].click()
            else:
                input_box.send_keys(Keys.ENTER)

            logger.info("[GUI Agent • Claude AI] Prompt submitted. Waiting for response stream...")
            time.sleep(5)

            prev_length = 0
            stable_count = 0
            extracted_text = ""
            messages = []

            for _ in range(40):
                messages = driver.find_elements(By.CSS_SELECTOR, "div.font-claude-message, div[data-is-streaming], div.prose")
                if messages:
                    last_msg = messages[-1].text.strip()
                    if len(last_msg) == prev_length and len(last_msg) > 100:
                        stable_count += 1
                        if stable_count >= 3:
                            extracted_text = last_msg
                            break
                    else:
                        prev_length = len(last_msg)
                        stable_count = 0
                time.sleep(1)

            if not extracted_text and messages:
                extracted_text = messages[-1].text.strip()

            logger.info(f"[GUI Agent • Claude AI] Completed extraction: {len(extracted_text)} chars.")
            return {
                "source": "Claude AI Web (Human GUI Agent)",
                "success": bool(extracted_text),
                "content": extracted_text,
                "url": url
            }
        except Exception as e:
            logger.error(f"[GUI Agent • Claude AI] Error: {e}")
            return {
                "source": "Claude AI Web",
                "success": False,
                "content": "",
                "error": str(e)
            }

    # --------------------------------------------------------------------------
    # 3. GEMINI WEB OPERATOR
    # --------------------------------------------------------------------------
    def research_gemini(self, prompt: str) -> Dict[str, Any]:
        """Interact with Google Gemini web interface (gemini.google.com/app)."""
        driver = self.get_driver()
        url = "https://gemini.google.com/app"
        logger.info(f"[GUI Agent • Gemini Web] Navigating to {url}...")
        driver.get(url)
        time.sleep(3)

        current_url = driver.current_url
        if "accounts.google.com" in current_url:
            return {
                "source": "Gemini Web",
                "success": False,
                "needs_login": True,
                "message": "Google Gemini requires a one-time Google account login in Chrome.",
                "url": current_url
            }

        try:
            wait = WebDriverWait(driver, 10)
            input_box = wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "rich-textarea div[contenteditable='true'], div[role='textbox']"
                ))
            )
            input_box.click()
            time.sleep(0.5)

            self.insert_full_prompt(input_box, prompt)
            time.sleep(1.0)

            send_btns = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Send'], button.send-button")
            if send_btns and send_btns[0].is_enabled():
                send_btns[0].click()
            else:
                input_box.send_keys(Keys.ENTER)

            logger.info("[GUI Agent • Gemini Web] Prompt submitted. Waiting for response...")
            time.sleep(5)

            extracted_text = ""
            prev_len = 0
            stable_count = 0
            responses = []

            for _ in range(35):
                responses = driver.find_elements(By.CSS_SELECTOR, "message-content, div.response-container, div.model-response")
                if responses:
                    last_resp = responses[-1].text.strip()
                    if len(last_resp) == prev_len and len(last_resp) > 80:
                        stable_count += 1
                        if stable_count >= 3:
                            extracted_text = last_resp
                            break
                    else:
                        prev_len = len(last_resp)
                        stable_count = 0
                time.sleep(1)

            if not extracted_text and responses:
                extracted_text = responses[-1].text.strip()

            logger.info(f"[GUI Agent • Gemini Web] Completed extraction: {len(extracted_text)} chars.")
            return {
                "source": "Gemini Web (Human GUI Agent)",
                "success": bool(extracted_text),
                "content": extracted_text,
                "url": url
            }
        except Exception as e:
            logger.error(f"[GUI Agent • Gemini Web] Error: {e}")
            return {
                "source": "Gemini Web",
                "success": False,
                "content": "",
                "error": str(e)
            }

    # --------------------------------------------------------------------------
    # 4. GOOGLE SEARCH OPERATOR
    # --------------------------------------------------------------------------
    def research_google(self, query: str) -> Dict[str, Any]:
        """Perform human-like Google search and scrape overview cards."""
        driver = self.get_driver()
        clean_q = query.replace(" ", "+")
        url = f"https://www.google.com/search?q={clean_q}"
        logger.info(f"[GUI Agent • Google] Navigating to {url}...")
        driver.get(url)
        time.sleep(2)

        extracted_text = ""
        sources = []

        try:
            snippets = driver.find_elements(By.CSS_SELECTOR, "div.kno-rdesc, div[data-attrid='description'], div.VwiC3b, div.BNeawe")
            collected = []
            for s in snippets[:8]:
                t = s.text.strip()
                if t and len(t) > 40 and t not in collected:
                    collected.append(t)
            extracted_text = "\n\n".join(collected)

            links = driver.find_elements(By.CSS_SELECTOR, "#search a[href^='http'], div.g a[href^='http'], div.yuRUbf a")
            for a in links:
                try:
                    href = a.get_attribute("href")
                    if href and href.startswith("http") and not any(d in href for d in ["google.com", "youtube", "accounts.", "support."]):
                        title = a.text.strip()
                        if not title:
                            h3s = a.find_elements(By.TAG_NAME, "h3")
                            title = h3s[0].text.strip() if h3s else "Academic Reference"
                        if not any(s["link"] == href for s in sources):
                            sources.append({"title": title[:70], "link": href})
                        if len(sources) >= 5:
                            break
                except Exception:
                    continue

            logger.info(f"[GUI Agent • Google] Extracted {len(extracted_text)} chars and {len(sources)} sources.")
            return {
                "source": "Google Web Search (Human GUI Agent)",
                "success": bool(extracted_text),
                "content": extracted_text,
                "sources": sources,
                "url": url
            }
        except Exception as e:
            logger.error(f"[GUI Agent • Google] Error: {e}")
            return {
                "source": "Google Web Search",
                "success": False,
                "content": "",
                "error": str(e)
            }

    def research_all(self, topic: str, prompt: Optional[str] = None, raw_query: Optional[str] = None) -> Dict[str, Any]:
        """Collect and combine grounded research across web platforms (Perplexity, Claude, Gemini, Google)."""
        from .prompt_engineer import HumanPromptEngineer

        query_prompt = prompt or HumanPromptEngineer.craft_prompt(topic, platform="all", raw_query=raw_query or topic)
        sections = []
        combined_sources = []

        # 1. Perplexity (Instant Web Research)
        p_res = self.research_perplexity(query_prompt)
        if p_res.get("content"):
            sections.append(f"### 🟢 Output from Perplexity AI Web\n\n{p_res.get('content')}")
            combined_sources.extend(p_res.get("sources", []))

        # 2. Claude AI (if logged in)
        c_res = self.research_claude(query_prompt)
        if c_res.get("content") and not c_res.get("needs_login"):
            sections.append(f"### 🟣 Output from Claude AI Web\n\n{c_res.get('content')}")

        # 3. Gemini Web (if logged in)
        g_res = self.research_gemini(query_prompt)
        if g_res.get("content") and not g_res.get("needs_login"):
            sections.append(f"### 🔵 Output from Google Gemini Web\n\n{g_res.get('content')}")

        # 4. Google Search Overview (if only 1 source so far)
        if len(sections) < 2:
            goog_res = self.research_google(topic)
            if goog_res.get("content"):
                sections.append(f"### 🟡 Output from Google Search & AI Overview\n\n{goog_res.get('content')}")
                combined_sources.extend(goog_res.get("sources", []))

        full_content = "\n\n---\n\n".join(sections) if sections else ""

        return {
            "source": f"Multi-Platform GUI Agent ({len(sections)} Web Engines)",
            "success": bool(full_content),
            "content": full_content,
            "sources": combined_sources,
            "url": "https://claude.ai • https://gemini.google.com • https://perplexity.ai"
        }

    # --------------------------------------------------------------------------
    # UNIFIED ENTRYPOINT
    # --------------------------------------------------------------------------
    def research_topic(
        self,
        target: str,
        topic: str,
        prompt: Optional[str] = None,
        raw_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Route to appropriate web operator based on user intent with HumanPromptEngineer."""
        from .prompt_engineer import HumanPromptEngineer

        target_lower = (target or "perplexity").lower().strip()
        query_prompt = prompt or HumanPromptEngineer.craft_prompt(
            topic=topic,
            platform=target_lower,
            raw_query=raw_query or topic
        )
        logger.info(f"🤖 [Human Prompt Engineer] Crafted prompt for {target_lower.upper()}:\n{query_prompt}")

        if any(w in target_lower for w in ["all", "combined", "multi", "both"]):
            return self.research_all(topic, prompt=query_prompt, raw_query=raw_query)

        elif "claude" in target_lower:
            res = self.research_claude(query_prompt)
            if res.get("needs_login") or not res.get("success"):
                logger.warning("Claude Web requires login. Auto-routing to Perplexity Web for instant research...")
                fallback = self.research_perplexity(query_prompt)
                fallback["warning"] = "Claude AI requires login in Chrome. Automatically retrieved authoritative content via Perplexity Web."
                return fallback
            return res

        elif "gemini" in target_lower:
            res = self.research_gemini(query_prompt)
            if res.get("needs_login") or not res.get("success"):
                logger.warning("Gemini Web requires Google login. Auto-routing to Perplexity Web...")
                fallback = self.research_perplexity(query_prompt)
                fallback["warning"] = "Google Gemini requires login in Chrome. Automatically retrieved authoritative content via Perplexity Web."
                return fallback
            return res

        elif "google" in target_lower:
            return self.research_google(topic)

        else:
            return self.research_perplexity(query_prompt)

    def close(self):
        """Safely shut down the browser session."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            logger.info("Human GUI Agent browser closed.")
        self._clean_stale_locks()
