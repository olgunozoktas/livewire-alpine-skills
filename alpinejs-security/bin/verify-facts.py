#!/usr/bin/env python3
"""Check this skill's statements about Alpine against a real Alpine checkout.

The skill names line numbers, a sink, an evaluator and a default. Any of those
can change in a release, and the skill would then give confident wrong advice
with nobody noticing.

    python3 verify-facts.py <path-to-alpine>   # a checkout or node_modules/alpinejs

Exit code is the number of failed statements.
"""

import os
import sys

# (relative path, must-contain, the claim in the skill it supports)
CHECKS = [
    ("packages/alpinejs/src/evaluator.js", "AsyncFunction",
     "Alpine still compiles expressions with the Function constructor (Seam B)"),
    ("packages/alpinejs/src/evaluator.js", "with (scope)",
     "The compiled body still wraps the expression in `with (scope)`"),
    ("packages/alpinejs/src/mutation.js", "subtree: true",
     "The MutationObserver still watches the whole document, so injected x-* is compiled"),
    ("packages/alpinejs/src/directives/x-html.js", "innerHTML",
     "x-html still assigns innerHTML with no sanitisation"),
    ("packages/alpinejs/src/directives/x-text.js", "textContent",
     "x-text still assigns textContent, which is why it is the safe one"),
    ("packages/alpinejs/src/directives/x-ignore.js", "_x_ignore",
     "x-ignore still only sets a flag, so it stays a mitigation and not a sink"),
    ("packages/alpinejs/src/scope.js", "_x_dataStack",
     "Component state still lives on the DOM node, reachable from the console"),
    ("packages/alpinejs/src/store.js", "stores[name] = value",
     "Any store is still writable with no guard"),
    ("packages/persist/src/index.js", "localStorage",
     "$persist still defaults to localStorage"),
    ("packages/csp/src/parser.js", "__proto__",
     "The CSP build still blocks the constructor/prototype escape"),
]

# Statements that must NOT be true. A checker that only confirms is half a checker.
MUST_NOT_CONTAIN = [
    ("packages/csp/src/parser.js", "new Function",
     "The CSP build still constructs no function from a string"),
]


def main(argv):
    if len(argv) < 2 or argv[1] in ("--help", "-h"):
        print(__doc__)
        return 0

    root = argv[1].rstrip("/")
    if not os.path.isdir(root):
        print(f"not a directory: {root}", file=sys.stderr)
        return 1

    results = []

    for rel, must, claim in CHECKS:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            results.append((False, f"{claim} — the file is gone: {rel}"))
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        results.append((must in body, claim if must in body
                        else f'{claim} — "{must}" is no longer in {rel}'))

    for rel, absent, claim in MUST_NOT_CONTAIN:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            results.append((False, f"{claim} — the file is gone: {rel}"))
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        results.append((absent not in body, claim if absent not in body
                        else f'{claim} — but "{absent}" now APPEARS in {rel}'))

    failed = sum(1 for ok, _ in results if not ok)

    print(f"alpinejs-security verify-facts — {root}\n")
    for ok, claim in results:
        print(f"  {' ok ' if ok else 'FAIL'}  {claim}")
    print(f"\n{len(results) - failed}/{len(results)} statements still hold")

    if failed:
        print("\nThe skill states something this Alpine version no longer does. "
              "Correct the skill.", file=sys.stderr)

    return failed


if __name__ == "__main__":
    sys.exit(main(sys.argv))
