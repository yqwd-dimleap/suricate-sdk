# Upstream origin

This tree was copied from https://github.com/OpenHands/software-agent-sdk
(shallow clone of `main` at import time) to bootstrap **Suricate SDK**.

Retained for Suricate Desktop / agent runtime:

- `suricate-sdk/` — core agent SDK
- `suricate-tools/` — tools
- `suricate-workspace/` — workspace backends
- `suricate-agent-server/` — agent server
- `clients/`, `examples/`, `tests/` — clients, samples, tests

Product-facing branding (docs, HTML UI titles, repo links) uses **Suricate**.
Python import/package names stay `openhands*` for compatibility with the upstream
layout and existing tooling.

Further Suricate-specific changes should land on top of this import.
