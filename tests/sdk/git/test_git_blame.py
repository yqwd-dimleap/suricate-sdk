"""Tests for git_blame.py using temporary repositories."""

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from openhands.sdk.git.exceptions import GitPathError, GitRepositoryError
from openhands.sdk.git.git_blame import get_git_blame, _parse_blame_porcelain
from openhands.sdk.git.models import GitBlameLine


def run_bash_command(command: str, cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def setup_git_repo(repo_dir: str) -> None:
    run_bash_command("git init -b main", repo_dir)
    run_bash_command("git config user.name 'Test User'", repo_dir)
    run_bash_command("git config user.email 'test@example.com'", repo_dir)


def commit_file(repo_dir: str, name: str, content: str, message: str) -> str:
    (Path(repo_dir) / name).write_text(content)
    run_bash_command("git add .", repo_dir)
    run_bash_command(f"git commit -m '{message}'", repo_dir)
    return run_bash_command("git rev-parse HEAD", repo_dir).stdout.strip()


def test_get_git_blame_returns_one_line_per_source_line():
    with tempfile.TemporaryDirectory() as temp_dir:
        setup_git_repo(temp_dir)
        sha = commit_file(temp_dir, "a.txt", "one\ntwo\nthree\n", "add a")

        blame = get_git_blame(Path(temp_dir) / "a.txt")

        assert [line.line for line in blame] == [1, 2, 3]
        assert all(line.sha == sha for line in blame)
        assert all(line.author == "Test User" for line in blame)
        assert all(line.summary == "add a" for line in blame)
        assert datetime.fromisoformat(blame[0].author_time) is not None


def test_get_git_blame_tracks_different_authors_across_commits():
    with tempfile.TemporaryDirectory() as temp_dir:
        setup_git_repo(temp_dir)
        sha1 = commit_file(temp_dir, "a.txt", "first\n", "first")
        run_bash_command("git config user.name 'Other Author'", temp_dir)
        sha2 = commit_file(temp_dir, "a.txt", "first\nsecond\n", "second")

        blame = get_git_blame(Path(temp_dir) / "a.txt")

        assert blame[0].sha == sha1
        assert blame[0].author == "Test User"
        assert blame[1].sha == sha2
        assert blame[1].author == "Other Author"


def test_get_git_blame_untracked_file_returns_empty():
    with tempfile.TemporaryDirectory() as temp_dir:
        setup_git_repo(temp_dir)
        commit_file(temp_dir, "tracked.txt", "ok\n", "init")
        untracked = Path(temp_dir) / "new.txt"
        untracked.write_text("brand new\n")

        assert get_git_blame(untracked) == []


def test_get_git_blame_missing_file_raises():
    with tempfile.TemporaryDirectory() as temp_dir:
        setup_git_repo(temp_dir)
        with pytest.raises(GitPathError):
            get_git_blame(Path(temp_dir) / "missing.txt")


def test_get_git_blame_outside_repo_raises():
    with tempfile.TemporaryDirectory() as temp_dir:
        orphan = Path(temp_dir) / "orphan.txt"
        orphan.write_text("no git here\n")
        with pytest.raises(GitRepositoryError):
            get_git_blame(orphan)


def test_parse_blame_porcelain_minimal_block():
    porcelain = (
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 1 1 1\n"
        "author Alice\n"
        "author-mail <a@example.com>\n"
        "author-time 1700000000\n"
        "author-tz +0000\n"
        "committer Alice\n"
        "committer-mail <a@example.com>\n"
        "committer-time 1700000000\n"
        "committer-tz +0000\n"
        "summary hello\n"
        "filename a.txt\n"
        "\tline one\n"
    )

    lines = _parse_blame_porcelain(porcelain)

    assert lines == [
        GitBlameLine(
            line=1,
            sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            author="Alice",
            author_time="2023-11-14T22:13:20+00:00",
            summary="hello",
        )
    ]
