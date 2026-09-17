"""Per-line git blame for a single file (line-porcelain)."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from openhands.sdk.git.exceptions import (
    GitCommandError,
    GitPathError,
    GitRepositoryError,
)
from openhands.sdk.git.git_diff import (
    MAX_FILE_SIZE_FOR_GIT_DIFF,
    get_closest_git_repo,
)
from openhands.sdk.git.models import GitBlameLine
from openhands.sdk.git.utils import run_git_command, validate_git_repository


logger = logging.getLogger(__name__)

# Same size ceiling as git diff — blame porcelain for a huge file is
# expensive and the Files editor will not annotate it usefully.
MAX_FILE_SIZE_FOR_GIT_BLAME = MAX_FILE_SIZE_FOR_GIT_DIFF

_SHA_LINE = re.compile(
    r"^([0-9a-f]{40}|0{40})\s+(\d+)\s+(\d+)(?:\s+(\d+))?$"
)


def _unix_to_iso(author_time: str, author_tz: str) -> str:
    """Convert porcelain author-time + author-tz to an ISO-8601 string.

    Falls back to UTC when the timezone offset is missing or malformed so
    the GUI always receives a parseable timestamp.
    """
    try:
        epoch = int(author_time)
    except (TypeError, ValueError):
        return datetime.fromtimestamp(0, tz=timezone.utc).isoformat()

    tz = timezone.utc
    if author_tz and len(author_tz) == 5 and author_tz[0] in "+-":
        try:
            sign = 1 if author_tz[0] == "+" else -1
            hours = int(author_tz[1:3])
            minutes = int(author_tz[3:5])
            tz = timezone(sign * timedelta(hours=hours, minutes=minutes))
        except ValueError:
            tz = timezone.utc

    return datetime.fromtimestamp(epoch, tz=tz).isoformat()


def _parse_blame_porcelain(output: str) -> list[GitBlameLine]:
    """Parse ``git blame --line-porcelain`` stdout into blame lines."""
    lines: list[GitBlameLine] = []
    if not output:
        return lines

    sha = ""
    final_line = 0
    author = ""
    author_time = ""
    author_tz = "+0000"
    summary = ""
    awaiting_content = False

    for raw in output.splitlines():
        if awaiting_content:
            # Content lines start with a tab; ignore anything else.
            awaiting_content = False
            if sha and final_line > 0:
                lines.append(
                    GitBlameLine(
                        line=final_line,
                        sha=sha,
                        author=author or "Unknown",
                        author_time=_unix_to_iso(author_time or "0", author_tz),
                        summary=summary,
                    )
                )
            continue

        match = _SHA_LINE.match(raw)
        if match:
            sha = match.group(1)
            final_line = int(match.group(3))
            author = ""
            author_time = ""
            author_tz = "+0000"
            summary = ""
            continue

        if raw.startswith("author "):
            author = raw[len("author ") :]
        elif raw.startswith("author-time "):
            author_time = raw[len("author-time ") :]
        elif raw.startswith("author-tz "):
            author_tz = raw[len("author-tz ") :]
        elif raw.startswith("summary "):
            summary = raw[len("summary ") :]
        elif raw.startswith("filename "):
            # Last header before the content line.
            awaiting_content = True

    return lines


def get_git_blame(relative_file_path: str | Path) -> list[GitBlameLine]:
    """Return per-line blame for a single file.

    Args:
        relative_file_path: Path to the file (absolute or cwd-relative).

    Returns:
        One ``GitBlameLine`` per line of the file (1-based ``line``).

    Raises:
        GitPathError: If the file is missing, too large, or outside the repo.
        GitRepositoryError: If the file is not inside a git repository.
        GitCommandError: If git blame fails (e.g. untracked / binary).
    """
    path = Path(os.getcwd(), relative_file_path).resolve()

    if not path.exists():
        raise GitPathError(f"File does not exist: {path}")
    if not path.is_file():
        raise GitPathError(f"Path is not a file: {path}")

    try:
        file_size = os.path.getsize(path)
    except OSError as e:
        raise GitPathError(f"Cannot access file: {path}") from e
    if file_size > MAX_FILE_SIZE_FOR_GIT_BLAME:
        raise GitPathError(
            f"File too large for git blame: {file_size} bytes "
            f"(max: {MAX_FILE_SIZE_FOR_GIT_BLAME} bytes)"
        )

    closest_git_repo = get_closest_git_repo(path)
    if not closest_git_repo:
        raise GitRepositoryError(f"File is not in a git repository: {path}")

    validated_repo = validate_git_repository(closest_git_repo)

    try:
        relative_path_from_repo = path.relative_to(validated_repo)
    except ValueError as e:
        raise GitPathError(f"File is not within git repository: {path}") from e

    # --root: treat root commits as normal (no ^ prefix).
    # --line-porcelain: full metadata on every line.
    try:
        output = run_git_command(
            [
                "git",
                "--no-pager",
                "blame",
                "--line-porcelain",
                "--root",
                "--",
                str(relative_path_from_repo),
            ],
            validated_repo,
            timeout=60,
        )
    except GitCommandError:
        # Untracked / empty / binary — surface as empty annotate rather
        # than a hard failure so the Files toggle stays usable.
        logger.debug("git blame failed for %s; returning no lines", path)
        return []

    return _parse_blame_porcelain(output)
