# Alpine.js — directives, magics, globals

Alpine v3. Source: `github.com/alpinejs/alpine`, `packages/docs/src/en`.

## Installing

**Script tag** — `defer` is required:

```html
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

**As a module:**

```js
import Alpine from 'alpinejs'

window.Alpine = Alpine
Alpine.start()
```

**Inside Laravel Livewire — install nothing.** Livewire bundles Alpine 3.16.3
plus every Alpine plugin except `@alpinejs/ui`. Adding a CDN tag or calling
`Alpine.start()` yourself there produces "Detected multiple instances of Alpine
running" and `$wire is not defined`. See the Livewire section at the end.

---

## The 18 directives

| Directive | Purpose |
|---|---|
| `x-data` | Declare a component and its reactive state |
| `x-bind` / `:` | Set an attribute from an expression |
| `x-on` / `@` | Run code on a DOM event |
| `x-text` | Set `textContent` |
| `x-html` | Set `innerHTML` — **never on untrusted content** |
| `x-model` | Two-way bind an input |
| `x-modelable` | Expose inner state as an `x-model` target |
| `x-show` | Toggle `display` |
| `x-if` | Add/remove from the DOM — needs `<template>` |
| `x-for` | Loop — needs `<template>` |
| `x-transition` | Animate show/hide |
| `x-effect` | Re-run an expression when any dependency changes |
| `x-ignore` | Do not initialize this subtree |
| `x-ref` | Name an element for `$refs` |
| `x-cloak` | Hide until Alpine initializes |
| `x-teleport` | Render elsewhere in the DOM — needs `<template>` |
| `x-init` | Run code when an element initializes |
| `x-id` | Scope generated `$id()` values |

### x-data

```alpine
<div x-data="{ open: false }">
    <button @click="open = ! open">Toggle</button>
    <div x-show="open">Content...</div>
</div>
```

Scope flows **down** to all children, including nested `x-data` components. An
inner property of the same name shadows the outer one.

Methods and getters live on the same object, with `this` bound to it:

```alpine
<div x-data="{ open: false, toggle() { this.open = ! this.open } }">
    <button @click="toggle()">Toggle</button>
    <button @click="toggle">Toggle</button>   <!-- parens optional -->
</div>
```

An `init()` method on the data object runs automatically.

### x-bind

```alpine
<input :placeholder="placeholderText">
<div :class="open ? '' : 'hidden'">
<div :class="open || 'hidden'">            <!-- short-circuit equivalent -->
<div :class="closed && 'hidden'">
<div :class="{ 'hidden': ! show }">        <!-- object syntax -->
```

Object syntax merges with the existing `class` attribute rather than replacing
it — the usual reason to prefer it.

### x-on

```alpine
<button @click="alert('Hi')">Say Hi</button>
<button @click="handleClick">…</button>     <!-- receives the event object -->
<button @click="alert($event.target.dataset.message)">…</button>
```

> `x-on` listens for **lowercase** event names only — HTML attributes are
> case-insensitive. Use `.camel` for a camelCase custom event, or attach the
> listener via `x-bind`.

**Modifiers:** `.prevent` `.stop` `.self` `.once` `.outside` `.window`
`.document` `.passive` `.passive.false` `.capture` `.camel` `.dot`
`.debounce[.500ms]` `.throttle[.750ms]`.

**Key modifiers** on `keydown`/`keyup`: any [`KeyboardEvent.key`] value in
kebab-case — `.enter` `.escape` `.tab` `.space` `.page-down` — plus the system
keys `.shift` `.ctrl` `.cmd` `.meta` `.alt`. Chain them:
`@keyup.shift.enter="…"`.

```alpine
<input @keyup.enter="submit">
<input @keyup.shift.enter="submitAndStay">
<div @keyup.escape.window="close">
<div @scroll.window.throttle.750ms="onScroll">
<input @input.debounce.500ms="search">
```

### x-model

Works on `text`, `textarea`, `checkbox`, `radio`, `select`, and `range`.

```alpine
<div x-data="{ message: '' }">
    <input x-model="message">
    <span x-text="message"></span>
