#!/usr/bin/env python3
"""Review Alpine.js markup for v2-isms and documented traps.

    python3 bin/review.py path/to/file.blade.php [more...]
    python3 bin/review.py --json <file>
    python3 bin/review.py --self-test

Exit code is the number of ERROR findings, so it works as a gate.

Every rule maps to something in the official docs. `--self-test` feeds each rule
a sample that must trigger it and one that must not — a checker that can never
fire is indistinguishable from a broken one.
"""
import re
import sys
import json
import os

ERROR, WARN = "ERROR", "WARN"

RULES = [
    ("v2-x-spread", ERROR,
     r"\bx-spread\s*=",
     "x-spread was renamed in v3.",
     "Use x-bind with no attribute: x-bind=\"trigger\".",
     '<button x-spread="trigger">', '<button x-bind="trigger">'),

    ("v2-show-transition", ERROR,
     r"x-show\.transition[.\w]*\s*=",
     "x-show.transition was replaced in v3.",
     "Use x-show=\"open\" plus a separate x-transition directive.",
     '<div x-show.transition="open">', '<div x-show="open" x-transition>'),

    ("v2-if-transition", ERROR,
     r"x-if\.transition\b",
     "x-if never supports transitions in v3.",
     "Only x-show transitions. Use x-show + x-transition.",
     '<template x-if.transition="open">', '<template x-if="open">'),

    ("v2-click-away", WARN,
     r"@[a-z]+\.away\b|x-on:[a-z]+\.away\b",
     "The .away modifier is deprecated.",
     "Use .outside.",
     '<div @click.away="open = false">', '<div @click.outside="open = false">'),

    ("v2-defer-loading", ERROR,
     r"deferLoadingAlpine",
     "Alpine.deferLoadingAlpine() was removed in v3.",
     "Use the alpine:init and alpine:initialized events.",
     'window.deferLoadingAlpine = cb => cb()',
     "document.addEventListener('alpine:init', () => {})"),

    ("v2-dynamic-ref", ERROR,
     r":x-ref\s*=|x-bind:x-ref\s*=",
     "x-ref cannot be bound in v3.",
     "$refs only resolves statically declared refs; a bound one yields the "
     "literal expression string.",
     '<div :x-ref="item.name">', '<div x-ref="row">'),

    ("if-not-on-template", ERROR,
     r"<(?!template\b)[a-zA-Z][\w.-]*[^>]*\sx-if\s*=",
     "x-if must be on a <template> tag.",
     "On any other element it silently does nothing.",
     '<div x-if="open">…</div>',
     '<template x-if="open"><div>…</div></template>'),

    ("for-not-on-template", ERROR,
     r"<(?!template\b)[a-zA-Z][\w.-]*[^>]*\sx-for\s*=",
     "x-for must be on a <template> tag.",
     "On any other element it silently does nothing.",
     '<li x-for="c in colors">…</li>',
     '<template x-for="c in colors"><li>…</li></template>'),

    ("for-missing-key", WARN,
     r"<template[^>]*\sx-for\s*=\s*\"[^\"]*\"(?![^>]*:key)[^>]*>",
     "x-for with no :key.",
     "Without a key Alpine cannot tell a move from a change, and destroys "
     "elements it should have moved.",
     '<template x-for="c in colors">',
     '<template x-for="c in colors" :key="c.id">'),

    ("html-injection", WARN,
     r"x-html\s*=",
     "x-html sets innerHTML.",
     "Only ever use it on trusted content — third-party HTML here is a direct "
     "XSS vector.",
     '<div x-html="body">', '<div x-text="body">'),

    ("persist-arrow-in-data", ERROR,
     r"Alpine\.data\(\s*['\"][\w-]+['\"]\s*,\s*\(\s*\)\s*=>\s*\(\{[\s\S]{0,300}?\$persist\(",
     "$persist inside an arrow function passed to Alpine.data().",
     "An arrow function has no `this` to bind. Use a normal function: "
     "Alpine.data('x', function () { return { v: this.$persist(0) } }).",
     "Alpine.data('d', () => ({ v: $persist(0) }))",
     "Alpine.data('d', function () { return { v: this.$persist(0) } })"),

    ("watch-self-mutation", ERROR,
     r"\$watch\(\s*['\"](\w+)['\"]\s*,\s*(?:\([^)]*\)|\w+)\s*=>\s*\1\.\w+\s*=",
     "$watch callback writes to the object it watches.",
     "That loops forever and eventually errors.",
     "$watch('foo', value => foo.bar = 1)",
     "$watch('foo', value => other.bar = 1)"),

]

CLOAK_RE = re.compile(r"\bx-cloak\b")
CLOAK_CSS_RE = re.compile(r"\[x-cloak\]")

# Element-level "is there an x-data?" cannot see an ANCESTOR's x-data, so it
# fires on correct markup. This is the file-level version, and it stays silent
# inside a Livewire component, where every root is implicitly an Alpine
# component and x-data is not required.
ALPINE_DIRECTIVE_RE = re.compile(r"\sx-(?:show|text|model|effect|for|if|html|bind|on)\b|\s@[a-z]+\s*=|\s:[a-z-]+\s*=")
XDATA_RE = re.compile(r"\bx-data\b")
LIVEWIRE_RE = re.compile(r"\bwire:|\$wire\b|new class extends Component|extends Component")


