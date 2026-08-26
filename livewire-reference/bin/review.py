#!/usr/bin/env python3
"""Review Livewire component source for v3-isms, security holes and known traps.

    python3 bin/review.py path/to/⚡component.blade.php [more...]
    python3 bin/review.py --json path/to/component.php
    python3 bin/review.py --self-test

Exit code is the number of ERROR-level findings, so it works as a gate.

Every rule here corresponds to a documented behaviour or a defect that has
actually bitten. `--self-test` feeds each rule a snippet that must trigger it
and one that must not — a checker that can never fire is indistinguishable from
a broken one.
"""
import re
import sys
import io
import json
import os

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"

# Helper methods on Livewire\Component that a component must NOT redefine.
#
# Deliberately excluded: mount, render, boot, booted, hydrate, dehydrate,
# updating, updated, rendering, rendered, exception, placeholder. Those are
# LIFECYCLE HOOKS — defining them is how Livewire is meant to be used.
RESERVED = [
    "reset", "validate", "dispatch", "redirect", "redirectRoute", "redirectIntended",
    "redirectAction", "skipRender", "fill", "pull", "only", "all", "js", "stream",
    "authorize", "resetPage", "setPage", "nextPage", "previousPage", "getId",
    "resetValidation", "addError", "getErrorBag", "skipTransition", "transition",
]