</div>
```

**Modifiers:** `.lazy` `.number` `.boolean` `.debounce[.500ms]`
`.throttle[.500ms]` `.fill` `.blur` `.change` `.enter`.

These match `wire:model`'s modifiers by design.

### x-text / x-html

```alpine
<strong x-text="username"></strong>
<span x-html="username"></span>
```

> `x-html` sets `innerHTML`. Use it only on trusted content — third-party HTML
> here is a direct XSS vector.

### x-show vs x-if

`x-show` toggles `display`; the element stays in the DOM. `x-if` adds and removes
it.

```alpine
<div x-show="open">…</div>
<div x-show.important="open">…</div>   <!-- display: none !important -->

<template x-if="open">
    <div>…</div>
</template>
```

- `x-if` **must** be on a `<template>`, and that template must hold **one** root
  element.
- `x-if` does **not** support `x-transition`. `x-show` does.
- Use `x-cloak` alongside `x-show` when the initial state is hidden, or the
  element flashes before Alpine loads.

### x-for

```alpine
<template x-for="color in colors">
    <li x-text="color"></li>
</template>

<template x-for="(value, index) in car">
    <li><span x-text="index"></span>: <span x-text="value"></span></li>
</template>
```

Two hard rules: `x-for` **must** be on a `<template>`, and that template must
hold exactly **one** root element.

**Always key a list that can reorder:**

```alpine
<template x-for="color in colors" :key="color.id">
    <li x-text="color.label"></li>
</template>
```

### x-transition

```alpine
<div x-show="open" x-transition>…</div>
```

Defaults: 150 ms entering, 75 ms leaving, fading and scaling.

```alpine
<div x-transition.duration.500ms>
<div x-transition.delay.50ms>
<div x-transition.opacity>              <!-- fade only, no scale -->
<div x-transition.scale.80>
<div x-transition.scale.origin.top>

<div x-transition:enter.duration.500ms
     x-transition:leave.duration.400ms>
```

**Transition classes** — full control via six hooks, usually Tailwind utilities:

```alpine
<div
    x-show="open"
    x-transition:enter="transition ease-out duration-300"
    x-transition:enter-start="opacity-0 scale-90"
    x-transition:enter-end="opacity-100 scale-100"
    x-transition:leave="transition ease-in duration-300"
    x-transition:leave-start="opacity-100 scale-100"
    x-transition:leave-end="opacity-0 scale-90"
>Hello</div>
```

Use the helper plus modifiers for the common case. Drop to classes when you need
a specific easing curve, or a property the helper does not animate.

> This is Alpine's `x-transition`. Livewire's `wire:transition` is a **different**
> thing in v4 — it uses the View Transitions API and takes no modifiers.

### x-effect

A watcher that infers its own dependencies:

```alpine
<div x-data="{ label: 'Hello' }" x-effect="console.log(label)">
    <button @click="label += ' World!'">Change</button>
</div>
```

Runs immediately, then again whenever anything it read changes.

### x-init and $nextTick

```alpine
<div x-init="console.log('initializing')"></div>

<div x-data="{ posts: [] }" x-init="posts = await (await fetch('/posts')).json()"></div>

<div x-init="$nextTick(() => { /* after Alpine renders */ })"></div>
```

`x-init` works on any element, inside or outside an `x-data` block.

### x-ref, x-cloak, x-ignore

```alpine
<button @click="$refs.text.remove()">Remove</button>
<span x-ref="text">Hello</span>

<span x-cloak x-show="false">…</span>
```

`x-cloak` needs the CSS to exist:

```css
[x-cloak] { display: none !important; }
```

`$refs` only resolves **statically declared** refs. `:x-ref="item.name"` inside
an `x-for` does not work in v3 — the key is the literal string.

```alpine
<div x-data="{ label: 'From Alpine' }">
    <div x-ignore>
        <span x-text="label"></span>   <!-- stays empty -->
    </div>
</div>
```

### x-modelable

Expose an inner property as the target of an outer `x-model`:

```alpine
<div x-data="{ number: 5 }">
    <div x-data="{ count: 0 }" x-modelable="count" x-model="number">
        <button @click="count++">Increment</button>
    </div>

    Number: <span x-text="number"></span>
