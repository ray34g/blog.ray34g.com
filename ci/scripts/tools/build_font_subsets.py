#!/usr/bin/env python3
"""Build subset fonts for this site from generated Hugo HTML."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_EXTRA_CHARS = " "
DEFAULT_DICTIONARY_DIR = Path("assets/fonts/dictionaries")
DEFAULT_LANGUAGES = ("ja", "en")
LANGUAGE_DICTIONARY_FILES = {
    "ja": [
        "keyboard.txt",
        "japanese_symbols.txt",
        "hiragana.txt",
        "katakana.txt",
        "joyo_kanji.txt",
        "site-extra.txt",
    ],
    "en": [
        "keyboard.txt",
        "japanese_symbols.txt",
        "site-extra.txt",
    ],
}
TARGET_DICTIONARY_FILE_OVERRIDES = {
    ("line-seed-jp", "ja"): [
        "keyboard.txt",
        "japanese_symbols.txt",
        "hiragana.txt",
        "katakana.txt",
        "site-extra.txt",
    ],
}

IGNORED_TAGS = {"script", "style", "noscript", "template"}
EMOJI_RANGES = (
    (0x200D, 0x200D),
    (0xFE0E, 0xFE0F),
    (0x1F300, 0x1F5FF),
    (0x1F600, 0x1F64F),
    (0x1F680, 0x1F6FF),
    (0x1F900, 0x1F9FF),
    (0x1FA70, 0x1FAFF),
)


@dataclass(frozen=True)
class FontVariant:
    key: str
    base_name: str
    weight: int
    source: Path
    style: str = "normal"
    variable_weight: int | None = None


FONT_TARGETS = {
    "noto": [
        FontVariant(
            key="noto-sans-jp-300",
            base_name="noto-sans-jp",
            weight=300,
            source=Path("assets/fonts/source/noto-sans-jp/NotoSansJP-VariableFont_wght.ttf"),
            variable_weight=300,
        ),
        FontVariant(
            key="noto-sans-jp-400",
            base_name="noto-sans-jp",
            weight=400,
            source=Path("assets/fonts/source/noto-sans-jp/NotoSansJP-VariableFont_wght.ttf"),
            variable_weight=400,
        ),
        FontVariant(
            key="noto-sans-jp-500",
            base_name="noto-sans-jp",
            weight=500,
            source=Path("assets/fonts/source/noto-sans-jp/NotoSansJP-VariableFont_wght.ttf"),
            variable_weight=500,
        ),
        FontVariant(
            key="noto-sans-jp-600",
            base_name="noto-sans-jp",
            weight=600,
            source=Path("assets/fonts/source/noto-sans-jp/NotoSansJP-VariableFont_wght.ttf"),
            variable_weight=600,
        ),
        FontVariant(
            key="noto-sans-jp-700",
            base_name="noto-sans-jp",
            weight=700,
            source=Path("assets/fonts/source/noto-sans-jp/NotoSansJP-VariableFont_wght.ttf"),
            variable_weight=700,
        ),
        FontVariant(
            key="noto-sans-jp-900",
            base_name="noto-sans-jp",
            weight=900,
            source=Path("assets/fonts/source/noto-sans-jp/NotoSansJP-VariableFont_wght.ttf"),
            variable_weight=900,
        ),
    ],
    "line-seed": [
        FontVariant(
            key="line-seed-jp-300",
            base_name="line-seed-jp",
            weight=300,
            source=Path("assets/fonts/source/line-seed-jp/LINESeedJP-Thin.ttf"),
        ),
        FontVariant(
            key="line-seed-jp-400",
            base_name="line-seed-jp",
            weight=400,
            source=Path("assets/fonts/source/line-seed-jp/LINESeedJP-Regular.ttf"),
        ),
        FontVariant(
            key="line-seed-jp-500",
            base_name="line-seed-jp",
            weight=500,
            source=Path("assets/fonts/source/line-seed-jp/LINESeedJP-Regular.ttf"),
        ),
        FontVariant(
            key="line-seed-jp-600",
            base_name="line-seed-jp",
            weight=600,
            source=Path("assets/fonts/source/line-seed-jp/LINESeedJP-Bold.ttf"),
        ),
        FontVariant(
            key="line-seed-jp-700",
            base_name="line-seed-jp",
            weight=700,
            source=Path("assets/fonts/source/line-seed-jp/LINESeedJP-ExtraBold.ttf"),
        ),
    ],
    "poppins": [
        FontVariant(
            key="poppins-300",
            base_name="poppins",
            weight=300,
            source=Path("assets/fonts/source/poppins/Poppins-Light.ttf"),
        ),
        FontVariant(
            key="poppins-400",
            base_name="poppins",
            weight=400,
            source=Path("assets/fonts/source/poppins/Poppins-Regular.ttf"),
        ),
        FontVariant(
            key="poppins-400-italic",
            base_name="poppins",
            weight=400,
            source=Path("assets/fonts/source/poppins/Poppins-Italic.ttf"),
            style="italic",
        ),
        FontVariant(
            key="poppins-500",
            base_name="poppins",
            weight=500,
            source=Path("assets/fonts/source/poppins/Poppins-Medium.ttf"),
        ),
        FontVariant(
            key="poppins-600",
            base_name="poppins",
            weight=600,
            source=Path("assets/fonts/source/poppins/Poppins-SemiBold.ttf"),
        ),
        FontVariant(
            key="poppins-700",
            base_name="poppins",
            weight=700,
            source=Path("assets/fonts/source/poppins/Poppins-Bold.ttf"),
        ),
        FontVariant(
            key="poppins-800",
            base_name="poppins",
            weight=800,
            source=Path("assets/fonts/source/poppins/Poppins-ExtraBold.ttf"),
        ),
    ],
}


class VisibleTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._ignored_stack: list[bool] = []
        self.parts: list[str] = []
        self.document_lang = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "html" and not self.document_lang:
            attr_map = dict(attrs)
            self.document_lang = normalize_lang(attr_map.get("lang", ""))

        ignored = tag in IGNORED_TAGS or any(name == "hidden" for name, _ in attrs)
        self._ignored_stack.append(ignored)
        if ignored:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        ignored = self._ignored_stack.pop() if self._ignored_stack else tag in IGNORED_TAGS
        if ignored and self._ignored_depth > 0:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0 and data:
            self.parts.append(data)

    def get_text(self) -> str:
        return "".join(self.parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build subset fonts from generated Hugo HTML."
    )
    parser.add_argument("--input-dir", required=True, type=Path, help="Directory containing generated HTML files.")
    parser.add_argument("--output-dir", default=Path("assets/fonts/subsets"), type=Path, help="Directory to write subset font files into.")
    parser.add_argument("--families", nargs="+", choices=("noto", "line-seed", "poppins", "all"), default=("all",), help="Font families to build.")
    parser.add_argument("--languages", nargs="+", default=DEFAULT_LANGUAGES, help="Languages to build subsets for, for example ja en.")
    parser.add_argument("--extra-chars", default=DEFAULT_EXTRA_CHARS, help="Additional characters to force-include in every subset.")
    parser.add_argument("--dictionary-dir", default=DEFAULT_DICTIONARY_DIR, type=Path, help="Directory containing plain-text dictionary files to include.")
    parser.add_argument("--dictionary-files", nargs="*", default=None, help="Specific dictionary filenames to load. Defaults to all *.txt files in the dictionary directory.")
    parser.add_argument("--exclude-emoji", action="store_true", help="Exclude common emoji codepoint ranges from subset generation.")
    parser.add_argument("--fail-on-html-only", action="store_true", help="Exit with code 1 when HTML contains characters not covered by dictionaries.")
    parser.add_argument("--include-html-only", action="store_true", help="Include HTML-only characters in subset generation for backward compatibility.")
    parser.add_argument("--max-bytes", default=1_000_000, type=int, help="Soft size limit used for reporting.")
    parser.add_argument("--manifest", default=Path("assets/fonts/subsets/manifest.json"), type=Path, help="JSON manifest path written after generation.")
    parser.add_argument("--verbose", action="store_true", help="Print extracted character statistics.")
    return parser.parse_args()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_existing_manifest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def ensure_pyftsubset() -> str:
    pyftsubset = shutil.which("pyftsubset")
    if pyftsubset:
        return pyftsubset
    raise FileNotFoundError("pyftsubset was not found in PATH.")


def normalize_lang(lang: str) -> str:
    value = (lang or "").strip().lower()
    if not value:
        return ""
    return re.split(r"[-_]", value)[0]


def normalize_subset_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r", "\n")
    text = text.replace("\t", " ")
    text = text.replace("\u00A0", " ")
    text = text.replace("\u202F", " ")
    return text


def normalize_dictionary_text(text: str) -> str:
    text = normalize_subset_text(text)
    return text.replace("\n", "")


def extract_page_data(html_path: Path) -> tuple[str, str]:
    parser = VisibleTextExtractor()
    parser.feed(html_path.read_text(encoding="utf-8"))
    parser.close()
    return parser.document_lang, normalize_subset_text(html.unescape(parser.get_text()))


def collect_chars_by_language(input_dir: Path, extra_chars: str, languages: list[str]) -> dict[str, str]:
    chars_by_lang = {lang: set(extra_chars) for lang in languages}
    html_files = sorted(input_dir.rglob("*.html"))
    if not html_files:
        raise FileNotFoundError(f"No HTML files found under {input_dir}")

    for html_file in html_files:
        lang, text = extract_page_data(html_file)
        if lang in chars_by_lang:
            chars_by_lang[lang].update(char for char in text if char != "\n")

    return {lang: "".join(sorted(chars)) for lang, chars in chars_by_lang.items()}


def load_dictionary_chars(dictionary_dir: Path, dictionary_files: list[str] | None, lang: str) -> tuple[str, list[str]]:
    if not dictionary_dir.exists():
        return "", []

    if dictionary_files:
        paths = [dictionary_dir / name for name in dictionary_files]
    else:
        file_names = LANGUAGE_DICTIONARY_FILES.get(lang, [])
        paths = [dictionary_dir / name for name in file_names]

    chars: set[str] = set()
    loaded: list[str] = []

    for path in paths:
        if not path.exists():
            if path.name == "site-extra.txt":
                print(
                    f"warning: optional dictionary file was not found and will be treated as empty: {path}",
                    file=sys.stderr,
                )
                continue
            raise FileNotFoundError(f"Dictionary file was not found: {path}")
        chars.update(normalize_dictionary_text(path.read_text(encoding="utf-8")))
        loaded.append(path.name)

    return "".join(sorted(chars)), loaded


def get_dictionary_files_for_target(args: argparse.Namespace, lang: str, target: FontVariant | None) -> list[str] | None:
    if args.dictionary_files is not None:
        return args.dictionary_files
    if target is None:
        return None
    return TARGET_DICTIONARY_FILE_OVERRIDES.get((target.base_name, lang))


def build_char_profile(
    args: argparse.Namespace,
    lang: str,
    content_chars: str,
    dictionary_files: list[str] | None,
    force_include_html_only: bool = False,
) -> tuple[str, dict[str, object], bool]:
    dictionary_chars, loaded_dictionary_files = load_dictionary_chars(args.dictionary_dir, dictionary_files, lang)
    content_set = set(content_chars)
    dictionary_set = set(dictionary_chars) | set(args.extra_chars)

    diff_content_set = content_set
    diff_dictionary_set = dictionary_set
    if args.exclude_emoji:
        filtered_content_chars, _ = filter_emoji("".join(sorted(content_set)))
        filtered_dictionary_chars, _ = filter_emoji("".join(sorted(dictionary_set)))
        diff_content_set = set(filtered_content_chars)
        diff_dictionary_set = set(filtered_dictionary_chars)

    html_only_chars = sorted(diff_content_set - diff_dictionary_set)
    dictionary_only_chars = sorted(diff_dictionary_set - diff_content_set)
    shared_chars = sorted(diff_content_set & diff_dictionary_set)

    include_html_only = args.include_html_only or force_include_html_only
    if include_html_only:
        chars = "".join(sorted(content_set | dictionary_set))
        subset_source = "dictionary_plus_html"
    else:
        chars = "".join(sorted(dictionary_set))
        subset_source = "dictionary"

    emoji_removed_chars: list[str] = []
    if args.exclude_emoji:
        chars, emoji_removed_chars = filter_emoji(chars)

    profile = {
        "char_count": len(chars),
        "chars_sha256": sha256_text(chars),
        "content_char_count": len(content_chars),
        "content_chars_sha256": sha256_text(content_chars),
        "dictionary_char_count": len(dictionary_chars),
        "dictionary_chars_sha256": sha256_text(dictionary_chars),
        "dictionary_files": loaded_dictionary_files,
        "subset_source": subset_source,
        "include_html_only": include_html_only,
        "fail_on_html_only": args.fail_on_html_only,
        "emoji_removed_count": len(emoji_removed_chars),
        "emoji_removed_lines": group_chars(emoji_removed_chars),
        "diff": {
            "html_only_count": len(html_only_chars),
            "dictionary_only_count": len(dictionary_only_chars),
            "shared_count": len(shared_chars),
            "html_only_lines": group_chars(html_only_chars),
            "dictionary_only_lines": group_chars(dictionary_only_chars),
        },
    }
    return chars, profile, bool(html_only_chars)


def group_chars(chars: list[str], line_width: int = 80) -> list[str]:
    if not chars:
        return []
    return ["".join(chars[index : index + line_width]) for index in range(0, len(chars), line_width)]


def is_emoji_char(char: str) -> bool:
    codepoint = ord(char)
    for start, end in EMOJI_RANGES:
        if start <= codepoint <= end:
            return True
    return False


def filter_emoji(chars: str) -> tuple[str, list[str]]:
    kept: list[str] = []
    removed: list[str] = []
    for char in chars:
        if is_emoji_char(char):
            removed.append(char)
        else:
            kept.append(char)
    return "".join(kept), sorted(set(removed))


def resolve_targets(families: tuple[str, ...] | list[str]) -> list[FontVariant]:
    if "all" in families:
        families = ("noto", "line-seed", "poppins")

    targets: list[FontVariant] = []
    for family in families:
        targets.extend(FONT_TARGETS[family])
    return targets


def chars_to_unicode_ranges(chars: str) -> list[str]:
    if not chars:
        return []

    codepoints = sorted({ord(char) for char in chars})
    ranges: list[str] = []
    start = prev = codepoints[0]

    for codepoint in codepoints[1:]:
        if codepoint == prev + 1:
            prev = codepoint
            continue
        ranges.append(format_range(start, prev))
        start = prev = codepoint

    ranges.append(format_range(start, prev))
    return ranges


def format_range(start: int, end: int) -> str:
    if start == end:
        return f"U+{start:04X}"
    return f"U+{start:04X}-U+{end:04X}"


def portable_path(path: Path) -> str:
    """Return a stable repository-relative path when possible."""
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def run_subset(pyftsubset_bin: str, target: FontVariant, output_path: Path, chars: str) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
        tmp.write(chars)
        tmp_path = Path(tmp.name)

    try:
        source_font = target.source
        instance_path: Path | None = None
        variable_subset_path: Path | None = None
        if target.variable_weight is not None:
            # Subset the variable font before instancing it. Noto Sans JP has
            # tens of thousands of glyphs; instancing the complete source for
            # every weight is needlessly expensive in CI.
            with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as variable_subset:
                variable_subset_path = Path(variable_subset.name)
            subprocess.run(
                [
                    pyftsubset_bin,
                    str(target.source),
                    f"--text-file={tmp_path}",
                    f"--output-file={variable_subset_path}",
                    "--layout-features=*",
                    "--no-hinting",
                    "--notdef-glyph",
                    "--recommended-glyphs",
                ],
                check=True,
            )
            with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as instance:
                instance_path = Path(instance.name)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "fontTools.varLib.instancer",
                    str(variable_subset_path),
                    f"wght={target.variable_weight}",
                    "--static",
                    "--no-recalc-timestamp",
                    "--quiet",
                    f"--output={instance_path}",
                ],
                check=True,
            )
            source_font = instance_path

        subprocess.run(
            [
                pyftsubset_bin,
                str(source_font),
                f"--text-file={tmp_path}",
                "--flavor=woff2",
                f"--output-file={output_path}",
                "--layout-features=*",
                "--no-hinting",
                "--notdef-glyph",
                "--recommended-glyphs",
            ],
            check=True,
        )
    finally:
        tmp_path.unlink(missing_ok=True)
        if "instance_path" in locals() and instance_path is not None:
            instance_path.unlink(missing_ok=True)
        if "variable_subset_path" in locals() and variable_subset_path is not None:
            variable_subset_path.unlink(missing_ok=True)


def main() -> int:
    args = parse_args()

    try:
        pyftsubset_bin = ensure_pyftsubset()
        targets = resolve_targets(args.families)
        languages = [normalize_lang(lang) for lang in args.languages]
        content_chars_by_lang = collect_chars_by_language(args.input_dir, args.extra_chars, languages)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        existing_manifest = load_existing_manifest(args.manifest)

        manifest: dict[str, object] = {
            "dictionary_dir": str(args.dictionary_dir),
            "exclude_emoji": args.exclude_emoji,
            "languages": {},
            "target_char_sets": {},
            "targets": {},
        }
        html_only_detected = False
        char_profiles: dict[tuple[str, str], tuple[str, dict[str, object], bool]] = {}

        for lang in languages:
            content_chars = content_chars_by_lang.get(lang, args.extra_chars)
            chars, language_profile, has_html_only = build_char_profile(
                args=args,
                lang=lang,
                content_chars=content_chars,
                dictionary_files=get_dictionary_files_for_target(args, lang, None),
            )
            char_profiles[(lang, "default")] = (chars, language_profile, has_html_only)

            if has_html_only:
                html_only_detected = True
                print(
                    f"warning: [{lang}] HTML contains characters not covered by dictionaries: "
                    f"{''.join(language_profile['diff']['html_only_lines'])}. "
                    f"Add them to {args.dictionary_dir / 'site-extra.txt'} if they are allowed site characters.",
                    file=sys.stderr,
                )

            manifest["languages"][lang] = language_profile

            if args.verbose:
                print(f"[{lang}] Collected {len(chars)} unique characters from {args.input_dir}")
                print(f"[{lang}] Included {language_profile['dictionary_char_count']} dictionary characters from {len(language_profile['dictionary_files'])} files")
                print(
                    f"[{lang}] HTML-only chars: {language_profile['diff']['html_only_count']}, "
                    f"dictionary-only chars: {language_profile['diff']['dictionary_only_count']}, "
                    f"shared chars: {language_profile['diff']['shared_count']}"
                )
                if args.exclude_emoji:
                    print(f"[{lang}] Excluded {language_profile['emoji_removed_count']} emoji characters")

            for target in targets:
                target_profile_key = f"{target.base_name}.{lang}"
                target_dictionary_files = get_dictionary_files_for_target(args, lang, target)
                if target_dictionary_files is None:
                    target_chars, target_profile, _ = char_profiles[(lang, "default")]
                else:
                    cache_key = (lang, target.base_name)
                    if cache_key not in char_profiles:
                        char_profiles[cache_key] = build_char_profile(
                            args=args,
                            lang=lang,
                            content_chars=content_chars,
                            dictionary_files=target_dictionary_files,
                            force_include_html_only=True,
                        )
                        manifest["target_char_sets"][target_profile_key] = char_profiles[cache_key][1]
                    target_chars, target_profile, _ = char_profiles[cache_key]

                output = build_single_subset(
                    pyftsubset_bin=pyftsubset_bin,
                    target=target,
                    chars=target_chars,
                    chars_sha256=target_profile["chars_sha256"],
                    output_dir=args.output_dir,
                    max_bytes=args.max_bytes,
                    lang=lang,
                    existing_manifest=existing_manifest,
                )
                manifest["targets"][output["key"]] = {
                    "lang": lang,
                    "weight": target.weight,
                    "style": target.style,
                    "source": portable_path(target.source),
                    "source_sha256": output["source_sha256"],
                    "output": output["output"],
                    "size_bytes": output["size_bytes"],
                    "size_limit_bytes": output["size_limit_bytes"],
                    "status": output["status"],
                    "char_count": output["char_count"],
                    "chars_sha256": output["chars_sha256"],
                    "unicode_ranges": output["unicode_ranges"],
                }
                action = "reused" if output["reused_existing_file"] else "built"
                print(f"{output['key']}: {output['size_bytes']} bytes ({output['status']}, {action})")

        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.fail_on_html_only and html_only_detected:
        return 1

    return 0


def build_single_subset(
    pyftsubset_bin: str,
    target: FontVariant,
    chars: str,
    chars_sha256: str,
    output_dir: Path,
    max_bytes: int,
    lang: str,
    existing_manifest: dict[str, object],
) -> dict[str, object]:
    if not chars:
        raise ValueError("No characters were collected for subset generation.")

    subset_chars = "".join(sorted(chars))
    style_suffix = "" if target.style == "normal" else f"-{target.style}"
    output_path = output_dir / f"{target.base_name}-{target.weight}{style_suffix}.{lang}.woff2"
    unicode_ranges = chars_to_unicode_ranges(subset_chars)
    source_sha256 = sha256_file(target.source)
    reused_existing_file = can_reuse_existing_subset(
        existing_manifest=existing_manifest,
        key=f"{target.key}.{lang}",
        output_path=output_path,
        chars_sha256=chars_sha256,
        char_count=len(subset_chars),
        unicode_ranges=unicode_ranges,
        source=target.source,
        source_sha256=source_sha256,
        max_bytes=max_bytes,
    )

    if not reused_existing_file:
        run_subset(pyftsubset_bin, target, output_path, subset_chars)

    size_bytes = output_path.stat().st_size

    return {
        "key": f"{target.key}.{lang}",
        "output": portable_path(output_path),
        "size_bytes": size_bytes,
        "size_limit_bytes": max_bytes,
        "status": "ok" if size_bytes <= max_bytes else "over-limit",
        "char_count": len(subset_chars),
        "chars_sha256": chars_sha256,
        "source_sha256": source_sha256,
        "unicode_ranges": unicode_ranges,
        "reused_existing_file": reused_existing_file,
    }


def can_reuse_existing_subset(
    existing_manifest: dict[str, object],
    key: str,
    output_path: Path,
    chars_sha256: str,
    char_count: int,
    unicode_ranges: list[str],
    source: Path,
    source_sha256: str,
    max_bytes: int,
) -> bool:
    if not output_path.exists():
        return False

    targets = existing_manifest.get("targets")
    if not isinstance(targets, dict):
        return False

    existing_target = targets.get(key)
    if not isinstance(existing_target, dict):
        return False

    if existing_target.get("output") != portable_path(output_path):
        return False
    if existing_target.get("source") != portable_path(source):
        return False
    if existing_target.get("size_limit_bytes") != max_bytes:
        return False

    existing_chars_sha256 = existing_target.get("chars_sha256")
    if existing_chars_sha256 is not None:
        if existing_chars_sha256 != chars_sha256:
            return False
    else:
        if existing_target.get("char_count") != char_count:
            return False
        if existing_target.get("unicode_ranges") != unicode_ranges:
            return False

    existing_source_sha256 = existing_target.get("source_sha256")
    if existing_source_sha256 is not None and existing_source_sha256 != source_sha256:
        return False

    return True


if __name__ == "__main__":
    raise SystemExit(main())
