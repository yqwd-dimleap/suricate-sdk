"""Hooks service for Suricate Agent Server.

This module contains the business logic for loading hooks from the workspace,
keeping the router clean and focused on HTTP concerns.

Hook Sources:
- Project hooks: {workspace}/.suricate/hooks.json (preferred)
- Project hooks: {workspace}/.openhands/hooks.json (legacy)
- User hooks: ~/.suricate/hooks.json (future)
"""

from openhands.sdk.hooks import HookConfig
from openhands.sdk.logger import get_logger
from openhands.sdk.utils.path import resolve_project_config_file


logger = get_logger(__name__)


def load_hooks_from_workspace(project_dir: str | None = None) -> HookConfig | None:
    """Load hooks from the workspace hooks.json file.

    Reads ``.suricate/hooks.json`` first, then falls back to legacy
    ``.openhands/hooks.json`` so existing workspaces keep working.

    Args:
        project_dir: Workspace directory path for project hooks.

    Returns:
        HookConfig if hooks.json exists and is valid, None otherwise.
    """
    if not project_dir:
        logger.debug("No project_dir provided, skipping hooks loading")
        return None

    hooks_path = resolve_project_config_file(project_dir, "hooks.json")

    if hooks_path is None:
        logger.debug(
            "No hooks.json found under .suricate/ or .openhands/ in %s",
            project_dir,
        )
        return None

    try:
        hook_config = HookConfig.load(path=hooks_path)

        if hook_config.is_empty():
            logger.debug(f"hooks.json at {hooks_path} is empty")
            return None

        logger.info(f"Loaded hooks from {hooks_path}")
        return hook_config

    except Exception as e:
        logger.warning(f"Failed to load hooks from {hooks_path}: {e}")
        return None
