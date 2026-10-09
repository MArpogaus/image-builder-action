# Image Builder Action

[![Build and publish](https://github.com/MArpogaus/image-builder-action/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/MArpogaus/image-builder-action/actions/workflows/build-and-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Composite action: build with buildah, push, sign with cosign, verify.
Workflow template: the same, plus SLSA level 3 provenance, in a copyable
file. Optional verification of the base image by cosign key or SLSA source.
Podman layers are cached between runs, and tags and labels come from the Git
event.

## Usage

Commit the public key that matches `SIGNING_SECRET` as `cosign.pub` in the
repository root. The verify step reads it from the checkout.

For build, signing and SLSA provenance, copy
`.github/workflows/reusable-build-and-publish-one-image.yml` into your
`.github/workflows/`, replace its `uses: ./` with a SHA pin of this action,
and call it per matrix entry:

```yaml
jobs:
  build:
    permissions:
      contents: read
      packages: write
      id-token: write
      actions: read
    uses: ./.github/workflows/reusable-build-and-publish-one-image.yml
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
      - uses: MArpogaus/image-builder-action@v1.7.0   # pin to the SHA in your own repo
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

Every non-scratch `FROM` image is resolved, verified and pinned. See
"Base images".

## Outputs

| Output            | Description                                  |
|-------------------|----------------------------------------------|
| `full-image-ref`  | The pushed image reference including its tag |
| `image-digest`    | The digest of the pushed image               |

### Building several versions from one Containerfile

`overwrite-ref-tag` exists so a matrix can publish `:31`, `:32` and so on from
one file. Set `latest-tag` only for the highest version. Otherwise `:latest` is
whichever job finished last. Two jobs that publish one tag at once race for its
digest. Set `max-parallel: 1` only when more than one matrix entry can publish
the same tag. One entry with `latest-tag` and a distinct `overwrite-ref-tag`
per entry make the tag sets disjoint, and the matrix can run in parallel.

## Security

- The provenance workflow is a template carrying `uses: ./`. It runs as it is
  in this repo's CI and fails when called directly from another repository, so
  a consumer can never silently get a stale action. Callers copy the file and
  pin it by SHA. Every CI job, including the ones going through the template,
  runs the commit's own action tree.
- Every action is pinned to a SHA except the SLSA generator, which verifies its
  own tag and refuses a digest ref. `pinact run -u` updates and re-pins them.
  `.pinact.yaml` holds two rules: the SLSA generator stays on its tag, and
  `cosign-installer` stays on v3.
- The SLSA generator signs provenance keyless through GitHub OIDC. Images are
  signed with `SIGNING_SECRET`.
- A pull request reaches the build jobs with an empty signing key. Those jobs
  run the action from the pull request's own head. The `if:` that holds the
  signing step back therefore sits in a file the pull request can edit. Only a
  branch in this repository carries the repository's secrets, so the ref is the
  gate.
- Base digests are read with `skopeo`. That tool ships in the runner image,
  so it is trusted as much as the runner's `buildah` and `curl`. Verification
  gates on `cosign-public-key` and `slsa-verify-source`. Pinning to the
  resolved digest happens either way.
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

## Base images

Every `FROM` image in the Containerfile is resolved, verified and pinned
before the build. `FROM scratch` helper stages are exempt. They carry build
files and have no base.

1. Each image reference resolves with `build-args`. A `FROM ${BASE}` needs
   its value there, even when the Containerfile has an `ARG` default.
   Without it the digest lookup fails on the literal `${BASE}`.
2. `skopeo` reads the current digest. When `cosign-public-key` or
   `slsa-verify-source` is set, that digest is verified with it. One key
   and one source cover all bases.
3. The step rewrites the `FROM` line to `<image>@<digest>` in the
   checkout's Containerfile, so the build runs on exactly what was
   verified.

`org.opencontainers.image.base.name` and `org.opencontainers.image.base.digest`
describe the last stage's base, the base of the published image.

The `FROM` match is deliberately permissive. Any line that opens like
`FROM` counts, also one inside a `RUN` heredoc. Such a line is treated as
a base and breaks the build, so reword it. Over-counting refuses or
breaks a build, under-counting ships an unverified base.

## License

MIT
