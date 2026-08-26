#!/usr/bin/env bash
# Report what THIS project actually does, so the agent stops guessing.
#
# Read-only. Prints a short report: Livewire version, the component format
# already in use, the emoji setting, namespaces, locations, Boost, and a few
# checks that catch real misconfiguration.
#
#   bash bin/detect.sh              # inspect the current directory
#   bash bin/detect.sh /path/to/app
set -uo pipefail

APP="${1:-$PWD}"
cd "$APP" 2>/dev/null || { echo "not a directory: $APP"; exit 1; }

say()  { printf '%s\n' "$*"; }
kv()   { printf '  %-22s %s\n' "$1" "$2"; }
warn() { printf '  ! %s\n' "$*"; }

[ -f artisan ] || { say "No artisan file — this is not a Laravel application."; exit 1; }

say "== Project"
kv "path" "$PWD"
[ -f composer.json ] && kv "laravel" "$(php -r '
$l=@json_decode(@file_get_contents("composer.lock"),true);
foreach(($l["packages"]??[]) as $p) if($p["name"]==="laravel/framework") { echo $p["version"]; exit; }
echo "unknown";' 2>/dev/null)"
kv "php" "$(php -r 'echo PHP_VERSION;' 2>/dev/null)"

say ""
say "== Livewire"
LW=$(php -r '
$l=@json_decode(@file_get_contents("composer.lock"),true);
foreach(($l["packages"]??[]) as $p) if($p["name"]==="livewire/livewire") { echo $p["version"]; exit; }
echo "";' 2>/dev/null)

if [ -z "$LW" ]; then
    warn "livewire/livewire is NOT installed"
    kv "install" "composer require livewire/livewire"
    MAJOR=0
else
    kv "version" "$LW"
    MAJOR=$(printf '%s' "$LW" | sed 's/^v//' | cut -d. -f1)
    kv "major" "v$MAJOR"
    case "$MAJOR" in
      4) kv "skill applies" "YES — this skill documents v4" ;;
      3) warn "v3 — read references/version-guide.md BEFORE writing anything" ;;
      2) warn "v2 — this skill does NOT apply. See references/version-guide.md" ;;
      *) warn "unrecognised major version" ;;
    esac
fi

VOLT=$(php -r '
$l=@json_decode(@file_get_contents("composer.lock"),true);
foreach(($l["packages"]??[]) as $p) if($p["name"]==="livewire/volt") { echo $p["version"]; exit; }
echo "";' 2>/dev/null)
[ -n "$VOLT" ] && kv "volt" "$VOLT — see references/volt.md"

say ""
say "== Component conventions (these OUTRANK the skill's defaults)"

# Form objects live under Livewire/Forms and are NOT components — exclude them.
CLASS_N=$(find app/Livewire app/Http/Livewire -name '*.php' 2>/dev/null \
          | grep -v '/Forms/' | xargs grep -l 'extends Component' 2>/dev/null | wc -l | tr -d ' ')
FORM_N=$(find app/Livewire app/Http/Livewire -path '*/Forms/*' -name '*.php' 2>/dev/null | wc -l | tr -d ' ')
SFC_N=$(find resources/views -name '*.blade.php' -path '*components*' 2>/dev/null \
        -exec grep -l 'new class extends' {} + 2>/dev/null | wc -l | tr -d ' ')
MFC_N=$(find resources/views -type d -name '⚡*' 2>/dev/null | wc -l | tr -d ' ')
EMOJI_N=$(find resources/views -name '⚡*' 2>/dev/null | wc -l | tr -d ' ')

kv "class-based" "$CLASS_N"
[ "$FORM_N" -gt 0 ] && kv "form objects" "$FORM_N (not components)"
kv "single-file (SFC)" "$SFC_N"
kv "multi-file dirs" "$MFC_N"
kv "files with ⚡ prefix" "$EMOJI_N"

[ -d app/Http/Livewire ] && warn "app/Http/Livewire exists — that is the v2 namespace"

if   [ "$CLASS_N" -gt 0 ] && [ "$SFC_N" -eq 0 ]; then FORMAT="class"
elif [ "$SFC_N" -gt 0 ] && [ "$CLASS_N" -eq 0 ]; then FORMAT="sfc"
elif [ "$SFC_N" -gt 0 ] && [ "$CLASS_N" -gt 0 ]; then FORMAT="mixed"
else FORMAT="none"; fi

case "$FORMAT" in
  class) kv "=> WRITE" "class-based, to match this project" ;;
  sfc)   kv "=> WRITE" "single-file, to match this project" ;;
  mixed) kv "=> WRITE" "MIXED — ask, or match the nearest sibling component" ;;
  none)  kv "=> WRITE" "no components yet — use the config default below" ;;
esac

