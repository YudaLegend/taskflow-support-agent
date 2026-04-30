"""Tests for app/main.py::_extract_turn_tools.

This helper walks the conversation history backwards from the latest message
to find tool calls made during THIS turn (since the most recent HumanMessage).
Important because graph.ainvoke returns the FULL history, not just the new
messages — without this, /chat would report tools from past turns too.
"""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.main import _extract_turn_tools


def _ai_with_tool_calls(*tool_names: str) -> AIMessage:
    """Build an AIMessage with a list of tool_calls, one per name."""
    return AIMessage(
        content="",
        tool_calls=[
            {"name": name, "args": {}, "id": f"call_{i}", "type": "tool_call"}
            for i, name in enumerate(tool_names)
        ],
    )


def test_no_tools_when_no_ai_messages() -> None:
    messages = [HumanMessage(content="hi")]
    assert _extract_turn_tools(messages) == []


def test_no_tools_when_ai_has_no_tool_calls() -> None:
    """An AIMessage with plain text content but no tool calls = answered from memory."""
    messages = [
        HumanMessage(content="hi"),
        AIMessage(content="Hello!"),
    ]
    assert _extract_turn_tools(messages) == []


def test_extracts_single_tool_call() -> None:
    messages = [
        HumanMessage(content="What's the price?"),
        _ai_with_tool_calls("search_docs_tool"),
        ToolMessage(content="...", tool_call_id="call_0"),
        AIMessage(content="The Pro plan is $12/mo."),
    ]
    assert _extract_turn_tools(messages) == ["search_docs_tool"]


def test_extracts_multiple_tool_calls_in_order() -> None:
    messages = [
        HumanMessage(content="Show my tickets"),
        _ai_with_tool_calls("get_user"),
        ToolMessage(content="...", tool_call_id="call_0"),
        _ai_with_tool_calls("list_user_tickets"),
        ToolMessage(content="...", tool_call_id="call_0"),
        AIMessage(content="You have 3 tickets."),
    ]
    assert _extract_turn_tools(messages) == ["get_user", "list_user_tickets"]


def test_only_walks_back_to_last_human_message() -> None:
    """Tool calls from PREVIOUS turns must not bleed into the current turn."""
    messages = [
        # Previous turn — should NOT appear in result
        HumanMessage(content="What's the price?"),
        _ai_with_tool_calls("search_docs_tool"),
        ToolMessage(content="...", tool_call_id="call_0"),
        AIMessage(content="$12/mo"),
        # Current turn
        HumanMessage(content="Show my tickets"),
        _ai_with_tool_calls("get_user"),
        ToolMessage(content="...", tool_call_id="call_0"),
        AIMessage(content="..."),
    ]
    assert _extract_turn_tools(messages) == ["get_user"]
