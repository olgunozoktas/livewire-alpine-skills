# Magics, globals, and lifecycle

---

## The 9 magics

| Magic | Returns |
|---|---|
| `$el` | The current DOM element |
| `$refs` | Elements marked with `x-ref` |
| `$root` | The closest `x-data` element |
| `$data` | The current scope as an object |
| `$store` | Global stores registered with `Alpine.store()` |
| `$watch` | Watch a property for changes |
| `$dispatch` | Dispatch a browser CustomEvent |
| `$nextTick` | Run after Alpine's next DOM update |
| `$id` | Generate a collision-free id |

---

### $el

```alpine
<button @click="$el.innerHTML = 'Hello World!'">Replace me</button>
```

---

### $refs

```alpine
<button @click="$refs.text.remove()">Remove Text</button>
<span x-ref="text">Hello</span>
```

Only **statically declared** refs resolve. A `:x-ref` inside `x-for` does not
work in v3.

---

### $root

The closest ancestor carrying `x-data`.

```alpine
<div x-data data-message="Hello World!">
    <button @click="alert($root.dataset.message)">Say Hi</button>
</div>
```

---

### $data

The scope as a real object, so it can be passed around.

```alpine
<div x-data="{ greeting: 'Hello' }">
    <div x-data="{ name: 'Caleb' }">
        <button @click="sayHello($data)">Say Hello</button>
    </div>
</div>
```
```js
function sayHello({ greeting, name }) {
    alert(greeting + ' ' + name + '!')
}
```

Most applications never need it. It is for deeper utilities.

---

### $watch

```alpine
<div x-data="{ open: false }" x-init="$watch('open', value => console.log(value))">
```

**The old value** is the second argument:

```alpine
<div x-init="$watch('open', (value, oldValue) => console.log(value, oldValue))">
```

**Dot notation** watches nested properties:

```alpine
<div x-init="$watch('foo.bar', value => …)">
```

**Deep watching is automatic**, but the callback receives the whole watched
object — not the sub-property that changed:

```alpine
<div x-data="{ foo: { bar: 'baz' } }"
     x-init="$watch('foo', (value, oldValue) => console.log(value, oldValue))">
    <button @click="foo.bar = 'bob'">Update</button>
</div>
<!-- logs: {bar: 'bob'} {bar: 'baz'} -->
```

> **Infinite loop warning.** Changing a property of a watched object inside its
> own `$watch` callback loops forever and eventually errors:
>
> ```alpine
> <!-- broken -->
> <div x-data="{ foo: { bar: 'baz', bob: 'lob' } }"
>      x-init="$watch('foo', value => foo.bob = foo.bar)">
> ```

---

### $dispatch

A wrapper over `element.dispatchEvent(new CustomEvent(...))`.

```alpine
<div @notify="alert('Hello World!')">
    <button @click="$dispatch('notify')">Notify</button>
</div>
```

Data goes in `$event.detail`:

```alpine
<div @notify="alert($event.detail.message)">
    <button @click="$dispatch('notify', { message: 'Hello World!' })">Notify</button>
</div>
```

**Events bubble — a sibling will not hear one without `.window`:**

```alpine
{{-- broken: the event bubbles up to the div, never sideways to the span --}}
<div x-data>
    <span @notify="..."></span>
    <button @click="$dispatch('notify')">Notify</button>
</div>

{{-- works --}}
<div x-data>
    <span @notify.window="..."></span>
    <button @click="$dispatch('notify')">Notify</button>
</div>
```

**Component-to-component**, using the same technique:

```alpine
<div x-data="{ title: 'Hello' }" @set-title.window="title = $event.detail">
    <h1 x-text="title"></h1>
</div>

<div x-data>
    <button @click="$dispatch('set-title', 'Hello World!')">Click me</button>
</div>
```

**Driving `x-model`** — dispatch a bubbling `input` event:

```alpine
<div x-data="{ title: 'Hello' }">
    <span x-model="title">
        <button @click="$dispatch('input', 'Hello World!')">Click me</button>
    </span>
</div>
```

This is how you build a custom input whose value is settable via `x-model`.

**Cancelable events** — `$dispatch` returns falsy when a handler called
`preventDefault()`:

```alpine
<div x-data x-on:open="$event.preventDefault()">
    <div x-data="{ open: false }">
        <button @click="if ($dispatch('open')) { open = true }">Click me</button>
        <div x-show="open"><h1>Hello</h1></div>
    </div>
</div>
```

**Event options** are the third parameter:

```alpine
{{-- bubbles: false — only a listener on the same element hears it --}}
<div x-data="{ title: 'Hello' }">
    <button x-on:update-title="title = $event.detail"
            @click="$dispatch('update-title', 'Hello World!', { bubbles: false })">
        Click me
    </button>
</div>
```

---

### $nextTick

Runs after Alpine has applied its reactive DOM updates.

```alpine
<div x-data="{ title: 'Hello' }">
    <button
        @click="title = 'Hello World!'; $nextTick(() => { console.log($el.innerText) })"
        x-text="title"
    ></button>
</div>
```

It returns a promise, so it can be awaited with no argument:

```alpine
<button @click="title = 'Hello World!'; await $nextTick(); console.log($el.innerText)">
```

---

### $id

Generates an id that will not collide with others of the same name on the page.

