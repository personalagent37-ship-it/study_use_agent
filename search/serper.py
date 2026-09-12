import json
import logging
import requests
from typing import Any

logger = logging.getLogger(__name__)

class SerperClient:
    """Client for Serper.dev Google Search API."""

    ENDPOINT = "https://google.serper.dev/search"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, query: str, num_results: int = 5) -> dict[str, Any]:
        """Perform a Google search query via Serper API.
        
        Returns structured results including organic results, answer box, and knowledge graph.
        """
        if not self.api_key:
            logger.error("Serper API key is missing.")
            return {"error": "Missing Serper API key", "organic": []}

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": num_results
        }

        try:
            response = requests.post(self.ENDPOINT, headers=headers, json=payload, timeout=12)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.RequestException as e:
            logger.error(f"Serper API search failed for '{query}': {e}")
            return {"error": str(e), "organic": []}

    def search_educational_notes(self, topic: str, num_results: int = 5) -> list[dict[str, str]]:
        """Search specifically for educational notes, tutorials, or academic summaries for a topic."""
        # Query optimization for student notes
        query = f"{topic} comprehensive study notes key concepts summary"
        raw_res = self.search(query, num_results=num_results)
        
        results = []
        # Include answerBox if available
        if "answerBox" in raw_res:
            ab = raw_res["answerBox"]
            snippet = ab.get("snippet") or ab.get("answer") or ""
            if snippet:
                results.append({
                    "title": ab.get("title", "Quick Answer"),
                    "link": ab.get("link", ""),
                    "snippet": snippet,
                    "source": "Google Answer Box"
                })

        for item in raw_res.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "Organic Search"
            })
        return results
