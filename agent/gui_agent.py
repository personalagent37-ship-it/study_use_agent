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
from selenium.webdriver.common.action_chains import ActionChains
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

    def _inject_human_cursor(self):
        """Inject an animated, glowing red mouse pointer into the page so the student can visibly see the agent's cursor gliding across the interface."""
        try:
            self.driver.execute_script("""
                if (!document.getElementById('alexandria-human-cursor')) {
                    const cursor = document.createElement('div');
                    cursor.id = 'alexandria-human-cursor';
                    cursor.style.position = 'fixed';
                    cursor.style.width = '20px';
                    cursor.style.height = '20px';
                    cursor.style.borderRadius = '50%';
                    cursor.style.backgroundColor = 'rgba(239, 68, 68, 0.9)';
                    cursor.style.border = '2px solid white';
                    cursor.style.boxShadow = '0 0 12px rgba(239, 68, 68, 0.8), 0 2px 4px rgba(0,0,0,0.3)';
                    cursor.style.pointerEvents = 'none';
                    cursor.style.zIndex = '2147483647';
                    cursor.style.transition = 'all 0.35s cubic-bezier(0.25, 1, 0.5, 1)';
                    cursor.style.transform = 'translate(-50%, -50%) scale(1)';
                    cursor.style.top = '120px';
                    cursor.style.left = '120px';
                    document.body.appendChild(cursor);
                }
            """)
        except Exception:
            pass

    def human_move_mouse(self, element):
        """Visually glide the mouse pointer to the element and perform ActionChains move."""
        self._inject_human_cursor()
        try:
            self.driver.execute_script("""
                const el = arguments[0];
                const cursor = document.getElementById('alexandria-human-cursor');
                if (el && cursor) {
                    const rect = el.getBoundingClientRect();
                    const targetX = Math.max(10, rect.left + (rect.width / 2));
                    const targetY = Math.max(10, rect.top + (rect.height / 2));
                    cursor.style.left = targetX + 'px';
                    cursor.style.top = targetY + 'px';
                    cursor.style.transform = 'translate(-50%, -50%) scale(1.2)';
                    setTimeout(() => {
                        cursor.style.transform = 'translate(-50%, -50%) scale(1)';
                    }, 300);
                }
            """, element)
        except Exception:
            pass

        try:
            ActionChains(self.driver).move_to_element(element).pause(random.uniform(0.15, 0.35)).perform()
        except Exception:
            pass

    def human_move_and_click(self, element):
        """Move mouse realistically to element, pause, flash click ripple, and click."""
        self.human_move_mouse(element)
        time.sleep(random.uniform(0.2, 0.4))
        try:
            self.driver.execute_script("""
                const cursor = document.getElementById('alexandria-human-cursor');
                if (cursor) {
                    cursor.style.transform = 'translate(-50%, -50%) scale(0.7)';
                    cursor.style.backgroundColor = 'rgba(34, 197, 94, 0.95)';
                    setTimeout(() => {
                        cursor.style.transform = 'translate(-50%, -50%) scale(1)';
                        cursor.style.backgroundColor = 'rgba(239, 68, 68, 0.9)';
                    }, 220);
                }
            """)
        except Exception:
            pass

        try:
            ActionChains(self.driver).click(element).perform()
        except Exception:
            try:
                element.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", element)

    def human_typing(self, element, text: str, max_duration: float = 5.5):
        """
        Simulate fast, authentic human keystrokes with visible typing animation.
        CRITICAL: All newlines (\n) are entered with Shift+Enter so they NEVER trigger early form submission.
        The entire prompt is entered cleanly as ONE single atomic prompt.
        """
        lines = text.split("\n")
        total_chars = max(len(text), 1)
        # Calculate delay per char so typing completes in 3-6 seconds
        delay = max(0.003, min(0.025, max_duration / total_chars))

        for line_idx, line in enumerate(lines):
            # Fast touch-typing in natural chunks
            chunk_size = 1 if len(line) < 80 else 3
            for i in range(0, len(line), chunk_size):
                chunk = line[i:i + chunk_size]
                try:
                    element.send_keys(chunk)
                except Exception:
                    element = self.driver.switch_to.active_element
                    element.send_keys(chunk)
                time.sleep(delay * len(chunk))

            # Newline without submitting! Shift+Enter creates line break
            if line_idx < len(lines) - 1:
                try:
                    element.send_keys(Keys.SHIFT, Keys.ENTER)
                except Exception:
                    element = self.driver.switch_to.active_element
                    element.send_keys(Keys.SHIFT, Keys.ENTER)
                time.sleep(0.04)

        time.sleep(0.4)

    def insert_full_prompt(self, element, text: str):
        """Fast fallback prompt insertion if needed."""
        self.human_typing(element, text, max_duration=4.5)

    # --------------------------------------------------------------------------
    # 1. PERPLEXITY WEB OPERATOR (Human Mouse + Typing)
    # --------------------------------------------------------------------------
    def research_perplexity(self, query: str) -> Dict[str, Any]:
        """Perform web-grounded research on Perplexity AI web interface like a human student."""
        driver = self.get_driver()
        url = "https://www.perplexity.ai"
        logger.info(f"[GUI Agent • Perplexity] Navigating to {url}...")
        driver.get(url)
        time.sleep(3)

        extracted_text = ""
        sources = []

        try:
            self._inject_human_cursor()

            # Press Escape to clear any overlay modals
            try:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(0.3)
            except Exception:
                pass

            # 1. Dismiss cookie banners if present
            cookie_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Got it') or contains(., 'Accept') or contains(., 'Decline optional')]")
            if cookie_btns:
                try:
                    self.human_move_and_click(cookie_btns[0])
                    time.sleep(0.5)
                except Exception:
                    pass

            # 2. Dismiss sign-in popup if present
            close_btns = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Close'], button[aria-label*='close']")
            if close_btns:
                try:
                    self.human_move_and_click(close_btns[0])
                    time.sleep(0.4)
                except Exception:
                    pass

            # 3. Locate search input
            wait = WebDriverWait(driver, 8)
            input_box = None
            for sel in ["#ask-input", "textarea[placeholder*='Ask']", "div[contenteditable='true']", "textarea"]:
                matching = driver.find_elements(By.CSS_SELECTOR, sel)
                if matching and matching[0].is_displayed():
                    input_box = matching[0]
                    break

            if not input_box:
                input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ask-input, div[contenteditable='true'], textarea")))

            # Move mouse to search box and click
            logger.info("[GUI Agent • Perplexity] Moving mouse to search bar...")
            self.human_move_and_click(input_box)
            time.sleep(0.4)

            # Human typing into search box
            logger.info(f"[GUI Agent • Perplexity] Human typing query ({len(query)} chars)...")
            self.human_typing(input_box, query, max_duration=4.5)
            time.sleep(0.5)

            # 4. Find submit button or press ENTER
            submit_btn = None
            submit_candidates = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Submit'], button[aria-label*='Search'], button[aria-label*='Send'], form button")
            for b in submit_candidates:
                if b.is_displayed():
                    submit_btn = b
                    break

            if submit_btn:
                logger.info("[GUI Agent • Perplexity] Moving mouse to submit button...")
                self.human_move_and_click(submit_btn)
            else:
                input_box.send_keys(Keys.ENTER)

            logger.info("[GUI Agent • Perplexity] Query submitted. Waiting for answer stream...")
            time.sleep(5)

            # 5. Extract streaming answer
            prev_len = 0
            stable_count = 0
            for _ in range(35):
                # Check for sign-in wall
                body_txt = driver.find_element(By.TAG_NAME, "body").text
                if "Sign in to continue using Perplexity" in body_txt and "Answer" not in body_txt:
                    logger.warning("[GUI Agent • Perplexity] Perplexity guest quota hit or login wall shown.")
                    break

                answer_elements = driver.find_elements(By.CSS_SELECTOR, "div.prose, [data-testid='answer'], div[class*='answer']")
                if answer_elements:
                    for el in answer_elements:
                        txt = el.text.strip()
                        if len(txt) > len(extracted_text):
                            extracted_text = txt

                if extracted_text and len(extracted_text) == prev_len and len(extracted_text) > 80:
                    stable_count += 1
                    if stable_count >= 3:
                        break
                else:
                    prev_len = len(extracted_text)
                    stable_count = 0

                time.sleep(1)

            # Extract source links
            links = driver.find_elements(By.CSS_SELECTOR, "a[href^='http']")
            for a in links[:8]:
                try:
                    href = a.get_attribute("href")
                    if href and not any(skip in href for skip in ["perplexity.ai", "google", "login", "account"]):
                        title = a.text.strip() or "Perplexity Reference"
                        if not any(s["link"] == href for s in sources):
                            sources.append({"title": title[:70], "link": href})
                except Exception:
                    continue

            if not extracted_text:
                logger.warning("[GUI Agent • Perplexity] Insufficient output from Perplexity. Seamlessly retrieving via Google Search AI Overview...")
                return self.research_google(query)

            logger.info(f"[GUI Agent • Perplexity] Extracted {len(extracted_text)} chars of grounded research.")
            return {
                "source": "Perplexity AI Web (Human GUI Agent)",
                "success": bool(extracted_text),
                "content": extracted_text,
                "sources": sources,
                "url": driver.current_url
            }
        except Exception as e:
            logger.error(f"[GUI Agent • Perplexity] Error: {e}. Seamlessly falling back to Google Search...")
            return self.research_google(query)

    # --------------------------------------------------------------------------
    # 2. CLAUDE AI WEB OPERATOR (Human Mouse + Typing)
    # --------------------------------------------------------------------------
    def research_claude(self, prompt: str) -> Dict[str, Any]:
        """Interact with Claude AI web interface (claude.ai/new) with mouse actions and human typing."""
        driver = self.get_driver()
        url = "https://claude.ai/new"
        logger.info(f"[GUI Agent • Claude AI] Navigating to {url}...")
        driver.get(url)
        time.sleep(3)

        current_url = driver.current_url
        if "login" in current_url:
            logger.warning("[GUI Agent • Claude AI] Session not logged in. Waiting for student login in Chrome...")
            # If not headless, give user 20 seconds to log in in the opened Chrome window
            if not self.headless:
                for sec in range(20):
                    time.sleep(1)
                    try:
                        if "login" not in driver.current_url:
                            logger.info("[GUI Agent • Claude AI] Student login detected! Proceeding...")
                            break
                    except Exception:
                        pass

            if "login" in driver.current_url:
                return {
                    "source": "Claude AI Web",
                    "success": False,
                    "needs_login": True,
                    "message": "Claude AI requires a one-time login. Please log in in the opened Chrome window (session is saved).",
                    "url": current_url
                }

        try:
            self._inject_human_cursor()
            wait = WebDriverWait(driver, 10)
            input_box = wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div[contenteditable='true'], fieldset div[contenteditable='true'], div.ProseMirror, textarea"
                ))
            )

            # Move mouse to input box and click
            logger.info("[GUI Agent • Claude AI] Moving mouse to chat input...")
            self.human_move_and_click(input_box)
            time.sleep(0.4)

            # Type with human keystrokes (Shift+Enter for newlines so prompt is submitted as ONE single message)
            logger.info(f"[GUI Agent • Claude AI] Human typing prompt ({len(prompt)} chars)...")
            self.human_typing(input_box, prompt, max_duration=5.0)
            time.sleep(0.5)

            # Move mouse to Send button and click
            send_btns = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Send'], button[class*='send'], button:has(svg)")
            send_btn = None
            for b in send_btns:
                if b.is_displayed() and b.is_enabled():
                    send_btn = b
                    break

            if send_btn:
                logger.info("[GUI Agent • Claude AI] Moving mouse to Send button...")
                self.human_move_and_click(send_btn)
            else:
                input_box.send_keys(Keys.ENTER)

            logger.info("[GUI Agent • Claude AI] Prompt submitted in ONE go. Waiting for response stream...")
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
    # 3. GEMINI WEB OPERATOR (Human Mouse + Typing in ONE Prompt)
    # --------------------------------------------------------------------------
    def research_gemini(self, prompt: str) -> Dict[str, Any]:
        """Interact with Google Gemini web interface (gemini.google.com/app) with mouse and human typing."""
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
            self._inject_human_cursor()
            wait = WebDriverWait(driver, 10)
            input_box = wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "rich-textarea div[contenteditable='true'], div[role='textbox']"
                ))
            )

            # Move mouse to input box and click
            logger.info("[GUI Agent • Gemini Web] Moving mouse to chat input box...")
            self.human_move_and_click(input_box)
            time.sleep(0.4)

            # Human typing with Shift+Enter for newlines: stays in ONE single prompt!
            logger.info(f"[GUI Agent • Gemini Web] Human typing prompt ({len(prompt)} chars)...")
            self.human_typing(input_box, prompt, max_duration=5.0)
            time.sleep(0.6)

            # Move mouse to Send button and click
            send_btns = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Send'], button.send-button")
            send_btn = None
            for b in send_btns:
                if b.is_displayed() and b.is_enabled():
                    send_btn = b
                    break

            if send_btn:
                logger.info("[GUI Agent • Gemini Web] Moving mouse to Send button...")
                self.human_move_and_click(send_btn)
            else:
                input_box.send_keys(Keys.ENTER)

            logger.info("[GUI Agent • Gemini Web] Prompt submitted in ONE go. Waiting for response...")
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
                logger.warning("Claude Web requires login. Auto-routing to Gemini Web & Perplexity for research...")
                # First try Gemini Web (already logged in and authenticated)
                g_res = self.research_gemini(query_prompt)
                if g_res.get("success") and g_res.get("content"):
                    g_res["warning"] = "Claude AI requires a one-time sign-in in Chrome. Retrieved authoritative content via Gemini Web."
                    return g_res
                fallback = self.research_perplexity(query_prompt)
                fallback["warning"] = "Claude AI requires a one-time sign-in in Chrome. Retrieved authoritative content via Web Agent."
                return fallback
            return res

        elif "gemini" in target_lower:
            res = self.research_gemini(query_prompt)
            if res.get("needs_login") or not res.get("success"):
                logger.warning("Gemini Web requires Google login. Auto-routing to Perplexity Web...")
                fallback = self.research_perplexity(query_prompt)
                fallback["warning"] = "Google Gemini requires login in Chrome. Automatically retrieved authoritative content via Web Agent."
                return fallback
            return res

        elif "google" in target_lower:
            return self.research_google(topic)

        else:
            res = self.research_perplexity(query_prompt)
            if not res.get("success") or not res.get("content"):
                logger.warning("Perplexity search returned empty or blocked. Seamlessly routing to Gemini Web & Google...")
                g_res = self.research_gemini(query_prompt)
                if g_res.get("success") and g_res.get("content"):
                    return g_res
                return self.research_google(topic)
            return res

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
