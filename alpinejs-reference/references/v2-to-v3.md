# Upgrading Alpine v2 → v3

Alpine v3 is current. This file exists for two reasons: you may meet v2 code in
an old project, and several v2 idioms still circulate in tutorials and in model
training data.

**If you see any of the left-hand column below, the code is v2.**

---

## Quick diff

| v2 | v3 |
|---|---|
| `$el` was the component root | **`$el` is the current element.** Use `$root` for the root |
| `x-data="foo()" x-init="init()"` | `init()` on the data object runs **automatically** |
| `import 'alpinejs'` | `import Alpine from 'alpinejs'` + `Alpine.start()` |
| `x-show.transition="open"` | `x-show="open" x-transition` |
| `<template x-if.transition>` | Not supported — use `x-show` + `x-transition` |
| Nested `x-data` did **not** inherit scope | Scope **cascades** to children |
| `x-init="() => {...}"` (callback return) | `x-init="$nextTick(() => {...})"` |
| `return false` implied `preventDefault()` | Call `$event.preventDefault()` yourself |
| `x-spread="obj"` | `x-bind="obj"` |
| `Alpine.deferLoadingAlpine()` | `alpine:init` / `alpine:initialized` events |
| `:x-ref="item.name"` (dynamic) | `x-ref` is **static only** |
| IE11 supported | **Dropped.** Stay on v2 if you need IE11 |
| `@click.away` | `@click.outside` (`.away` deprecated, still works) |
| `x-data="dropdown()"` global function | `Alpine.data('dropdown', …)` preferred |

---

## Breaking changes

### `$el` is now the current element

The single most likely source of silently wrong v2 code.

```alpine
<!-- v2: $el was the <div> -->
<div x-data>
    <button @click="console.log($el)"></button>
</div>

<!-- v3: use $root for the component root -->
<div x-data>
    <button @click="console.log($root)"></button>
</div>
```

In v3, `$el` is the element the expression ran on. This replaces most uses of
`x-ref`.

### `init()` is called automatically

```alpine
<!-- v2 -->
<div x-data="foo()" x-init="init()"></div>

<!-- v3 -->
<div x-data="foo()"></div>
```

```js
function foo() {
    return {
        init() { /* runs by itself */ },
    }
}
```

Leaving the old `x-init="init()"` in place calls it **twice**.

### `Alpine.start()` is required when importing

```js
// v2
import 'alpinejs'

// v3
import Alpine from 'alpinejs'

window.Alpine = Alpine
Alpine.start()
```

Unaffected if you use the CDN build.

### `x-show.transition` became `x-transition`

```alpine
<!-- v2 -->
<div x-show.transition="open"></div>
<div x-show.transition.duration.500ms="open"></div>
<div x-show.transition.in.duration.500ms.out.duration.750ms="open"></div>

<!-- v3 -->
<div x-show="open" x-transition></div>
<div x-show="open" x-transition.duration.500ms></div>
<div x-show="open"
     x-transition:enter.duration.500ms
     x-transition:leave.duration.750ms></div>
```

Every convenience survived; the API was unified.

### `x-if` no longer transitions

```alpine
<!-- v2 -->
<template x-if.transition="open">
    <div>...</div>
</template>

<!-- v3 -->
<div x-show="open" x-transition>...</div>
```

Transitioning an element in and out of the DOM was dropped deliberately — the
transition system is complex enough that supporting it on `x-show` alone was the
maintainable choice.

### `x-data` scope now cascades

```alpine
<div x-data="{ foo: 'bar' }">
    <div x-data="{}">
        <!-- v2: foo is undefined -->
        <!-- v3: foo is 'bar'    -->
    </div>
</div>
```

An inner property of the same name still shadows the outer one.

### `x-init` no longer accepts a callback return

In v2, returning a function from `x-init` deferred it until Alpine finished
initializing the tree. v3 is not return-value aware.

