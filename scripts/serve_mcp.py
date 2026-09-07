# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "fastmcp>=3.0",
#     "okf-parser>=0.45.6",
#     "cyclopts>=4.0",
# ]
# ///
"""Standalone FastMCP runner adhering to PEP 723."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is in path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wisk.mcp import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
