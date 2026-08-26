#!/usr/bin/env python3
"""Find Alpine.js security defects in server templates.

The rules come from source-verified behaviour, not from taste. The most
important one is `server-interp-in-expression`: an Alpine attribute is a
JavaScript context, so a server template that HTML-escapes into one has used
the wrong encoder and the value executes.

Exit code is the number of ERRORS, so this gates.

    python3 review-security.py <file>...
    python3 review-security.py --self-test
"""

import re
import sys

ERROR, WARN = "error", "warn"

# A server-template interpolation of any common engine.
INTERP = r"(?:\{\{(?!--).*?\}\}|\{!!.*?!!\}|<\?=.*?\?>|<%=.*?%>|\$\{.*?\})"

# Alpine attributes whose value Alpine COMPILES as JavaScript (Seam B).
EXPR_ATTRS = (
    r"x-data|x-init|x-effect|x-show|x-if|x-for|x-text|x-model|x-modelable|"
    r"x-id|x-teleport|x-on:[\w.\-]+|@[\w.\-]+|x-bind:[\w.\-]+|:[\w.\-]+"
)

RULES = [
    # ---- Seam B: the severe one -------------------------------------------
    (
        "server-interp-in-expression", ERROR,
        re.compile(r"""(?<![\w:.-])(?P<attr>""" + EXPR_ATTRS + r""")\s*=\s*(?P<q>["'])(?P<val>(?:(?!(?P=q)).)*?"""
                   + INTERP + r"""(?:(?!(?P=q)).)*?)(?P=q)""", re.S),
        "Server data is interpolated into an Alpine expression, which Alpine "
        "compiles with new Function.",
        "HTML-escaping does NOT protect this: the browser decodes the entity "
        "before Alpine reads the attribute, so a quote in the data closes the "
        "string and the rest executes. Encode for JAVASCRIPT with @js(...) / "
        "Js::from(...), or pass the value in a data-* attribute and read it "
        "with $el.dataset. NOTE: this flags the PATTERN. Whether it is "
        "exploitable today depends on where the value comes from -- a "
        "hard-coded loop constant is latent, a user-supplied field is live. "
        "Fix it either way: the pattern becomes a hole the day the source "
        "changes, and nothing will flag that day.",
    ),
    # ---- Seam A -----------------------------------------------------------
    (
        "x-html-directive", WARN,
        re.compile(r"""\bx-html\s*=\s*["'][^"']+["']"""),
        "x-html assigns straight to innerHTML with no sanitisation.",
        "Use x-text unless the HTML is genuinely trusted. x-html also re-runs "
        "Alpine over the injected markup, so x-* inside it is compiled too.",
    ),
    (
        "bind-url-no-scheme-check", WARN,
        re.compile(r"""(?:x-bind:|:)(?:href|src|action|formaction)\s*=\s*["'][^"']+["']"""),
        "A URL attribute is bound from Alpine state, and Alpine applies no "
        "scheme filter.",
        "A value of javascript:... becomes a live javascript: URL. Validate "
        "the scheme server-side, or check it in the expression.",
    ),
    # ---- Client state mistaken for a control ------------------------------
    (
        "authz-flag-in-x-data", WARN,
        re.compile(r"""\bx-data\s*=\s*["'][^"']*\b(is_?[Aa]dmin|is_?[Ss]taff|"""
                   r"""can_?[A-Za-z]+|role|permission|is_?[Pp]aid|is_?[Pp]remium|"""
                   r"""price|amount|total_?cents)\b"""),
        "An authorization- or money-carrying name is in x-data, where the user "
        "can rewrite it from the console.",
        "State on the element is public and writable (node._x_dataStack). Use "
        "it for display only and re-derive the real value on the server for "
        "every request.",
    ),
    (
        "persist-sensitive", ERROR,
        re.compile(r"""\$persist\s*\([^)]*\)\s*\.?\s*as\s*\(\s*["'][^"']*"""
                   r"""(token|secret|api[_-]?key|password|jwt|bearer|session)""",
                   re.I),
        "A sensitive name is persisted to localStorage.",
        "$persist writes plain text to localStorage, keyed _x_<property>, "
        "readable by any script on the origin, and it survives logout. Never "
        "persist a credential.",
    ),
    (
        "model-number-is-not-validation", WARN,
        re.compile(r"""\bx-model\.number\b"""),
        "x-model.number does not guarantee a number.",
        "x-model.js:276 falls back to the raw string when the input is not "
        "numeric, so \"abc\" stays \"abc\" despite the docs saying it will "
        "force a number. Validate on the server.",
    ),
    # ---- The evaluate() sink ----------------------------------------------
    (
        "alpine-evaluate-nonliteral", ERROR,
        re.compile(r"""Alpine\.(?:evaluate|evaluateLater|evaluateRaw)\s*\(\s*[^,()]+,\s*(?P<expr>\S)"""),
        "Alpine.evaluate() is called with an expression that is not a literal.",
        "The expression is compiled with new Function. If any part of it comes "
        "from a request, a form or storage, that is arbitrary code execution. "
        "Expressions must be author-written literals.",
    ),
]


