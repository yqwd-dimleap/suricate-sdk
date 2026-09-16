"""DEFAULT prompt workflow sections should bias toward short, finishable loops."""

from openhands.sdk.context.prompts.presets import PromptPreset, create_registry
from openhands.sdk.context.prompts.section import PromptContext
from openhands.sdk.context.prompts.sections.static import (
    CodeQualitySection,
    EfficiencySection,
    ProblemSolvingSection,
)


def test_problem_solving_prioritizes_finish_over_exhaustive_explore():
    body = ProblemSolvingSection().body
    assert "FINISH" in body
    assert "Call `finish`" in body or "call `finish`" in body
    assert "Thoroughly explore" not in body
    assert "ORIENT" in body
    assert "REPRODUCE" in body


def test_efficiency_discourages_archaeology_and_urges_finish():
    body = EfficiencySection().body
    assert "finish" in body.lower()
    assert "archaeology" in body.lower()


def test_code_quality_no_longer_requires_exhaustive_pre_explore():
    body = CodeQualitySection().body
    assert "thoroughly understand the codebase through exploration" not in body.lower()
    assert "Explore just enough" in body


def test_default_registry_includes_updated_workflow_sections():
    rendered = create_registry(PromptPreset.DEFAULT).build(PromptContext())
    static = rendered.static or ""
    assert "PROBLEM_SOLVING_WORKFLOW" in static
    assert "call `finish`" in static
    assert "Thoroughly explore relevant files" not in static
