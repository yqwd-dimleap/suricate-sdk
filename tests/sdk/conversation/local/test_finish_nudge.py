"""Near-limit finish nudge on LocalConversation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from openhands.sdk.conversation.state import ConversationExecutionStatus
from openhands.sdk.event import MessageEvent
from openhands.sdk.llm import Message, TextContent


def _conversation_stub(max_iters: int = 40, has_finish: bool = True):
    """Minimal object exercising LocalConversation._maybe_emit_finish_nudge."""
    from openhands.sdk.conversation.impl.local_conversation import LocalConversation

    conv = object.__new__(LocalConversation)
    conv.max_iteration_per_run = max_iters
    conv._finish_nudge_emitted = False
    conv._state = MagicMock()
    conv._state.execution_status = ConversationExecutionStatus.RUNNING
    conv.agent = MagicMock()
    conv.agent.tools_map = {"finish": object()} if has_finish else {}
    conv._events: list = []

    def _on_event(event):
        conv._events.append(event)

    conv._on_event = _on_event
    return conv


def test_finish_nudge_emits_once_near_limit():
    from openhands.sdk.conversation.impl.local_conversation import LocalConversation

    conv = _conversation_stub(max_iters=40)
    # remaining = 4 -> threshold max(3, 4) = 4, so emit
    LocalConversation._maybe_emit_finish_nudge(conv, iteration=36)
    assert conv._finish_nudge_emitted is True
    assert len(conv._events) == 1
    event = conv._events[0]
    assert isinstance(event, MessageEvent)
    assert event.source == "environment"
    assert isinstance(event.llm_message, Message)
    parts = event.llm_message.content
    assert parts and isinstance(parts[0], TextContent)
    text = parts[0].text
    assert "Iteration budget" in text
    assert "4 iteration(s) remaining" in text
    assert "`finish`" in text

    # Second call is a no-op
    LocalConversation._maybe_emit_finish_nudge(conv, iteration=37)
    assert len(conv._events) == 1


def test_finish_nudge_skips_when_budget_still_comfortable():
    from openhands.sdk.conversation.impl.local_conversation import LocalConversation

    conv = _conversation_stub(max_iters=40)
    LocalConversation._maybe_emit_finish_nudge(conv, iteration=10)
    assert conv._finish_nudge_emitted is False
    assert conv._events == []


def test_finish_nudge_skips_without_finish_tool():
    from openhands.sdk.conversation.impl.local_conversation import LocalConversation

    conv = _conversation_stub(max_iters=10, has_finish=False)
    LocalConversation._maybe_emit_finish_nudge(conv, iteration=8)
    assert conv._finish_nudge_emitted is False
    assert conv._events == []


@pytest.mark.parametrize(
    ("max_iters", "iteration", "should_emit"),
    [
        (10, 7, True),  # remaining 3 == threshold 3
        (10, 6, False),  # remaining 4 > 3
        (100, 90, True),  # remaining 10 == threshold 10
        (100, 89, False),
    ],
)
def test_finish_nudge_threshold(max_iters: int, iteration: int, should_emit: bool):
    from openhands.sdk.conversation.impl.local_conversation import LocalConversation

    conv = _conversation_stub(max_iters=max_iters)
    LocalConversation._maybe_emit_finish_nudge(conv, iteration=iteration)
    assert conv._finish_nudge_emitted is should_emit
    assert bool(conv._events) is should_emit