```alpine
<!-- v2 -->
<div x-data x-init="() => { ... }">...</div>

<!-- v3 -->
<div x-data x-init="$nextTick(() => { ... })">...</div>
```

### Returning `false` no longer prevents default

v2 mirrored inline `oninput="…"` semantics, where returning `false` called
`preventDefault()`. v3 dropped it — the behavior surprised almost everyone.

```alpine
<!-- v2 -->
<div x-data="{ blockInput() { return false } }">
    <input type="text" @input="blockInput()">
</div>

<!-- v3 -->
<div x-data="{ blockInput(e) { e.preventDefault() } }">
    <input type="text" @input="blockInput($event)">
</div>
```

### `x-spread` became `x-bind`

Same behavior, new name — `x-bind` with no attribute.

```alpine
<!-- v2 -->
<button x-spread="trigger">Toggle</button>

<!-- v3 -->
<button x-bind="trigger">Toggle</button>
```

```js
function dropdown() {
    return {
        open: false,
        trigger: {
            'x-on:click'() { this.open = ! this.open },
        },
        dialogue: {
            'x-show'() { return this.open },
            'x-bind:class'() { return 'foo bar' },
        },
    }
}
```

### Lifecycle events replace `Alpine.deferLoadingAlpine()`

```html
<!-- v2 -->
<script>
    window.deferLoadingAlpine = startAlpine => {
        // before init
        startAlpine()
        // after init
    }
</script>

<!-- v3 -->
<script>
    document.addEventListener('alpine:init', () => { /* before init */ })
    document.addEventListener('alpine:initialized', () => { /* after init */ })
</script>
```

### `x-ref` no longer supports binding

```alpine
<div x-data="{ options: [{ value: 1 }, { value: 2 }] }">
    <div x-ref="0">0</div>

    <template x-for="option in options">
        <div :x-ref="option.value" x-text="option.value"></div>
    </template>
</div>
```

In v2 every ref resolved. In v3 only **statically created** refs do, so only the
first is returned. Dynamic refs need another approach entirely.

### IE11 dropped

No official support. Projects that need IE11 should stay on Alpine v2.

---

## Deprecated but still working

These run in v3 and are likely to be removed later.

### `.away` → `.outside`

```alpine
<!-- deprecated -->
<div x-show="open" @click.away="open = false">…</div>

<!-- current -->
<div x-show="open" @click.outside="open = false">…</div>
```

### Global data functions → `Alpine.data()`

```alpine
<!-- deprecated: a global function -->
<div x-data="dropdown()">…</div>
```
```js
function dropdown() {
    return { open: false }
}
```

```alpine
<!-- current -->
<div x-data="dropdown">…</div>
```
```js
document.addEventListener('alpine:init', () => {
    Alpine.data('dropdown', () => ({ open: false }))
})
```

`Alpine.data()` gets you `init()`, `destroy()`, initial parameters, and a proper
`this` binding. See `magics-globals.md`.

---

## Checklist

- [ ] Replace `$el` with `$root` wherever the component **root** was meant
- [ ] Remove `x-init="init()"` where the data object already defines `init()`
- [ ] Add `Alpine.start()` after the import, and call it **exactly once**
- [ ] `x-show.transition` → `x-show` + `x-transition`
- [ ] Convert `x-if.transition` to `x-show` + `x-transition`
- [ ] Check nested `x-data` blocks that relied on **not** inheriting scope
- [ ] Wrap deferred `x-init` callbacks in `$nextTick()`
- [ ] Replace `return false` handlers with `$event.preventDefault()`
- [ ] `x-spread` → `x-bind`
- [ ] `Alpine.deferLoadingAlpine()` → `alpine:init` / `alpine:initialized`
- [ ] Find dynamic `:x-ref` bindings — they no longer resolve
- [ ] `.away` → `.outside`
- [ ] Move global data functions into `Alpine.data()`