def strip_comments(src: str) -> str:
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
            j = src.find("\n", i)
            j = n if j == -1 else j
            for k in range(i, j):
                out[k] = " "
            i = j
        elif two == "<!":
            j = src.find("-->", i)
            if src[i:i + 4] == "<!--" and j != -1:
                for k in range(i, j + 3):
                    if out[k] != "\n":
                        out[k] = " "
                i = j + 3
            else:
                i += 1
        else:
            i += 1
    return "".join(out)


def line_of(src: str, pos: int) -> int:
    return src.count("\n", 0, pos) + 1


def review(src: str, path: str = "<input>"):
    findings = []
    scan = strip_comments(src)

    for rid, sev, pat, msg, fix, _h, _m in RULES:
        for m in re.finditer(pat, scan, re.M):
            findings.append({
                "rule": rid, "severity": sev, "file": path,
                "line": line_of(src, m.start()), "message": msg, "fix": fix,
                "snippet": src[m.start():m.end()].strip().split("\n")[0][:90],
            })

    # x-cloak needs its CSS to exist somewhere, or it does nothing at all.
    if CLOAK_RE.search(scan) and not CLOAK_CSS_RE.search(scan):
        m = CLOAK_RE.search(scan)
        findings.append({
            "rule": "cloak-without-css", "severity": WARN, "file": path,
            "line": line_of(src, m.start()),
            "message": "x-cloak is used but [x-cloak] CSS is not in this file.",
            "fix": "x-cloak does NOTHING without `[x-cloak] { display: none "
                   "!important; }`. Confirm it is in a global stylesheet.",
            "snippet": "x-cloak",
        })

    if (ALPINE_DIRECTIVE_RE.search(scan)
            and not XDATA_RE.search(scan)
            and not LIVEWIRE_RE.search(scan)):
        m = ALPINE_DIRECTIVE_RE.search(scan)
        findings.append({
            "rule": "no-x-data-in-file", "severity": WARN, "file": path,
            "line": line_of(src, m.start()),
            "message": "Alpine directives here, but no x-data anywhere in this file.",
            "fix": "Alpine does nothing outside an x-data scope. Either this is "
                   "a partial whose parent supplies x-data, or the x-data is "
                   "missing. (Inside a Livewire component x-data is not needed — "
                   "every component root is already an Alpine component.)",
            "snippet": src[m.start():m.end()].strip()[:60],
        })

    findings.sort(key=lambda f: (f["line"], f["rule"]))
    return findings


def self_test() -> int:
    bad = 0
    for rid, sev, pat, msg, fix, hit, miss in RULES:
        if not [f for f in review(hit) if f["rule"] == rid]:
            print(f"  FAIL {rid}: did not fire on its hit sample"); bad += 1
        if [f for f in review(miss) if f["rule"] == rid]:
            print(f"  FAIL {rid}: fired on its miss sample"); bad += 1
    if not [f for f in review('<div x-cloak x-show="false">') if f["rule"] == "cloak-without-css"]:
        print("  FAIL cloak-without-css: did not fire"); bad += 1
    if [f for f in review('<style>[x-cloak]{display:none!important}</style>\n<div x-cloak>')
        if f["rule"] == "cloak-without-css"]:
        print("  FAIL cloak-without-css: fired when the CSS was present"); bad += 1

    xdata_cases = [
        ("no x-data at all", '<div x-show="open">hi</div>', True),
        ("x-data on an ANCESTOR", '<div x-data="{ open: false }">\n  <div x-show="open">hi</div>\n</div>', False),
        ("inside a Livewire component", '<div wire:id="x">\n  <div x-show="open">hi</div>\n</div>', False),
        ("plain HTML, no Alpine", '<div class="card">hi</div>', False),
    ]
    for label, src, should_fire in xdata_cases:
        if bool([f for f in review(src) if f["rule"] == "no-x-data-in-file"]) != should_fire:
            print(f"  FAIL no-x-data-in-file ({label})"); bad += 1

    total = len(RULES) * 2 + 2 + len(xdata_cases)
    print(f"  {total - bad}/{total} checks passed")
    return bad


def main() -> int:
    args = sys.argv[1:]
    if "--self-test" in args:
        print("alpine review.py self-test — every rule must fire, and must not over-fire")
        return self_test()

    as_json = "--json" in args
    paths = [a for a in args if not a.startswith("--")]
    if not paths:
        print(__doc__)
        return 0

    out = []
    for p in paths:
        if not os.path.isfile(p):
            print(f"not a file: {p}", file=sys.stderr)
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            out += review(fh.read(), p)

    if as_json:
        print(json.dumps(out, indent=2))
    else:
        for f in out:
            print(f"{f['severity']:5} {f['file']}:{f['line']}  [{f['rule']}]")
            print(f"      {f['message']}")
            print(f"      fix: {f['fix']}")
            print(f"      >>> {f['snippet']}\n")
        e = sum(1 for f in out if f["severity"] == ERROR)
        w = sum(1 for f in out if f["severity"] == WARN)
        print(f"{len(out)} finding(s): {e} error, {w} warn")
    return sum(1 for f in out if f["severity"] == ERROR)


if __name__ == "__main__":
    sys.exit(main())
