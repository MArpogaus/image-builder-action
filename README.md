# Image Builder Action

[![Build and publish](https://github.com/MArpogaus/image-builder-action/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/MArpogaus/image-builder-action/actions/workflows/build-and-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A GitHub Action that builds, pushes and signs container images with SLSA Level 3 provenance.

## Features

- **Two entry points**: a **Composite Action** (build and push) or a **Reusable Workflow** (the full SLSA chain).
- **Multi-platform support**: Build for `linux/amd64`, `linux/arm64`, etc.
- **SLSA Provenance**: Generates SLSA Level 3 provenance attestations.
- **Cosign Signing**: Signs images with a provided private key.
- **Base Image Verification**: Optionally verifies the provenance of the base image.
- **Disk Optimization**: Maximizes available disk space for large builds.
- **Caching**: Caches Podman layers.
- **Automatic Metadata**: Generates Docker labels and tags based on Git events.

---

## Usage Option 1: Reusable Workflow (Recommended)

This is the most secure way to build images, as it automatically generates **SLSA Level 3 provenance**.

```yaml
jobs:
  build:
    permissions:
      contents: read
      packages: write
      id-token: write
      actions: read
    uses: MArpogaus/image-builder-action/.github/workflows/reusable-build-and-publish-one-image.yml@v1.5.2
    with:
      image-name: my-cool-app
      containerfile: ./Containerfile
      platform: linux/amd64
    secrets:
      SIGNING_SECRET: ${{ secrets.SIGNING_SECRET }}
```

## Usage Option 2: Composite Action

Use this if you want to integrate the build/push logic into your own existing job. Note that this **does not** generate SLSA provenance on its own.

```yaml
jobs:
  my-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: MArpogaus/image-builder-action@main
        with:
          image-name: my-cool-app
          containerfile: ./Containerfile
          platform: linux/amd64
          signing-secret: ${{ secrets.SIGNING_SECRET }}
```

---

## Inputs

| Input                | Description                                                        | Required | Default   |
|----------------------|--------------------------------------------------------------------|----------|-----------|
| `image-name`         | Name of the image to be published                                  | **Yes**  | -         |
| `containerfile`      | Path to the Containerfile                                          | **Yes**  | -         |
| `platform`           | Target platform (e.g. `linux/amd64`)                               | **Yes**  | -         |
| `signing-secret`     | The cosign private key. A secret named `SIGNING_SECRET` for the reusable workflow | **Yes** | - |
| `context`            | Build context directory                                            | No       | `.`       |
| `registry`           | The registry to push to                                            | No       | `ghcr.io` |
| `slsa-verify-source` | Source URI for SLSA verification of the base image                 | No       | `''`      |
| `cosign-public-key`  | Public key, or a URL to one, to verify the base image's signature  | No       | `''`      |
| `build-args`         | Build arguments, newline-separated `KEY=VALUE`                     | No       | `''`      |
| `free-disk-space`    | Maximize build space by removing preinstalled tooling              | No       | `false`   |
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

This action is designed with security in mind:
- **Immutable Actions**: It uses hashes for most actions to prevent supply chain attacks.
- **SLSA Level 3**: Provides the highest level of build integrity for GitHub Actions.
- **OIDC**: Uses GitHub OIDC for signing and provenance.

## Development

```bash
pre-commit install --install-hooks -t pre-commit -t commit-msg -t pre-push
```

Plain `pre-commit install` wires up only the pre-commit stage, so the
commitizen message and branch checks stay dormant. Hooks: shellcheck,
pretty-format-yaml, commitizen for conventional commits.
CI runs the same set on push and pull request. Actions are pinned to SHAs, and
dependabot updates actions and hook revisions weekly against `dev`.

## License

MIT
