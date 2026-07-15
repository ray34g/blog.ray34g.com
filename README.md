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

## Validation

```sh
npm test
```

`npm run build:fast` performs the immediate single-pass build when reviewed
derived assets are available. `npm run build` performs the full two-pass asset and
font refresh. The migration Pages workflow intentionally uses the full path until
the two-stage fast/full reconciliation workflow is introduced.

Shared brand/theme changes arrive as reviewed backport pull requests from the
private upstream. This repository must never require private-upstream access at
build time.

## License

Code is licensed under the MIT License. Third-party notices are listed in
`THIRD_PARTY_NOTICES.md`.