RULES = [
    # id, severity, pattern, message, fix, a hit sample, a miss sample
    ("v3-route-get", ERROR,
     r"Route::get\(\s*['\"][^'\"]*['\"]\s*,\s*[A-Z]\w*::class\s*\)",
     "v3 routing for a page component.",
     "Use Route::livewire('/path', 'pages::name') — required for SFC/MFC.",
     "Route::get('/posts', ShowPosts::class);",
     "Route::livewire('/posts', 'pages::posts');"),

    ("v3-wire-model-defer", ERROR,
     r"wire:model\.defer\b",
     "wire:model.defer was removed in v4.",
     "Deferred is the DEFAULT in v4 — just use wire:model.",
     '<input wire:model.defer="title">',
     '<input wire:model="title">'),

    ("v3-wire-scroll", ERROR,
     r"\bwire:scroll\b",
     "wire:scroll was renamed in v4.",
     "Use wire:navigate:scroll.",
     '<div wire:scroll>',
     '<div wire:navigate:scroll>'),

    ("v3-transition-modifiers", ERROR,
     r"wire:transition\.(opacity|scale|duration|delay|origin)\b",
     "wire:transition modifiers were removed in v4.",
     "v4 uses the View Transitions API and takes no modifiers. "
     "Use #[Transition(type:)] plus CSS, or Alpine's x-transition.",
     '<div wire:transition.opacity>',
     '<div wire:transition>'),

    ("v3-js-action", WARN,
     r"\$wire\.\$js\(\s*['\"]",
     "Deprecated JS action syntax.",
     "Assign instead: this.$js.name = () => {}",
     "$wire.$js('save', () => {})",
     "this.$js.save = () => {}"),

    ("v3-hooks", ERROR,
     r"Livewire\.hook\(\s*['\"](commit|request)['\"]",
     "The commit/request hooks are deprecated.",
     "Use Livewire.interceptMessage() / Livewire.interceptRequest().",
     "Livewire.hook('commit', cb)",
     "Livewire.interceptMessage(cb)"),

    ("v3-stream-to", ERROR,
     r"\$this->stream\([^)]*\bto\s*:",
     "stream(to:) is the legacy v3 parameter.",
     "Use name: (matches wire:stream), el: (a selector) or ref: (a wire:ref).",
     "$this->stream(to: '#out', content: 'x');",
     "$this->stream(content: 'x', name: 'out');"),

    ("v3-entangle-directive", ERROR,
     r"@entangle\(",
     "The @entangle Blade directive is deprecated and breaks on element removal.",
     "Read and write $wire.property directly.",
     'x-data="{ o: @entangle(\'open\') }"',
     'x-data="{ o: false }"'),

    ("entangle-discouraged", WARN,
     r"\$wire\.entangle\(",
     "$wire.entangle() duplicates state and is discouraged.",
     "Use $wire.property directly.",
     "$wire.entangle('open')",
     "$wire.open"),

    ("unclosed-component-tag", ERROR,
     r"<livewire:[a-z0-9:.-]+(?:\s+[^>]*?)?(?<![/\"'])>(?![\s\S]*?</livewire:)",
     "Component tag is not closed.",
     "v4 needs <livewire:name /> or an explicit closing tag, or later markup "
     "is read as slot content and the component does not render.",
     '<livewire:counter>',
     '<livewire:counter />'),

    ("foreach-missing-key", ERROR,
     r"@foreach\s*\([^)]*\)\s*\n(?:(?!wire:key|@endforeach|:wire:key)[\s\S]){0,220}?@endforeach",
     "A @foreach with no wire:key.",
     "Add wire:key to the first element inside the loop. Without it you get "
     '"Component already initialized" and "Snapshot missing".',
     '@foreach ($posts as $p)\n    <div>{{ $p->title }}</div>\n@endforeach',
     '@foreach ($posts as $p)\n    <div wire:key="{{ $p->id }}">{{ $p->title }}</div>\n@endforeach'),

    ("script-wrapper-in-sfc", WARN,
     r"@script\b",
     "@script is only for CLASS-BASED components.",
     "Single-file and multi-file components use a bare <script> tag.",
     "@script\n<script></script>\n@endscript",
     "<script>this.$js.x = () => {}</script>"),

    ("alpine-double-include", ERROR,
     r"(cdn\.jsdelivr\.net/npm/alpinejs|from\s+['\"]alpinejs['\"]|Alpine\.start\(\))",
     "Alpine looks separately included.",
     'Livewire bundles Alpine. Two copies give "Detected multiple instances of '
     'Alpine running" and "$wire is not defined".',
     "<script src='https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js'></script>",
     "<div x-data='{ open: false }'></div>"),

    ("unquoted-blade-in-js", ERROR,
     r"\$wire\.[A-Za-z_]\w*\(\s*\{\{\s*\$[A-Za-z_][\w>\-]*(?:->\w+)*\s*\}\}\s*\)",
     "Unquoted Blade value inside a JavaScript expression.",
     "Quote it: $wire.method('{{ $model->uuid }}'). Integer ids happen to work, "
     "so this only breaks the day you switch to UUIDs.",
     'x-on:click="$wire.del({{ $p->uuid }})"',
     'x-on:click="$wire.del(\'{{ $p->uuid }}\')"'),

    ("async-mutates-state", ERROR,
     r"#\[Async\][\s\S]{0,240}?\$this->\w+\s*(?:\+\+|--|=[^=])",
     "An #[Async] action mutating component state.",
     "Async actions run in PARALLEL from the same snapshot, so updates are "
     "lost. Use async only for pure side effects.",
     "#[Async]\npublic function inc() { $this->count++; }",
     "#[Async]\npublic function log() { Activity::log('x'); }"),

    ("public-model-id", WARN,
     r"public\s+\$(\w*[Ii]d)\s*(?:=|;)",
     "A public id property is client-mutable.",
     "Add #[Locked], or store the whole model — a model property has its key "
     "locked automatically.",
     "public $postId;",
     "#[Locked]\npublic $postId;"),

    ("find-without-authorize", ERROR,
     r"function\s+\w+\s*\([^)]*\)\s*(?::\s*\w+\s*)?\{(?:(?!\bfunction\b)[\s\S]){0,400}?::(?:find|findOrFail)\s*\((?:(?!\bfunction\b)[\s\S]){0,400}?->(?:delete|update|save)\s*\(",
     "A model is fetched and written without an authorization check.",
     "Action parameters are untrusted input. Call $this->authorize(...) or use "
     "#[Authorize] before writing.",
     "public function del($id) { $p = Post::find($id); $p->delete(); }",
     "public function del($id) { $p = Post::find($id); $this->authorize('delete', $p); $p->delete(); }"),

    ("eloquent-public-property", WARN,
     r"public\s+\$\w+\s*=\s*\[\s*\];?\s*\n[\s\S]{0,200}?\$this->\w+\s*=\s*\w+::(?:all|where|query)\(",
     "A query result stored in a public property.",
     "Query constraints are lost between requests and the query re-runs on "
     "every hydrate. Use a #[Computed] property.",
     "public $posts = [];\npublic function mount() { $this->posts = Post::all(); }",
     "#[Computed]\npublic function posts() { return Post::all(); }"),

    ("upload-reserved", ERROR,
     r"use\s+WithFileUploads;[\s\S]{0,600}?public\s+function\s+upload\s*\(",
     '"upload" is reserved on a WithFileUploads component.',
     "Rename the method — save() is the convention.",
     "use WithFileUploads;\npublic function upload() {}",
     "use WithFileUploads;\npublic function save() {}"),

]

