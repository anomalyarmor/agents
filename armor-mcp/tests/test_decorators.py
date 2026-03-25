"""Tests for _decorators module: sdk_tool, _serialize, _attr."""

import asyncio
from unittest.mock import Mock

import pytest
from fastmcp.exceptions import ToolError

from armor_mcp._decorators import _attr, _serialize, sdk_tool


class TestSerialize:
    """Tests for the _serialize standalone function."""

    def test_model_dump(self):
        mock_model = Mock()
        mock_model.model_dump.return_value = {"key": "value"}
        assert _serialize(mock_model) == {"key": "value"}

    def test_list_of_models(self):
        mock1 = Mock()
        mock1.model_dump.return_value = {"id": 1}
        mock2 = Mock()
        mock2.model_dump.return_value = {"id": 2}
        assert _serialize([mock1, mock2]) == [{"id": 1}, {"id": 2}]

    def test_dict_passthrough(self):
        assert _serialize({"already": "dict"}) == {"already": "dict"}

    def test_plain_value(self):
        assert _serialize("plain string") == {"result": "plain string"}

    def test_none(self):
        assert _serialize(None) == {"result": None}

    def test_mixed_list(self):
        mock_model = Mock()
        mock_model.model_dump.return_value = {"id": 1}
        assert _serialize([mock_model, {"id": 2}]) == [{"id": 1}, {"id": 2}]


class TestSdkTool:
    """Tests for the sdk_tool decorator."""

    def test_serializes_model(self):
        mock_model = Mock()
        mock_model.model_dump.return_value = {"key": "value"}

        @sdk_tool
        def func():
            return mock_model

        result = func()
        assert result == {"key": "value"}
        mock_model.model_dump.assert_called_once()

    def test_serializes_list(self):
        mock1 = Mock()
        mock1.model_dump.return_value = {"id": 1}
        mock2 = Mock()
        mock2.model_dump.return_value = {"id": 2}

        @sdk_tool
        def func():
            return [mock1, mock2]

        assert func() == [{"id": 1}, {"id": 2}]

    def test_dict_passthrough(self):
        @sdk_tool
        def func():
            return {"already": "dict"}

        assert func() == {"already": "dict"}

    def test_plain_value(self):
        @sdk_tool
        def func():
            return "plain string"

        assert func() == {"result": "plain string"}

    def test_none(self):
        @sdk_tool
        def func():
            return None

        assert func() == {"result": None}

    def test_raises_tool_error_for_generic_exception(self):
        @sdk_tool
        def func():
            raise ValueError("test error")

        with pytest.raises(ToolError, match="test error"):
            func()

    def test_passes_through_tool_error(self):
        @sdk_tool
        def func():
            raise ToolError("already correct")

        with pytest.raises(ToolError, match="already correct"):
            func()

    def test_reraises_keyboard_interrupt(self):
        @sdk_tool
        def func():
            raise KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            func()

    def test_reraises_system_exit(self):
        @sdk_tool
        def func():
            raise SystemExit(1)

        with pytest.raises(SystemExit):
            func()

    def test_preserves_function_name(self):
        @sdk_tool
        def my_tool():
            """My docstring."""
            return {}

        assert my_tool.__name__ == "my_tool"
        assert my_tool.__doc__ == "My docstring."

    def test_mixed_list(self):
        mock_model = Mock()
        mock_model.model_dump.return_value = {"id": 1}

        @sdk_tool
        def func():
            return [mock_model, {"id": 2}]

        assert func() == [{"id": 1}, {"id": 2}]


class TestSdkToolAsync:
    """Tests for sdk_tool with async functions."""

    def test_serializes_model(self):
        mock_model = Mock()
        mock_model.model_dump.return_value = {"key": "value"}

        @sdk_tool
        async def func():
            return mock_model

        result = asyncio.run(func())
        assert result == {"key": "value"}

    def test_raises_tool_error_for_generic_exception(self):
        @sdk_tool
        async def func():
            raise ValueError("async error")

        with pytest.raises(ToolError, match="async error"):
            asyncio.run(func())

    def test_passes_through_tool_error(self):
        @sdk_tool
        async def func():
            raise ToolError("async tool error")

        with pytest.raises(ToolError, match="async tool error"):
            asyncio.run(func())

    def test_preserves_function_name(self):
        @sdk_tool
        async def my_async_tool():
            """Async docstring."""
            return {}

        assert my_async_tool.__name__ == "my_async_tool"
        assert my_async_tool.__doc__ == "Async docstring."


class TestAttr:
    """Tests for the _attr accessor."""

    def test_pydantic_model(self):
        mock = Mock()
        mock.name = "test"
        assert _attr(mock, "name") == "test"

    def test_dict(self):
        assert _attr({"name": "test"}, "name") == "test"

    def test_dict_default(self):
        assert _attr({}, "name", "default") == "default"

    def test_missing_attr_default(self):
        assert _attr(object(), "missing", "fallback") == "fallback"

    def test_none_default(self):
        assert _attr({}, "key") is None

    def test_prefers_dict_over_attr(self):
        """Dict check first to avoid returning bound methods for colliding keys."""
        assert _attr({"get": "my_value"}, "get") == "my_value"

    def test_non_dict_uses_attr(self):
        mock = Mock()
        mock.name = "from_attr"
        assert _attr(mock, "name") == "from_attr"
