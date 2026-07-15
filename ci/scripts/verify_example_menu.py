#!/usr/bin/env python3
"""Verify exampleSite header menu fixture output."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class MenuHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.dropdown_toggles = 0
        self.main_menu_gap_toggles = 0
        self.dropdown_menus = 0
        self.responsive_main_dropdowns = 0
        self.desktop_nowrap_menus = 0
        self.dropdown_columns = 0
        self.site_sprite_uses: list[str] = []
        self.links: list[dict[str, str]] = []
        self.ids: set[str] = set()
        self.text_parts: list[str] = []
        self.search_modal = False
        self.theme_menu = False
        self.main_menu = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "button" and attr.get("data-bs-toggle") == "dropdown":
            self.dropdown_toggles += 1
            if attr.get("id", "").startswith("main-dd-") and "gap-2" in classes:
                self.main_menu_gap_toggles += 1
        if "dropdown-menu" in classes:
            self.dropdown_menus += 1
        if "main-menu-dropdown" in classes:
            self.responsive_main_dropdowns += 1
        if {"d-flex", "flex-wrap", "flex-lg-nowrap"}.issubset(classes):
            self.desktop_nowrap_menus += 1
        if {"flex-grow-1", "flex-shrink-0"}.issubset(classes):
            self.dropdown_columns += 1
        if tag == "use":
            href = attr.get("href") or attr.get("xlink:href")
            if href and "site-sprite.svg" in href:
                self.site_sprite_uses.append(href)
        if tag == "a":
            self.links.append(attr)

        element_id = attr.get("id")
        if element_id:
            self.ids.add(element_id)
            if element_id == "searchModal":
                self.search_modal = True
            elif element_id == "theme-menu-dropdown":
                self.theme_menu = True
            elif element_id == "mainMenu":
                self.main_menu = True

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.text_parts.append(data)

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)


def parse_html(path: Path) -> MenuHTMLParser:
    parser = MenuHTMLParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def verify_page(path: Path, lang: str) -> list[str]:
    parser = parse_html(path)
    failures: list[str] = []
    text = parser.text

    expected = {
        "ja": [
            "研究",
            "機能領域",
            "パフォーマンス",
            "レイアウト種別",
            "投稿セクション",
            "Markdown記事",
            "Shortcode記事",
            "タグ一覧",
            "fixtureタグ",
            "年別アーカイブ",
            "リソース",
        ],
        "en": [
            "Lab",
            "Capabilities",
            "Performance",
            "Layout types",
            "Posts section",
            "Markdown article",
            "Shortcode article",
            "Tag terms",
            "Fixture taxonomy",
            "Yearly archive",
            "Resources",
        ],
    }[lang]

    expected_paths = {
        "ja": [
            "/posts/",
            "/posts/2026/01/markdown-kitchen-sink/",
            "/posts/2026/01/shortcode-kitchen-sink/",
            "/tags/",
            "/tags/fixture/",
            "/archive/",
        ],
        "en": [
            "/en/posts/",
            "/en/posts/2026/01/markdown-kitchen-sink/",
            "/en/posts/2026/01/shortcode-kitchen-sink/",
            "/en/tags/",
            "/en/tags/fixture/",
            "/en/archive/",
        ],
    }[lang]

    require(parser.dropdown_toggles >= 2, f"{path}: expected at least 2 dropdown toggles", failures)
    require(parser.main_menu_gap_toggles >= 2, f"{path}: main dropdown icon spacing is not gap-2", failures)
    require(parser.dropdown_menus >= 2, f"{path}: expected at least 2 dropdown menus", failures)
    require(parser.responsive_main_dropdowns >= 2, f"{path}: responsive main dropdown class missing", failures)
    require(parser.desktop_nowrap_menus >= 1, f"{path}: missing desktop nowrap menu layout", failures)
    require(parser.dropdown_columns >= 2, f"{path}: expected at least 2 dropdown columns", failures)
    require(parser.search_modal, f"{path}: missing search modal", failures)
    require(parser.theme_menu, f"{path}: missing theme menu", failures)
    require(parser.main_menu, f"{path}: missing offcanvas main menu", failures)
    require("main-content" in parser.ids, f"{path}: missing skip target #main-content", failures)

    for label in expected:
        require(label in text, f"{path}: missing menu label {label!r}", failures)

    rendered_paths = {link.get("href", "") for link in parser.links}
    for expected_path in expected_paths:
        require(expected_path in rendered_paths, f"{path}: missing layout fixture link {expected_path!r}", failures)

    require(
        any("#icon-custom-chevron-down" in href for href in parser.site_sprite_uses),
        f"{path}: dropdown chevron icon is not referenced",
        failures,
    )
    require(
        any("#icon-fab-github" in href for href in parser.site_sprite_uses),
        f"{path}: GitHub icon is not referenced",
        failures,
    )

    github_links = [link for link in parser.links if "github.com/ray34g" in link.get("href", "")]
    require(github_links, f"{path}: missing GitHub link", failures)
    for link in github_links:
        require(link.get("target") == "_blank", f"{path}: GitHub link is not external", failures)
        require("noopener" in link.get("rel", ""), f"{path}: GitHub link missing noopener", failures)
        require("gap-2" in link.get("class", "").split(), f"{path}: external link icon spacing is not gap-2", failures)

    dropdown_links = [link for link in parser.links if "dropdown-item" in link.get("class", "").split()]
    for link in dropdown_links:
        require("gap-2" in link.get("class", "").split(), f"{path}: dropdown item icon spacing is not gap-2", failures)

    return failures


def verify_sprite(path: Path) -> list[str]:
    failures: list[str] = []
    text = path.read_text(encoding="utf-8")
    for symbol in [
        "icon-custom-chevron-down",
        "icon-fab-github",
        "icon-fas-link",
    ]:
        require(
            re.search(rf'\bid=(?:"{re.escape(symbol)}"|{re.escape(symbol)}\b)', text) is not None,
            f"{path}: missing sprite symbol {symbol}",
            failures,
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("public_dir", type=Path)
    args = parser.parse_args()

    public_dir = args.public_dir
    failures: list[str] = []
    failures.extend(verify_page(public_dir / "index.html", "ja"))
    failures.extend(verify_page(public_dir / "en" / "index.html", "en"))
    failures.extend(verify_sprite(public_dir / "images" / "site-sprite.svg"))

    if failures:
        for failure in failures:
            print(f"[example-menu] ERROR: {failure}", file=sys.stderr)
        return 1

    print(f"[example-menu] ok ({public_dir})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
