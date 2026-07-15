# Blog repository guide

This repository is the independent Hugo source for `blog.ray34g.com`.

- Use `npm run serve` for local development.
- Run `npm test` for a full build and generated-output verification.
- Use `npm run build:fast` only for the immediate deployment path.
- Keep Japanese and English navigation/content synchronized.
- Do not commit generated `public/`, `resources/`, analysis output, or secrets.
- Shared theme files are updated through explicit backport changes; blog content
  and blog-specific layouts remain owned here.
