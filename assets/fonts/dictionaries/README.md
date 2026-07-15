These dictionary files are plain UTF-8 text. Every non-newline character present
in these files is force-included in generated subsets. Characters extracted from
Hugo HTML are reported as dictionary coverage gaps, but are not included in
generated subsets unless the builder is run with `--include-html-only`.

Files:
- `keyboard.txt`: half-width and full-width keyboard-friendly Latin letters,
  digits, and symbols.
- `japanese_symbols.txt`: common Japanese punctuation and UI symbols.
- `hiragana.txt`: hiragana set including small kana and iteration marks.
- `katakana.txt`: katakana set including small kana and iteration marks.
- `joyo_kanji.txt`: kanji extracted from the Agency for Cultural Affairs
  "常用漢字表の音訓索引" HTML table. The extracted file currently contains
  2132 characters from that index page. This broad kanji dictionary is used for
  Noto Sans JP, but LINE Seed JP subsets intentionally use only the smaller
  base dictionaries plus characters found in the built HTML.
- `site-extra.txt`: optional site-specific allowed characters. If this file is
  absent, the subset builder treats it as empty and prints a warning.
