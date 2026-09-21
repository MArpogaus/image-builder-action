#!/usr/bin/env python3
"""Every GitHub action must be pinned to a commit sha.

A tag moves, and these workflows hand out a signing key and publish signed
images. Written as a parser rather than a chain of greps: two grep versions of
this check leaked bypasses, one where a comment whitewashed the line
(`uses: evil/act@v1 # see slsa-github-generator`) and one where YAML flow style
hid it from a line anchor (`- {uses: evil/act@v1}`).
"""

import re
import sys

# `uses:` anywhere on the line. The KEY may be quoted too -- GitHub accepts
# `"uses":`, the same way `"on":` is routinely quoted -- and the value may be
# quoted. The value ends at any character that closes a YAML scalar in block
# or flow style.
REF = re.compile(r"""uses['"]?\s*:\s*['"]?([^\s'"\],}#]+)""")
# A commit sha, or a digest for a docker:// reference.
PINNED = re.compile(r"^[^@]+@(?:[0-9a-f]{40}|sha256:[0-9a-f]{64})$")
LOCAL = re.compile(r"^\.{1,2}/")
# The SLSA generator is the documented exception: the workflow it publishes
# provenance with must be a tag. See .pinact.yaml. Anchored to the start of
# the reference so it cannot be spelled into a comment or a path traversal.
EXEMPT = re.compile(r"^slsa-framework/slsa-github-generator/(?!.*\.\.)[\w./-]+@v[\d.]+$")

bad = []
for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            # Strip a trailing comment. A reference never contains '#'.
            line = re.sub(r"\s#.*$", "", line.rstrip("\n"))
            for match in REF.finditer(line):
                ref = match.group(1)
                if LOCAL.match(ref) or EXEMPT.match(ref):
                    continue
                if not PINNED.match(ref):
                    bad.append(f"{path}:{number}: {ref}")

if bad:
    print("Action reference is not pinned to a commit sha:", file=sys.stderr)
    print("\n".join(bad), file=sys.stderr)
    sys.exit(1)
