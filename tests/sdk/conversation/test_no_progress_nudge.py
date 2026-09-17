"""Unit tests for explore-without-edit no-progress nudge."""

from __future__ import annotations

import uuid

from openhands.sdk.agent import Agent
from openhands.sdk.conversation.state import ConversationState
from openhands.sdk.conversation.stuck_detector import StuckDetector
from openhands.sdk.conversation.types import StuckDetectionThresholds
from openhands.sdk.event import ActionEvent, MessageEvent
from openhands.sdk.llm import LLM, Message, MessageToolCall, TextContent
from openhands.sdk.workspace import LocalWorkspace


def _terminal_action(cmd: str = "ls") -> ActionEvent:
    cid = f"call-{uuid.uuid4().hex[:8]}"
    return ActionEvent(
        source="agent",
        thought=[TextContent(text="explore")],
        tool_name="terminal",
        tool_call_id=cid,
        tool_call=MessageToolCall(
            id=cid,
            name="terminal",
            arguments=f'{{"command": "{cmd}"}}',
            origin="completion",
        ),
        llm_response_id=str(uuid.uuid4()),
    )


def _view_action(path: str = "/tmp/x.py") -> ActionEvent:
    cid = f"call-{uuid.uuid4().hex[:8]}"
    return ActionEvent(
        source="agent",
        thought=[TextContent(text="view")],
        tool_name="file_editor",
        tool_call_id=cid,
        tool_call=MessageToolCall(
            id=cid,
            name="file_editor",
            arguments=f'{{"command": "view", "path": "{path}"}}',
            origin="completion",
        ),
        llm_response_id=str(uuid.uuid4()),
    )


def _edit_action(path: str = "/tmp/x.py") -> ActionEvent:
    cid = f"call-{uuid.uuid4().hex[:8]}"
    return ActionEvent(
        source="agent",
        thought=[TextContent(text="edit")],
        tool_name="file_editor",
        tool_call_id=cid,
        tool_call=MessageToolCall(
            id=cid,
            name="file_editor",
            arguments=(
                f'{{"command": "str_replace", "path": "{path}", '
                f'"old_str": "a", "new_str": "b"}}'
            ),
            origin="completion",
        ),
        llm_response_id=str(uuid.uuid4()),
    )


def _make_detector(
    actions: list[ActionEvent],
    *,
    threshold: int = 4,
) -> StuckDetector:
    llm = LLM(model="gpt-4o-mini", usage_id="test-llm")
    agent = Agent(llm=llm)
    state = ConversationState.create(
        id=uuid.uuid4(), agent=agent, workspace=LocalWorkspace(working_dir="/tmp")
    )
    state.events.append(
        MessageEvent(
            source="user",
            llm_message=Message(role="user", content=[TextContent(text="fix it")]),
        )
    )
    for action in actions:
        state.events.append(action)
    return StuckDetector(
        state, thresholds=StuckDetectionThresholds(no_progress_actions=threshold)
    )


def test_no_progress_nudge_after_explore_streak():
    detector = _make_detector([_terminal_action() for _ in range(4)], threshold=4)
    nudge = detector.get_no_progress_nudge()
    assert nudge is not None
    assert "consecutive explore/read" in nudge
    assert "`finish`" in nudge
    # one-shot
    assert detector.get_no_progress_nudge() is None


def test_no_progress_nudge_disabled_by_default():
    """Default thresholds leave no_progress_actions at 0 so the explore
    streak never injects a chat-visible corrective message."""
    llm = LLM(model="gpt-4o-mini", usage_id="test-llm")
    agent = Agent(llm=llm)
    state = ConversationState.create(
        id=uuid.uuid4(), agent=agent, workspace=LocalWorkspace(working_dir="/tmp")
    )
    state.events.append(
        MessageEvent(
            source="user",
            llm_message=Message(role="user", content=[TextContent(text="fix it")]),
        )
    )
    for _ in range(15):
        state.events.append(_terminal_action())
    detector = StuckDetector(state)
    assert detector.no_progress_actions_threshold == 0
    assert detector.get_no_progress_nudge() is None


def test_no_progress_nudge_disabled_when_threshold_zero():
    detector = _make_detector([_terminal_action() for _ in range(5)], threshold=0)
    assert detector.get_no_progress_nudge() is None


def test_edit_breaks_no_progress_streak():
    actions = [_view_action() for _ in range(3)] + [_edit_action()]
    detector = _make_detector(actions, threshold=4)
    assert detector.get_no_progress_nudge() is None


def test_mixed_view_and_terminal_still_no_progress():
    actions = [_view_action(), _terminal_action(), _view_action(), _terminal_action()]
    detector = _make_detector(actions, threshold=4)
    assert detector.get_no_progress_nudge() is not None
