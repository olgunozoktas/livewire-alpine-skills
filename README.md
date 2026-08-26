# Livewire v4 + Alpine.js — Agent Skills

[![Skills](https://img.shields.io/badge/skills-4-0f172a)](#whats-inside)
[![Self-tests](https://img.shields.io/badge/self--tests-124%20checks-2ea44f)](#the-skill-ships-tools-not-just-text)
[![Recipes](https://img.shields.io/badge/recipes-executed%20%C2%B7%2014%20tests%2C%2054%20assertions-2ea44f)](#the-recipes-are-executed-not-just-written)
[![Livewire](https://img.shields.io/badge/livewire-v4.4.2-fb70a9)](https://livewire.laravel.com)
[![Alpine.js](https://img.shields.io/badge/alpine.js-v3-77c1d2)](https://alpinejs.dev)
[![Entry point](https://img.shields.io/badge/loads%20on%20invoke-514%20lines-64748b)](#whats-inside)
[![Depth](https://img.shields.io/badge/read%20on%20demand-8,416%20lines-64748b)](#whats-inside)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Four [Agent Skills](https://agentskills.io/what-are-skills) that teach an AI coding
assistant **Laravel Livewire v4** and **Alpine.js v3** accurately — with complete
working recipes, a symptom-to-fix troubleshooting guide, version detection, and
the security half that Livewire's own defaults make easy to get wrong.

Works with Claude Code, Codex, Cursor, Gemini CLI, and anything else that reads
the `SKILL.md` format.

| Skill | Loads on invoke | Read on demand | Covers |
|---|---|---|---|
| [`livewire-reference`](livewire-reference/) | **514** | 8,416 | All 98 files of the Livewire 4.x documentation, plus v3 differences |
| [`alpinejs-reference`](alpinejs-reference/) | **250** | 2,646 | All 55 files of the Alpine.js documentation, plus the v2→v3 guide |
| [`livewire-security`](livewire-security/) | **324** | 418 | What a component publishes, what a browser can change, how to detect a leak |
| [`livewire-performance`](livewire-performance/) | **178** | 328 | What a request costs, how to measure it, and which fix matches which number |

**Only `SKILL.md` enters context when a skill is invoked.** The `references/`
files are read on demand through a routing table inside it, and `bin/` is
executed rather than read. So the entry point is 514 lines, not 10,000 — the
depth is there when a task needs it and costs nothing when it does not.

The always-loaded cost is smaller still: an agent sees only each skill's
`description`, which is about 220 tokens for the largest of the four.

> **Renamed in 1.0.0.** `livewire-development` → **`livewire-reference`**, and
> `alpinejs-development` → **`alpinejs-reference`**. Laravel Boost ships its own
> skill named `livewire-development`, and an identical name read as a
> replacement for it; the Alpine rename follows for consistency. To update a
> copy you installed:
>
> ```bash
> rm -rf ~/.claude/skills/livewire-development ~/.claude/skills/alpinejs-development
> cp -R livewire-reference alpinejs-reference livewire-security ~/.claude/skills/
> ```
>
> No stub remains at either old name — a stub would restore the collision.
> [`CHANGELOG.md`](CHANGELOG.md) has the rest.

**Every badge above is a local measurement, not a CI run.** This repository has
no GitHub Actions workflow. The self-test counts come from the commands in
[Validation](#validation); run them yourself and the numbers should match.

**Invoke `livewire-reference` for the stack.** `livewire-security` is separate
because it is read at a different moment — before shipping a component on a
public route, or during a security review — and because most Livewire work does
not need it.

**Invoke `livewire-reference` and you get both halves of the stack.** Livewire bundles Alpine, so
real work touches both halves — `bash bin/stack.sh` finds the Alpine skill and
prints both file maps. They stay two skills because Alpine also runs with Rails,
Django and Hotwire.

---

## Why these exist

**Livewire v4 changed its defaults, and most model training data is v2 or v3.**
An assistant left to its own knowledge will confidently write code that no longer
works. These are the twelve items the skill corrects before anything else:

| Topic | v2 / v3 (what models write) | v4 (correct) |
|---|---|---|
| Component format | Class in `app/Livewire/` + separate view | **Single-file component** at `resources/views/components/…/⚡name.blade.php` |
| Page routing | `Route::get('/x', Show::class)` | **`Route::livewire('/x', 'pages::show')`** |
| Volt | The way to get single-file components | **Only the class-based half moved into core** — the functional API is still a separate package |
| `<script>` in a template | Always needs `@script` | Bare `<script>` in SFC/MFC; `@script` only for class-based |
| `wire:model.blur` | Controlled network timing | Controls **client-side sync** too — use `.live.blur` for the old behavior |
| `wire:transition` | Alpine wrapper with modifiers | **View Transitions API**, no modifiers |
| Component tags | Unclosed tags rendered | **Must be closed**, or content is read as a slot |
| `wire:model` on a container | Caught child events | Element only — add `.deep` for the old behavior |
| Config layout key | `'layout'` | **`'component_layout' => 'layouts::app'`** |
| Endpoint URLs | `/livewire/update` | **`/livewire-{hash}/…`**, derived from `APP_KEY` |
| `$this->stream()` | `stream(to: …, content: …)` | **`stream(content: …, name:/el:/ref: …)`** |
| JS actions | `$js('name', cb)` | **`this.$js.name = () => {}`** |

Plus everything new in v4: islands, `wire:sort`, `wire:intersect`, `wire:ref`,
`wire:bind`, `wire:text`, `#[Async]`, `#[Json]`, `#[Authorize]`, the automatic
`data-loading` and `data-current` attributes, the `$errors` magic, and
interceptors.

---

## Use cases

What the skills are actually for. Each names the file that answers it.

| You ask | The skill gives you |
|---|---|
| "Build a post editor with validation" | A complete component — real-time validation on blur, `data-loading` button states, authorization in both `mount()` and the action |
| "Add search, filters, sorting and pagination to this table" | The whole screen, plus the four things that make it correct: computed property, `resetPage()` on filter change, `wire:key` per row, debounced search |
| "Why does my list show the wrong rows after sorting?" | A triage table — almost always a missing or colliding `wire:key` |
| "This page is slow" | Islands vs `lazy` vs `defer` vs bundling, and the rule for choosing |
| "Make this feel instant" | Optimistic UI with `wire:text` + `#[Renderless]` |
| "Upgrade this app from Livewire 3" | The full migration guide and a checklist |
| "Is this component secure?" | The three ways a Livewire component leaks, and `#[Locked]` / `#[Authorize]` |
| "Add real-time updates" | Laravel Echo wiring, including the leading dot on `broadcastAs()` names that silently breaks listeners |
| "Write tests for this" | Every `Livewire::test()` assertion, and which tests are worth writing |
| "Add a modal / dropdown / drag-and-drop" | Accessible implementations, and which half belongs to Alpine |
| "What version is this project on?" | Detection commands, every v3 difference, and what does not exist before v4 |

---

## Install

### Claude Code

```bash
git clone https://github.com/olgunozoktas/livewire-alpine-skills.git /tmp/lw-skills
cp -R /tmp/lw-skills/livewire-reference  ~/.claude/skills/
cp -R /tmp/lw-skills/alpinejs-reference  ~/.claude/skills/
cp -R /tmp/lw-skills/livewire-security   ~/.claude/skills/
cp -R /tmp/lw-skills/livewire-performance ~/.claude/skills/
```

Per-project instead of global: copy into `.claude/skills/` in the repo.

Restart the session. The assistant loads a skill on its own when the task
matches; `/livewire-reference` invokes it explicitly.

### One invocation covers both

Livewire bundles Alpine, so real work touches both. From a Laravel project you
only need to invoke **`livewire-reference`** — it is the entry point for the
whole stack:

```bash
bash bin/stack.sh     # finds the Alpine skill and prints both file maps
```

It resolves the pairing in any layout (installed, this repo, or a source tree,
symlinks included) and shows which half answers which question. They stay two
skills because Alpine is also used with Rails, Django and Hotwire — invoke
`alpinejs-reference` directly for those.

### Other agents

Copy the same two directories into whatever skills directory your tool reads —
`.ai/skills/` for Laravel Boost, `.codex/skills/`, `.cursor/skills/`, and so on.

---

## Using this alongside Laravel Boost

Boost ships its own Livewire skill, named `livewire-development`
(`author: laravel`), and installs it into `.ai/skills/`.

**This skill used to carry that same name, and no longer does.** An identical
name reads as a replacement for Boost's skill, which was never the intent. Boost
documents that a project-level skill of the same name overrides its built-in
one — so the old name did not break anything, it just said the wrong thing.

**They are complementary — run both.** Boost knows your Livewire version and
reads your `config/livewire.php`; it is deliberately terse because it is paired
with a live `search-docs` index. These skills are the depth behind it.

### Side by side

Measured against `laravel/boost`'s `.ai/livewire/4/skill/livewire-development`.

| | Laravel Boost | These skills |
|---|---|---|
| **Livewire skill size** | 203 lines, 2 files | **10,603 lines, 48 files** |
| **Alpine skill** | none | **3,132 lines** |
| Complete worked recipes | 1 (a counter) | **12, all executed** |
| Troubleshooting | 5 bullets | **30-row triage + deep dives** |
| Per-directive coverage | a 5-row table | **every directive, every modifier** |
| Per-attribute coverage | not covered | **every attribute, every parameter** |
| Volt | separate skill | functional API + migration path |
| **Version-aware** | **ships v2/v3/v4 variants** | detects, and documents v3 differences |
| **Project-aware config** | **Blade-rendered: real artisan + app paths** | `detect.sh` reports it |
| **Live documentation** | **`search-docs`, 17k entries, semantic** | defers to Boost's |
| **Auto-updates** | **`boost:update`** | `refresh.sh`, run manually |
| Recipes executed | — | **14 tests, 54 assertions** |
| Code reviewer | — | **80 self-tested checks, gates on exit code** |
| Scaffolder | `make:livewire` guidance | **refuses v4-only flags on v3** |
| Objective eval | — | **`eval.sh --compare`** |
| Maintained by | **Laravel, with the framework** | this repo |
| Install | `composer require laravel/boost` | copy two directories |

**Boost wins on the bolded rows in its column, and those wins are structural.**
It is a Composer package, so it knows your Livewire version, renders your real
paths, and updates itself. It is terse *on purpose* — it is paired with a live
documentation index, so it does not need to carry the depth.

These skills win on depth, on worked examples, on debugging, and on being
*verified* rather than asserted. Neither replaces the other.

### Which to ask

| Question | Best source |
|---|---|
| "What changed in the release last week?" | Boost `search-docs` — live and version-aware |
| "Which format does *this* project use?" | Boost, or `bin/detect.sh` |
| "Every modifier of `wire:target`" | These skills |
| "Why did my morph put state on the wrong element?" | These skills |
| "A complete searchable, paginated table" | These skills |
| "Is this component secure / idiomatic?" | These skills — `bin/review.py` |

If the two contradict each other on a fact, **prefer the live docs** and treat
this snapshot's date as the tiebreaker. `bin/detect.sh` warns when your project's
Livewire is newer than this skill's verification.

---

## What's inside

### `livewire-reference`

| File | Covers |
|---|---|
| `SKILL.md` | Version + convention preflight, the v3→v4 correction table, component anatomy, the mental model, security rules, task routing |
| `references/recipes.md` | **Fast idioms**, then **twelve complete components** — CRUD, search/filter/sort/paginate, modal, upload with progress, infinite scroll, wizard, optimistic UI, dependent selects, Echo, form objects, tests |
| `references/troubleshooting.md` | **Symptom → cause → fix** table, the three most common bugs in depth, debugging tools, reading the network tab |
| `references/version-guide.md` | Detecting the installed version, every v3 difference, what does not exist before v4, why v2 is out of scope |
| `references/directives.md` | Every `wire:` directive — every modifier, `wire:target`'s four targeting forms |
| `references/attributes.md` | Every PHP attribute — parameters and non-obvious behaviors |
| `references/components.md` | The three formats, pages, layouts, namespaces, nesting, reactive props, slots, attribute forwarding |
| `references/properties-actions.md` | Property types and serialization, `wire:model`, actions, magic actions, `#[Async]`, events, Laravel Echo, lifecycle hooks |
| `references/forms-validation.md` | Forms, form objects, validation, file uploads, pagination, URL and session state |
| `references/islands-performance.md` | Islands, lazy vs deferred, `data-loading`, polling, `wire:navigate` and its JS hooks |
| `references/javascript.md` | Component scripts, the full `$wire` API, interceptors, the `Livewire` global, hooks, custom directives, scoped styles |
| `references/advanced.md` | Hydration and snapshots, synthesizers, morphing, component hooks, persistent middleware, downloads, package development, CSP, streaming |
| `references/alpine.md` | Alpine **inside** Livewire — `$wire`, entangle, morph vs Alpine state, event crossover |
| `references/testing.md` | Pest setup, every `Livewire::test()` method and assertion, browser testing |
| `references/reference.md` | Redirects, Blade directives, the full config, advanced installation |
| `references/volt.md` | The Volt functional API, and migrating class-based Volt to core |
| `references/v3-to-v4.md` | The complete upgrade guide |
| `bin/detect.sh` | Reports what the project actually does. Read-only |
| `bin/scaffold.sh` | Creates a component in the project's own conventions |
| `bin/review.py` | 21 checks for v3-isms, security holes and known traps |
| `bin/verify-recipes.sh` | Scaffolds a throwaway app and **runs every recipe**. 14 tests, 54 assertions |
| `bin/refresh.sh` | Re-audits the skill against the current docs. Read-only |
| `bin/check-update.sh` | Reports a newer release of these skills. Fails open on every path, caches 24h, one unauthenticated GET. `--self-test` proves it can speak and stay silent |
| `bin/eval.sh` | Scores code quality objectively |
| `tests/` | The verification harness and the eval baseline |

### `livewire-security`

| File | Covers |
|---|---|
| `SKILL.md` | Why `public` means published AND writable, the six rules, why an allow-list is not a boundary in Livewire, how to build a canary sweep that does not lie, and the traps that cost real time |
| `references/attack-surface.md` | The features that carry their own risk — a cached computed property shared by every user, event listeners a browser can call, the upload defaults, `wire:navigate` state, `#[Url]`, and parent access in v4. Each statement names the file that proves it |
| `bin/scan.php` | 7 static checks — a model on a public property, an identity-named public property, a non-private page-prop bag, an unauthorized record mutator, a `#[Url]` identifier without `#[Locked]`, an untyped public property, a `#[Computed(cache: true)]` with no key. No bootstrap, no database, no autoloader |
| `bin/verify-facts.php` | Checks the skill's own statements against the installed Livewire — the exception namespace, the persistent middleware list, the computed cache keys, the upload defaults. 28 statements. Run it after an upgrade |

### `livewire-performance`

| File | Covers |
|---|---|
| `SKILL.md` | What one request costs — the snapshot both ways, a model property as a query through the WRITE connection, re-render frequency, request frequency, and the page-level cache header |
| `references/measuring.md` | The three numbers and the code that produces them: snapshot bytes, queries per update, render milliseconds. Includes a console paste that needs no package |
| `references/bottlenecks.md` | Ten symptoms, each with its cause, the measurement that confirms it, and the fix |
| `bin/scan-performance.php` | 6 static checks — a model on a public property, an unlocked public array, `wire:model.live` on a text input, `wire:poll` with no interval, a computed property in a loop, `#[Reactive]` |

### `alpinejs-reference`

| File | Covers |
|---|---|
| `SKILL.md` | The mental model, the three rules that cause most bugs, common patterns, Livewire pairing |
| `references/directives.md` | All 18 directives — every `x-on` and `x-model` modifier, every input type, the transition helper *and* class APIs, the `x-bind` object syntax |
| `references/magics-globals.md` | All 9 magics, the 3 globals, `init()`/`destroy()`, lifecycle events, installing |
| `references/plugins.md` | All 9 official plugins — mask, intersect, persist, collapse, focus/trap, anchor, sort, resize, morph |
| `references/extending.md` | `Alpine.directive()` and `Alpine.magic()`, `evaluateLater`/`effect`/`cleanup`, authoring plugins, the reactivity engine, async, the CSP build |
| `references/v2-to-v3.md` | The v2 → v3 upgrade guide — every breaking change and both deprecations |

---

## The skill ships tools, not just text

Static text cannot know what your project does. These scripts read it:

```bash
bash bin/detect.sh                  # what does THIS project actually do?
bash bin/stack.sh                   # load BOTH halves — Livewire + Alpine
bash bin/scaffold.sh post.create    # create in the project's own conventions
python3 bin/review.py <file>        # v3-isms, security holes, known traps
bash bin/eval.sh --compare          # score code quality objectively
```

| Script | Does |
|---|---|
| `detect.sh` | Livewire version, the component format already on disk, emoji setting, namespaces, routing style, Boost, duplicated Alpine. Read-only |
| `stack.sh` | Finds the paired Alpine skill in any layout, symlinks followed, and prints both file maps plus which half answers which question |
| `scaffold.sh` | Creates a component in **your** conventions — and refuses a v4-only flag on a v3 project instead of emitting broken output |
| `review.py` | **21 rules**, 53 self-test cases: v3-isms, unauthorized writes, `#[Async]` mutating state, `@foreach` without `wire:key`, **multi-root templates** (nesting-aware, not a regex), unquoted Blade in JS, duplicated Alpine, invalid SKILL.md frontmatter. Exit code = error count, so it gates. Refuses a `.md` file — documentation holds many components, so whole-file rules would compare across them |
| `verify-recipes.sh` | Runs every recipe against a real Livewire install |
| `refresh.sh` | Re-audits against the current documentation |
| `eval.sh` | Scores a directory. `--compare` for baseline-vs-skill |

**Alpine has its own reviewer too** — `alpinejs-reference/bin/review.py`, 14
rules proven by 30 self-test cases, for v2-isms and the quiet traps (`x-if` off a `<template>`,
`x-cloak` with no CSS, a `$watch` that writes to what it watches).

**Both are calibrated in two directions.** Livewire: 9 errors on deliberately
v3-style code, **0 findings on the twelve verified recipes**. Alpine: 7 errors on
v2-era markup, **0 on correct Livewire+Alpine**. A checker that fires on correct
code is one people switch off.

`--self-test` proves every check still fires. It caught three bugs in the
Livewire reviewer's own rules — including one where the `//` in `https://` was
parsed as a comment, so the duplicated-Alpine check could never fire — and two
false positives that only appeared when it was run against the verified
recipes.

### Verified against v2 and v3 too

`detect.sh` and `scaffold.sh` are tested against real v2 and v3 project fixtures,
not only v4. On a v3 project `scaffold.sh` **refuses** `--sfc`, `--mfc` and
namespaces rather than emitting output that cannot work there, and `detect.sh`
warns when the project's Livewire is newer than this skill's verification.

### Measured

```
$ bash bin/eval.sh --compare

  no skill (v3 habits)    46/100   errors:10  warns:2
  skill's recipes        100/100   errors:0   warns:0

  delta: +54 points
```

Both sides are fixed artifacts scored by the same deterministic rules — not
anyone's opinion.

---

## The recipes are executed, not just written

Every component in `references/recipes.md` is rendered and exercised against a
real Livewire install:

```bash
cd livewire-reference && bash bin/verify-recipes.sh
```

It scaffolds a throwaway Laravel + Livewire 4 app, extracts each recipe into a
real component file, lints it, then renders it and exercises its actions with
`Livewire::test()`. No browser and no dev server — Livewire renders server-side,
so the whole suite runs in under a second.

**Last run: 14 tests, 54 assertions, all passing on livewire v4.4.2** — a
release newer than the documented snapshot.

This is not ceremony. It found two defects that every text-level audit had
missed, because both fail at runtime rather than at review:

- the wizard defined `public function reset()`, silently overriding
  `Livewire\Component::reset()`
- four blocks called `Auth::user()` with no facade import — a fatal error

## Validation

Every badge above is a number you can reproduce. There is no CI run behind them.

```bash
php     livewire-security/bin/scan.php          --self-test   # 22 checks
php     livewire-performance/bin/scan-performance.php --self-test # 13 checks
php     livewire-security/bin/check-update.sh   --self-test   #  6 checks
python3 livewire-reference/bin/review.py        --self-test   # 53 checks
python3 alpinejs-reference/bin/review.py        --self-test   # 30 checks
#                                                              124 total

# Are the security skill's statements still true of the installed Livewire?
php livewire-security/bin/verify-facts.php <path-to-a-laravel-app>   # 28 statements

# The recipe gate. Scaffolds a throwaway Laravel app and runs every recipe.
bash livewire-reference/bin/verify-recipes.sh                        # 14 tests, 54 assertions

# The update check, which must be able to speak AND stay silent.
bash livewire-security/bin/check-update.sh --self-test                # 6 checks
```

The first three need no network and no Laravel install. `verify-facts.php` needs
a project with `livewire/livewire` in `vendor/`. `verify-recipes.sh` needs
Composer, PHP and a temporary directory.

---

## Staying current

```bash
cd livewire-reference && bash bin/refresh.sh
```

Re-clones both documentation sets, extracts the API surface, and reports
anything now documented that the skills do not mention. **Read-only — it never
edits the skills.** It carries an allowlist of verified noise, so a clean run
says `CLEAN` rather than crying wolf.

---

## Provenance

Written from the primary sources, not from memory:

- **Livewire** — all 98 files in `docs/` on the `4.x` branch of
  [`livewire/livewire`](https://github.com/livewire/livewire), commit `81f35ea`.
  v3 differences read from the `3.x` branch.
- **Alpine** — all 55 files in `packages/docs/src/en` of
  [`alpinejs/alpine`](https://github.com/alpinejs/alpine). Version 3.16.3, which
  is what Livewire 4.x bundles.

Coverage is verified three ways:

1. **API-surface diff** — every directive, attribute, magic, global, component
   method, static, test assertion and lifecycle event extracted from both
   documentation trees and diffed against the skills. **Clean.**
2. **Execution** — every recipe rendered and exercised against a real Livewire
   install. **14 tests, 54 assertions, passing on v4.4.2.**
3. **An independent model** — twelve high-risk claims fact-checked by Codex with
   the documentation excerpts supplied inline. **12/12 supported, 0
   contradicted.**

**Last audit 2026-08-26.**

A few signatures the documentation omits (`#[Authorize]`, `#[Transition]`,
`renderIsland()`, `streamIsland()`) were read from the package source and are
labelled as source-derived where they appear.

**Livewire moves.** Run `bin/refresh.sh`, or check
[livewire.laravel.com/docs/4.x](https://livewire.laravel.com/docs/4.x), before
relying on anything version-sensitive in production.

---

## License

MIT — see [LICENSE](LICENSE).

Content derived from the Livewire and Alpine.js documentation, both MIT licensed
and © Caleb Porzio and contributors.