</div>
```

This is how a Blade component accepts `wire:model` or `x-model` from outside —
see `forms-validation.md` → "Custom form controls".

> **`x-modelable` clones values as JSON**, so inner and outer state stay
> independent. That means `File`, `FileList`, `Map`, `Set`, `Date`, class
> instances and DOM nodes **do not survive** the boundary — a `File` loses its
> name, size and type. For a control producing such a value, drop `x-modelable`
> and dispatch an `input` event instead; `x-model` reads the value off the event
> without cloning:
>
> ```alpine
> <div x-data="{ files: [] }">
>     <div x-model="files">
>         <input type="file" multiple
>             @change="$dispatch('input', Array.from($event.target.files))">
>     </div>
> </div>
> ```

### x-teleport

```alpine
<template x-teleport="body">
    <div x-show="open">Modal contents...</div>
</template>
```

The selector is anything `document.querySelector()` accepts. Must be on a
`<template>`.

> Inside a Livewire component, prefer Livewire's `@teleport` directive — same
> underlying mechanism, and it participates in Livewire's rendering.

### x-id

Scope generated ids so a repeated component does not collide:

```alpine
<div x-id="['text-input']">
    <label :for="$id('text-input')">Username</label>   <!-- text-input-1 -->
    <input :id="$id('text-input')">                    <!-- text-input-1 -->
</div>

<div x-id="['text-input']">
    <label :for="$id('text-input')">Username</label>   <!-- text-input-2 -->
    <input :id="$id('text-input')">                    <!-- text-input-2 -->
</div>
```

---

## The 9 magics

| Magic | Returns |
|---|---|
| `$el` | The current DOM element |
| `$refs` | Elements marked with `x-ref` |
| `$root` | The closest `x-data` element |
| `$data` | The current scope as an object |
| `$store` | Global stores from `Alpine.store()` |
| `$watch` | Watch a property for changes |
| `$dispatch` | Dispatch a browser CustomEvent |
| `$nextTick` | Run after Alpine's next DOM update |
| `$id` | Generate a collision-free id |

```alpine
<button @click="$el.innerHTML = 'Hello'">…</button>
<button @click="$refs.text.remove()">…</button>
<button @click="alert($root.dataset.message)">…</button>
<button @click="sayHello($data)">…</button>
<button @click="$store.darkMode.toggle()">…</button>

<div x-init="$watch('open', (value, old) => console.log(value))">
<button @click="$dispatch('notify', { message: 'Hello' })">…</button>
<div @notify="alert($event.detail.message)">…</div>
```

`$nextTick` returns a promise, so it can be awaited with no argument:

```alpine
<button @click="title = 'New'; await $nextTick(); console.log($el.innerText)">
```

### $dispatch into x-model

`x-model` listens for a bubbling `input` event, so `$dispatch('input', value)`
updates it from a child element. This is the escape hatch for custom controls
whose value cannot survive `x-modelable`'s JSON clone:

```alpine
<div x-data="{ title: 'Hello' }">
    <span x-model="title">
        <button @click="$dispatch('input', 'Hello World!')">Click me</button>
    </span>
</div>
```

> Inside Livewire, `$wire` is available as a tenth magic. `$wire.$errors`,
> `$wire.$refs`, `$wire.$island()` and the rest are documented in
> `javascript.md`.

---

## Globals

### Alpine.data — reusable `x-data`

```alpine
<div x-data="dropdown">
    <button @click="toggle">…</button>
    <div x-show="open">…</div>
</div>
```
```js
document.addEventListener('alpine:init', () => {
    Alpine.data('dropdown', () => ({
        open: false,
        toggle() { this.open = ! this.open },
    }))
})
```

From a bundle:

```js
import Alpine from 'alpinejs'
import dropdown from './dropdown.js'

