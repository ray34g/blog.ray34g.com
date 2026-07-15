#!/usr/bin/env python3
"""Verify the exampleSite menu, Markdown rendering, and theme shortcodes."""

from __future__ import annotations

import argparse
import sys
from html.parser import HTMLParser
from pathlib import Path

from verify_example_menu import verify_page, verify_sprite


class FeatureHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str]]] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, {key: value or "" for key, value in attrs}))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.text_parts.append(data.strip())

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)

    def matching(self, tag: str, **attrs: str) -> list[dict[str, str]]:
        return [
            element_attrs
            for element_tag, element_attrs in self.elements
            if element_tag == tag
            and all(element_attrs.get(name) == value for name, value in attrs.items())
        ]

    def with_class(self, tag: str, class_name: str) -> list[dict[str, str]]:
        return [
            attrs
            for element_tag, attrs in self.elements
            if element_tag == tag and class_name in attrs.get("class", "").split()
        ]


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def parse_html(path: Path) -> FeatureHTMLParser:
    parser = FeatureHTMLParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def verify_markdown_page(path: Path, lang: str) -> list[str]:
    parser = parse_html(path)
    failures: list[str] = []

    expected_text = {
        "ja": ["太字", "取り消し線", "1つ目の定義", "脚注の内容", "強調されないアスタリスク"],
        "en": ["strong text", "deleted text", "First definition", "Footnote content", "literal asterisks"],
    }[lang]
    for text in expected_text:
        require(text in parser.text, f"{path}: missing rendered text {text!r}", failures)

    require(bool(parser.matching("h2", id="fixture-heading")), f"{path}: missing attributed heading", failures)
    require(bool(parser.with_class("a", "heading-anchor")), f"{path}: missing heading anchor link", failures)
    for level in range(1, 7):
        require(bool(parser.matching(f"h{level}")), f"{path}: missing h{level} heading", failures)
    no_anchor_heading = parser.with_class("h3", "no-heading-anchor")
    require(len(no_anchor_heading) == 1, f"{path}: missing no-heading-anchor heading", failures)

    tables = parser.with_class("table", "fixture-table")
    require(len(tables) == 1, f"{path}: custom table class was not rendered", failures)
    if tables:
        require(tables[0].get("data-fixture") == "markdown-table", f"{path}: table attribute missing", failures)
    require(bool(parser.with_class("th", "text-start")), f"{path}: left-aligned table column missing", failures)
    require(bool(parser.with_class("th", "text-center")), f"{path}: center-aligned table column missing", failures)
    require(bool(parser.with_class("th", "text-end")), f"{path}: right-aligned table column missing", failures)
    table_wraps = parser.with_class("div", "content-table-wrap")
    require(
        any("--table-wrap-width:90vw" in attrs.get("style", "").replace(" ", "") for attrs in table_wraps),
        f"{path}: table wrapper style missing",
        failures,
    )

    require(bool(parser.with_class("div", "highlight")), f"{path}: fenced code was not highlighted", failures)
    require(len(parser.matching("pre")) >= 2, f"{path}: indented code block missing", failures)
    require(bool(parser.with_class("a", "footnote-ref")), f"{path}: footnote reference missing", failures)
    require(len(parser.matching("input", type="checkbox")) == 2, f"{path}: task list inputs missing", failures)
    require(bool(parser.matching("mark", **{"data-fixture": "unsafe-html"})), f"{path}: raw HTML missing", failures)
    require(bool(parser.matching("br")), f"{path}: hard line break missing", failures)
    require(bool(parser.matching("dl")), f"{path}: definition list missing", failures)
    require(bool(parser.matching("hr")), f"{path}: thematic break missing", failures)
    require(len(parser.matching("blockquote")) >= 2, f"{path}: nested block quote missing", failures)
    require(bool(parser.matching("ol", start="5")), f"{path}: ordered list start missing", failures)
    require(bool(parser.matching("details")), f"{path}: HTML details element missing", failures)
    require(bool(parser.matching("summary")), f"{path}: HTML summary element missing", failures)

    markdown_images = parser.matching("figure", id="markdown-image")
    require(len(markdown_images) == 1, f"{path}: Markdown image render hook missing", failures)
    fixture_images = parser.with_class("img", "fixture-image")
    require(len(fixture_images) == 1, f"{path}: Markdown image attributes missing", failures)
    if fixture_images:
        require(fixture_images[0].get("width") == "720", f"{path}: Markdown image width missing", failures)
        require(
            fixture_images[0].get("src", "").endswith("/images/placeholders/item-coming-soon.svg"),
            f"{path}: Markdown image did not resolve the shared coming-soon asset",
            failures,
        )
        require(fixture_images[0].get("loading") == "lazy", f"{path}: Markdown image loading missing", failures)

    return failures


