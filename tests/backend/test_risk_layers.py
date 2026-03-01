"""
Tests for the 7-Layer Safety System.

Validates that each safety layer correctly blocks, warns, or passes
trade proposals based on the defined rules.
"""

import pytest
from backend.risk.safety_layers import SafetyLayers, TradeProposal
from backend.data.models import SafetyLayerResult


@pytest.fixture
def safety():
    """Create a fresh SafetyLayers instance."""
    return SafetyLayers()


@pytest.fixture
def valid_proposal():
    """A proposal that should pass all layers."""
    return TradeProposal(
        symbol="RELIANCE",
        side="BUY",
        quantity=3,
        price=2500.0,
        sector="Energy",
        ai_confidence=85.0,
        volatility=20.0,
        news_sources=3,
        beta=1.0,
    )


class TestLayer1InformationQuality:
    """Test Layer 1: Information Quality."""

    def test_passes_with_multiple_sources(self, safety: SafetyLayers):
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            ai_confidence=80, news_sources=3,
        )
        result = safety._layer_1_information_quality(proposal)
        assert result.result == SafetyLayerResult.PASSED

    def test_warns_with_single_source(self, safety: SafetyLayers):
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            ai_confidence=80, news_sources=1,
        )
        result = safety._layer_1_information_quality(proposal)
        assert result.result == SafetyLayerResult.WARNING

    def test_blocks_with_no_sources(self, safety: SafetyLayers):
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            ai_confidence=80, news_sources=0,
        )
        result = safety._layer_1_information_quality(proposal)
        assert result.result == SafetyLayerResult.BLOCKED

    def test_sell_bypasses(self, safety: SafetyLayers):
        proposal = TradeProposal(
            symbol="TCS", side="SELL", quantity=1, price=3500,
            news_sources=0,
        )
        result = safety._layer_1_information_quality(proposal)
        assert result.result == SafetyLayerResult.PASSED


class TestLayer2AIConfidence:
    """Test Layer 2: AI Confidence."""

    def test_passes_high_confidence(self, safety: SafetyLayers):
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            ai_confidence=85, news_sources=2,
        )
        result = safety._layer_2_ai_confidence(proposal)
        assert result.result == SafetyLayerResult.PASSED

    def test_warns_medium_confidence(self, safety: SafetyLayers):
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            ai_confidence=65, news_sources=2,
        )
        result = safety._layer_2_ai_confidence(proposal)
        assert result.result == SafetyLayerResult.WARNING

    def test_blocks_low_confidence(self, safety: SafetyLayers):
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            ai_confidence=40, news_sources=2,
        )
        result = safety._layer_2_ai_confidence(proposal)
        assert result.result == SafetyLayerResult.BLOCKED


class TestLayer3VolatilityFilter:
    """Test Layer 3: Volatility Filter."""

    def test_passes_low_volatility(self, safety: SafetyLayers):
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            volatility=20, news_sources=2, ai_confidence=80,
        )
        result = safety._layer_3_volatility_filter(proposal)
        assert result.result == SafetyLayerResult.PASSED

    def test_warns_elevated_volatility(self, safety: SafetyLayers):
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            volatility=40, news_sources=2, ai_confidence=80,
        )
        result = safety._layer_3_volatility_filter(proposal)
        assert result.result == SafetyLayerResult.WARNING

    def test_blocks_extreme_volatility(self, safety: SafetyLayers):
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            volatility=60, news_sources=2, ai_confidence=80,
        )
        result = safety._layer_3_volatility_filter(proposal)
        assert result.result == SafetyLayerResult.BLOCKED


class TestLayer7KillSwitch:
    """Test Layer 7: Kill Switch."""

    def test_passes_when_inactive(self, safety: SafetyLayers):
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            news_sources=2, ai_confidence=80,
        )
        result = safety._layer_7_kill_switch(proposal)
        assert result.result == SafetyLayerResult.PASSED

    def test_blocks_when_active(self, safety: SafetyLayers):
        safety.activate_kill_switch("Test")
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            news_sources=2, ai_confidence=80,
        )
        result = safety._layer_7_kill_switch(proposal)
        assert result.result == SafetyLayerResult.BLOCKED

    def test_deactivation_allows_trading(self, safety: SafetyLayers):
        safety.activate_kill_switch("Test")
        safety.deactivate_kill_switch()
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            news_sources=2, ai_confidence=80,
        )
        result = safety._layer_7_kill_switch(proposal)
        assert result.result == SafetyLayerResult.PASSED


class TestFullSafetyCheck:
    """Test the complete 7-layer check."""

    def test_valid_proposal_passes_all(
        self, safety: SafetyLayers, valid_proposal: TradeProposal
    ):
        result = safety.check_all(valid_proposal)
        assert result.passed is True
        assert result.layers_checked == 7
        assert result.blocked_by is None

    def test_low_confidence_blocks(self, safety: SafetyLayers):
        proposal = TradeProposal(
            symbol="TCS", side="BUY", quantity=1, price=3500,
            ai_confidence=30, news_sources=2,
        )
        result = safety.check_all(proposal)
        assert result.passed is False
        assert "AI Confidence" in (result.blocked_by or "")

    def test_sell_always_allowed(self, safety: SafetyLayers):
        """Sell orders should bypass most checks."""
        proposal = TradeProposal(
            symbol="TCS", side="SELL", quantity=1, price=3500,
            ai_confidence=0, volatility=100, news_sources=0,
        )
        result = safety.check_all(proposal)
        assert result.passed is True
