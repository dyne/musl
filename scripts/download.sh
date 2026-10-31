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
        if (count != 1 || url !~ /^(https?|git\+https):\/\//) exit 1;
        print url
    }' "$url_manifest") || { echo "Missing or invalid source URL entry: $key" >&2; exit 1; }
fi
mkdir -p "$(dirname "$destination")"
temporary=$(mktemp "$destination.tmp.XXXXXX")
git_temporary=
cleanup() {
    rm -f "$temporary"
    if [ -n "$git_temporary" ]; then rm -rf "$git_temporary"; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
case "$url" in
    git+*)
        # git+https://REPOSITORY#FULL_COMMIT:PATH avoids fragile web frontends.
        repository=${url#git+}
        object=${repository#*#}
        repository=${repository%%#*}
        revision=${object%%:*}
        source_path=${object#*:}
        case "$repository" in https://*|file://*) ;; *) echo 'Unsupported Git transport' >&2; exit 2;; esac
        case "$revision" in ''|*[!0-9a-f]*) echo 'Git source requires a full commit ID' >&2; exit 2;; esac
        if [ "${#revision}" -ne 40 ] || [ "$source_path" = "$object" ]; then
            echo 'Git source requires FULL_COMMIT:PATH' >&2; exit 2;
        fi
        case "$source_path" in ''|/*|..|../*|*/../*|*/..|*[!a-zA-Z0-9_./-]*)
            echo 'Invalid Git source path' >&2; exit 2;;
        esac
        command -v git >/dev/null
        command -v timeout >/dev/null
        git_temporary=$(mktemp -d "$destination.git.XXXXXX")
        git init --bare --quiet "$git_temporary"
        attempt=1
        until GIT_TERMINAL_PROMPT=0 timeout 120 git -C "$git_temporary" \
            -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=30 \
            fetch --quiet --no-tags --depth=1 "$repository" "$revision"; do
            if [ "$attempt" -eq 3 ]; then echo "Git source fetch failed: $key" >&2; exit 1; fi
            sleep "$attempt"
            attempt=$((attempt + 1))
        done
        [ "$(git -C "$git_temporary" cat-file -t "$revision:$source_path")" = blob ] || {
            echo 'Git source is not a file' >&2; exit 1;
        }
        git -C "$git_temporary" cat-file blob "$revision:$source_path" > "$temporary"
        ;;
    *)
        curl --fail --location --silent --show-error --retry 3 --connect-timeout 20 \
            --max-time 600 --output "$temporary" "$url"
        ;;
esac
verify "$temporary" || { echo "Downloaded source failed SHA-256 verification: $key" >&2; exit 1; }
chmod 644 "$temporary"
mv -f "$temporary" "$destination"