# Some rules need context a single regex cannot express.
# If this pattern appears INSIDE the match, the finding is suppressed.
SUPPRESS_IF_IN_MATCH = {
    "find-without-authorize": r"\bauthorize\s*\(|#\[Authorize",
}
# If this pattern appears in the N characters BEFORE the match, suppress it.
SUPPRESS_IF_BEFORE = {
    "public-model-id": (r"#\[Locked\]", 40),
}

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
}

# Blade control directives that open a block, and the ones that close it.
BLADE_OPEN = re.compile(
    r"@(if|unless|foreach|forelse|for|while|isset|empty|switch|auth|guest|"
    r"production|env|can|cannot|canany|error|once|push|prepend|section|verbatim|"
    r"island|placeholder|persist|teleport|assets|script|volt|fragment)\b")
BLADE_CLOSE = re.compile(
    r"@(endif|endunless|endforeach|endforelse|endfor|endwhile|endisset|endempty|"
    r"endswitch|endauth|endguest|endproduction|endenv|endcan|endcannot|endcanany|"
    r"enderror|endonce|endpush|endprepend|endsection|endverbatim|endisland|"
    r"endplaceholder|endpersist|endteleport|endassets|endscript|endvolt|"
    r"endfragment)\b")

TAG_RE = re.compile(r"<(/?)([a-zA-Z][\w.:-]*)([^>]*?)(/?)>", re.S)


def count_root_elements(template: str):
    """Count top-level elements in a component template, nesting-aware.

    Returns (count, [line numbers of each root]). Anything inside a Blade
    control block is skipped — a component whose root is wrapped in @if has one
    conditional root, not zero, and we must not guess which branch wins.
    """
    # Remove comments and the CONTENTS of script/style, keeping the tags.
    t = re.sub(r"<!--.*?-->", "", template, flags=re.S)
    t = re.sub(r"\{\{--.*?--\}\}", "", t, flags=re.S)
    t = re.sub(r"(<(script|style)\b[^>]*>)(.*?)(</\2>)",
               lambda m: m.group(1) + m.group(4), t, flags=re.S | re.I)

    depth = 0
    blade_depth = 0
    roots = []
    pos = 0
    for m in TAG_RE.finditer(t):
        # Track Blade block depth in the text between tags.
        between = t[pos:m.start()]
        blade_depth += len(BLADE_OPEN.findall(between)) - len(BLADE_CLOSE.findall(between))
        pos = m.end()

        closing, name, attrs, self_closed = m.groups()
        lname = name.lower()
        if lname in ("script", "style") and depth == 0:
            continue                      # sibling <script> is allowed by Livewire
        if lname.startswith("x-slot"):
            continue                      # layout slots live outside the root
        if lname in VOID_TAGS or self_closed:
            if not closing and depth == 0 and blade_depth <= 0:
                roots.append(t.count("\n", 0, m.start()) + 1)
            continue
        if closing:
            depth = max(0, depth - 1)
        else:
            if depth == 0 and blade_depth <= 0:
                roots.append(t.count("\n", 0, m.start()) + 1)
            depth += 1
    return len(roots), roots


