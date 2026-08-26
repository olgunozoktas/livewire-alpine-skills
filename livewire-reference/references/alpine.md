# Alpine inside Livewire

Livewire **bundles Alpine 3.16.3**. There is nothing to install, and adding a
second copy breaks the page. Every Livewire component is an Alpine component
underneath, so every Alpine directive and magic works inside one.

> **For the Alpine language itself** — all 18 directives, the 9 magics, the
> globals, the extension API and the 9 plugins — use the **`alpinejs-development`
> skill**. This file covers only what changes when Alpine runs inside Livewire.

---

## Never install Alpine separately

A CDN tag, or `Alpine.start()` in `resources/js/app.js`, produces:

```
Error: Detected multiple instances of Alpine running
Alpine Expression Error: $wire is not defined
```

Remove the extra copy. From a Breeze-style `resources/js/app.js`:

```js
import Alpine from 'alpinejs';   // remove
window.Alpine = Alpine;          // remove
Alpine.start();                  // remove
```

From a layout:

```html
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

Separate Alpine **plugin** tags can go too — Livewire bundles all of them except
`@alpinejs/ui`. If you use headless Alpine Components and hit
`Uncaught Alpine: no element provided to x-anchor`, add that one plugin from a
CDN.

**Alpine is only present where Livewire's scripts are.** On a page with no
Livewire component, include `@livewireScripts` anyway if you want Alpine there.

---

## `$wire` — the gateway from Alpine to PHP

`$wire` is a magic object available in every Alpine expression inside a Livewire
component. Treat it as a JavaScript mirror of the PHP class.

```blade
{{-- read a property, reactively --}}
<span x-text="$wire.content.length"></span>

{{-- write a property, no network request --}}
<button x-on:click="$wire.title = ''">Clear</button>

{{-- write and sync immediately --}}
<button x-on:click="$wire.set('title', '')">Clear</button>

{{-- write and defer the sync to the next request --}}
<button x-on:click="$wire.set('title', '', false)">Clear</button>

{{-- call an action --}}
<input x-on:blur="$wire.save()">
<button x-on:click="$wire.deletePost(1)">Delete</button>

{{-- actions return promises --}}
<span x-init="$el.innerHTML = await $wire.getPostCount()"></span>

{{-- refresh --}}
<button x-on:click="$wire.$refresh()">Refresh</button>
```

The full `$wire` API — `$island()`, `$errors`, `$refs`, `$upload()`,
`intercept()`, `$watch()` — is in `javascript.md`.

### Passing Blade values — quote your strings

```blade
{{-- integer id: works --}}
<button x-on:click="$wire.deletePost({{ $post->id }})">Delete</button>

{{-- UUID unquoted: "Uncaught SyntaxError: Invalid or unexpected token" --}}
<button x-on:click="$wire.deletePost({{ $post->uuid }})">Delete</button>

{{-- correct --}}
<button x-on:click="$wire.deletePost('{{ $post->uuid }}')">Delete</button>
```

Integer ids hide this bug until the day you switch to UUIDs. When a Blade
expression lands inside a JavaScript expression, inspect the rendered HTML.

### `@js` for structured data

```blade
<div x-data="{ posts: @js($posts) }">…</div>
```

---

## `$wire.entangle()` — you probably don't need it

```blade
<div x-data="{ open: $wire.entangle('showDropdown') }">
<div x-data="{ open: $wire.entangle('showDropdown').live }">
```

**Discouraged for new code.** It creates duplicate state, which costs
predictability and performance. Read and write `$wire.property` directly instead.
Kept only for backwards compatibility.

**The `@entangle` Blade directive is deprecated outright** — it breaks when DOM
elements are removed. Do not use it.

---

## What Livewire's rendering does to Alpine state

Livewire **morphs** the DOM rather than replacing it, so Alpine components keep
their state across a Livewire update. That is usually what you want.

When it is not:

- **`wire:replace.self`** — force an element and its children to be recreated, so
  Alpine state resets on every render.
  ```blade
  <div x-data="{ open: false }" wire:replace.self>
      {{-- "open" returns to false on each render --}}
  </div>
  ```
- **`wire:ignore`** — keep Livewire's morph away from a subtree entirely. Needed
  around any third-party library that manages its own DOM.

---

## Choosing between the two

**Use Alpine when the server is not involved:** toggling a dropdown, a character
counter, optimistic UI before a save, client-side filtering of already-loaded
data.

**Use Livewire when the server is:** anything touching the database,
authorization, validation, or state that must survive a refresh.

**Three plugins have a Livewire counterpart.** Inside a component, prefer the
Livewire one — it calls a component action directly:

| Task | Alpine | Prefer in Livewire |
|---|---|---|
| Viewport intersection | `x-intersect` | `wire:intersect` |
| Drag-and-drop sorting | `x-sort` | `wire:sort` |
| Teleporting markup | `x-teleport` | `@teleport` |

**`wire:transition` is not `x-transition`.** In v4 it uses the browser's View
Transitions API and accepts **no** modifiers. Alpine's `x-transition` keeps its
full modifier and class API, and still works on `x-show`.

The plugins with no Livewire equivalent — `x-mask`, `x-persist`, `x-collapse`,
`x-trap`/`$focus`, `x-anchor`, `x-resize` — are bundled and ready to use.

---

## Events cross the boundary freely

Livewire events are plain browser CustomEvents.

```blade
{{-- Alpine listens for a Livewire event --}}
<div x-on:post-created.window="notify('New post: ' + $event.detail.title)"></div>

{{-- Alpine dispatches one a Livewire component handles --}}
<button x-on:click="$dispatch('post-created', { title: 'Post Title' })">…</button>
```
```php
#[On('post-created')]
public function handle($title) { }
```

> **Unregister global listeners when using `wire:navigate`.** A listener added in
> Alpine's `init()` accumulates on every page visit. Collect them and remove them
> in `destroy()`:
>
> ```js
> Alpine.data('MyComponent', () => ({
>     listeners: [],
>     init() {
>         this.listeners.push(Livewire.on('post-created', () => { /* … */ }))
>     },
>     destroy() {
>         this.listeners.forEach(remove => remove())
>     },
> }))
> ```

---

## Registering Alpine plugins and directives

Livewire injects Alpine for you, so there is no `Alpine.start()` to hook. To add
your own plugins or directives, bundle Livewire and Alpine yourself.

Swap `@livewireScripts` for `@livewireScriptConfig` in the layout, then:

```js
// resources/js/app.js
import { Livewire, Alpine } from '../../vendor/livewire/livewire/dist/livewire.esm'
import Clipboard from '@ryangjchandler/alpine-clipboard'

Alpine.plugin(Clipboard)

Alpine.directive('clipboard', (el) => {
    let text = el.textContent
    el.addEventListener('click', () => navigator.clipboard.writeText(text))
})

Livewire.start()
```

Rebuild assets (`npm run build`) after every Composer update of Livewire.

---

## CSP

Do not install Alpine's CSP build directly. Set `'csp_safe' => true` in
`config/livewire.php` — it switches **both** Livewire and Alpine to the CSP-safe
evaluator. Enabling it restricts Alpine expressions across the whole app, which
is where the limits are felt. See `advanced.md` → Content Security Policy.
