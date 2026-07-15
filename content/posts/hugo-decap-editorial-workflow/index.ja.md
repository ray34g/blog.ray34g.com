---
title: Hugo と Decap CMS で編集者向けワークフローを作る
date: 2026-06-28
draft: true
description: Git ベースの静的サイトで、非エンジニアが安全に更新できる編集体験を作るための設計メモ。
techs:
  - Hugo
  - Decap CMS
  - GitLab
roles:
  - Frontend Engineering
  - Static Site Architecture
capabilities:
  - Editorial Workflow
  - Content Modeling
  - Multilingual Site
contexts:
  - Campaign Site
  - Production Website
---

Hugo と Decap CMS の組み合わせは、静的サイトの堅さと CMS の編集しやすさを両立できます。ただし、CMS を置けば自然に運用しやすくなるわけではありません。編集者が迷わない入力設計と、公開前に戻れる Git ワークフローが必要です。

## コンテンツモデルから始める

最初に決めるべきなのはテンプレートではなく、編集者が何を入力するかです。

たとえばニュース記事なら、タイトル、公開日、下書きフラグ、スラッグ、翻訳キー、本文、ヒーロー画像を分けて考えます。会場ページなら、住所、開催期間、アクセス、関連ニュースなど、再利用される情報を構造化します。

```yaml
fields:
  - name: title
    widget: string
  - name: date
    widget: datetime
  - name: draft
    widget: boolean
  - name: slug
    widget: string
  - name: translationKey
    widget: string
  - name: body
    widget: markdown
```

実運用では、自由入力を増やすほど編集の自由度は上がりますが、表示崩れや翻訳漏れも増えます。CMS のフィールド定義は、編集者を縛るためではなく、公開後に壊れにくくするためのガードレールです。

## 多言語では翻訳キーを先に決める

多言語サイトでは、URL、記事一覧、関連記事、公開日、翻訳状態が絡みます。日英で別々に記事を作れるだけでは不十分で、同じトピックの翻訳であることを機械的に追える必要があります。

そのため、各記事に共通の `translationKey` を持たせます。スラッグは言語ごとに変えても、翻訳キーは同じにします。これで CMS 上の一覧、Hugo 側の翻訳リンク、運用上の確認がつながりやすくなります。

## 公開前レビューを前提にする

編集者が保存した内容をすぐ本番に出すと、短期的には速く見えます。しかし、キャンペーンサイトでは関係者確認、日付修正、表記確認が頻繁に入ります。

そこで、CMS の editorial workflow や branch を使って、次のような段階を作ります。

```text
Draft
  -> Preview
  -> Release candidate
  -> Production
```

大切なのは、技術的な厳密さだけではなく、関係者が「今どこを見ればよいか」を迷わないことです。preview URL、反映タイミング、差し戻し方法は、ドキュメントとセットで設計します。

## 再利用できる形にするなら

将来的に theme や starter として切り出すなら、CMS config をそのまま再配布するのではなく、次のような部品に分けると扱いやすくなります。

- content type のサンプル
- i18n の命名規則
- preview/release 用の CI 例
- media folder の設計例
- editor 向け README

公開可能なテンプレートに落とすには、固有のブランド名や運用アカウントを完全に外す必要があります。まずはノートとして判断を公開し、汎用化できる部分だけを後から抽出するのが安全です。