def check_roots(src: str, path: str):
    """A component template must have exactly one root element."""
    if "new class extends" not in src and "extends Component" not in src:
        return []                          # not a component template
    i = src.rfind("?>")
    if i == -1:
        return []                          # class-based: view is a separate file
    template = src[i + 2:]
    if not template.strip():
        return []
    n, lines = count_root_elements(template)
    if n <= 1:
        return []
    return [{
        "rule": "multi-root", "severity": ERROR, "file": path,
        "line": lines[1],
        "message": f"The template has {n} root elements; a component needs exactly one.",
        "fix": "Wrap them in a single element. (Layout <x-slot> tags and a "
               "sibling <script> are allowed and are not counted.)",
        "snippet": f"roots at lines {', '.join(map(str, lines))}",
    }]


RESERVED_RE = re.compile(
    r"public\s+function\s+(" + "|".join(RESERVED) + r")\s*\(")


def strip_comments(src: str) -> str:
    """Blank out // and # line comments and /* */ blocks, preserving offsets."""
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        two = src[i:i + 2]
        if two == "/*":
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
        elif two == "//" and not (i > 0 and src[i - 1] == ":"):
            # ':' before '//' means a URL (https://…), not a comment.
            j = src.find("\n", i)
            j = n if j == -1 else j
            for k in range(i, j):
                out[k] = " "
            i = j
        else:
            i += 1
    return "".join(out)


def line_of(src: str, pos: int) -> int:
    return src.count("\n", 0, pos) + 1


def review(src: str, path: str = "<input>"):
    findings = []
    scan = strip_comments(src)

    for rid, sev, pat, msg, fix, _hit, _miss in RULES:
        for m in re.finditer(pat, scan, re.M):
            if rid in SUPPRESS_IF_IN_MATCH and re.search(SUPPRESS_IF_IN_MATCH[rid], m.group(0)):
                continue
            if rid in SUPPRESS_IF_BEFORE:
                pre_pat, window = SUPPRESS_IF_BEFORE[rid]
                if re.search(pre_pat, scan[max(0, m.start() - window):m.start()]):
                    continue
            findings.append({
                "rule": rid, "severity": sev, "file": path,
                "line": line_of(src, m.start()),
                "message": msg, "fix": fix,
                "snippet": src[m.start():m.end()].strip().split("\n")[0][:90],
            })

    for m in RESERVED_RE.finditer(scan):
        name = m.group(1)
        findings.append({
            "rule": "reserved-method", "severity": ERROR, "file": path,
            "line": line_of(src, m.start()),
            "message": f'public function {name}() overrides Livewire\\Component::{name}().',
            "fix": f"Rename it. Overriding {name}() silently breaks $this->{name}() "
                   "everywhere in this component.",
            "snippet": m.group(0),
        })

    findings += check_roots(src, path)

    findings.sort(key=lambda f: (f["line"], f["rule"]))
    return findings


