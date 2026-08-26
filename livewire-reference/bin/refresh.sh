#!/usr/bin/env bash
# Re-verify this skill against the CURRENT official documentation.
#
# Read-only: clones docs into a temp dir, extracts the API surface, and reports
# anything documented that the skill never mentions. It never edits the skill.
#
#   bash bin/refresh.sh            # audit against the branches below
#   LW_BRANCH=5.x bash bin/refresh.sh
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ALPINE_SKILL="$(cd "$SKILL_DIR/../../misc/alpinejs-reference" 2>/dev/null && pwd || true)"
WORK="${TMPDIR:-/tmp}/livewire-skill-refresh"
LW_BRANCH="${LW_BRANCH:-4.x}"

mkdir -p "$WORK"

clone() { # repo, dir, branch, sparse-path
  if [ ! -d "$WORK/$2/.git" ]; then
    git clone --depth 1 --branch "$3" --filter=blob:none --sparse "$1" "$WORK/$2" -q
  else
    git -C "$WORK/$2" fetch --depth 1 origin "$3" -q
    git -C "$WORK/$2" checkout -q FETCH_HEAD
  fi
  # Always (re)apply — a checkout can drop the sparse spec.
  git -C "$WORK/$2" sparse-checkout set "$4"
}

echo "==> Fetching official documentation"
clone https://github.com/livewire/livewire.git lw   "$LW_BRANCH" docs
clone https://github.com/alpinejs/alpine.git    ax   main         packages/docs/src/en

LW_SHA=$(git -C "$WORK/lw" rev-parse --short HEAD)
AX_SHA=$(git -C "$WORK/ax" rev-parse --short HEAD)
echo "    livewire@$LW_BRANCH  $LW_SHA"
echo "    alpine@main          $AX_SHA"

echo "==> Auditing API surface"
python3 - "$WORK" "$SKILL_DIR" "${ALPINE_SKILL:-}" <<'PY'
import re, sys, glob, os
work, lw_skill, al_skill = sys.argv[1], sys.argv[2], (sys.argv[3] or None)

# Verified noise: example component names, HTML anchor slugs, docs-site demo
# markup, and prose placeholders. Each was checked against the source and is NOT
# a real API. Reported once here so the tool does not cry wolf on every run.
NOISE = {
    # <livewire:name ...> tags caught by a `wire:` pattern
    'wire:date-picker','wire:rich-editor','wire:user-index','wire:search-results',
    'wire:survey-question','wire:dynamic-child','wire:clicks','wire:visible',
    'wire:preserve-scroll','wire:name',
    # Alpine anchor slugs and demo markup
    'x-bind:foo','x-data-scope','x-if-no-transitions','x-init-no-callback',
    'x-inputs','x-intersect-enter','x-intersect-leave','x-on:mouseenter',
    'x-ref-no-more-dynamic','x-spread-now-x-bind','x-teleport-target',
    'x-with-boolean','x-liveview-interactive-real-time-apps-no-need-to-write-javascript',
}

def corpus(paths):
    return "\n".join(open(p, encoding='utf-8', errors='replace').read() for p in paths)

def audit(label, doc_glob, skill_globs, patterns, skip_files=()):
    docs = [p for p in glob.glob(doc_glob, recursive=True)
            if os.path.basename(p) not in skip_files]
    if not docs:
        print(f"  {label}: no docs found, skipped"); return 0
    dt = corpus(docs)
    st = corpus([p for g in skill_globs for p in glob.glob(g)])
    gaps = 0
    for name, pat in patterns.items():
        items = {m.group(0) for m in re.finditer(pat, dt)}
        missing = sorted(i for i in items if i not in st and i not in NOISE)
        if missing:
            gaps += len(missing)
            print(f"  {label} / {name}: {len(missing)} not mentioned")
            for m in missing[:25]:
                print(f"      {m}")
    return gaps

total = 0
total += audit("livewire", f"{work}/lw/docs/*.md",
    [f"{lw_skill}/SKILL.md", f"{lw_skill}/references/*.md"],
    {"wire: directives": r'(?<![-<a-z])wire:[a-z][a-z0-9:-]*',
     "PHP attributes":   r'#\[[A-Z][A-Za-z]*',
     "artisan commands": r'(?<=artisan )(?:make:livewire|livewire:[a-z-]+)',
     "traits":           r'\bWith[A-Z][a-zA-Z]*\b'},
    skip_files={'AGENTS.md','__nav.md','__outline.md','contribution-guide.md',
                'upgrade-guide-scratch-file.md','undocumented-features-todo.md'})

if al_skill:
    total += audit("alpine", f"{work}/ax/packages/docs/src/en/**/*.md",
        [f"{al_skill}/SKILL.md", f"{al_skill}/references/*.md"],
        {"x- directives": r'x-[a-z][a-z0-9:-]*',
         "Alpine.* API":  r'Alpine\.[a-zA-Z$][a-zA-Z0-9_]*'})

print()
if total == 0:
    print("CLEAN — nothing documented is missing from the skills.")
else:
    print(f"{total} candidate gap(s). Most are example names or anchor slugs — verify each before editing.")
PY

echo
echo "==> Provenance line for SKILL.md:"
echo "    livewire/livewire@$LW_BRANCH $LW_SHA · alpinejs/alpine@main $AX_SHA · audited $(date -u +%Y-%m-%d)"