# Alpine's own magics are the only `$name` identifiers that are JavaScript.
# Anything else beginning with `$` inside an attribute is a PHP variable, which
# means the attribute is Blade's `:prop="$var"` component binding and not
# Alpine's `:attr` shorthand at all.
#
# MEASURED on a real 343-template application: without this the URL rule
# produced 14 findings and all 14 were Blade bindings. A rule that is wrong
# every time is a rule people switch off.
ALPINE_MAGICS = (
    "$el", "$refs", "$store", "$watch", "$dispatch", "$nextTick",
    "$id", "$root", "$data", "$persist", "$queryString", "$wire",
)

PHP_TELL = re.compile(r"->|::|\b(?:__|e|route|url|asset|trans|config)\s*\(")


def looks_like_php(fragment):
    """True when an attribute's value is PHP rather than an Alpine expression.

    It tests the RAW fragment, not a neatly extracted value. A rule regex may
    stop at the first inner quote -- `:href="$routes->url('` -- which leaves the
    fragment unbalanced and unparsable as a quoted value, while the PHP tell it
    contains is still plainly there.
    """
    if PHP_TELL.search(fragment):
        return True

    # The text just after the attribute's opening quote.
    m = re.search(r"""=\s*["']\s*(?P<head>[^\s"']{0,40})""", fragment)
    if not m:
        return False

    dollar = re.match(r"""\$\w+""", m.group("head"))

    return bool(dollar and dollar.group(0) not in ALPINE_MAGICS)

def line_of(src, pos):
    return src.count("\n", 0, pos) + 1