def self_test() -> int:
    """Every rule must fire on its hit sample and stay quiet on its miss sample."""
    bad = 0
    for rid, sev, pat, msg, fix, hit, miss in RULES:
        # Go through review() so the suppressors are exercised, not just the regex.
        if not [f for f in review(hit) if f["rule"] == rid]:
            print(f"  FAIL {rid}: did not fire on its hit sample"); bad += 1
        if [f for f in review(miss) if f["rule"] == rid]:
            print(f"  FAIL {rid}: fired on its miss sample"); bad += 1
    if not RESERVED_RE.search("public function reset() {}"):
        print("  FAIL reserved-method: did not fire"); bad += 1
    if RESERVED_RE.search("public function resetTheThing() {}"):
        print("  FAIL reserved-method: fired on a longer name"); bad += 1
    if strip_comments("// public function reset() {}").strip():
        print("  FAIL strip_comments: line comment not blanked"); bad += 1

    # The .md refusal, exercised through main() — the guard lives there, so a
    # rule-level test would not reach it. A markdown file holds many components,
    # and reviewing it as one source file invents cross-component findings.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        md = os.path.join(td, "recipes.md")
        with open(md, "w", encoding="utf-8") as fh:
            fh.write("new class extends Component {};\n?>\n<div>a</div>\n<div>b</div>\n")
        argv, out = sys.argv, sys.stdout
        try:
            sys.stdout = io.StringIO()          # main() prints; the test only wants its exit code
            err = sys.stderr; sys.stderr = io.StringIO()
            sys.argv = ["review.py", md]
            if main() != 0:
                print("  FAIL md-guard: did not refuse a .md file"); bad += 1
            sys.argv = ["review.py", "--force-md", md]
            if main() == 0:
                print("  FAIL md-guard: --force-md did not review the file"); bad += 1
            php = os.path.join(td, "c.blade.php")
            with open(php, "w", encoding="utf-8") as fh:
                fh.write("new class extends Component {};\n?>\n<div>a</div>\n<div>b</div>\n")
            sys.argv = ["review.py", php]
            if main() == 0:
                print("  FAIL md-guard: refused a real component file"); bad += 1
        finally:
            sys.argv, sys.stdout = argv, out
            sys.stderr = err

    root_cases = [
        ("two siblings", "new class extends Component {};\n?>\n<div>a</div>\n<div>b</div>", True),
        ("one root, nested", "new class extends Component {};\n?>\n<div><span>a</span><span>b</span></div>", False),
        ("one root + script", "new class extends Component {};\n?>\n<div>a</div>\n<script>let x = 1 < 2</script>", False),
        ("one root + x-slot", "new class extends Component {};\n?>\n<x-slot:lang>fr</x-slot>\n<div>a</div>", False),
        ("void tag inside", "new class extends Component {};\n?>\n<form><input type=\"text\"><br></form>", False),
        ("root wrapped in @if", "new class extends Component {};\n?>\n@if ($x)\n<div>a</div>\n@endif", False),
        ("foreach inside root", "new class extends Component {};\n?>\n<div>@foreach ($a as $b)<p>{{ $b }}</p>@endforeach</div>", False),
        ("self-closing sibling", "new class extends Component {};\n?>\n<div/>\n<div/>", True),
        ("comment then root", "new class extends Component {};\n?>\n<!-- hi -->\n<div>a</div>", False),
    ]
    for label, src, should_fire in root_cases:
        fired = bool(check_roots(src, "t"))
        if fired != should_fire:
            print(f"  FAIL multi-root ({label}): expected {'a finding' if should_fire else 'silence'}")
            bad += 1

    total = len(RULES) * 2 + 3 + len(root_cases) + 3   # +3: the .md guard, both ways, plus a real file
    print(f"  {total - bad}/{total} checks passed")
    return bad


