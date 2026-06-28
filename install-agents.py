#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich>=13.7"]
# ///
"""Install local agent CLIs."""
from __future__ import annotations

from agentic_env.install_agents import main


if __name__ == "__main__":
    raise SystemExit(main())
