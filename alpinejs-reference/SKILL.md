---
name: alpinejs-reference
version: 1.3.1
description: 'Use for all Alpine.js v3 work. Covers x-data, x-show, x-if, x-for, x-model, x-transition, x-bind, x-on, magic properties, stores, custom directives, CSP, official plugins, and Livewire integration. Use it before you create, change, review, or debug Alpine behavior in Blade, Livewire, Rails, Django, Hotwire, or plain HTML. Use livewire-reference as the entry point inside Laravel Livewire projects. Keywords: alpine, alpinejs, x-data, x-init, x-show, x-if, x-for, x-model, x-modelable, x-bind, x-on, x-text, x-html, x-effect, x-ref, x-cloak, x-ignore, x-teleport, x-transition, x-id, $refs, $store, $watch, $dispatch, $nextTick, Alpine.data, Alpine.store, Alpine.bind, Alpine.directive, Alpine.reactive.'
---

# Alpine.js v3

---

## Before you start: is this copy current?

Run once. It is cached for 24 hours, it fails open, and it prints nothing when
the copy is current.

From this skill's own directory:

```bash
bash bin/check-update.sh 2>/dev/null || true
```

If the output is `SKILL_UPDATE_AVAILABLE <local> <remote>`, tell the person one
line — the two versions and that `CHANGELOG.md` says what changed — then carry
on with their task. Do not stop, and do not upgrade anything without being
asked.

If there is no output, say nothing about versions.

Set `LW_SKILLS_NO_UPDATE_CHECK=1` to switch the check off.


Alpine is fifteen attributes, six properties and three methods. It gives you
reactive, declarative behavior directly in markup, with no build step and no
virtual DOM. It is designed to complement server-rendered HTML rather than
replace it.

Source of truth: `alpinejs.dev` and `packages/docs/src/en` in
`github.com/alpinejs/alpine`.

---

## The mental model

```alpine
<div x-data="{ open: false }">
    <button @click="open = ! open">Toggle</button>

    <div x-show="open">Content...</div>
</div>
```

- **`x-data` declares a component** and its reactive state. Everything else is
  scoped to it.
- **Scope flows down** to all children, including nested `x-data` blocks. An
  inner property of the same name shadows the outer one.
- **Expressions are real JavaScript**, evaluated with `this` bound to the data
  object.
- **Reactivity is automatic.** Anything reading a property re-runs when it
  changes — Alpine uses Vue's reactivity engine underneath.

---

## The three rules that cause most bugs

1. **`x-if` and `x-for` must be on a `<template>` tag, wrapping exactly one root
   element.** Putting them on a normal element silently does nothing.
   ```alpine
   <template x-if="open"><div>…</div></template>
   <template x-for="c in colors" :key="c.id"><li x-text="c.label"></li></template>
   ```
2. **Key every list that can reorder.** Without `:key`, Alpine loses track and
   produces wrong or duplicated rows.
3. **`x-cloak` needs its CSS to exist**, or it does nothing:
   ```css
   [x-cloak] { display: none !important; }
   ```

Two more worth internalizing:

- **`x-show` vs `x-if`** — `x-show` toggles `display` and keeps the element in
  the DOM; `x-if` adds and removes it. Only `x-show` supports `x-transition`.
- **`x-on` listens for lowercase event names only.** HTML attributes are
  case-insensitive, so `@CLICK` listens for `click`. Use `.camel` for a
  camelCase custom event.

---

## Quick reference

**18 directives:** `x-data` `x-init` `x-show` `x-bind`/`:` `x-on`/`@` `x-text`
`x-html` `x-model` `x-modelable` `x-for` `x-if` `x-effect` `x-ref` `x-cloak`
`x-ignore` `x-teleport` `x-transition` `x-id`

**9 magics:** `$el` `$refs` `$root` `$data` `$store` `$watch` `$dispatch`
`$nextTick` `$id`

**3 globals:** `Alpine.data()` `Alpine.store()` `Alpine.bind()`

**9 plugins:** mask · intersect · persist · collapse · focus (`x-trap`/`$focus`)
· anchor · sort · resize · morph

---

## Working in a Laravel project?

Invoke **`livewire-reference`** instead — it is the entry point for the whole
stack and pulls this skill in:

```bash
bash bin/stack.sh          # in the livewire-reference skill
```

This skill stands alone for Alpine outside Laravel — Rails, Django, Hotwire, or
plain HTML.

---

## Tool — run it, do not eyeball it

```bash
python3 bin/review.py <file>...      # v2-isms and documented traps
python3 bin/review.py --self-test    # prove all 30 checks still fire
```