def check_frontmatter(path: str):
    """A SKILL.md whose YAML does not parse is a skill no agent can load.

    The usual cause is an unquoted description containing ": " — YAML reads that
    as a nested mapping. GitHub shows it as
    "mapping values are not allowed in this context".
    """
    try:
        import yaml
    except ImportError:
        return []
    try:
        src = open(path, encoding="utf-8").read()
    except OSError:
        return [{"rule": "frontmatter", "severity": ERROR, "file": path, "line": 1,
                 "message": "SKILL.md not found.", "fix": "", "snippet": ""}]
    if not src.startswith("---"):
        return [{"rule": "frontmatter", "severity": ERROR, "file": path, "line": 1,
                 "message": "SKILL.md has no YAML frontmatter.",
                 "fix": "Open with --- , then name: and description: , then --- .",
                 "snippet": src[:40]}]
    try:
        end = src.index("\n---", 3)
    except ValueError:
        return [{"rule": "frontmatter", "severity": ERROR, "file": path, "line": 1,
                 "message": "Frontmatter is never closed.", "fix": "Add a closing --- .",
                 "snippet": ""}]
    block = src[4:end]
    try:
        data = yaml.safe_load(block)
    except Exception as e:
        first = str(e).split("\n")[0]
        return [{"rule": "frontmatter", "severity": ERROR, "file": path, "line": 2,
                 "message": f"Frontmatter is not valid YAML: {first}",
                 "fix": "Single-quote the description. An unquoted \": \" reads as a "
                        "nested mapping, and a backslash (Livewire\\Component) breaks "
                        "double-quoted style.",
                 "snippet": block.split("\n")[0][:70]}]
    out = []
    for key in ("name", "description"):
        if not data or key not in data:
            out.append({"rule": "frontmatter", "severity": ERROR, "file": path,
                        "line": 2, "message": f"Frontmatter has no `{key}`.",
                        "fix": "Both name and description are required.", "snippet": ""})
    return out


def main() -> int:
    args = [a for a in sys.argv[1:]]
    if "--self-test" in args:
        print("review.py self-test — every rule must fire, and must not over-fire")
        return self_test()
    if "--frontmatter" in args:
        paths = [a for a in args if not a.startswith("--")] or \
                [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SKILL.md")]
        bad = 0
        for p in paths:
            fs = check_frontmatter(p)
            if fs:
                bad += len(fs)
                for f in fs:
                    print(f"ERROR {f['file']}:{f['line']}  [{f['rule']}]")
                    print(f"      {f['message']}")
                    if f["fix"]:
                        print(f"      fix: {f['fix']}")
            else:
                print(f"  OK  {p}")
        return bad

    as_json = "--json" in args
    paths = [a for a in args if not a.startswith("--")]
    if not paths:
        print(__doc__)
        return 0

    all_findings = []
    for p in paths:
        if not os.path.isfile(p):
            print(f"not a file: {p}", file=sys.stderr)
            continue
        # A .md file holds MANY components. Reviewing it as one source file makes
        # every whole-file rule compare across component boundaries — multi-root
        # counts roots from twelve different templates and reports a defect that
        # is not there. A checker that fires on correct input gets switched off,
        # so refuse the input instead of producing the false finding.
        if p.lower().endswith((".md", ".markdown")) and "--force-md" not in args:
            print(f"REFUSED {p}", file=sys.stderr)
            print("        This is documentation, not a component. It holds several",
                  file=sys.stderr)
            print("        components, so whole-file rules would compare across them.",
                  file=sys.stderr)
            print("        Extract them first, then review the real files:",
                  file=sys.stderr)
            print("          python3 tests/extract-recipes.py <outdir>", file=sys.stderr)
            print("          python3 bin/review.py <outdir>/**/*.php", file=sys.stderr)
            print("        --force-md overrides, and its findings are not trustworthy.",
                  file=sys.stderr)
            print("        (SKILL.md YAML is checked by --frontmatter.)", file=sys.stderr)
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            all_findings += review(fh.read(), p)

    if as_json:
        print(json.dumps(all_findings, indent=2))
    else:
        for f in all_findings:
            print(f"{f['severity']:5} {f['file']}:{f['line']}  [{f['rule']}]")
            print(f"      {f['message']}")
            print(f"      fix: {f['fix']}")
            if f["snippet"]:
                print(f"      >>> {f['snippet']}")
            print()
        errs = sum(1 for f in all_findings if f["severity"] == ERROR)
        warns = sum(1 for f in all_findings if f["severity"] == WARN)
        print(f"{len(all_findings)} finding(s): {errs} error, {warns} warn")

    return sum(1 for f in all_findings if f["severity"] == ERROR)


if __name__ == "__main__":
    sys.exit(main())
