# blog.ray34g.com

Hugo source for <https://blog.ray34g.com>. The repository is independently
buildable and publishes its own GitHub Pages artifact.

## Development

Open `/workspaces/workspace/ray34g-sites.code-workspace` to work on this repository
beside the private main/portal source repository in the same devcontainer.

```sh
npm ci
npm run serve
```

The server listens on <http://localhost:1315>.
Use `npm run serve:preview` to include draft and future-dated posts.

## Validation

```sh
npm test
npm run check:links
npm run lhci
```

## Content management

The lockfile-pinned Sveltia CMS editor is published at `/admin/` and writes to
this repository. It manages multilingual Posts and external-link Videos under
`content/posts/`; the private OAuth broker URL will be configured separately.

`npm run build:fast` performs the immediate single-pass build when reviewed
derived assets are available. `npm run build` performs the full two-pass asset and
font refresh. The migration Pages workflow intentionally uses the full path until
the two-stage fast/full reconciliation workflow is introduced.

Shared brand/theme changes arrive as reviewed backport pull requests from the
private upstream. This repository must never require private-upstream access at
build time.

`theme-backport.lock.json` records the exact upstream commit, Bootstrap version
and SHA-256 of every allowlisted shared file. `npm run verify:theme` checks it
against this repository's independent `config/theme-backport-policy.yaml` before
the production build.

## License

Code is licensed under the MIT License. Third-party notices are listed in
`THIRD_PARTY_NOTICES.md`.
