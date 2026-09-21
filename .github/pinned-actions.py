#!/usr/bin/env python3
"""Every GitHub action must be pinned to a commit sha.

A tag moves, and these workflows hand out a signing key and publish signed
images. The file is parsed as YAML rather than scanned as text. Three text
versions of this check leaked bypasses in a row -- a comment whitewashing the
line, YAML flow style hiding it from a line anchor, then a `#` inside a quoted
string fooling the comment stripper -- and each fix moved the hole rather than
closing it. A parser has no such holes: it sees the same `uses` values GitHub
does, including flow style, quoted keys, anchors, aliases and wrapped values.
"""

import re
import sys

import yaml

# A commit sha, or a digest for a docker:// reference.
PINNED = re.compile(r"^[^@]+@(?:[0-9a-f]{40}|sha256:[0-9a-f]{64})$")
LOCAL = re.compile(r"^\.{1,2}/")
# The SLSA generator is the documented exception: the workflow it publishes
# provenance with must be a tag. See .pinact.yaml. Anchored to the whole
# reference, and no "..", so it cannot be spelled into a traversal.
EXEMPT = re.compile(r"^slsa-framework/slsa-github-generator/(?!.*\.\.)[\w./-]+@v[\d.]+$")


def uses_values(node):
    """Yield every value of a `uses` key, at any depth."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "uses" and isinstance(value, str):
                yield value
            yield from uses_values(value)
    elif isinstance(node, list):
        for value in node:
            yield from uses_values(value)


bad = []
for path in sys.argv[1:]:
    try:
        with open(path, encoding="utf-8") as handle:
            documents = list(yaml.safe_load_all(handle))
    except RecursionError:
        bad.append(f"{path}: cannot parse: nested too deeply")
        continue
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        bad.append(f"{path}: cannot parse: {error}")
        continue
    for document in documents:
        for ref in uses_values(document):
            ref = ref.strip()
            if LOCAL.match(ref) or ref == "." or EXEMPT.match(ref):
                continue
            if not PINNED.match(ref):
                bad.append(f"{path}: {ref}")

if bad:
    print("Action reference is not pinned to a commit sha:", file=sys.stderr)
    print("\n".join(bad), file=sys.stderr)
    sys.exit(1)
