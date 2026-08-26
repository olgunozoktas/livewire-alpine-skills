#!/usr/bin/env bash
# Create a component in THIS PROJECT'S conventions, not the skill's defaults.
#
# Reads the installed Livewire version, config/livewire.php, and the components
# already on disk, then calls make:livewire with the right flags — or refuses and
# explains, when the project's version does not support what you asked for.
#
#   bash bin/scaffold.sh post.create
#   bash bin/scaffold.sh pages::post.create
#   bash bin/scaffold.sh post.create --mfc --test
#   bash bin/scaffold.sh post.create --dry-run
set -uo pipefail

NAME="${1:-}"
[ -z "$NAME" ] && { echo "usage: bash bin/scaffold.sh <name> [--sfc|--mfc|--class] [--test] [--js] [--css] [--dry-run]"; exit 1; }
shift

DRY=0; PASS=()
for a in "$@"; do
    case "$a" in
        --dry-run) DRY=1 ;;
        *) PASS+=("$a") ;;
    esac
done

[ -f artisan ] || { echo "Run this from a Laravel project root."; exit 1; }

LW=$(php -r '
$l=@json_decode(@file_get_contents("composer.lock"),true);
foreach(($l["packages"]??[]) as $p) if($p["name"]==="livewire/livewire") { echo $p["version"]; exit; }
echo "";' 2>/dev/null)
[ -z "$LW" ] && { echo "livewire/livewire is not installed."; exit 1; }
MAJOR=$(printf '%s' "$LW" | sed 's/^v//' | cut -d. -f1)

echo "livewire $LW (v$MAJOR)"

# ---- v2 / v3 guardrails --------------------------------------------------
if [ "$MAJOR" -lt 4 ]; then
    for a in "${PASS[@]:-}"; do
        case "$a" in
            --sfc|--mfc)
                echo "REFUSED: $a needs Livewire v4. This project is v$MAJOR."
                echo "         Single-file and multi-file components do not exist before v4."
                echo "         See references/version-guide.md."
                exit 1 ;;
        esac
    done
    case "$NAME" in
        *::*) echo "REFUSED: component namespaces (name::) need v4. This project is v$MAJOR."; exit 1 ;;
    esac
    echo "v$MAJOR: creating a class-based component (the only format available)."
    [ "$DRY" = "1" ] && { echo "would run: php artisan make:livewire $NAME ${PASS[*]:-}"; exit 0; }
    exec php artisan make:livewire "$NAME" ${PASS[@]:-}
fi

# ---- v4: infer the project's format -------------------------------------
CLASS_N=$(find app/Livewire -name '*.php' 2>/dev/null | grep -v '/Forms/' \
          | xargs grep -l 'extends Component' 2>/dev/null | wc -l | tr -d ' ')
SFC_N=$(find resources/views -name '*.blade.php' -path '*components*' 2>/dev/null \
        -exec grep -l 'new class extends' {} + 2>/dev/null | wc -l | tr -d ' ')
MFC_N=$(find resources/views -type d -name '⚡*' 2>/dev/null | wc -l | tr -d ' ')

CFG_TYPE=""; CFG_EMOJI=""
if [ -f config/livewire.php ]; then
    CFG_TYPE=$(php -r '$c=require "config/livewire.php"; echo $c["make_command"]["type"] ?? "";' 2>/dev/null)
    CFG_EMOJI=$(php -r '$c=require "config/livewire.php"; echo array_key_exists("emoji",$c["make_command"]??[]) ? var_export($c["make_command"]["emoji"],true) : "";' 2>/dev/null)
fi

# An explicit flag from the caller always wins.
EXPLICIT=0
for a in "${PASS[@]:-}"; do
    case "$a" in --sfc|--mfc|--class|--type=*) EXPLICIT=1 ;; esac
done

CHOSEN=""; WHY=""
if [ "$EXPLICIT" = "1" ]; then
    WHY="you asked for it explicitly"
elif [ "$CLASS_N" -gt 0 ] && [ "$SFC_N" -eq 0 ] && [ "$MFC_N" -eq 0 ]; then
    CHOSEN="--class"; WHY="every existing component here is class-based ($CLASS_N)"
elif [ "$MFC_N" -gt 0 ] && [ "$SFC_N" -eq 0 ] && [ "$CLASS_N" -eq 0 ]; then
    CHOSEN="--mfc";   WHY="every existing component here is multi-file ($MFC_N)"
elif [ "$SFC_N" -gt 0 ] && [ "$CLASS_N" -eq 0 ]; then
    CHOSEN="--sfc";   WHY="every existing component here is single-file ($SFC_N)"
elif [ "$SFC_N" -gt 0 ] && [ "$CLASS_N" -gt 0 ]; then
    WHY="MIXED formats on disk (sfc:$SFC_N class:$CLASS_N) — falling back to the config default"
    [ -n "$CFG_TYPE" ] && CHOSEN="--$CFG_TYPE"
elif [ -n "$CFG_TYPE" ]; then
    CHOSEN="--$CFG_TYPE"; WHY="no components yet; config make_command.type = $CFG_TYPE"
else
    WHY="no components yet and no config — using the v4 default (sfc)"
fi

echo "format: ${CHOSEN:-(livewire default)}  <- $WHY"
[ -n "$CFG_EMOJI" ] && echo "emoji:  $CFG_EMOJI (from config) — filenames follow this, not the skill's examples"

CMD=(php artisan make:livewire "$NAME")
[ -n "$CHOSEN" ] && CMD+=("$CHOSEN")
CMD+=(${PASS[@]:-})

echo "run:    ${CMD[*]}"
[ "$DRY" = "1" ] && exit 0
echo
"${CMD[@]}"
