# Livewire v4 + Alpine.js — Agent Skills

Two [Agent Skills](https://agentskills.io/what-are-skills) that teach an AI coding
assistant **Laravel Livewire v4** and **Alpine.js v3** accurately.

They work with Claude Code, Codex, Cursor, Gemini CLI, and anything else that
reads the `SKILL.md` format.

| Skill | Lines | Covers |
|---|---|---|
| `livewire-development` | ~7,650 | All 98 files of the Livewire 4.x documentation |
| `alpinejs-development` | ~2,790 | All 55 files of the Alpine.js documentation |

---

## Why these exist

**Livewire v4 changed its defaults, and most model training data is v2 or v3.**
An assistant left to its own knowledge will confidently write code that no longer
works. These are the twelve items the skill corrects first:

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
| `$this->stream()` | `stream(to: …, content: …)` | **`stream(content: …, el: …)`** |
| JS actions | `$js('name', cb)` | **`this.$js.name = () => {}`** |

Plus everything new in v4: islands, `wire:sort`, `wire:intersect`, `wire:ref`,
`wire:bind`, `wire:text`, `#[Async]`, `#[Json]`, `#[Authorize]`, the automatic
`data-loading` and `data-current` attributes, the `$errors` magic, and
interceptors.

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

> **Laravel Boost ships a skill also named `livewire-development`.** Boost
> documents that a project-level skill of the same name overrides its built-in
> one. If guidance ever looks contradictory, check which file is loaded.

---

## What's inside

### `livewire-development`

| File | Covers |
|---|---|
| `SKILL.md` | The v3→v4 correction table, component anatomy, the mental model, security rules, and routing to the rest |
| `references/components.md` | The three formats, pages, layouts, namespaces, nesting, reactive props, slots, attribute forwarding |
| `references/properties-actions.md` | Property types and serialization, `wire:model` and every modifier, actions, magic actions, `#[Async]`, events, Laravel Echo, lifecycle hooks |
| `references/forms-validation.md` | Forms, form objects, validation in full, file uploads, pagination, URL and session state |
| `references/islands-performance.md` | Islands, lazy vs deferred loading, `data-loading`, polling, `wire:navigate` and its JS hooks |
| `references/javascript.md` | Component scripts, the full `$wire` API, interceptors, the `Livewire` global, hooks, custom directives, scoped styles |
| `references/advanced.md` | Hydration and snapshots, synthesizers, morphing, component hooks, persistent middleware, downloads, package development, CSP, streaming |
| `references/directives.md` | Every `wire:` directive in full — every modifier, `wire:target`'s four targeting forms |
| `references/attributes.md` | Every PHP attribute in full — parameters and non-obvious behaviors |
| `references/alpine.md` | Alpine **inside** Livewire — `$wire`, entangle, morph vs Alpine state, event crossover |
| `references/testing.md` | Pest setup, every `Livewire::test()` method and assertion, browser testing |
| `references/reference.md` | Redirects, Blade directives, the full config, advanced installation, troubleshooting |
| `references/volt.md` | The Volt functional API, and migrating class-based Volt to core |
| `references/v3-to-v4.md` | The complete upgrade guide |

### `alpinejs-development`

| File | Covers |
|---|---|
| `SKILL.md` | The mental model, the three rules that cause most bugs, common patterns, Livewire pairing |
| `references/directives.md` | All 18 directives in full — every `x-on` and `x-model` modifier, every input type, the transition helper *and* class APIs, the `x-bind` object syntax |
| `references/magics-globals.md` | All 9 magics, the 3 globals, `init()`/`destroy()`, the lifecycle events, installing |
| `references/plugins.md` | All 9 official plugins in full — mask, intersect, persist, collapse, focus/trap, anchor, sort, resize, morph |
| `references/extending.md` | `Alpine.directive()` and `Alpine.magic()`, `evaluateLater`/`effect`/`cleanup`, authoring plugins, the reactivity engine, async, the CSP build |
| `references/v2-to-v3.md` | The v2 → v3 upgrade guide — every breaking change and both deprecations |

---

## Provenance

Written from the primary sources, not from memory:

- **Livewire** — all 98 files in `docs/` on the `4.x` branch of
  [`livewire/livewire`](https://github.com/livewire/livewire), at commit
  `81f35ea` (2026-08-24). Attribute signatures the docs omit
  (`#[Authorize]`, `#[Transition]`) were read from the package source.
- **Alpine** — all 55 files in `packages/docs/src/en` of
  [`alpinejs/alpine`](https://github.com/alpinejs/alpine). Version 3.16.3, which
  is what Livewire 4.x bundles.

Coverage was verified by extracting the **API surface** from both documentation
trees — every directive, attribute, magic, global, component method, static,
test assertion and lifecycle event — and diffing it against the skills. A few
signatures the documentation omits (`#[Authorize]`, `#[Transition]`,
`renderIsland()`, `streamIsland()`) were read from the package source and are
labelled as source-derived where they appear.

**Livewire moves.** Re-check anything version-sensitive against the live docs at
[livewire.laravel.com/docs/4.x](https://livewire.laravel.com/docs/4.x) before
relying on it in production.

---

## License

MIT — see [LICENSE](LICENSE).

The content is derived from the Livewire and Alpine.js documentation, both MIT
licensed. Livewire is © Caleb Porzio and contributors. Alpine.js is © Caleb
Porzio and contributors.
