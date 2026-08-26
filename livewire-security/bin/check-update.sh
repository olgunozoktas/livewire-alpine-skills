#!/usr/bin/env bash
# Report a newer release of these skills, and say nothing in every other case.
#
# WHY THIS FAILS OPEN, ALWAYS
#
# A skill that interrupts a person because GitHub is slow is worse than a skill
# that never mentions updates. Every failure path is silent: no network, a rate
# limit, a proxy, a missing tool, a malformed answer, a poisoned cache. The
# script prints one line when a newer release exists, and nothing otherwise.
#
# It also caches, because without a cache it would reach the network on every
# skill invocation.
#
# WHAT IT SENDS
#
# One unauthenticated GET for a plain text file on raw.githubusercontent.com.
# No identifier, no telemetry, no project data. The whole request is the curl
# line below.
#
# The exit code is always 0. This script never fails a caller.

set -u

REPO="olgunozoktas/livewire-alpine-skills"
REMOTE_URL="https://raw.githubusercontent.com/${REPO}/main/VERSION"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/livewire-alpine-skills"
CACHE_FILE="$CACHE_DIR/last-check"
MAX_AGE_HOURS="${LW_SKILLS_CHECK_HOURS:-24}"

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# A version string is digits and dots. Anything else is treated as no answer —
# a proxy error page must never become a version.
is_version() {
    case "${1:-}" in
        ''|*[!0-9.]*) return 1 ;;
        *) return 0 ;;
    esac
}

# The local version. VERSION first, then a skill's frontmatter, so the check
# still works when somebody copied one skill directory on its own.
read_local_version() {
    local candidate version

    # THE SKILL'S OWN FRONTMATTER FIRST.
    #
    # A person copies one skill directory into ~/.claude/skills/. The repository
    # root does not travel with it, so a VERSION file there cannot be relied on.
    # `SKILL.md` always travels, because it IS the skill.
    if [ -f "$here/../SKILL.md" ]; then
        version="$(sed -n 's/^version: *//p' "$here/../SKILL.md" | head -1 | tr -d ' \t\r\n')"
        if [ -n "$version" ]; then
            printf '%s' "$version"
            return 0
        fi
    fi

    for candidate in "$here/../VERSION" "$here/../../VERSION"; do
        if [ -f "$candidate" ]; then
            tr -d ' \t\r\n' < "$candidate"
            return 0
        fi
    done
}

# Print the line only when $2 is a valid version strictly newer than $1.
# A local version AHEAD of the remote is normal inside this repository, and it
# must stay silent.
report_if_newer() {
    local local_v="$1" remote_v="$2" newer

    is_version "$local_v" || return 0
    is_version "$remote_v" || return 0
    [ "$local_v" = "$remote_v" ] && return 0

    newer="$(printf '%s\n%s\n' "$local_v" "$remote_v" | sort -V | tail -1)"
    [ "$newer" != "$remote_v" ] && return 0

    printf 'SKILL_UPDATE_AVAILABLE %s %s\n' "$local_v" "$remote_v"
}

self_test() {
    local dir failed=0 local_v out got
    dir="$(mktemp -d)"
    trap 'rm -rf "$dir"' RETURN
    mkdir -p "$dir/livewire-alpine-skills"
    local_v="$(read_local_version)"
    [ -n "$local_v" ] || local_v="1.0.0"

    check() {
        printf '%s %s\n' "$(date +%s)" "$2" > "$dir/livewire-alpine-skills/last-check"
        out="$(XDG_CACHE_HOME="$dir" bash "$here/$(basename "${BASH_SOURCE[0]}")" 2>/dev/null || true)"
        got="silent"; [ -n "$out" ] && got="speak"
        if [ "$got" != "$3" ]; then
            printf '  FAIL  %-42s expected %s, got %s\n' "$1" "$3" "$got"
            failed=$(( failed + 1 ))
        fi
    }

    check "a newer release speaks"              "99.0.0"         "speak"
    check "the same version stays silent"       "$local_v"       "silent"
    check "an older remote stays silent"        "0.0.1"          "silent"
    check "a poisoned cache stays silent"       "not-a-version"  "silent"
    check "an empty cached version stays silent" ""              "silent"

    printf '%s %s\n' "$(date +%s)" "99.0.0" > "$dir/livewire-alpine-skills/last-check"
    out="$(LW_SKILLS_NO_UPDATE_CHECK=1 XDG_CACHE_HOME="$dir" bash "$here/$(basename "${BASH_SOURCE[0]}")" 2>/dev/null || true)"
    if [ -n "$out" ]; then
        printf '  FAIL  %-42s expected silent, got speak\n' "the opt-out is honoured"
        failed=$(( failed + 1 ))
    fi

    printf 'check-update.sh self-test — %d/6 checks passed\n' $(( 6 - failed ))
    [ "$failed" -eq 0 ]
}

if [ "${1:-}" = "--self-test" ]; then
    self_test
    exit $?
fi

# An explicit opt-out, honoured before anything reads a cache or a network.
[ "${LW_SKILLS_NO_UPDATE_CHECK:-}" = "1" ] && exit 0

local_version="$(read_local_version)"

# No version to compare is not an error. Somebody vendored the text without the
# metadata, which is allowed.
[ -z "$local_version" ] && exit 0

now="$(date +%s 2>/dev/null || echo 0)"

if [ -f "$CACHE_FILE" ]; then
    cached_at="$(awk 'NR==1{print $1}' "$CACHE_FILE" 2>/dev/null || echo 0)"
    cached_remote="$(awk 'NR==1{print $2}' "$CACHE_FILE" 2>/dev/null || echo "")"

    case "$cached_at" in
        ''|*[!0-9]*) cached_at=0 ;;
    esac

    age=$(( now - cached_at ))

    if [ "$age" -ge 0 ] && [ "$age" -lt $(( MAX_AGE_HOURS * 3600 )) ]; then
        report_if_newer "$local_version" "$cached_remote"
        exit 0
    fi
fi

command -v curl >/dev/null 2>&1 || exit 0

remote_version="$(curl -fsS --max-time 4 "$REMOTE_URL" 2>/dev/null | tr -d ' \t\r\n')"

is_version "$remote_version" || exit 0

mkdir -p "$CACHE_DIR" 2>/dev/null || exit 0
printf '%s %s\n' "$now" "$remote_version" > "$CACHE_FILE" 2>/dev/null || true

report_if_newer "$local_version" "$remote_version"
exit 0
