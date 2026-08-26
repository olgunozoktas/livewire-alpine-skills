#!/usr/bin/env bash
# Prove every recipe in references/recipes.md actually RUNS.
#
# Scaffolds a throwaway Laravel + Livewire 4 app, extracts each recipe into a
# real component file, lints it, then RENDERS it and exercises its actions with
# Livewire::test(). No browser and no dev server — Livewire renders server-side.
#
#   bash bin/verify-recipes.sh            # reuse the app if present
#   FRESH=1 bash bin/verify-recipes.sh    # scaffold from scratch
#
# The app is built under $TMPDIR and is never deleted by this script. Its path
# is printed at the end so you can inspect or remove it yourself.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP="${TMPDIR:-/tmp}/livewire-skill-verify/lwtest"

if [ "${FRESH:-0}" = "1" ] && [ -d "$APP" ]; then
    mv "$APP" "$APP.superseded-$(date -u +%Y%m%d-%H%M%S)"
    echo "==> Previous app moved aside (not deleted)"
fi

command -v composer >/dev/null || { echo "composer is required"; exit 1; }
case "$(php -m)" in *pdo_sqlite*) ;; *) echo "pdo_sqlite is required"; exit 1;; esac

if [ ! -f "$APP/artisan" ]; then
    echo "==> Scaffolding Laravel + Livewire 4 (first run only, a few minutes)"
    mkdir -p "$(dirname "$APP")"
    composer create-project laravel/laravel "$APP" --no-interaction --quiet
    (cd "$APP" && composer require livewire/livewire:^4.0 --no-interaction --quiet)
fi

cd "$APP"

LW_VERSION=$(php -r '$l=json_decode(file_get_contents("composer.lock"),true);
foreach($l["packages"] as $p) if($p["name"]==="livewire/livewire") echo $p["version"];')
echo "==> Testing against livewire/livewire $LW_VERSION"

echo "==> Installing fixtures (models, factories, migrations, policy)"
cp -R "$SKILL_DIR/tests/fixtures/." "$APP/"

# The User model needs a posts() relation for the recipes.
php -r '
$f = "app/Models/User.php"; $s = file_get_contents($f);
if (! str_contains($s, "function posts(")) {
    $s = preg_replace("/(\n    protected function casts)/",
        "\n    public function posts() { return \$this->hasMany(\\\\App\\\\Models\\\\Post::class); }\n\$1", $s, 1);
    file_put_contents($f, $s);
}'

php artisan migrate:fresh --no-interaction --quiet

echo "==> Extracting recipes from references/recipes.md"
python3 "$SKILL_DIR/tests/extract-recipes.py" "$APP"

echo "==> Linting every extracted file"
lint_fail=0
while IFS= read -r -d '' f; do
    if ! php -l "$f" >/dev/null 2>&1; then
        echo "  ! SYNTAX ERROR  $f"
        php -l "$f" 2>&1 | head -2 | sed 's/^/      /'
        lint_fail=1
    fi
done < <(find resources/views/components app/Livewire -name '*.php' -print0 2>/dev/null)
[ "$lint_fail" = "0" ] && echo "  all files lint clean"

echo "==> Rendering and exercising every recipe"
mkdir -p tests/Feature
cp "$SKILL_DIR/tests/RecipesTest.php" tests/Feature/RecipesTest.php

set +e
php artisan test --testsuite=Feature --filter=RecipesTest
status=$?
set -e

echo
echo "app kept at: $APP"
[ "$status" -eq 0 ] && [ "$lint_fail" -eq 0 ] \
    && echo "VERIFIED — every recipe compiles, renders and behaves, on livewire $LW_VERSION" \
    || echo "FAILURES above — fix references/recipes.md, then re-run"
exit "$status"
