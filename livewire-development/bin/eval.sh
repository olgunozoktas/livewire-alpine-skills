#!/usr/bin/env bash
# Score a directory of Livewire source objectively.
#
#   bash bin/eval.sh <dir> [<dir>...]
#   bash bin/eval.sh --compare      # baseline-v3-habits vs the skill's recipes
#
# Score per file = 100, minus 15 per ERROR and 5 per WARN from bin/review.py,
# minus 40 if it does not even parse. Deterministic, and it grades fixed
# artifacts rather than anyone's opinion.
set -uo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

score_dir() {
    local dir="$1" label="$2"
    local files n=0 total=0 errs=0 warns=0 lint_bad=0
    files=$(find "$dir" \( -name '*.php' -o -name '*.blade.php' -o -name '*.js' \) 2>/dev/null | sort -u)
    [ -z "$files" ] && { echo "  $label: no files"; return; }

    while IFS= read -r f; do
        [ -z "$f" ] && continue
        n=$((n + 1))
        local s=100
        case "$f" in
            *.js) ;;   # php -l does not apply
            *) php -l "$f" >/dev/null 2>&1 || { s=$((s - 40)); lint_bad=$((lint_bad + 1)); } ;;
        esac
        local json e w
        json=$(python3 "$SKILL_DIR/bin/review.py" --json "$f" 2>/dev/null)
        e=$(printf '%s' "$json" | grep -c '"severity": "ERROR"')
        w=$(printf '%s' "$json" | grep -c '"severity": "WARN"')
        errs=$((errs + e)); warns=$((warns + w))
        s=$((s - e * 15 - w * 5))
        [ "$s" -lt 0 ] && s=0
        total=$((total + s))
    done <<< "$files"

    local avg=$((n > 0 ? total / n : 0))
    printf '  %-22s %3d/100   files:%-3d errors:%-3d warns:%-3d lint-fail:%d\n' \
        "$label" "$avg" "$n" "$errs" "$warns" "$lint_bad"
    LAST_SCORE=$avg
}

if [ "${1:-}" = "--compare" ]; then
    APP="${TMPDIR:-/tmp}/livewire-skill-verify/lwtest"
    echo "== Livewire code quality, scored by bin/review.py"
    echo
    score_dir "$SKILL_DIR/tests/eval/baseline-v3-habits" "no skill (v3 habits)"
    BASE=$LAST_SCORE
    if [ -d "$APP/resources/views/components" ]; then
        score_dir "$APP/resources/views/components" "skill's recipes"
        SKILLED=$LAST_SCORE
        echo
        echo "  delta: +$((SKILLED - BASE)) points"
    else
        echo
        echo "  (run bin/verify-recipes.sh first to materialise the recipes)"
    fi
    exit 0
fi

[ $# -eq 0 ] && { echo "usage: bash bin/eval.sh <dir>... | --compare"; exit 1; }
echo "== Livewire code quality"
echo
for d in "$@"; do score_dir "$d" "$(basename "$d")"; done
