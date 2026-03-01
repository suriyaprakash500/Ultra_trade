"""
Trading Autopilot — News Analyzer.

Scrapes financial news from multiple RSS feeds and web sources,
then uses Grok AI to analyze sentiment and identify trading opportunities.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import feedparser
import httpx
from loguru import logger
from openai import OpenAI

from backend.ai.prompts import news_sentiment_prompt
from backend.config import get_settings


# ── News Source Configuration ──────────────────────────────────────

RSS_FEEDS: dict[str, str] = {
    "Moneycontrol": "https://www.moneycontrol.com/rss/latestnews.xml",
    "Economic Times": "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
    "LiveMint": "https://www.livemint.com/rss/markets",
    "Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
    "NDTV Business": "https://feeds.feedburner.com/ndtvprofit-latest",
    "Reuters India": "https://feeds.reuters.com/reuters/INtopNews",
}


class NewsAnalyzer:
    """
    Scrapes financial news and analyzes it with Grok AI.

    Pipeline:
    1. Fetch news from RSS feeds
    2. Filter for relevance (market/stock keywords)
    3. Send to Grok for sentiment analysis
    4. Return structured analysis results
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._grok_client: Optional[OpenAI] = None
        self._analyzed_urls: set[str] = set()  # Dedup

    def _get_grok_client(self) -> OpenAI:
        """Lazy-initialize the Grok API client."""
        if self._grok_client is None:
            self._grok_client = OpenAI(
                api_key=self._settings.grok_api_key,
                base_url=self._settings.grok_base_url,
            )
        return self._grok_client

    # ── News Fetching ──────────────────────────────────────────────

    async def fetch_all_news(
        self, max_per_source: int = 10
    ) -> list[dict]:
        """
        Fetch news from all configured RSS feeds.

        Returns a list of raw news items with title, source, url, summary.
        """
        all_news: list[dict] = []

        for source_name, feed_url in RSS_FEEDS.items():
            try:
                items = await self._fetch_rss_feed(
                    source_name, feed_url, max_per_source
                )
                all_news.extend(items)
            except Exception as exc:
                logger.warning(f"Failed to fetch {source_name}: {exc}")

        # Sort by published date (newest first)
        all_news.sort(key=lambda x: x.get("published", ""), reverse=True)

        logger.info(f"Fetched {len(all_news)} news items from {len(RSS_FEEDS)} sources")
        return all_news

    async def _fetch_rss_feed(
        self, source_name: str, feed_url: str, max_items: int
    ) -> list[dict]:
        """Fetch and parse a single RSS feed."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(feed_url)
                response.raise_for_status()

            feed = feedparser.parse(response.text)
            items = []

            for entry in feed.entries[:max_items]:
                url = entry.get("link", "")
                if url in self._analyzed_urls:
                    continue

                items.append({
                    "title": entry.get("title", "").strip(),
                    "source": source_name,
                    "url": url,
                    "summary": entry.get("summary", "").strip()[:500],
                    "published": entry.get("published", ""),
                })

            return items

        except Exception as exc:
            logger.warning(f"RSS fetch error for {source_name}: {exc}")
            return []

    # ── AI Analysis ────────────────────────────────────────────────

    async def analyze_news_item(
        self,
        title: str,
        content: str,
        watchlist: list[str] | None = None,
    ) -> dict:
        """
        Analyze a single news item using Grok AI.

        Returns structured analysis with sentiment, impact, affected symbols.
        """
        prompt = news_sentiment_prompt(title, content, watchlist)

        try:
            client = self._get_grok_client()
            response = client.chat.completions.create(
                model=self._settings.grok_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a financial news analyst. "
                            "Always respond with valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Low temperature for consistency
                max_tokens=500,
            )

            raw_text = response.choices[0].message.content.strip()

            # Parse JSON from response (handle markdown code blocks)
            json_text = raw_text
            if "```json" in raw_text:
                json_text = raw_text.split("```json")[1].split("```")[0]
            elif "```" in raw_text:
                json_text = raw_text.split("```")[1].split("```")[0]

            analysis = json.loads(json_text)
            analysis["title"] = title
            analysis["source"] = "grok_analysis"

            logger.info(
                f"News analyzed: [{analysis.get('sentiment', 'unknown')}] "
                f"{title[:60]}..."
            )
            return analysis

        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse Grok response as JSON: {exc}")
            return self._fallback_analysis(title, content)
        except Exception as exc:
            logger.error(f"Grok analysis failed: {exc}")
            return self._fallback_analysis(title, content)

    async def analyze_batch(
        self,
        news_items: list[dict],
        watchlist: list[str] | None = None,
        max_items: int = 10,
    ) -> list[dict]:
        """
        Analyze multiple news items in sequence.

        Limits to max_items to control API costs.
        """
        analyses = []

        for item in news_items[:max_items]:
            title = item.get("title", "")
            content = item.get("summary", "") or title

            if not title:
                continue

            analysis = await self.analyze_news_item(title, content, watchlist)
            analysis["url"] = item.get("url", "")
            analysis["original_source"] = item.get("source", "")
            analyses.append(analysis)

            # Mark as analyzed to avoid duplicates
            url = item.get("url", "")
            if url:
                self._analyzed_urls.add(url)

        logger.info(f"Batch analysis complete: {len(analyses)} items analyzed")
        return analyses

    def _fallback_analysis(self, title: str, content: str) -> dict:
        """
        Fallback analysis when AI is unavailable.

        Uses simple keyword matching for basic sentiment.
        """
        text = f"{title} {content}".lower()

        bullish_keywords = [
            "surge", "rally", "gains", "beat", "profit", "growth",
            "upgrade", "bullish", "boom", "record high", "buy",
        ]
        bearish_keywords = [
            "crash", "fall", "loss", "miss", "decline", "downgrade",
            "bearish", "selloff", "bankruptcy", "fraud", "sell",
        ]

        bull_count = sum(1 for kw in bullish_keywords if kw in text)
        bear_count = sum(1 for kw in bearish_keywords if kw in text)

        if bull_count > bear_count:
            sentiment = "bullish"
            score = min(bull_count * 0.5, 2.0)
        elif bear_count > bull_count:
            sentiment = "bearish"
            score = -min(bear_count * 0.5, 2.0)
        else:
            sentiment = "neutral"
            score = 0.0

        return {
            "title": title,
            "sentiment": sentiment,
            "sentiment_score": score,
            "impact_level": "low",
            "affected_symbols": [],
            "summary": f"Fallback analysis: {title}",
            "confidence": 30.0,
            "recommended_action": "watch",
            "source": "keyword_fallback",
        }


# ── Module-level singleton ─────────────────────────────────────────

_analyzer: NewsAnalyzer | None = None


def get_news_analyzer() -> NewsAnalyzer:
    """Return the global NewsAnalyzer singleton."""
    global _analyzer
    if _analyzer is None:
        _analyzer = NewsAnalyzer()
    return _analyzer
