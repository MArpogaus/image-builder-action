# Image Builder Action

[![Build and publish](https://github.com/MArpogaus/image-builder-action/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/MArpogaus/image-builder-action/actions/workflows/build-and-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Composite action: build with buildah, push, sign with cosign, verify.
Reusable workflow: the same, plus SLSA level 3 provenance. Optional
verification of the base image by cosign key or SLSA source. Podman layers are
cached between runs, and tags and labels come from the Git event.

## Usage

Commit the public key that matches `SIGNING_SECRET` as `cosign.pub` in the
repository root. The verify step reads it from the checkout.

The reusable workflow builds, signs and attaches SLSA provenance:

```yaml
jobs:
  build:
    permissions:
      contents: read
      packages: write
      id-token: write
      actions: read
    uses: MArpogaus/image-builder-action/.github/workflows/reusable-build-and-publish-one-image.yml@v1.6.0
    with:
      image-name: my-cool-app
      containerfile: ./Containerfile
      platform: linux/amd64
    secrets:
      SIGNING_SECRET: ${{ secrets.SIGNING_SECRET }}
```

The composite action fits into an existing job. It produces no SLSA provenance
on its own.

```yaml
jobs:
  my-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: MArpogaus/image-builder-action@v1.6.0   # pin to the SHA in your own repo
        with:
          image-name: my-cool-app
          containerfile: ./Containerfile
          platform: linux/amd64
          signing-secret: ${{ secrets.SIGNING_SECRET }}
```

Every image carries `org.opencontainers.image.base.name` and
`org.opencontainers.image.base.digest`. A scheduled workflow can compare the
digest with the current base image and skip the build when nothing changed.

## Inputs

| Input                | Description                                                        | Required | Default   |
|----------------------|--------------------------------------------------------------------|----------|-----------|
| `image-name`         | Name of the image to be published                                  | **Yes**  | -         |
| `containerfile`      | Path to the Containerfile                                          | **Yes**  | -         |
| `platform`           | Target platform (e.g. `linux/amd64`)                               | **Yes**  | -         |
| `signing-secret`     | The cosign private key. A secret named `SIGNING_SECRET` for the reusable workflow | **Yes** | - |
| `context`            | Build context directory                                            | No       | `.`       |
| `registry`           | The registry to push to (not exposed by the reusable workflow)     | No       | `ghcr.io/<owner>` |
| `slsa-verify-source` | Source URI for SLSA verification of the base image                 | No       | `''`      |
| `cosign-public-key`  | Public key, or a URL to one, to verify the base image's signature  | No       | `''`      |
| `build-args`         | Build arguments, newline-separated `KEY=VALUE`                     | No       | `''`      |
| `free-disk-space`    | Maximize build space by removing preinstalled tooling              | No       | `true`    |
| `overwrite-ref-tag`  | Replace `{{branch}}` in generated tags, e.g. `31` gives `:31` and `:31-<sha>`. Use for a version matrix | No | `''` |
| `latest-tag`         | Also publish `:latest` from the default branch; a matrix sets it for its highest version only | No | `true` |

The base image is the last non-`scratch` `FROM` in the Containerfile. A
multi-stage build whose final stage starts from an earlier stage would hand a
stage name to the digest lookup, so this action expects the final `FROM` to
name a real image. A `FROM ${BASE}` is resolved from `build-args` only: give
the same value there even when the Containerfile has an `ARG` default, or the
digest lookup fails on the literal `${BASE}`.

## Outputs

| Output            | Description                                  |
|-------------------|----------------------------------------------|
| `full-image-ref`  | The pushed image reference including its tag |
| `image-digest`    | The digest of the pushed image               |

### Building several versions from one Containerfile

`overwrite-ref-tag` exists so a matrix can publish `:31`, `:32` and so on from
one file. Set `latest-tag` only for the highest version, otherwise `:latest`
is whichever job finished last. Two jobs publishing the same tag at once race
for which digest it ends up on, so `max-parallel: 1` is needed only when more
than one matrix entry can publish one: with `latest-tag` on a single entry and
a distinct `overwrite-ref-tag` per entry, the tag sets are disjoint and the
matrix can run in parallel.

## Security

- The reusable workflow pins this repo's own action by SHA, because a relative
  ref inside a reusable workflow resolves against the caller's checkout. Bump
  that pin before a release tag, or a consumer gets a workflow that calls an
  older action than the tag it took. `build-derived` and `build-overwrite-tag`
  call the action with `uses: ./` so the tree in a commit is exercised by its
  own CI; they get no SLSA provenance, which `build-basic` and `test-slsa`
  cover through the reusable workflow.
- Every action is pinned to a SHA except the SLSA generator, which verifies its
  own tag and refuses a digest ref. `pinact run` re-pins them; `.pinact.yaml`
  holds the rule that leaves the SLSA generator on its tag. It is not a
  pre-commit hook because pinact ships no hook manifest.
- The SLSA generator signs provenance keyless through GitHub OIDC; images are
  signed with `SIGNING_SECRET`.
- The base image digest is read with `skopeo`, which ships in the runner image,
  so it is trusted exactly as much as the runner's `buildah` and `curl`. The
  digest is a label, not a gate: the gates are `cosign-public-key` and
  `slsa-verify-source`, and `slsa-verifier` is installed only when one is set.
- `cosign-installer` stays on its v3 line (Cosign 2). With v4 the signature does
  not reach GHCR and `cosign verify` fails with "no signatures found".
  Dependabot ignores v4 in `.github/dependabot.yml`.

## Development

Work on `dev`. Conventional commits. Hooks: shellcheck, pretty-format-yaml,
commitizen. Setup:

```bash
pre-commit install --install-hooks -t pre-commit -t commit-msg -t pre-push
```

Plain `pre-commit install` wires up the pre-commit stage only, which leaves the
commit-message and branch hooks dormant. CI runs the same hooks on push and
pull request. Dependabot updates the actions and the hook revisions weekly
against `dev`.

## License

MIT
