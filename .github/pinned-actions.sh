#!/bin/bash
# Every GitHub action must be pinned to a commit sha. A tag moves, and the
# workflows here hand out a signing key and publish signed images.
#
# The comment is stripped first and the sha test is anchored to the end of the
# reference. A substring test anywhere on the line lets a comment whitewash an
# unpinned reference: `uses: evil/act@v1 # see slsa-github-generator` passed one.
set -euo pipefail

# The SLSA generator is the documented exception: the workflow it
# publishes provenance with must be a tag. See .pinact.yaml.

out="$(grep -HnE '^[[:space:]]*(-[[:space:]]*)?uses:' "$@" \
	| sed -E 's/[[:space:]]+#.*$//' \
	| grep -vE 'uses:[[:space:]]*\./' \
	| grep -vE 'uses:[[:space:]]*[^[:space:]@]+@[0-9a-f]{40}[[:space:]]*$' \
	| grep -vE 'uses:[[:space:]]*slsa-framework/slsa-github-generator/' || true)"
[ -z "${out}" ] || {
	echo "Action reference is not pinned to a commit sha:" >&2
	echo "${out}" >&2
	exit 1
}
