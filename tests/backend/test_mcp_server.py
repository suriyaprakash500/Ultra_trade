"""
Tests for the MCP Server (ToolRegistry + GrokToolAgent).

Validates:
- Tool registration and discovery
- Tool execution
- Error handling on unknown tools
- Registry singleton behavior
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from backend.mcp_server.server import ToolRegistry, create_tool_registry


class TestToolRegistry:
    """Test the ToolRegistry class."""

    def test_empty_registry(self):
        """New registry should have no tools."""
        registry = ToolRegistry()
        assert registry.get_tool_names() == []
        assert registry.get_tool_definitions() == []

    def test_register_tool(self):
        """Registering a tool adds it to the registry."""
        registry = ToolRegistry()

        async def dummy_handler(**kwargs):
            return {"result": "ok"}

        registry.register(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
            handler=dummy_handler,
        )

        assert "test_tool" in registry.get_tool_names()
        assert len(registry.get_tool_definitions()) == 1

    def test_tool_definition_format(self):
        """Tool definitions should follow OpenAI function calling format."""
        registry = ToolRegistry()

        async def dummy_handler(**kwargs):
            return {}

        registry.register(
            name="my_tool",
            description="Does something",
            parameters={"type": "object", "properties": {"x": {"type": "integer"}}},
            handler=dummy_handler,
        )

        defs = registry.get_tool_definitions()
        assert len(defs) == 1
        tool_def = defs[0]
        assert tool_def["type"] == "function"
        assert tool_def["function"]["name"] == "my_tool"
        assert tool_def["function"]["description"] == "Does something"
        assert "properties" in tool_def["function"]["parameters"]

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Executing a registered tool should call the handler."""
        registry = ToolRegistry()

        async def greet(name: str = "World"):
            return {"greeting": f"Hello, {name}!"}

        registry.register(
            name="greet",
            description="Greet someone",
            parameters={"type": "object", "properties": {"name": {"type": "string"}}},
            handler=greet,
        )

        result = await registry.execute_tool("greet", {"name": "Alice"})
        assert result == {"greeting": "Hello, Alice!"}

    @pytest.mark.asyncio
    async def test_execute_unknown_tool_raises(self):
        """Executing an unregistered tool should raise KeyError."""
        registry = ToolRegistry()

        with pytest.raises(KeyError, match="not found"):
            await registry.execute_tool("nonexistent", {})

    def test_multiple_tools(self):
        """Multiple tools can be registered."""
        registry = ToolRegistry()

        for i in range(5):
            async def handler(**kwargs):
                return {}

            registry.register(
                name=f"tool_{i}",
                description=f"Tool {i}",
                parameters={"type": "object", "properties": {}},
                handler=handler,
            )

        assert len(registry.get_tool_names()) == 5


class TestCreateToolRegistry:
    """Test the full tool registry creation with all trading tools."""

    def test_creates_10_tools(self):
        """The factory should create a registry with exactly 10 tools."""
        registry = create_tool_registry()
        tool_names = registry.get_tool_names()

        assert len(tool_names) == 10
        assert "place_order" in tool_names
        assert "get_portfolio" in tool_names
        assert "get_positions" in tool_names
        assert "get_performance_metrics" in tool_names
        assert "get_stock_price" in tool_names
        assert "get_stock_history" in tool_names
        assert "analyze_news" in tool_names
        assert "check_trade_risk" in tool_names
        assert "activate_kill_switch" in tool_names
        assert "get_technical_indicators" in tool_names

    def test_all_tools_have_definitions(self):
        """Every registered tool should have a valid definition."""
        registry = create_tool_registry()
        definitions = registry.get_tool_definitions()

        for defn in definitions:
            assert defn["type"] == "function"
            assert "name" in defn["function"]
            assert "description" in defn["function"]
            assert "parameters" in defn["function"]

    def test_technical_indicators_tool_present(self):
        """The technical indicators tool should be registered."""
        registry = create_tool_registry()
        assert "get_technical_indicators" in registry.get_tool_names()