say ""
say "== config/livewire.php"
if [ -f config/livewire.php ]; then
    php -r '
    $c = require "config/livewire.php";
    printf("  %-22s %s\n", "make_command.type",  $c["make_command"]["type"]  ?? "(default: sfc)");
    printf("  %-22s %s\n", "make_command.emoji", isset($c["make_command"]["emoji"]) ? var_export($c["make_command"]["emoji"], true) : "(default: true)");
    printf("  %-22s %s\n", "component_layout",   $c["component_layout"] ?? "(default: layouts::app)");
    printf("  %-22s %s\n", "csp_safe",           isset($c["csp_safe"]) ? var_export($c["csp_safe"], true) : "(default: false)");
    foreach (($c["component_namespaces"] ?? []) as $ns => $path) {
        printf("  %-22s %s\n", "namespace ".$ns."::", str_replace(getcwd()."/", "", $path));
    }
    foreach (($c["component_locations"] ?? []) as $i => $path) {
        printf("  %-22s %s%s\n", "location[".$i."]", str_replace(getcwd()."/", "", $path), $i === 0 ? "   <- make:livewire writes here" : "");
    }
    ' 2>/dev/null || warn "config/livewire.php present but could not be read"
    if [ -n "$LW" ] && [ "$MAJOR" = "4" ] && grep -qE "^\s*'layout'\s*=>" config/livewire.php 2>/dev/null; then
        warn "config uses the v3 key 'layout' — v4 wants 'component_layout'"
    fi
else
    kv "published" "no — all defaults apply"
    kv "publish with" "php artisan livewire:config"
fi

say ""
say "== Routing"
RL=$(grep -rl 'Route::livewire(' routes/ 2>/dev/null | wc -l | tr -d ' ')
# Any Route::get() mapped straight to a class — the v3 page-component shape.
RG=$(grep -rlE "Route::get\(\s*['\"][^'\"]*['\"]\s*,\s*[A-Z][A-Za-z0-9_\\\\]*::class" routes/ 2>/dev/null | wc -l | tr -d ' ')
kv "Route::livewire()" "$RL file(s)"
kv "Route::get(Component)" "$RG file(s)"
[ "$MAJOR" = "4" ] && [ "$RG" -gt 0 ] && warn "v4 prefers Route::livewire() for page components"

say ""
say "== Tooling"
if grep -q '"laravel/boost"' composer.json 2>/dev/null; then
    kv "laravel/boost" "installed — use its search-docs for anything newer than this skill"
    [ -d .ai/skills/livewire-development ] && warn ".ai/skills/livewire-development exists — Boost's skill, same name as this one"
else
    kv "laravel/boost" "not installed"
fi
grep -q '"pestphp/pest"' composer.json 2>/dev/null \
    && kv "test runner" "Pest" || kv "test runner" "PHPUnit"

say ""
say "== Sanity checks"
ALPINE_HITS=$(grep -rl "alpinejs@\|from 'alpinejs'\|Alpine.start()" resources/ 2>/dev/null | grep -v vendor | head -3)
if [ -n "$ALPINE_HITS" ] && [ -n "$LW" ]; then
    warn "Alpine looks separately included — Livewire bundles it. Two copies break \$wire:"
    printf '      %s\n' $ALPINE_HITS
else
    kv "alpine" "no separate copy detected (Livewire bundles it)"
fi

LAYOUT=$(ls resources/views/layouts/app.blade.php 2>/dev/null || true)
if [ -n "$LAYOUT" ]; then
    grep -q '@livewireStyles' "$LAYOUT" || warn "layouts/app.blade.php has no @livewireStyles"
    grep -q '@livewireScripts\|@livewireScriptConfig' "$LAYOUT" || warn "layouts/app.blade.php has no @livewireScripts"
    kv "layout" "resources/views/layouts/app.blade.php"
else
    kv "layout" "resources/views/layouts/app.blade.php not found (php artisan livewire:layout)"
fi

say ""
say "== Is this skill current?"
SKILL_MINOR="4.4"       # highest livewire minor this skill has been verified against
SKILL_AUDIT="2026-08-26"
kv "skill verified against" "livewire $SKILL_MINOR (audited $SKILL_AUDIT)"
if [ -n "$LW" ] && [ "$MAJOR" = "4" ]; then
    PROJ_MINOR=$(printf '%s' "$LW" | sed 's/^v//' | cut -d. -f1,2)
    if [ "$PROJ_MINOR" != "$SKILL_MINOR" ] \
       && [ "$(printf '%s\n%s\n' "$SKILL_MINOR" "$PROJ_MINOR" | sort -V | tail -1)" = "$PROJ_MINOR" ]; then
        warn "this project is on $PROJ_MINOR — NEWER than the skill's verification"
        warn "run: bash bin/refresh.sh    (and prefer Boost's search-docs, or the live docs)"
    else
        kv "status" "skill covers this project's version"
    fi
fi

say ""
say "Write code that matches the conventions above, not the skill's defaults."