def verify_shortcode_page(path: Path, lang: str) -> list[str]:
    parser = parse_html(path)
    failures: list[str] = []

    expected_text = {
        "ja": ["カラム内でレンダリングされたMarkdown", "Primary・全幅", "Outline・内容幅", "投稿一覧へ", "アイコン付き投稿一覧"],
        "en": ["Markdown rendered inside a column", "Primary, full width", "Outline, content width", "View all posts", "View posts with icons"],
    }[lang]
    for text in expected_text:
        require(text in parser.text, f"{path}: missing shortcode text {text!r}", failures)

    require(bool(parser.with_class("div", "fixture-row")), f"{path}: row shortcode missing", failures)
    require(len(parser.with_class("div", "stat-value")) == 2, f"{path}: stat shortcode items missing", failures)
    cta_labels = (
        {"Primary・全幅", "Outline・全幅", "Primary・内容幅", "Outline・内容幅", "投稿一覧へ", "アイコン付き投稿一覧"}
        if lang == "ja"
        else {"Primary, full width", "Outline, full width", "Primary, content width", "Outline, content width", "View all posts", "View posts with icons"}
    )
    cta_links = [link for link in parser.matching("a") if link.get("aria-label") in cta_labels]
    require(len(cta_links) == 6, f"{path}: CTA variants missing", failures)
    for link in cta_links:
        classes = set(link.get("class", "").split())
        require({"btn", "rounded-pill", "d-inline-flex"}.issubset(classes), f"{path}: CTA base styling classes missing", failures)
        require("px-4" in classes, f"{path}: CTA horizontal padding is not standardized", failures)
        require("gap-2" in classes, f"{path}: CTA leading-icon gap is not standardized", failures)
    require(sum("btn-primary" in link.get("class", "").split() for link in cta_links) == 4, f"{path}: primary CTA variants missing", failures)
    require(sum("btn-outline-primary" in link.get("class", "").split() for link in cta_links) == 2, f"{path}: outline CTA variants missing", failures)
    require(sum("w-100" in link.get("class", "").split() for link in cta_links) == 2, f"{path}: CTA width variants missing", failures)
    require(any("fixture-cta-trailing-arrow" in link.get("class", "").split() for link in cta_links), f"{path}: trailing-arrow CTA missing", failures)
    require(
        any("#icon-custom-arrow-right" in use.get("href", "") for use in parser.matching("use")),
        f"{path}: trailing arrow icon missing",
        failures,
    )
    require(
        not parser.with_class("svg", "icon-sm"),
        f"{path}: standard CTA icons should inherit the surrounding text size",
        failures,
    )
    require(any("fixture-cta-leading-and-trailing" in link.get("class", "").split() for link in cta_links), f"{path}: leading-and-trailing icon CTA missing", failures)
    label_groups = parser.with_class("span", "cta-label-group")
    require(len(label_groups) >= len(cta_links), f"{path}: CTA label groups missing", failures)
    for label_group in label_groups:
        require("gap-2" in label_group.get("class", "").split(), f"{path}: label-to-trailing-icon gap is not standardized", failures)
    trailing_wrappers = parser.with_class("span", "cta-trailing-icon")
    require(len(trailing_wrappers) == 2, f"{path}: trailing icon wrappers missing", failures)
    for trailing_wrapper in trailing_wrappers:
        wrapper_classes = set(trailing_wrapper.get("class", "").split())
        require(
            {"d-inline-flex", "align-items-center", "lh-1"}.issubset(wrapper_classes),
            f"{path}: trailing icon is not vertically centered",
            failures,
        )
        require(not any(name.startswith("ms-") for name in wrapper_classes), f"{path}: trailing icon uses margin instead of gap", failures)
    require(any(link.get("target") == "_blank" and "noopener" in link.get("rel", "") for link in cta_links), f"{path}: external CTA safety attributes missing", failures)

    site_icons = parser.with_class("svg", "fixture-site-icon")
    page_icons = parser.with_class("svg", "fixture-page-icon")
    require(len(site_icons) == 1, f"{path}: site sprite icon shortcode missing", failures)
    require(len(page_icons) == 1, f"{path}: page sprite icon shortcode missing", failures)
    require(bool(parser.matching("symbol", id="icon-fas-check")), f"{path}: page sprite symbol missing", failures)

    figures = parser.matching("figure", id="shortcode-figure")
    require(len(figures) == 1, f"{path}: figure shortcode missing", failures)
    require(bool(parser.matching("picture")), f"{path}: responsive picture missing", failures)
    require(bool(parser.matching("source")), f"{path}: responsive mobile source missing", failures)
    zoom_links = [link for link in parser.matching("a") if link.get("data-zoom") == "true"]
    require(len(zoom_links) >= 2, f"{path}: figure zoom links missing", failures)
    require(len(parser.matching("figcaption")) >= 2, f"{path}: figure captions missing", failures)
    caption_text = "caption属性から渡されたキャプション" if lang == "ja" else "Caption passed with the caption parameter"
    require(caption_text in parser.text, f"{path}: figure caption parameter missing", failures)

    return failures


