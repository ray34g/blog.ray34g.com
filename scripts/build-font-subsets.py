#!/usr/bin/env python3
"""Compatibility wrapper for the font subset builder."""

from pathlib import Path
import runpy


SCRIPT = Path(__file__).resolve().parents[1] / "ci/scripts/tools/build_font_subsets.py"


if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
