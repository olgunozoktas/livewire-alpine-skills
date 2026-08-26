# Livewire v4 + Alpine.js — Agent Skills

Two [Agent Skills](https://agentskills.io/what-are-skills) that teach an AI coding
assistant **Laravel Livewire v4** and **Alpine.js v3** accurately — with complete
working recipes, a symptom-to-fix troubleshooting guide, and version detection.

Works with Claude Code, Codex, Cursor, Gemini CLI, and anything else that reads
the `SKILL.md` format.

| Skill | Lines | Covers |
|---|---|---|
| `livewire-development` | ~9,000 | All 98 files of the Livewire 4.x documentation, plus v3 differences |
| `alpinejs-development` | ~2,840 | All 55 files of the Alpine.js documentation, plus the v2→v3 guide |

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
cp -R /tmp/lw-skills/livewire-development   ~/.claude/skills/
cp -R /tmp/lw-skills/alpinejs-development   ~/.claude/skills/
```

Per-project instead of global: copy into `.claude/skills/` in the repo.

Restart the session. The assistant loads a skill on its own when the task
matches; `/livewire-development` invokes it explicitly.

### Other agents

Copy the same two directories into whatever skills directory your tool reads —
`.ai/skills/` for Laravel Boost, `.codex/skills/`, `.cursor/skills/`, and so on.

---

## Using this alongside Laravel Boost

Boost ships **its own skill with the identical name**, `livewire-development`.
Boost documents that a project-level skill of that name overrides its built-in
one, so both may be present.

**They are complementary — run both.** Boost knows your Livewire version and
reads your `config/livewire.php`; it is deliberately terse because it is paired
with a live `search-docs` index. These skills are the depth behind it.

| Question | Best source |
|---|---|
| "What changed in the release last week?" | Boost `search-docs` — live and version-aware |
| "Which format does *this* project use?" | Boost — its skill reads your config |
| "Every modifier of `wire:target`" | These skills |
| "Why did my morph put state on the wrong element?" | These skills |
| "A complete searchable, paginated table" | These skills |

If the two contradict each other on a fact, **prefer the live docs** and treat
this snapshot's date as the tiebreaker.

---

## What's inside

### `livewire-development`

| File | Covers |
|---|---|
| `SKILL.md` | Version + convention preflight, the v3→v4 correction table, component anatomy, the mental model, security rules, task routing |
| `references/recipes.md` | **Twelve complete components** — CRUD, search/filter/sort/paginate, modal, upload with progress, infinite scroll, wizard, optimistic UI, dependent selects, Echo, form objects, tests |
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
| `bin/verify-recipes.sh` | Scaffolds a throwaway app and **runs every recipe**. 14 tests, 54 assertions |
| `bin/refresh.sh` | Re-audits the skill against the current docs. Read-only |
| `tests/` | The verification harness — test suite, extractor, and fixtures |

### `alpinejs-development`

| File | Covers |
|---|---|
| `SKILL.md` | The mental model, the three rules that cause most bugs, common patterns, Livewire pairing |
| `references/directives.md` | All 18 directives — every `x-on` and `x-model` modifier, every input type, the transition helper *and* class APIs, the `x-bind` object syntax |
| `references/magics-globals.md` | All 9 magics, the 3 globals, `init()`/`destroy()`, lifecycle events, installing |
| `references/plugins.md` | All 9 official plugins — mask, intersect, persist, collapse, focus/trap, anchor, sort, resize, morph |
| `references/extending.md` | `Alpine.directive()` and `Alpine.magic()`, `evaluateLater`/`effect`/`cleanup`, authoring plugins, the reactivity engine, async, the CSP build |
| `references/v2-to-v3.md` | The v2 → v3 upgrade guide — every breaking change and both deprecations |

---

## The recipes are executed, not just written

Every component in `references/recipes.md` is rendered and exercised against a
real Livewire install:

```bash
cd livewire-development && bash bin/verify-recipes.sh
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

## Staying current

```bash
cd livewire-development && bash bin/refresh.sh
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

Coverage is verified by extracting the **API surface** from both trees — every
directive, attribute, magic, global, component method, static, test assertion
and lifecycle event — and diffing it against the skills. **Last audit
2026-08-26: clean.**

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
