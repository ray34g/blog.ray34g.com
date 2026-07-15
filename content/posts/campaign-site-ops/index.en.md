---
title: Operating a Short-Running Campaign Site as a Static Site
date: 2026-06-28
description: An anonymized architecture note about running a multilingual campaign site with static-site generation and editor-friendly workflows.
techs:
  - Hugo
  - GitLab CI
  - Decap CMS
roles:
  - Static Site Architecture
  - CI/CD
  - Technical Writing
capabilities:
  - Editorial Workflow
  - Multilingual Site
  - Release Operations
contexts:
  - Campaign Site
  - Nonprofit
  - Production Website
---

This note extracts reusable technical lessons from a real production campaign site while omitting names, partner details, private URLs, and operational information that should not be public.

The core pattern is simple: editors update structured content, Git keeps the history, CI builds static output, and reviewers inspect preview or release variants before production.

```text
Editor
  -> CMS
  -> Git repository
  -> CI build
  -> Preview / Release / Production
```

The interesting work is not only the site implementation. It is the operating model around it: content modeling, multilingual URLs, preview review, release checks, documentation, and a rollback-friendly publishing path.

Keeping the source project anonymous does not remove the value. The value is in the decisions that can be reused.
