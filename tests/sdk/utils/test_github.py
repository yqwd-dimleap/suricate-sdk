"""Tests for GitHub utility functions."""

from openhands.sdk.utils.github import ZWJ, sanitize_openhands_mentions


def test_sanitize_basic_mention():
    """Test basic @Suricate mention is sanitized."""
    text = "Thanks @Suricate for the help!"
    expected = f"Thanks @{ZWJ}Suricate for the help!"
    assert sanitize_openhands_mentions(text) == expected


def test_sanitize_case_insensitive():
    """Test that mentions are sanitized regardless of case."""
    test_cases = [
        ("Check @Suricate here", f"Check @{ZWJ}Suricate here"),
        ("Check @openhands here", f"Check @{ZWJ}openhands here"),
        ("Check @OPENHANDS here", f"Check @{ZWJ}OPENHANDS here"),
        ("Check @oPeNhAnDs here", f"Check @{ZWJ}oPeNhAnDs here"),
    ]
    for input_text, expected in test_cases:
        assert sanitize_openhands_mentions(input_text) == expected


def test_sanitize_multiple_mentions():
    """Test multiple mentions in the same text."""
    text = "Both @Suricate and @openhands should be sanitized"
    expected = f"Both @{ZWJ}Suricate and @{ZWJ}openhands should be sanitized"
    assert sanitize_openhands_mentions(text) == expected


def test_sanitize_with_punctuation():
    """Test mentions followed by punctuation."""
    test_cases = [
        ("Thanks @Suricate!", f"Thanks @{ZWJ}Suricate!"),
        ("Hello @Suricate.", f"Hello @{ZWJ}Suricate."),
        ("See @Suricate,", f"See @{ZWJ}Suricate,"),
        ("By @Suricate:", f"By @{ZWJ}Suricate:"),
        ("From @Suricate;", f"From @{ZWJ}Suricate;"),
        ("Hi @Suricate?", f"Hi @{ZWJ}Suricate?"),
        ("Use @Suricate)", f"Use @{ZWJ}Suricate)"),
        ("Try (@Suricate)", f"Try (@{ZWJ}Suricate)"),
    ]
    for input_text, expected in test_cases:
        assert sanitize_openhands_mentions(input_text) == expected


def test_no_sanitize_partial_words():
    """Test that partial word matches are NOT sanitized."""
    test_cases = [
        "OpenHandsTeam",
        "MyOpenHands",
        "OpenHandsBot",
        "#Suricate",
    ]
    for text in test_cases:
        # Partial words without @ should remain unchanged
        assert sanitize_openhands_mentions(text) == text


def test_no_op_cases():
    """Test cases where no sanitization should occur."""
    test_cases = [
        "",
        "No mentions here",
        "Just some text",
        "@GitHub",
        "@Other",
        "Suricate without @",
    ]
    for text in test_cases:
        assert sanitize_openhands_mentions(text) == text


def test_sanitize_at_line_boundaries():
    """Test mentions at the start and end of lines."""
    test_cases = [
        ("@Suricate at start", f"@{ZWJ}Suricate at start"),
        ("at end @Suricate", f"at end @{ZWJ}Suricate"),
        ("@Suricate", f"@{ZWJ}Suricate"),
    ]
    for input_text, expected in test_cases:
        assert sanitize_openhands_mentions(input_text) == expected


def test_sanitize_multiline_text():
    """Test sanitization in multiline text."""
    text = """Hello @Suricate!

This is a test with @openhands mentioned.

Thanks @OPENHANDS for everything!"""

    expected = f"""Hello @{ZWJ}Suricate!

This is a test with @{ZWJ}openhands mentioned.

Thanks @{ZWJ}OPENHANDS for everything!"""

    assert sanitize_openhands_mentions(text) == expected


def test_sanitize_with_urls():
    """Test that URLs containing Suricate are handled correctly."""
    test_cases = [
        # URL should not be sanitized
        ("Visit https://github.com/Suricate", "Visit https://github.com/Suricate"),
        # But mention should be sanitized
        (
            "See @Suricate at https://github.com/Suricate",
            f"See @{ZWJ}Suricate at https://github.com/Suricate",
        ),
    ]
    for input_text, expected in test_cases:
        assert sanitize_openhands_mentions(input_text) == expected


def test_sanitize_preserves_whitespace():
    """Test that whitespace is preserved correctly."""
    text = "  @Suricate  \n  @openhands  "
    expected = f"  @{ZWJ}Suricate  \n  @{ZWJ}openhands  "
    assert sanitize_openhands_mentions(text) == expected


def test_zwj_constant():
    """Test that ZWJ constant is correctly defined."""
    assert ZWJ == "\u200d"
    assert len(ZWJ) == 1
    assert ord(ZWJ) == 0x200D