```alpine
<input type="text" :id="$id('text-input')">   <!-- text-input-1 -->
<input type="text" :id="$id('text-input')">   <!-- text-input-2 -->
```

**Grouping with `x-id`** — so a label and its input share one id:

```alpine
<div x-id="['text-input']">
    <label :for="$id('text-input')">Username</label>   <!-- text-input-1 -->
    <input type="text" :id="$id('text-input')">        <!-- text-input-1 -->
</div>

<div x-id="['text-input']">
    <label :for="$id('text-input')">Username</label>   <!-- text-input-2 -->
    <input type="text" :id="$id('text-input')">        <!-- text-input-2 -->
</div>
```

Scopes **nest**, with inner scopes numbering independently.

**Keyed ids for loops** — a second argument appends a suffix, so each item in a
group is unique but addressable:

```alpine
<ul
    x-id="['list-item']"
    :aria-activedescendant="$id('list-item', activeItem.id)"
>
    <template x-for="item in items" :key="item.id">
        <li :id="$id('list-item', item.id)">...</li>
    </template>
</ul>
```

This is the standard pattern for an accessible listbox or combobox.

---

### $store

See `Alpine.store()` below.

---

## The 3 globals

### Alpine.data — reusable `x-data`

```alpine
<div x-data="dropdown">
    <button @click="toggle">Toggle Content</button>
    <div x-show="open">Content...</div>
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

**From a bundle:**

```js
import Alpine from 'alpinejs'
import dropdown from './dropdown.js'

Alpine.data('dropdown', dropdown)
Alpine.start()
```
```js
// dropdown.js
export default () => ({
    open: false,
    toggle() { this.open = ! this.open },
})
```

**Initial parameters** — call it as a function:

```alpine
<div x-data="dropdown(true)">
```
```js
Alpine.data('dropdown', (initialOpenState = false) => ({
    open: initialOpenState,
}))
```

**`init()`** runs automatically before the component renders.

**`destroy()`** runs automatically before cleanup — the place to release
anything Alpine does not own:

```js
Alpine.data('timer', () => ({
    timer: null,
    counter: 0,
    init() {
        this.timer = setInterval(() => { ++this.counter }, 1000)
    },
    destroy() {
        clearInterval(this.timer)       // avoids a leak
    },
}))
```

A component is destroyed when, for example, an `x-if` wrapping it goes false:

```alpine
<span x-data="{ enabled: false }">
    <button @click.prevent="enabled = ! enabled">Toggle</button>
    <template x-if="enabled">
        <span x-data="timer" x-text="counter"></span>
    </template>
</span>
```

**Magics inside a data object** go through `this`:

```js
Alpine.data('dropdown', () => ({
    open: false,
    init() {
        this.$watch('open', () => { /* … */ })
    },
}))
```

**Encapsulating directives too**, via `x-bind`:

```alpine
<div x-data="dropdown">
    <button x-bind="trigger"></button>
    <div x-bind="dialogue"></div>
</div>
```
```js
Alpine.data('dropdown', () => ({
    open: false,
    trigger: {
        ['@click']() { this.open = ! this.open },
    },
    dialogue: {
        ['x-show']() { return this.open },
    },
}))
```

---

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

**From outside Alpine**, omit the second parameter:

```js
Alpine.store('darkMode').toggle()
```

**`init()` runs right after registration** — the place to seed from the
environment before anything renders:

```js
Alpine.store('darkMode', {
    init() {
        this.on = window.matchMedia('(prefers-color-scheme: dark)').matches
    },
    on: false,
    toggle() { this.on = ! this.on },
})
```

**Single-value stores** need no object:

```js
Alpine.store('darkMode', false)
```
```alpine
<button x-data @click="$store.darkMode = ! $store.darkMode">Toggle</button>
```

---

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

Replaces repeating `type="button" @click="doSomething()" :disabled="shouldDisable"`
on every instance.

---

## Lifecycle

### Element initialization

`x-init`, and an automatic `init()` on any data object. See
`directives.md` → x-init.

### Reacting to state changes

`$watch` (lazy, gives you the old value) and `x-effect` (immediate, infers
dependencies). See the comparison in `directives.md` → x-effect.

### Alpine initialization

```js
document.addEventListener('alpine:init', () => {
    // Alpine loaded, not yet initialized.
    // Register data, stores, directives, magics and plugins HERE.
})

document.addEventListener('alpine:initialized', () => {
    // Alpine has finished initializing the page.
})
```

`alpine:init` is the hook that matters — everything you register must exist
before Alpine walks the DOM.

### Component destruction

A `destroy()` method on an `Alpine.data()` object. See above.

---

## Installing

**Script tag** — `defer` is mandatory:

```html
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

Pin the exact version in production:

```html
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.16.3/dist/cdn.min.js"></script>
```

**As a module:**

```shell
npm install alpinejs
```
```js
import Alpine from 'alpinejs'

window.Alpine = Alpine     // optional, handy for devtools
Alpine.start()
```

> **`Alpine.start()` must be called exactly once per page.** Calling it twice
> gives you two Alpine instances running at once.

> Registering extensions from a bundle must happen **between** the import and
> `Alpine.start()`.

**Inside Laravel Livewire — install nothing.** Livewire bundles Alpine 3.16.3
and every plugin except `@alpinejs/ui`. A second copy produces
"Detected multiple instances of Alpine running".
