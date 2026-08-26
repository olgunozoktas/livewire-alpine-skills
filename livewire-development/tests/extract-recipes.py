"""Extract every code block from recipes.md into real files in the test app."""
import re, os, sys, io

RECIPES = os.path.expanduser('~/Herd/olgun-skills/skills/laravel/livewire-development/references/recipes.md')
APP = sys.argv[1]

s = io.open(RECIPES, encoding='utf-8').read()

# A "recipe unit" is a ```php block whose first line names a file path, optionally
# followed immediately by the Blade template inside the SAME block (after ?>).
blocks = re.findall(r'```(php|blade)\n(.*?)```', s, re.S)

written = []
for lang, body in blocks:
    first = body.split('\n', 1)[0]
    m = re.match(r'<\?php\s*//\s*(\S+\.blade\.php|\S+\.php)\s*$', first.strip())
    if not m:
        continue
    rel = m.group(1)
    dest = os.path.join(APP, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    # strip the path comment from the first line, keep bare <?php
    out = '<?php\n' + body.split('\n', 1)[1]
    io.open(dest, 'w', encoding='utf-8').write(out)
    written.append(rel)

print(f"wrote {len(written)} files:")
for w in written:
    print("  ", w)
