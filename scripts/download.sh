#!/bin/sh
# An empty URL selects MANIFEST_KEY from URL_MANIFEST.
# Usage: sh download.sh URL DESTINATION SHA256_MANIFEST [MANIFEST_KEY [URL_MANIFEST]]
# Verify cached files too. Never publish an incomplete or unverified download.
set -eu
if [ "$#" -lt 3 ] || [ "$#" -gt 5 ]; then
    echo 'Usage: download.sh URL DESTINATION SHA256_MANIFEST [MANIFEST_KEY [URL_MANIFEST]]' >&2
    exit 2
fi
url=$1
destination=$2
manifest=$3
key=${4:-${destination##*/}}
expected=$(awk -v key="$key" '$2 == key { hash=$1; count++ } END {
    if (count != 1 || length(hash) != 64 || hash ~ /[^0-9a-f]/) exit 1;
    print hash
}' "$manifest") || { echo "Missing or invalid SHA-256 entry: $key" >&2; exit 1; }

verify() {
    actual=$(sha256sum "$1") || return 1
    [ "${actual%% *}" = "$expected" ]
}

if [ -e "$destination" ]; then
    verify "$destination" || {
        echo "Cached source failed SHA-256 verification: $destination" >&2
        exit 1
    }
    exit 0
fi
if [ -z "$url" ]; then
    url_manifest=${5:?An empty URL requires a URL manifest}
    url=$(awk -v key="$key" '$1 == key { url=$2; count++ } END {
        if (count != 1 || url !~ /^https?:\/\//) exit 1;
        print url
    }' "$url_manifest") || { echo "Missing or invalid source URL entry: $key" >&2; exit 1; }
fi
mkdir -p "$(dirname "$destination")"
temporary=$(mktemp "$destination.tmp.XXXXXX")
trap 'rm -f "$temporary"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
curl --fail --location --silent --show-error --retry 3 --connect-timeout 20 \
    --max-time 600 --output "$temporary" "$url"
verify "$temporary" || { echo "Downloaded source failed SHA-256 verification: $key" >&2; exit 1; }
chmod 644 "$temporary"
mv -f "$temporary" "$destination"
