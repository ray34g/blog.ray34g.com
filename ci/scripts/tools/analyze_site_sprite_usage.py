#!/usr/bin/env python3
"""Analyze built HTML and collect site sprite symbol usage."""

from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path


SITE_SPRITE_PATTERN = re.compile(r"(?:^|/|\.{1,2}/)images/site-sprite\.svg(?:\?[^#]*)?#(?P<symbol>icon-[a-z0-9-]+)$")
SYMBOL_PATTERN = re.compile(r"^icon-(?P<vendor>fas|far|fab|bi|lucide|custom)-(?P<name>[a-z0-9-]+)$")


class SiteSpriteUsageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.symbols: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in {"svg", "use"}:
            return

        attr_map = dict(attrs)
        for attr_name in ("href", "xlink:href"):
            value = attr_map.get(attr_name)
            if not value:
                continue
            match = SITE_SPRITE_PATTERN.search(value)
            if match:
                self.symbols.add(match.group("symbol"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze built HTML for site sprite usage.")
    parser.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Directory containing built HTML files.",
    )
    parser.add_argument(
        "--output",
        default=Path("data/site_sprite_usage.json"),
        type=Path,
        help="Path to write the usage analysis JSON.",
    )
    return parser.parse_args()


def list_html_files(input_dir: Path) -> list[Path]:
    html_files = sorted(input_dir.rglob("*.html"))
    if not html_files:
        raise FileNotFoundError(f"No HTML files found under {input_dir}")
    return html_files


def relative_page_path(input_dir: Path, html_path: Path) -> str:
    rel_path = html_path.relative_to(input_dir)
    return rel_path.as_posix()


def symbol_to_icon_id(symbol: str) -> str:
    match = SYMBOL_PATTERN.match(symbol)
    if not match:
        raise ValueError(f"Unsupported site sprite symbol: {symbol}")
    return f"{match.group('vendor')}:{match.group('name')}"


def main() -> int:
    args = parse_args()
    html_files = list_html_files(args.input_dir)

    pages: dict[str, list[str]] = {}
    symbols: set[str] = set()

    for html_file in html_files:
        parser = SiteSpriteUsageParser()
        parser.feed(html_file.read_text(encoding="utf-8"))
        parser.close()

        page_icon_ids = sorted(symbol_to_icon_id(symbol) for symbol in parser.symbols)
        if page_icon_ids:
            pages[relative_page_path(args.input_dir, html_file)] = page_icon_ids
            symbols.update(page_icon_ids)

    payload = {
        "icons": sorted(symbols),
        "pages": pages,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
