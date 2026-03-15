"""Tests for _decorators module: sdk_tool, ToolError, _attr."""

from unittest.mock import Mock

import pytest

from armor_mcp._decorators import ToolError, _attr, sdk_tool


class TestSdkTool:
    """Tests for the sdk_tool decorator."""

    def test_handles_model_dump(self):
        mock_model = Mock()
        mock_model.model_dump.return_value = {"key": "value"}

        @sdk_tool
        def func():
            return mock_model

        result = func()
        assert result == {"key": "value"}
        mock_model.model_dump.assert_called_once()

    def test_handles_list_of_models(self):
        mock1 = Mock()
        mock1.model_dump.return_value = {"id": 1}
        mock2 = Mock()
        mock2.model_dump.return_value = {"id": 2}

        @sdk_tool
        def func():
            return [mock1, mock2]

        result = func()
        assert result == [{"id": 1}, {"id": 2}]

    def test_handles_dict_passthrough(self):
        @sdk_tool
        def func():
            return {"already": "dict"}

        assert func() == {"already": "dict"}

    def test_handles_plain_value(self):
        @sdk_tool
        def func():
            return "plain string"

        assert func() == {"result": "plain string"}

    def test_handles_none(self):
        @sdk_tool
        def func():
            return None

        assert func() == {"result": None}

    def test_handles_generic_exception(self):
        @sdk_tool
        def func():
            raise ValueError("test error")

        result = func()
        assert result["error"] == "ValueError"
        assert "test error" in result["message"]

    def test_handles_tool_error(self):
        @sdk_tool
        def func():
            raise ToolError(
                "Connect Slack first.",
                error_type="NoSlackConnection",
                oauth_url="https://example.com/oauth",
            )

        result = func()
        assert result["error"] == "NoSlackConnection"
        assert "Connect Slack first." in result["message"]
        assert result["oauth_url"] == "https://example.com/oauth"

    def test_tool_error_without_details(self):
        @sdk_tool
        def func():
            raise ToolError("Something failed")

        result = func()
        assert result["error"] == "ToolError"
        assert result["message"] == "Something failed"
        assert len(result) == 2  # no extra keys

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

    def test_handles_mixed_list(self):
        """Lists with both models and plain dicts."""
        mock_model = Mock()
        mock_model.model_dump.return_value = {"id": 1}

        @sdk_tool
        def func():
            return [mock_model, {"id": 2}]

        result = func()
        assert result == [{"id": 1}, {"id": 2}]


class TestToolError:
    """Tests for the ToolError exception."""

    def test_basic_creation(self):
        err = ToolError("message")
        assert str(err) == "message"
        assert err.error_type == "ToolError"
        assert err.details == {}

    def test_custom_type_and_details(self):
        err = ToolError("msg", error_type="NotFound", key="value", count=3)
        assert err.error_type == "NotFound"
        assert err.details == {"key": "value", "count": 3}

    def test_is_exception(self):
        assert issubclass(ToolError, Exception)


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
        """Non-dict objects use attribute access."""
        mock = Mock()
        mock.name = "from_attr"
        assert _attr(mock, "name") == "from_attr"
