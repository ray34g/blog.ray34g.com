---
title: 静的サイトの変更レポートを Playwright で作る
date: 2026-06-28
draft: true
description: preview と release の静的出力を比較し、スクリーンショット、差分、補助レポートをまとめるための設計メモ。
techs:
  - Playwright
  - pixelmatch
  - Lighthouse
  - Hugo
roles:
  - CI/CD
  - Frontend Engineering
capabilities:
  - Visual Regression Testing
  - Release Operations
  - Performance Auditing
contexts:
  - Production Website
  - Campaign Site
---

静的サイトの変更は、差分がコードだけに閉じません。Markdown の更新、画像の差し替え、テンプレート変更、CSS 修正、ビルド環境の差が、最終的な HTML と見た目に影響します。

そこで、公開前に「どのページがどう変わったか」を人が確認しやすい形にする変更レポートを作ります。

## 比較対象を静的出力にする

比較はソースではなく、ビルド済みの静的出力に対して行います。

```text
release/
  index.html
  ...

main/
  index.html
  ...

report/
  screenshots/
  diffs/
  report.json
  index.html
```

この形なら、Hugo のテンプレート、content、assets、config の変更をまとめて検査できます。レビューする人にとっても、ソース差分より画面差分の方が判断しやすい場面があります。

## Playwright でページを撮る

Playwright でローカル HTTP サーバーを立て、対象ページを desktop と mobile の viewport で撮影します。アニメーションや動画がある場合は、検査時だけ停止できるパラメータを用意しておくと差分が安定します。

重要なのは、スクリーンショットを撮ることそのものより、差分がノイズだらけにならないようにすることです。

- viewport を固定する
- アニメーションを止める
- network idle だけに頼らず、必要な待ち時間を置く
- hero video は poster に切り替えられるようにする
- 画像差分の許容閾値を決める

## レポートは人間が読むものにする

CI の成否だけでは、関係者レビューには足りません。スクリーンショット、差分画像、URL、エラー、Lighthouse や broken link check の補助結果を一つの HTML にまとめると、レビューの入口が一つになります。

このレポートは、完全自動判定というより、公開前レビューの負担を下げる道具です。特に短期間で更新が続くサイトでは、「見れば分かる」状態を作るだけで運用がかなり楽になります。

## ポートフォリオで語れること

この領域は、匿名化しても価値が残りやすいです。実名や画面を出さなくても、ワークフロー、比較対象、検査の安定化、レポート構造を説明できます。

実装を公開する場合は、プロジェクト固有の URL や除外ルールを取り除き、最小のサンプルサイトに対して動く形にするのがよさそうです。
