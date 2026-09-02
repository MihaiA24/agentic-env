#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich>=13.7"]
# ///
"""Diagnose the installed agent stack (read-only)."""
from __future__ import annotations

from agentic_env.stack_doctor import main


if __name__ == "__main__":
    raise SystemExit(main())