14 checks: `x-spread`, `x-show.transition`, `x-if.transition`, `.away`,
`deferLoadingAlpine`, bound `x-ref`, `x-if`/`x-for` not on a `<template>`,
`x-for` without `:key`, `x-html` on untrusted content, `$persist` with an arrow
function inside `Alpine.data()`, a `$watch` callback that writes to the object
it watches, `x-cloak` with no `[x-cloak]` CSS, and Alpine directives in a file
with no `x-data`.

Exit code is the error count, so it gates. It is calibrated in both directions:
**7 errors on v2-era markup, 0 findings on correct Livewire+Alpine** — the
no-`x-data` check knows a Livewire component root is already an Alpine
component, and knows `x-data` may sit on an ancestor.

---

## Reference files

| File | Covers |
|---|---|
| `references/directives.md` | All 18 directives in full — every modifier, every caveat, every input type for `x-model`, the transition helper *and* class APIs, the `x-bind` object syntax |
| `references/magics-globals.md` | All 9 magics in full, `Alpine.data`/`Alpine.store`/`Alpine.bind`, `init()`/`destroy()`, the lifecycle events, and installing |
| `references/plugins.md` | All 9 official plugins in full — mask, intersect, persist, collapse, focus, anchor, sort, resize, morph |
| `references/extending.md` | `Alpine.directive()` and `Alpine.magic()` signatures, `evaluateLater`/`effect`/`cleanup`, custom order, authoring plugins, the reactivity engine, async, the CSP build |
| `references/v2-to-v3.md` | The v2 → v3 upgrade guide — every breaking change and both deprecations. Read it when you meet old Alpine code |

---

## Common patterns

**Dropdown with a click-outside close:**
```alpine
<div x-data="{ open: false }" @click.outside="open = false">
    <button @click="open = ! open">Menu</button>
    <div x-show="open" x-transition>…</div>
</div>
```

**Accessible modal** (focus plugin, bundled with Livewire):
```alpine
<div x-data="{ open: false }">
    <button @click="open = true">Open</button>

    <template x-teleport="body">
        <div x-show="open" x-trap.inert.noscroll="open" @keyup.escape.window="open = false">
            <div class="modal">…</div>
        </div>
    </template>
</div>
```

**Debounced search field:**
```alpine
<input x-model="query" @input.debounce.500ms="search()">
```

**Reusable component + global store:**
```js
document.addEventListener('alpine:init', () => {
    Alpine.data('dropdown', () => ({
        open: false,
        toggle() { this.open = ! this.open },
    }))

    Alpine.store('darkMode', {
        on: false,
        toggle() { this.on = ! this.on },
    })
})
```
```alpine
<div x-data="dropdown">…</div>
<button x-data @click="$store.darkMode.toggle()">Toggle theme</button>
```

**Persisting UI state across page loads:**
```alpine
<div x-data="{ tab: $persist('overview') }">…</div>
```

---

## Extending Alpine — get the timing right

Register directives, data and stores **after** Alpine loads but **before** it
initializes.

```html
<script>
    document.addEventListener('alpine:init', () => {
        Alpine.directive('clipboard', (el) => {
            let text = el.textContent
            el.addEventListener('click', () => navigator.clipboard.writeText(text))
        })
    })
</script>
```

From a bundle, register between the import and `Alpine.start()`.
**In a Livewire app, do neither** — bundle through Livewire's ESM entry and call
`Livewire.start()`. See `references/extending.md`.

---

## Using Alpine with Livewire

Livewire bundles Alpine, and every Livewire component **is** an Alpine component.
The pairing rules:

- **Reach for Alpine whenever the interaction does not need the server** — a
  toggle, a character count, a dropdown. No round trip.
- **`$wire` is your gateway to PHP.** `$wire.title = ''`, `$wire.save()`,
  `await $wire.getPostCount()`.
- **Prefer `$wire.property` over `$wire.$entangle()`.** Entangle is deprecated —
  it duplicates state. The `@entangle` Blade directive is deprecated outright.
- **Quote interpolated strings:** `$wire.deletePost('{{ $post->uuid }}')`. An
  unquoted UUID is a JavaScript syntax error — integer ids hide this until you
  switch to UUIDs.
- **Alpine state survives Livewire updates** because Livewire morphs rather than
  replaces. Use `wire:replace.self` when state must reset, and `wire:ignore`
  around libraries that own their own DOM.
- **Three plugins have a Livewire counterpart** — prefer the Livewire one inside
  a component: `wire:intersect` over `x-intersect`, `wire:sort` over `x-sort`,
  `@teleport` over `x-teleport`.
- **`wire:transition` is not `x-transition`.** In Livewire v4 it uses the View
  Transitions API and takes no modifiers.

For the Livewire half of all this, use the `livewire-reference` skill.
