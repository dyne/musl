#!/usr/bin/env bash
set -euo pipefail
[[ $# == 2 && $1 =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
    echo 'Usage: assert-release-tag.sh vX.Y.Z EXPECTED_COMMIT' >&2; exit 2;
}
tag_commit=$(git rev-parse --verify "refs/tags/$1^{commit}")
expected_commit=$(git rev-parse --verify "$2^{commit}")
[[ $tag_commit == "$expected_commit" ]] || {
    echo "Release tag $1 does not point to the validated commit" >&2; exit 1;
}
