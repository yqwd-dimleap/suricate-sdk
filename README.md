# Suricate SDK

Suricate SDK is a local fork of the **OpenHands Software Agent SDK**, providing Python / TypeScript / REST APIs for building agents that work with code.

It is the agent runtime used with [Suricate Desktop](https://github.com/yqwd-dimleap/suricate-desktop) (Agent Canvas desktop shell).

## Upstream

- Source: [OpenHands/software-agent-sdk](https://github.com/OpenHands/software-agent-sdk)
- License: MIT (see [LICENSE](./LICENSE))
- Docs (upstream): [docs.openhands.dev/sdk](https://docs.openhands.dev/sdk)

Python package import paths remain `openhands.*` / `openhands-*` for compatibility with the upstream ecosystem and PyPI package layout. Product branding in docs and UI uses **Suricate**.

## Packages (workspace)

| Path | Package |
|------|---------|
| `openhands-sdk/` | Core SDK |
| `openhands-tools/` | Tools |
| `openhands-workspace/` | Workspaces |
| `openhands-agent-server/` | Agent Server |

## Quick Start

```python
import os

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool


llm = LLM(
    model="gpt-5.5",
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

agent = Agent(
    llm=llm,
    tools=[
        Tool(name=TerminalTool.name),
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
    ],
)

conversation = Conversation(agent=agent, workspace=".")
conversation.send_message("Create a simple Python script that prints Hello World")
conversation.run()
```

See upstream examples under `examples/` and [DEVELOPMENT.md](./DEVELOPMENT.md) for local setup.

## Related

- Desktop UI: [yqwd-dimleap/suricate-desktop](https://github.com/yqwd-dimleap/suricate-desktop)
- This SDK repo: [yqwd-dimleap/suricate-sdk](https://github.com/yqwd-dimleap/suricate-sdk)