def verify_theme_css(public_dir: Path) -> list[str]:
    path = public_dir / "css" / "components" / "buttons.css"
    if not path.is_file():
        return [f"{path}: button component stylesheet missing"]

    css = path.read_text(encoding="utf-8")
    failures: list[str] = []
    require(".btn-primary" in css, f"{path}: global primary button override missing", failures)
    require("--bs-btn-bg: var(--bs-primary)" in css, f"{path}: primary button is not connected to theme primary", failures)
    require(".btn-outline-primary" in css, f"{path}: outline primary override missing", failures)

    icon_path = public_dir / "css" / "components" / "icons.css"
    if not icon_path.is_file():
        failures.append(f"{icon_path}: icon component stylesheet missing")
        return failures
    icon_css = icon_path.read_text(encoding="utf-8")
    require("font-size: .875em" in icon_css, f"{icon_path}: icon-sm is not text-relative", failures)
    require("font-size: 1em" in icon_css, f"{icon_path}: icon-base is not aligned with text", failures)
    return failures


def verify_taxonomy_page(path: Path, article_title: str) -> list[str]:
    failures: list[str] = []
    if not path.is_file():
        return [f"{path}: taxonomy fixture page was not generated"]

    parser = parse_html(path)
    require(article_title in parser.text, f"{path}: tagged article is not listed", failures)
    return failures


def verify_posts_section(path: Path, article_titles: list[str]) -> list[str]:
    failures: list[str] = []
    if not path.is_file():
        return [f"{path}: posts section page was not generated"]

    parser = parse_html(path)
    for article_title in article_titles:
        require(article_title in parser.text, f"{path}: missing post {article_title!r}", failures)
    return failures


def verify_archive_page(path: Path, expected_links: dict[str, str]) -> list[str]:
    failures: list[str] = []
    if not path.is_file():
        return [f"{path}: archive page was not generated"]

    parser = parse_html(path)
    require(bool(parser.matching("section", **{"data-archive-year": "2026"})), f"{path}: missing 2026 group", failures)
    rendered_links = {link.get("href", ""): link for link in parser.matching("a")}
    for href, title in expected_links.items():
        require(href in rendered_links, f"{path}: missing canonical post link {href!r}", failures)
        require(title in parser.text, f"{path}: missing archived post {title!r}", failures)
    require(len(parser.matching("time")) >= len(expected_links), f"{path}: archive dates missing", failures)
    return failures


def main() -> int:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("public_dir", type=Path)
    args = argument_parser.parse_args()

    public_dir = args.public_dir
    failures: list[str] = []
    failures.extend(verify_page(public_dir / "index.html", "ja"))
    failures.extend(verify_page(public_dir / "en" / "index.html", "en"))
    failures.extend(verify_sprite(public_dir / "images" / "site-sprite.svg"))
    failures.extend(verify_theme_css(public_dir))
    failures.extend(verify_markdown_page(public_dir / "posts" / "2026" / "01" / "markdown-kitchen-sink" / "index.html", "ja"))
    failures.extend(verify_markdown_page(public_dir / "en" / "posts" / "2026" / "01" / "markdown-kitchen-sink" / "index.html", "en"))
    failures.extend(verify_shortcode_page(public_dir / "posts" / "2026" / "01" / "shortcode-kitchen-sink" / "index.html", "ja"))
    failures.extend(verify_shortcode_page(public_dir / "en" / "posts" / "2026" / "01" / "shortcode-kitchen-sink" / "index.html", "en"))
    failures.extend(verify_posts_section(public_dir / "posts" / "index.html", ["標準Markdown機能一覧", "Shortcode機能一覧", "一覧項目fixture"]))
    failures.extend(verify_posts_section(public_dir / "en" / "posts" / "index.html", ["Standard Markdown kitchen sink", "Shortcode kitchen sink", "List item fixture"]))
    failures.extend(verify_taxonomy_page(public_dir / "tags" / "fixture" / "index.html", "標準Markdown機能一覧"))
    failures.extend(verify_taxonomy_page(public_dir / "en" / "tags" / "fixture" / "index.html", "Standard Markdown kitchen sink"))
    failures.extend(verify_archive_page(public_dir / "archive" / "index.html", {
        "/posts/2026/01/markdown-kitchen-sink/": "標準Markdown機能一覧",
        "/posts/2026/01/shortcode-kitchen-sink/": "Shortcode機能一覧",
        "/posts/2026/01/list-item-fixture/": "一覧項目fixture",
    }))
    failures.extend(verify_archive_page(public_dir / "en" / "archive" / "index.html", {
        "/en/posts/2026/01/markdown-kitchen-sink/": "Standard Markdown kitchen sink",
        "/en/posts/2026/01/shortcode-kitchen-sink/": "Shortcode kitchen sink",
        "/en/posts/2026/01/list-item-fixture/": "List item fixture",
    }))

    if failures:
        for failure in failures:
            print(f"[example-site] ERROR: {failure}", file=sys.stderr)
        return 1

    print(f"[example-site] ok ({public_dir})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
