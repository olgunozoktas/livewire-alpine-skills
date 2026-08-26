#!/usr/bin/env bash
# Locate BOTH halves of the Livewire stack and print what to read.
#
# Livewire bundles Alpine, so real work touches both. The two skills are kept
# separate because Alpine is also used with Rails, Django and Hotwire — but from
# a Laravel project you almost always want them together.
#
# Their relative positions differ by layout (installed / public repo / source
# tree), and the installed entries are symlinks, so `../alpinejs-development`
# is not reliable. This resolves it.
#
#   bash bin/stack.sh          # print the file map for both skills
#   bash bin/stack.sh --paths  # just the two skill roots, one per line
set -uo pipefail

# Resolve this script's real directory, following symlinks.
src="${BASH_SOURCE[0]}"
while [ -L "$src" ]; do
    dir="$(cd -P "$(dirname "$src")" && pwd)"
    src="$(readlink "$src")"
    [[ $src != /* ]] && src="$dir/$src"
done
LW_DIR="$(cd -P "$(dirname "$src")/.." && pwd)"

find_alpine() {
    local c
    # 1. sibling of the real source dir, and of the invoked (possibly symlinked) dir
    for c in "$LW_DIR/../alpinejs-development" \
             "$(dirname "$(dirname "$0")")/../alpinejs-development" \
             "$LW_DIR/../../misc/alpinejs-development" \
             "$LW_DIR/../../alpinejs-development" \
             "$HOME/.claude/skills/alpinejs-development" \
             "$HOME/.config/claude/skills/alpinejs-development"; do
        [ -f "$c/SKILL.md" ] && { (cd "$c" && pwd); return 0; }
    done
    # 2. last resort: a bounded search near the skill root
    c=$(find "$LW_DIR/../.." -maxdepth 3 -type d -name alpinejs-development 2>/dev/null | head -1)
    [ -n "$c" ] && [ -f "$c/SKILL.md" ] && { (cd "$c" && pwd); return 0; }
    return 1
}

AL_DIR="$(find_alpine)" || AL_DIR=""

if [ "${1:-}" = "--paths" ]; then
    printf '%s\n' "$LW_DIR"
    [ -n "$AL_DIR" ] && printf '%s\n' "$AL_DIR"
    exit 0
fi

echo "== The Livewire stack — one workflow"
echo
echo "LIVEWIRE   $LW_DIR"
echo "  SKILL.md                       always read this first"
echo "  references/recipes.md          12 complete, executed components"
echo "  references/troubleshooting.md  symptom -> cause -> fix"
echo "  references/version-guide.md    v3 differences; what is v4-only"
echo "  references/directives.md       every wire: directive"
echo "  references/attributes.md       every PHP attribute"
echo "  references/alpine.md           Alpine INSIDE Livewire (\$wire, morph, entangle)"
echo "  ... plus components, properties-actions, forms-validation,"
echo "      islands-performance, javascript, advanced, testing, reference,"
echo "      volt, v3-to-v4"
echo

if [ -z "$AL_DIR" ]; then
    echo "ALPINE     NOT FOUND"
    echo "  The alpinejs-development skill is not installed beside this one."
    echo "  Install it from the same source, or work from references/alpine.md,"
    echo "  which covers the integration but NOT the Alpine language itself."
    exit 1
fi

echo "ALPINE     $AL_DIR"
echo "  SKILL.md                       the mental model and the 3 rules"
echo "  references/directives.md       all 18 directives, every modifier"
echo "  references/magics-globals.md   9 magics, 3 globals, lifecycle"
echo "  references/plugins.md          all 9 official plugins"
echo "  references/extending.md        custom directives, reactivity, CSP"
echo "  references/v2-to-v3.md         the v2 upgrade guide"
echo
echo "== Which half answers your question"
echo "  server state, wire: directives, PHP attributes  -> LIVEWIRE"
echo "  \$wire, entangle, morph vs Alpine state          -> LIVEWIRE references/alpine.md"
echo "  x-data, x-model, x-for, \$refs, \$store           -> ALPINE"
echo "  x-mask, x-trap, x-anchor, \$persist              -> ALPINE references/plugins.md"
echo
echo "== Reviewers (both gate on exit code)"
echo "  python3 $LW_DIR/bin/review.py <file>"
echo "  python3 $AL_DIR/bin/review.py <file>"

# A POINTER, NOT A LOAD. Most Livewire work does not need the security skill,
# and loading it every time would train a reader to skip it.
echo ""
echo "SECURITY   read livewire-security before a component goes on a public route,"
echo "           or during a security review. It is a separate skill on purpose."
