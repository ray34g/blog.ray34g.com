#!/usr/bin/env python3
"""Analyze built HTML and infer page-level font family and weight usage."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote


@dataclass(frozen=True)
class ElementUsage:
    tag: str
    classes: tuple[str, ...]


class HtmlUsageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[ElementUsage] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        classes = attr_map.get("class", "")
        class_names = tuple(sorted({class_name for class_name in classes.split() if class_name}))
        self.elements.append(ElementUsage(tag=tag, classes=class_names))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze Bootstrap-related font weight usage from built HTML."
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Directory containing built HTML files.",
    )
    parser.add_argument(
        "--rules",
        default=Path("data/font_weight_rules.yaml"),
        type=Path,
        help="Path to the font weight rule definition YAML or JSON.",
    )
    parser.add_argument(
        "--output",
        default=Path("data/font_weight_usage.json"),
        type=Path,
        help="Path to write the analysis JSON.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print page summaries while analyzing.",
    )
    return parser.parse_args()


def load_rules(path: Path) -> dict:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))

    if path.suffix in {".yaml", ".yml"}:
        env = os.environ.copy()
        node_path_entries: list[str] = []
        if env.get("NODE_PATH"):
            node_path_entries.append(env["NODE_PATH"])

        ci_project_dir = env.get("CI_PROJECT_DIR")
        node_cwd = None
        if ci_project_dir:
            node_cwd = ci_project_dir
            node_modules = Path(ci_project_dir) / "node_modules"
            if node_modules.exists():
                node_path_entries.append(str(node_modules))

        script_node_modules = Path(__file__).resolve().parents[3] / "node_modules"
        if script_node_modules.exists():
            node_path_entries.append(str(script_node_modules))
            if node_cwd is None:
                node_cwd = str(Path(__file__).resolve().parents[3])

        if node_path_entries:
            env["NODE_PATH"] = os.pathsep.join(dict.fromkeys(node_path_entries))

        cmd = [
            "node",
            "-e",
            (
                "const fs=require('fs');"
                "const yaml=require('yaml');"
                "const path=process.argv[1];"
                "const data=yaml.parse(fs.readFileSync(path,'utf8'));"
                "process.stdout.write(JSON.stringify(data));"
            ),
            str(path),
        ]
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            env=env,
            cwd=node_cwd,
        )
        return json.loads(result.stdout)

    raise ValueError(f"Unsupported rules file format: {path}")


def list_html_files(input_dir: Path) -> list[Path]:
    html_files = sorted(input_dir.rglob("*.html"))
    if not html_files:
        raise FileNotFoundError(f"No HTML files found under {input_dir}")
    return html_files


def parse_usage(html_path: Path) -> list[ElementUsage]:
    parser = HtmlUsageParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    parser.close()
    return parser.elements


def page_key(input_dir: Path, html_path: Path) -> str:
    rel_path = html_path.relative_to(input_dir)
    if rel_path.name == "index.html":
        parent = rel_path.parent.as_posix()
        raw = "/" if parent == "." else f"/{parent}/"
    else:
        raw = f"/{rel_path.as_posix()}"
    return quote(raw, safe="/.-_~")


def match_rule(rule: dict, element: ElementUsage) -> tuple[bool, list[str]]:
    matched_tokens: list[str] = []
    class_names = set(element.classes)
    element_names = {element.tag}
    match = rule.get("match", {})

    classes_any = match.get("classes_any", [])
    if classes_any:
        hits = [name for name in classes_any if name in class_names]
        if not hits:
            return False, []
        matched_tokens.extend(hits)

    classes_all = match.get("classes_all", [])
    if classes_all:
        if not all(name in class_names for name in classes_all):
            return False, []
        matched_tokens.extend(classes_all)

    classes_glob = match.get("classes_glob", [])
    if classes_glob:
        glob_hits = []
        for pattern in classes_glob:
            glob_hits.extend(
                sorted(name for name in class_names if fnmatch.fnmatch(name, pattern))
            )
        if not glob_hits:
            return False, []
        matched_tokens.extend(glob_hits)

    elements_any = match.get("elements_any", [])
    if elements_any:
        hits = [name for name in elements_any if name in element_names]
        if not hits:
            return False, []
        matched_tokens.extend(hits)

    return True, sorted(set(matched_tokens))


def analyze_page(
    rules: dict,
    elements: list[ElementUsage],
) -> dict[str, dict[str, object]]:
    fonts: dict[str, dict[str, object]] = {}

    for font_family, default_weights in rules.get("defaults", {}).items():
        fonts[font_family] = {
            "weights": set(default_weights),
            "styles": {"normal"} if default_weights else set(),
            "reasons": {},
        }

    for element in elements:
        for rule in rules.get("rules", []):
            matched, matched_tokens = match_rule(rule, element)
            if not matched:
                continue

            font_family = rule["font_family"]
            if font_family not in fonts:
                fonts[font_family] = {"weights": set(), "styles": set(), "reasons": {}}

            fonts[font_family]["weights"].update(rule["weights"])
            fonts[font_family]["styles"].update(rule.get("styles", ["normal"]))

            existing = fonts[font_family]["reasons"].setdefault(
                rule["id"],
                {
                    "rule_id": rule["id"],
                    "reason": rule["reason"],
                    "matches": set(),
                    "styles": set(),
                },
            )
            existing["matches"].update(matched_tokens)
            existing["styles"].update(rule.get("styles", ["normal"]))

    result: dict[str, dict[str, object]] = {}
    for font_family, payload in fonts.items():
        if not payload["weights"] and not payload["styles"] and not payload["reasons"]:
            continue
        result[font_family] = {
            "weights": sorted(payload["weights"]),
            "styles": sorted(payload["styles"]),
            "reasons": sorted(
                (
                    {
                        "rule_id": reason["rule_id"],
                        "reason": reason["reason"],
                        "matches": sorted(reason["matches"]),
                        "styles": sorted(reason["styles"]),
                    }
                    for reason in payload["reasons"].values()
                ),
                key=lambda item: item["rule_id"],
            ),
        }
    return result


def main() -> int:
    args = parse_args()

    try:
        rules = load_rules(args.rules)
        html_files = list_html_files(args.input_dir)
        result = {
            "version": 1,
            "rules": str(args.rules),
            "pages": [],
        }

        for html_path in html_files:
            elements = parse_usage(html_path)
            key = page_key(args.input_dir, html_path)
            fonts = analyze_page(rules, elements)
            result["pages"].append(
                {
                    "rel_permalink": key,
                    "fonts": fonts,
                }
            )
            if args.verbose:
                summary = {
                    family: payload["weights"] for family, payload in fonts.items()
                }
                print(f"{key} {summary}")

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        details = stderr or stdout
        if details:
            print(f"error: {exc}\n{details}", file=sys.stderr)
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
