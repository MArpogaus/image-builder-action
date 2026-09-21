#!/bin/bash
# Every GitHub action must be pinned to a commit sha. A tag moves, and the
# workflows here hand out a signing key and publish signed images.
set -euo pipefail

# The SLSA generator is the documented exception: the workflow it
# publishes provenance with must be a tag. See .pinact.yaml.

out="$(grep -Hn 'uses:' "$@" | grep -v 'uses: \./' | grep -vE '@[0-9a-f]{40}' | grep -v slsa-github-generator || true)"
[ -z "${out}" ] || {
	echo "Action reference is not pinned to a commit sha:" >&2
	echo "${out}" >&2
	exit 1
}
