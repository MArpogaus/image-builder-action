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
    uses: MArpogaus/image-builder-action/.github/workflows/reusable-build-and-publish-one-image.yml@7e52129c98111d7437960159061f3ab0b6fa2f33 # v1.6.0
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
      - uses: MArpogaus/image-builder-action@7e52129c98111d7437960159061f3ab0b6fa2f33 # v1.6.0
        with:
          image-name: my-cool-app
          containerfile: ./Containerfile
          platform: linux/amd64
          signing-secret: ${{ secrets.SIGNING_SECRET }}
```

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

## Outputs

| Output            | Description                                  |
|-------------------|----------------------------------------------|
| `full-image-ref`  | The pushed image reference including its tag |
| `image-digest`    | The digest of the pushed image               |

### Building several versions from one Containerfile

`overwrite-ref-tag` exists so a matrix can publish `:31`, `:32` and so on from
one file. Run the matrix with `max-parallel: 1`: every job also publishes
`latest`, and in parallel they overwrite each other's digest between signing
and verification, which fails as "no signatures found".

## Security

- Every action is pinned to a SHA except the SLSA generator, which verifies its
  own tag and refuses a digest ref.
- The SLSA generator signs provenance keyless through GitHub OIDC; images are
  signed with `SIGNING_SECRET`.
- `cosign-installer` stays on its v3 line (Cosign 2). With v4 the signature did
  not reach GHCR and `cosign verify` failed with "no signatures found".
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
