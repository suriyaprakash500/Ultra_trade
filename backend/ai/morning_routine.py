"""
Trading Autopilot — Morning Intelligence Routine.

Automates the pre-market analysis pipeline:
1. Fetch latest news from all sources
2. Analyze each item with Grok AI
3. Review existing portfolio positions
4. Generate daily morning briefing
5. Produce actionable trade ideas for the day
"""

from __future__ import annotations

import json
from datetime import datetime, UTC
from typing import Optional

from loguru import logger
from openai import OpenAI

from backend.ai.news_analyzer import get_news_analyzer
from backend.ai.decision_engine import get_decision_engine
from backend.ai.prompts import morning_analysis_prompt
from backend.config import get_settings
from backend.trading.paper_trader import get_paper_trader


class MorningRoutine:
    """
    Comprehensive pre-market intelligence routine.

    Runs daily before market open (ideally 7:00 - 9:00 AM IST)
    and prepares the system for the trading day.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._last_run: Optional[datetime] = None
        self._last_briefing: Optional[dict] = None
        self._grok_client: Optional[OpenAI] = None

    def _get_grok_client(self) -> OpenAI:
        """Lazy-initialize the Grok API client."""
        if self._grok_client is None:
            self._grok_client = OpenAI(
                api_key=self._settings.grok_api_key,
                base_url=self._settings.grok_base_url,
            )
        return self._grok_client

    async def run(
        self, previous_day_summary: dict | None = None
    ) -> dict:
        """
        Execute the full morning routine.

        Returns a comprehensive morning briefing dictionary.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"═══ Starting Morning Routine for {today} ═══")

        # ── Step 1: Fetch news ─────────────────────────────────────
        logger.info("Step 1: Fetching news from all sources...")
        analyzer = get_news_analyzer()
        raw_news = await analyzer.fetch_all_news(max_per_source=10)
        logger.info(f"  → {len(raw_news)} news items collected")

        # ── Step 2: Analyze news with AI ───────────────────────────
        logger.info("Step 2: Analyzing news with Grok AI...")
        trader = get_paper_trader()
        watchlist = list(trader.positions.keys())
        news_analyses = await analyzer.analyze_batch(
            raw_news, watchlist=watchlist, max_items=10
        )
        logger.info(f"  → {len(news_analyses)} items analyzed")

        # ── Step 3: Get portfolio state ────────────────────────────
        logger.info("Step 3: Reviewing portfolio...")
        positions = trader.get_all_positions()
        portfolio = trader.get_portfolio_summary()
        logger.info(
            f"  → {len(positions)} positions, "
            f"value: ₹{portfolio['total_value']:,.2f}"
        )

        # ── Step 4: Generate morning briefing ──────────────────────
        logger.info("Step 4: Generating morning briefing...")
        briefing = await self._generate_briefing(
            today, raw_news, positions, previous_day_summary
        )
        logger.info(f"  → Outlook: {briefing.get('market_outlook', 'unknown')}")

        # ── Step 5: Generate trade ideas ───────────────────────────
        logger.info("Step 5: Generating trade ideas...")
        engine = get_decision_engine()
        trade_ideas = await engine.generate_trade_ideas(
            news_analyses=news_analyses,
            market_context=briefing.get("summary", ""),
        )
        logger.info(f"  → {len(trade_ideas)} trade ideas approved")

        # ── Compile results ────────────────────────────────────────
        result = {
            "date": today,
            "run_at": datetime.now(UTC).isoformat(),
            "news_collected": len(raw_news),
            "news_analyzed": len(news_analyses),
            "news_analyses": news_analyses,
            "portfolio_summary": portfolio,
            "positions": positions,
            "morning_briefing": briefing,
            "trade_ideas": trade_ideas,
            "status": "complete",
        }

        self._last_run = datetime.now(UTC)
        self._last_briefing = result

        logger.info(f"═══ Morning Routine Complete for {today} ═══")
        return result

    async def _generate_briefing(
        self,
        date: str,
        news_items: list[dict],
        positions: list[dict],
        previous_day_summary: dict | None,
    ) -> dict:
        """Generate the morning briefing via Grok AI."""
        prompt = morning_analysis_prompt(
            date=date,
            news_items=news_items,
            portfolio_positions=positions,
            previous_day_summary=previous_day_summary,
        )

        try:
            client = self._get_grok_client()
            response = client.chat.completions.create(
                model=self._settings.grok_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior portfolio manager at a "
                            "top-tier Indian investment firm. "
                            "Respond with valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
            )

            raw_text = response.choices[0].message.content.strip()

            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0]
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0]

            return json.loads(raw_text.strip())

        except Exception as exc:
            logger.error(f"Morning briefing generation failed: {exc}")
            return {
                "market_outlook": "neutral",
                "outlook_confidence": 50,
                "key_events": [],
                "portfolio_actions": [],
                "watchlist_additions": [],
                "risk_alerts": [f"Briefing failed: {exc}"],
                "summary": "Morning briefing could not be generated.",
            }

    @property
    def last_briefing(self) -> dict | None:
        """Return the most recent morning briefing."""
        return self._last_briefing

    @property
    def last_run_time(self) -> datetime | None:
        """Return the time of the last routine run."""
        return self._last_run


# ── Module-level singleton ─────────────────────────────────────────

_routine: MorningRoutine | None = None


def get_morning_routine() -> MorningRoutine:
    """Return the global MorningRoutine singleton."""
    global _routine
    if _routine is None:
        _routine = MorningRoutine()
    return _routine
