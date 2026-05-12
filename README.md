# Image Builder Action

[![Build and publish](https://github.com/MArpogaus/image-builder-action/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/MArpogaus/image-builder-action/actions/workflows/build-and-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A state-of-the-art GitHub Action repository for building, pushing, and signing container images with SLSA Level 3 provenance.

## Features

- **Double-sided**: Use as a **Composite Action** (just build/push) or a **Reusable Workflow** (full SLSA chain).
- **Multi-platform support**: Build for `linux/amd64`, `linux/arm64`, etc.
- **SLSA Provenance**: Generates SLSA Level 3 provenance attestations.
- **Cosign Signing**: Signs images with a provided private key.
- **Base Image Verification**: Optionally verifies the provenance of the base image.
- **Disk Optimization**: Maximizes available disk space for large builds.
- **Caching**: Efficiently caches Podman layers.
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
    uses: MArpogaus/image-builder-action/.github/workflows/build-and-publish.yml@main
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

| Input                | Description                                     | Required | Default   |
|----------------------|-------------------------------------------------|----------|-----------|
| `image-name`         | Name of the image to be published               | **Yes**  | -         |
| `containerfile`      | Path to the Containerfile                       | **Yes**  | -         |
| `context`            | Build context directory                         | No       | `.`       |
| `platform`           | Target platform (e.g., `linux/amd64`)           | **Yes**  | -         |
| `slsa-verify-source` | Source URI for SLSA verification of base image  | No       | `''`      |
| `signing-secret`     | The `cosign` private key (for action.yml usage) | No*      | -         |
| `registry`           | The registry to push to                         | No       | `ghcr.io` |

For the reusable workflow, this is passed as a **secret** named `SIGNING_SECRET`.

## Security

This action is designed with security in mind:
- **Immutable Actions**: It uses hashes for most actions to prevent supply chain attacks.
- **SLSA Level 3**: Provides the highest level of build integrity for GitHub Actions.
- **OIDC**: Uses GitHub OIDC for signing and provenance.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
