# alpinejs-development

An [Agent Skill](https://agentskills.io/what-are-skills) for **Alpine.js v3** —
written from all 55 files of the official documentation.

Alpine is not only a Laravel tool. It runs with Blade, Rails, Django, Hotwire and
any HTML-over-the-wire stack, so the language reference lives here rather than
inside a Laravel skill.

**In a Laravel project, invoke `livewire-reference` instead** — it is the entry
point for the whole stack and pulls this skill in via `bin/stack.sh`. Use this
one directly for Alpine outside Laravel.

---

## Why it exists

Alpine's traps are quiet ones. `x-if` on a non-`<template>` element silently does
nothing. `x-cloak` without its CSS does nothing. A `$watch` callback that writes
to the object it watches loops forever. `x-modelable` clones through JSON, so a
`File` arrives without its name, size or type. None of these produce a useful
error message.

And v2 idioms still circulate — one of them, `$el`, is *silently wrong* rather
than broken: it meant the component **root** in v2 and means the **current
element** in v3.

---

## Layout

```
SKILL.md                  always loaded — mental model, the three rules, Livewire pairing
references/               5 files, 2,646 lines
bin/review.py             14 rules, 30 self-test cases
```

| File | Covers |
|---|---|
| `references/directives.md` | All 18 directives — every `x-on` and `x-model` modifier, every input type, the transition helper *and* class APIs, the `x-bind` object syntax |
| `references/magics-globals.md` | All 9 magics, the 3 globals, `init()`/`destroy()`, lifecycle events, installing |
| `references/plugins.md` | All 9 official plugins — mask, intersect, persist, collapse, focus/trap, anchor, sort, resize, morph |
| `references/extending.md` | `Alpine.directive()` and `Alpine.magic()`, `evaluateLater`/`effect`/`cleanup`, authoring plugins, the reactivity engine, async, the CSP build |
| `references/v2-to-v3.md` | The v2 → v3 upgrade guide — every breaking change and both deprecations |

---

## The tool

```bash
python3 bin/review.py <file>...      # v2-isms and documented traps
python3 bin/review.py --self-test    # 30 cases prove all 14 rules still fire
python3 bin/review.py --json <file>  # machine-readable
```

Exit code is the error count, so it gates.

**14 rules** — 12 pattern rules plus two that read the whole file: `x-spread`, `x-show.transition`, `x-if.transition`, `.away`,
`deferLoadingAlpine`, bound `x-ref`, `x-if`/`x-for` not on a `<template>`,
`x-for` without `:key`, `x-html` on untrusted content, `$persist` with an arrow
function inside `Alpine.data()`, a `$watch` callback that writes to the object it
watches, `x-cloak` with no `[x-cloak]` CSS, and Alpine directives in a file with
no `x-data`.

**Calibrated in both directions** — 7 errors on v2-era markup, **0 findings on
correct Livewire+Alpine**. The no-`x-data` check knows two things a naive version
gets wrong: `x-data` may sit on an **ancestor**, and inside a Livewire component
it is not needed at all, because every component root is already an Alpine
component.

---

## Using it with Livewire

Livewire bundles **Alpine 3.16.3** and every Alpine plugin except
`@alpinejs/ui`. Do not add a second copy — that gives you
"Detected multiple instances of Alpine running" and `$wire is not defined`.

Three plugins have a Livewire counterpart. Inside a Livewire component prefer the
Livewire one, because it calls a component action directly:

| Task | Alpine | Prefer in Livewire |
|---|---|---|
| Viewport intersection | `x-intersect` | `wire:intersect` |
| Drag-and-drop sorting | `x-sort` | `wire:sort` |
| Teleporting markup | `x-teleport` | `@teleport` |

**`wire:transition` is not `x-transition`.** In Livewire v4 it uses the View
Transitions API and takes no modifiers; Alpine's keeps its full modifier and
class API.

---

## Provenance

All 55 files of `packages/docs/src/en` in
[`alpinejs/alpine`](https://github.com/alpinejs/alpine). Version 3.16.3 — what
Livewire 4.x bundles.

Coverage is verified by extracting the API surface — every directive, magic,
global and plugin — and diffing it against the skill.
**Last audit 2026-08-26: clean.**

The Livewire skill's `bin/refresh.sh` re-audits this one too.

---

## License

MIT. Content derived from the Alpine.js documentation, MIT licensed,
© Caleb Porzio and contributors.
