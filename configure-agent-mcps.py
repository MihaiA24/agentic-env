#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich>=13.7"]
# ///
"""Configure project-memory MCP servers and global agent skills."""
from __future__ import annotations

from agentic_env.configure_agent_mcps import main


if __name__ == "__main__":
    raise SystemExit(main())