def scan(src, path="<input>"):
    findings = []
    for rid, sev, rx, msg, fix in RULES:
        for m in rx.finditer(src):
            # An expression already encoded for JavaScript is correct, not a defect.
            # Blade's `:prop="$var"` component binding collides with
            # Alpine's `:attr` shorthand. Blade's value is PHP; Alpine's is
            # JavaScript. Telling them apart removes the whole false-positive
            # class that made an earlier checker unusable.
            if rid in ("bind-url-no-scheme-check", "server-interp-in-expression"):
                if looks_like_php(m.group(0)):
                    continue

            # A literal expression is the documented, correct use.
            if rid == "alpine-evaluate-nonliteral":
                if m.group("expr") in ('"', "'", "`"):
                    continue

            if rid == "server-interp-in-expression":
                window = m.group(0)
                if re.search(r"@js\s*\(|Js::from|json_encode|\|\s*json|@json\b", window):
                    continue
            findings.append({
                "rule": rid, "severity": sev, "file": path,
                "line": line_of(src, m.start()), "message": msg, "fix": fix,
                "snippet": m.group(0).strip().split("\n")[0][:100],
            })
    seen, unique = set(), []
    for f in findings:
        key = (f["file"], f["line"], f["rule"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(f)

    return sorted(unique, key=lambda f: (f["line"], f["rule"]))


def report(findings):
    for f in findings:
        mark = "ERROR" if f["severity"] == ERROR else "warn "
        print(f"{mark}  {f['file']}:{f['line']}  [{f['rule']}]")
        print(f"       {f['message']}")
        print(f"       {f['snippet']}")
        print(f"       fix: {f['fix']}")
        print()
    return sum(1 for f in findings if f["severity"] == ERROR)


# ---------------------------------------------------------------------------
# Self-test. Every rule must FIRE on the defect and stay SILENT on the fix.
# A checker that never fires is indistinguishable from a broken one, and one
# that fires on correct code is one people switch off.
# ---------------------------------------------------------------------------

MUST_FIRE = [
    ("server-interp-in-expression", """<div x-data="{ name: '{{ $displayName }}' }"></div>"""),
    ("server-interp-in-expression", """<button @click="buy('{{ $sku }}')">go</button>"""),
    ("server-interp-in-expression", """<div x-init="track('{{ $ref }}')"></div>"""),
    ("server-interp-in-expression", """<span x-text="'{{ $name }}'"></span>"""),
    ("server-interp-in-expression", """<div x-show="{{ $flag }}"></div>"""),
    ("server-interp-in-expression", """<li x-data="{ id: <?= $id ?> }"></li>"""),
    ("x-html-directive", """<div x-html="body"></div>"""),
    ("bind-url-no-scheme-check", """<a :href="userUrl">x</a>"""),
    ("bind-url-no-scheme-check", """<img x-bind:src="avatar">"""),
    ("authz-flag-in-x-data", """<div x-data="{ isAdmin: false }"></div>"""),
    ("authz-flag-in-x-data", """<div x-data="{ price: 100 }"></div>"""),
    ("persist-sensitive", """<div x-data="{ t: $persist('').as('api_token') }"></div>"""),
    ("model-number-is-not-validation", """<input x-model.number="qty">"""),
    ("alpine-evaluate-nonliteral", """Alpine.evaluate(el, userSuppliedString)"""),
]

MUST_STAY_SILENT = [
    # The documented fixes.
    """<div x-data="@js(['name' => $displayName])"></div>""",
    """<div x-data="{{ Js::from($data) }}"></div>""",
    """<div data-name="{{ $displayName }}" x-data="{ name: $el.dataset.name }"></div>""",
    """<button @click="buy(sku)">go</button>""",
    # Ordinary correct Alpine with no server data in the expression.
    """<div x-data="{ open: false }"><button @click="open = !open">t</button></div>""",
    """<span x-text="message"></span>""",
    """<template x-for="c in colors" :key="c.id"><li x-text="c.label"></li></template>""",
    # Server interpolation OUTSIDE any Alpine expression is fine.
    """<p>Hello {{ $name }}</p>""",
    """<div class="{{ $classes }}" x-data="{ open: false }"></div>""",
    # A literal expression passed to evaluate is the documented use.
    """Alpine.evaluate(el, 'count + 1')""",
    # A Blade comment must not read as an interpolation.
    """<div x-data="{ open: false }">{{-- a comment --}}</div>""",
    # data-* binding is the safe route and must not trip the URL rule's cousin.
    """<a href="{{ $url }}">plain link</a>""",
]


def self_test():
    passed = failed = 0

    for rule, src in MUST_FIRE:
        hits = [f["rule"] for f in scan(src)]
        if rule in hits:
            passed += 1
        else:
            failed += 1
            print(f"  DID NOT FIRE  [{rule}]  {src[:70]}")
            print(f"                got: {hits or 'nothing'}")

    for src in MUST_STAY_SILENT:
        hits = scan(src)
        if not hits:
            passed += 1
        else:
            failed += 1
            print(f"  OVER-FIRED    {src[:70]}")
            for h in hits:
                print(f"                [{h['rule']}] {h['snippet'][:60]}")

    total = passed + failed
    print(f"\nalpine review-security.py self-test — {passed}/{total} checks passed")
    if failed:
        print("A rule that cannot fire is indistinguishable from a broken one.")
    return failed


def main(argv):
    if "--self-test" in argv:
        return self_test()
    if "--help" in argv or not argv[1:]:
        print(__doc__)
        return 0

    errors = 0
    for path in argv[1:]:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                src = fh.read()
        except OSError as exc:
            print(f"cannot read {path}: {exc}", file=sys.stderr)
            continue
        errors += report(scan(src, path))

    if errors:
        print(f"{errors} error(s).")
    return errors


if __name__ == "__main__":
    sys.exit(main(sys.argv))