Alpine.data('dropdown', dropdown)
Alpine.start()
```

### Alpine.store — global state

```js
document.addEventListener('alpine:init', () => {
    Alpine.store('darkMode', {
        on: false,
        toggle() { this.on = ! this.on },
    })
})
```
```alpine
<button x-data @click="$store.darkMode.toggle()">Toggle Dark Mode</button>
<div x-data :class="$store.darkMode.on && 'bg-black'">…</div>
```

A store can be a bare value, not only an object:

```js
Alpine.store('darkMode', false)
```
```alpine
<button x-data @click="$store.darkMode = ! $store.darkMode">…</button>
```

Read or write it from outside Alpine with `Alpine.store('darkMode')`.

### Alpine.bind — reusable attribute sets

```alpine
<button x-bind="SomeButton"></button>
```
```js
Alpine.bind('SomeButton', () => ({
    type: 'button',
    '@click'() { this.doSomething() },
    ':disabled'() { return this.shouldDisable },
}))
```

---

## Lifecycle and extension

Register extensions **after** Alpine loads but **before** it initializes.

**Script tag** — inside `alpine:init`:

```html
<script>
    document.addEventListener('alpine:init', () => {
        Alpine.directive('foo', ...)
        Alpine.data('bar', ...)
        Alpine.store('baz', ...)
    })
</script>
```

**Bundle** — between the import and `Alpine.start()`:

```js
import Alpine from 'alpinejs'

Alpine.directive('foo', ...)

window.Alpine = Alpine
Alpine.start()
```

**In a Livewire app**, do neither of those — bundle through Livewire:

```js
import { Livewire, Alpine } from '../../vendor/livewire/livewire/dist/livewire.esm'
import Clipboard from '@ryangjchandler/alpine-clipboard'

Alpine.plugin(Clipboard)

Alpine.directive('clipboard', (el) => {
    let text = el.textContent
    el.addEventListener('click', () => navigator.clipboard.writeText(text))
})

Livewire.start()
```

and swap `@livewireScripts` for `@livewireScriptConfig` in the layout.

---

## Reactivity

Alpine uses Vue's reactivity engine. Two functions do all the work:

```js
let data = Alpine.reactive({ count: 1 })

Alpine.effect(() => {
    console.log(data.count)     // re-runs whenever count changes
})

data.count = 2                  // logs 2
```

`Alpine.reactive()` wraps an object in a Proxy that intercepts get and set.
`Alpine.effect()` runs a callback, records every reactive property it touched,
and re-runs when any of them change. `x-effect` is this, in the template.

---

## Async

Alpine supports async functions almost everywhere:

```js
async function getLabel() {
    let response = await fetch('/api/label')
    return await response.text()
}
```
```alpine
<span x-text="await getLabel()"></span>
<span x-text="getLabel"></span>          <!-- parens off: Alpine detects async -->
```

---

## CSP

Alpine compiles expressions with `new Function()`, which a strict CSP without
`'unsafe-eval'` forbids. The CSP build swaps in a restricted evaluator.

In a Livewire app you do not install the CSP build — set `'csp_safe' => true` in
`config/livewire.php`, which switches **both**. See `advanced.md` → Content
Security Policy for exactly which expressions stop working.

---

## Alpine inside Livewire — the rules that matter

1. **Alpine state is preserved across Livewire updates.** Livewire morphs rather
   than replaces, so `x-data` survives a re-render. Wrap anything that must
   reset in `wire:replace.self`.
2. **`wire:ignore` around third-party libraries.** If a library owns its DOM,
   Livewire's morph will fight it.
3. **Prefer Alpine for anything that does not need the server.** A toggle, a
   character count, a dropdown — no round trip needed.
4. **Prefer `$wire.property` over `$wire.$entangle()`.** Entangle is deprecated;
   it duplicates state and causes predictability and performance problems. The
   `@entangle` Blade directive is deprecated outright and breaks when elements
   are removed.
5. **Quote interpolated strings.** `$wire.deletePost({{ $post->uuid }})` renders
   an unquoted UUID and throws a syntax error. Write
   `$wire.deletePost('{{ $post->uuid }}')`. Integer ids happen to work unquoted,
   which is why this bites only once you switch to UUIDs.
6. **`@js($data)`** serializes PHP into an Alpine expression:
   `<div x-data="{ posts: @js($posts) }">`.
7. **Unregister global listeners in `destroy()`** when using `wire:navigate`, or
   they accumulate on every page visit.

Plugin reference: `plugins.md`.
