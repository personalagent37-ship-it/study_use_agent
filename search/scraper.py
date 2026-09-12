import logging
import re
import requests
from bs4 import BeautifulSoup

try:
    import trafilatura
except ImportError:
    trafilatura = None

logger = logging.getLogger(__name__)

class WebScraper:
    """Extracts clean readable text from academic and educational web pages."""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    def __init__(self, timeout: int = 10, max_chars_per_page: int = 4500):
        self.timeout = timeout
        self.max_chars_per_page = max_chars_per_page

    def scrape_url(self, url: str) -> str:
        """Fetch and extract clean text from a single URL."""
        if not url or not url.startswith("http"):
            return ""

        try:
            resp = requests.get(url, headers=self.DEFAULT_HEADERS, timeout=self.timeout)
            resp.raise_for_status()
            html = resp.text

            # 1. Primary: Trafilatura (best-in-class main-text extraction)
            if trafilatura:
                extracted = trafilatura.extract(html, include_comments=False, include_tables=True)
                if extracted and len(extracted.strip()) > 150:
                    return self._clean_and_truncate(extracted)

            # 2. Fallback: BeautifulSoup text extraction
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "svg"]):
                tag.decompose()

            # Prefer main article container if available
            article = soup.find("article") or soup.find("main") or soup.body
            if article:
                text = article.get_text(separator="\n")
                return self._clean_and_truncate(text)
            return ""

        except Exception as e:
            logger.warning(f"Could not scrape {url}: {e}")
            return ""

    def scrape_multiple(self, urls: list[str], max_total_chars: int = 12000) -> list[dict[str, str]]:
        """Scrape multiple URLs and return aggregated content up to a total character limit."""
        results = []
        total_chars = 0

        for url in urls:
            if total_chars >= max_total_chars:
                break
            content = self.scrape_url(url)
            if content:
                results.append({"url": url, "content": content})
                total_chars += len(content)

        return results

    def _clean_and_truncate(self, text: str) -> str:
        # Collapse excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = text.strip()
        if len(text) > self.max_chars_per_page:
            text = text[: self.max_chars_per_page] + "\n...[truncated]"
        return text
