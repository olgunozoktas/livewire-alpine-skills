# Alpine plugins — all 9

Each is a separate package. Install via CDN **before** Alpine's own script, or
via npm and `Alpine.plugin()` before `Alpine.start()`.

```html
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/mask@3.x.x/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```
```js
import Alpine from 'alpinejs'
import mask from '@alpinejs/mask'

Alpine.plugin(mask)
Alpine.start()
```

> **In Laravel Livewire, install none of these.** Livewire bundles every one of
> them. The only plugin it does *not* bundle is `@alpinejs/ui` (headless Alpine
> Components).

---

## Mask — `x-mask`

Formats a text input as the user types.

```alpine
<input x-mask="99/99/9999" placeholder="MM/DD/YYYY">
<input x-mask="(999) 999-9999">
<input x-mask="aaa-999">
```

Separators such as `/` and `(` are inserted automatically as the user types.

| Wildcard | Matches |
|---|---|
| `*` | Any character |
| `a` | Alpha only (a–z, A–Z) |
| `9` | Numeric only (0–9) |

### Dynamic masks

`x-mask:dynamic` re-evaluates on every keystroke, with the current value as
`$input`:

```alpine
<input x-mask:dynamic="
    $input.startsWith('34') || $input.startsWith('37')
        ? '9999 999999 99999' : '9999 9999 9999 9999'
">
```

That is the Amex-vs-everything-else credit card case. It also accepts a function,
which receives `$input` as its first parameter:

```alpine
<input x-mask:dynamic="creditCardMask">
```
```js
function creditCardMask(input) {
    return input.startsWith('34') || input.startsWith('37')
        ? '9999 999999 99999'
        : '9999 9999 9999 9999'
}
```

### Money inputs — `$money`

Writing a money mask by hand is genuinely hard, so Alpine ships one:

```alpine
<input x-mask:dynamic="$money($input)">
<input x-mask:dynamic="$money($input, ',')">          <!-- decimal separator -->
<input x-mask:dynamic="$money($input, '.', ' ')">     <!-- thousands separator -->
<input x-mask:dynamic="$money($input, '.', ',', 4)">  <!-- precision, default 2 -->
```

Signature: `$money(input, decimalSeparator = '.', thousandsSeparator = ',', precision = 2)`.

---

## Intersect — `x-intersect`

Wraps IntersectionObserver.

```alpine
<div x-data="{ shown: false }" x-intersect="shown = true">
    <div x-show="shown" x-transition>I'm in the viewport!</div>
</div>
```

`x-intersect:enter` is an alias — use it for clarity when you also use `:leave`:

```alpine
<div x-intersect:enter="shown = true">…</div>
<div x-intersect:leave="shown = false">…</div>
```

> `:leave` fires when the **whole** element leaves the viewport. Use
> `x-intersect:leave.full` to fire when only part of it has left.

### Modifiers

| Modifier | Effect |
|---|---|
| `.once` | Fire only the first time — for enter animations |
| `.half` | Fire once the threshold exceeds `0.5` |
| `.full` | Fire once the threshold exceeds `0.99` |
| `.threshold.[0-100]` | Custom percentage. `0` = any part, `100` = entire element |
| `.margin.[value]` | Adjust the viewport boundary (`rootMargin`) |
| `.parent` | Observe against the parent element instead of the viewport |

```alpine
<div x-intersect.once="shown = true">…</div>
<div x-intersect.threshold.50="shown = true">…</div>
<div x-intersect.threshold.05="shown = true">…</div>
```

**`.margin`** works like CSS margin — one, two, or four values; `px`, `%`, or a
bare number meaning pixels. Positive expands the boundary, negative shrinks it:

```alpine
<div x-intersect.margin.200px="loaded = true">…</div>
<div x-intersect.margin.-100px="visible = true">…</div>
<div x-intersect:leave.margin.10%.25px.25.25px="loaded = false">…</div>
```

**`.parent`** is for an element inside a scrollable container, where you care
about visibility within the container rather than the page:

```alpine
<div x-intersect.parent="shown = true">…</div>
```

---

## Persist — `$persist`

Persists a property to `localStorage` and restores it on load.

```alpine
<div x-data="{ count: $persist(0) }">
    <button x-on:click="count++">Increment</button>
    <span x-text="count"></span>
</div>
```

Alpine registers a watcher, writes on every change, and reads back on
initialization. Keys are namespaced with an `_x_` prefix so they do not collide
with other tools using localStorage.

Works with primitives, arrays and objects.

> **Clear localStorage when the stored type changes.** Going from `$persist(0)`
> to `$persist({ value: 0 })` requires clearing the key or renaming the property.

### Custom key — `.as()`

Necessary when several components on a page use the same property name:

```alpine
<div x-data="{ count: $persist(0).as('other-count') }">
```

### Custom storage — `.using()`

```alpine
<div x-data="{ count: $persist(0).using(sessionStorage) }">
```

Any object exposing `getItem` and `setItem` works — cookies, for example:

```js
window.cookieStorage = {
    getItem(key) {
        let cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].split('=')
            if (key == cookie[0].trim()) return decodeURIComponent(cookie[1])
        }
        return null
    },
    setItem(key, value) {
        document.cookie = key + ' = ' + encodeURIComponent(value)
    },
}
```
```alpine
<div x-data="{ count: $persist(0).using(cookieStorage) }">
```

### With Alpine.data — use a normal function

An arrow function has no `this` to bind:

```js
Alpine.data('dropdown', function () {
    return {
        open: this.$persist(false),
    }
})
```

### Outside `x-data` — `Alpine.$persist`

```js
Alpine.store('darkMode', {
    on: Alpine.$persist(true).as('darkMode_on'),
})
```

---

## Collapse — `x-collapse`

Animates height rather than fading. **Requires `x-show` on the same element.**

```alpine
<div x-data="{ expanded: false }">
    <button @click="expanded = ! expanded">Toggle Content</button>

    <p x-show="expanded" x-collapse>...</p>
</div>
```

| Modifier | Effect |
|---|---|
| `.duration.[time]` | Transition duration |
| `.min.[height]` | Minimum height when collapsed, instead of `0` |

```alpine
<p x-show="expanded" x-collapse.duration.1000ms>…</p>
<p x-show="expanded" x-collapse.min.50px>…</p>
```

Collapsed normally means `height: 0` plus `display: none`. `.min` "cuts off" the
element instead of hiding it — the standard "read more" teaser, with no extra
markup.

---

## Focus — `x-trap` and `$focus`

### x-trap

Traps focus inside an element while the expression is true, and returns focus
where it was when it becomes false.

```alpine
<div x-data="{ open: false }">
    <button @click="open = true">Open Dialog</button>

    <span x-show="open" x-trap="open">
        <input type="text" placeholder="Some input...">
        <button @click="open = false">Close Dialog</button>
    </span>
</div>
```

**Nesting is handled automatically and recursively** — each trap stores the last
actively focused element, so closing nested dialogs returns focus correctly at
every level.

| Modifier | Effect |
|---|---|
| `.inert` | Add `aria-hidden="true"` to everything outside while trapped |
| `.noscroll` | Remove the scrollbar and block background scrolling |
| `.noreturn` | Do not restore focus when the trap releases |
| `.noautofocus` | Do not focus the first focusable element on engage |

`.inert` and `.noscroll` together are the standard accessible modal:

```alpine
<div x-show="open" x-trap.inert.noscroll="open">…</div>
```

`.noreturn` exists for cases like a search input that opens a dropdown —
returning focus to the input would just reopen it:

```alpine
<div x-data="{ open: false }" x-trap.noreturn="open">
    <input type="search" placeholder="search for something">
    <div x-show="open">Search results</div>
</div>
```

### $focus

| Method | Does |
|---|---|
| `focus(el)` | Focus an element, handling the `nextTick` awkwardness internally |
| `focusable(el)` | Is this element focusable? |
| `focusables()` | All focusable elements within the current one |
| `focused()` | The currently focused element |
| `lastFocused()` | The previously focused element |
| `within(el)` | Scope the following call to another element |
| `first()` / `last()` | Focus the first / last focusable element |
| `next()` / `previous()` | Focus the next / previous |
| `wrap()` | Make `next`/`previous` wrap around the ends |
| `noscroll()` | Do not scroll to the element being focused |
| `getFirst()` / `getLast()` / `getNext()` / `getPrevious()` | Retrieve without focusing |

Arrow-key navigation within a button group:

```alpine
<div @keydown.right="$focus.wrap().next()"
     @keydown.left="$focus.wrap().previous()">
    <button>First</button>
    <button>Second</button>
    <button>Third</button>
</div>
```

Without `.wrap()`, pressing right on the last button does nothing.

`within()` scopes `$focus` to a different element — needed when the trigger sits
outside the group:

```alpine
<button @click="$focus.within($refs.buttons).first()">Focus "First"</button>
<button @click="$focus.within($refs.buttons).last()">Focus "Last"</button>

<div x-ref="buttons"
     @keydown.right="$focus.wrap().next()"
     @keydown.left="$focus.wrap().previous()">
    <button>First</button>
    <button>Second</button>
    <button>Third</button>
</div>
```

---

## Anchor — `x-anchor`

Positions an element relative to another, using Floating UI. For dropdowns,
popovers, tooltips and dialogs.

```alpine
<div x-data="{ open: false }">
    <button x-ref="button" @click="open = ! open">Toggle</button>

    <div x-show="open" x-anchor="$refs.button">Dropdown content</div>
</div>
```

By default it applies `position: absolute` plus `top`/`left`, and flips to the
other side when there is not enough room below.

### Placement modifiers

`.bottom` `.bottom-start` `.bottom-end` · `.top` `.top-start` `.top-end` ·
`.left` `.left-start` `.left-end` · `.right` `.right-start` `.right-end`

```alpine
<div x-show="open" x-anchor.bottom-start="$refs.button">…</div>
```

### Other modifiers

| Modifier | Effect |
|---|---|
| `.offset.[px]` | Gap between the elements |
| `.noflip` | Never flip to the opposite side |
| `.fixed` | Use `position: fixed` instead of `absolute` |
| `.no-style` | Skip Alpine's styling; use the `$anchor` magic yourself |

```alpine
<div x-anchor.offset.10="$refs.button">…</div>
<div x-anchor.noflip="$refs.button">…</div>
```

**`.fixed`** exists for a reference element inside `overflow: hidden`, `clip` or
`auto` — absolute positioning gets clipped along with the container.

> **A `transform`, `filter`, `perspective`, `backdrop-filter`, `will-change` or
> `contain` on any ancestor creates a new containing block for `position: fixed`
> descendants.** When that happens `.fixed` behaves like `absolute` relative to
> that ancestor and will not escape its `overflow: hidden`. **If `.fixed` seems
> to do nothing, look for a transformed ancestor.**

### Manual styling — `.no-style` and `$anchor`

```alpine
<div
    x-show="open"
    x-anchor.no-style="$refs.button"
    x-bind:style="{ position: 'absolute', top: $anchor.y + 'px', left: $anchor.x + 'px' }"
>Dropdown content</div>
```

> Combining `.no-style` with `.fixed` means you must set `position: 'fixed'`
> yourself. `$anchor.x`/`$anchor.y` come back in whichever coordinate space the
> active strategy uses — absolute is relative to the offset parent, fixed to the
> viewport — so the wrong `position` puts the element in the wrong place.

### Anchoring to an id

`x-anchor` accepts any DOM element:

```alpine
<div x-show="open" x-anchor="document.getElementById('trigger')">…</div>
<div x-show="open" x-anchor="document.querySelector('.trigger')">…</div>
```

---

## Sort — `x-sort`

Drag-and-drop reordering, powered by SortableJS.

```alpine
<ul x-sort>
    <li x-sort:item>foo</li>
    <li x-sort:item>bar</li>
    <li x-sort:item>baz</li>
</ul>
```

### Handlers

Pass an expression to `x-sort` and keys to each `x-sort:item`. `$item` is the
key, `$position` the new zero-based index:

```alpine
<ul x-sort="alert($item + ' - ' + $position)">
    <li x-sort:item="1">foo</li>
    <li x-sort:item="2">bar</li>
</ul>
```

A function receives them as parameters:

```alpine
<div x-data="{ handle: (item, position) => { ... } }">
    <ul x-sort="handle">
        <li x-sort:item="1">foo</li>
    </ul>
</div>
```

Persisting the new order is your job — that is what the handler is for.

### Groups

Matching `x-sort:group` values let items move between lists:

```alpine
<ul x-sort x-sort:group="todos">
    <li x-sort:item="1">foo</li>
</ul>

<ol x-sort x-sort:group="todos">
    <li x-sort:item="4">foo</li>
</ol>
```

> When dragging between groups, **only the destination list's handler** is
> called, with the key and new position.

### Handles and ignored elements

```alpine
<li x-sort:item>
    <span x-sort:handle> - </span>foo      <!-- only the hyphen drags -->
</li>

<li x-sort:item>
    <button x-sort:ignore>Edit</button>    <!-- clickable, never drags -->
</li>
```

`x-sort:ignore` elements still work normally — buttons click, inputs focus — they
are only excluded from starting a drag.

### Ghost element

By default the dragged item leaves an empty hole. `.ghost` leaves a copy
instead, carrying the `.sortable-ghost` class:

```alpine
<ul x-sort.ghost>
    <li x-sort:item>foo</li>
</ul>
```
```css
.sortable-ghost { opacity: .5 !important; }
```

### The `.sorting` class on `<body>`

Alpine adds `.sorting` to `<body>` during a drag, so you can style anything on
the page conditionally with CSS alone:

```css
#sort-warning { display: none; }
body.sorting #sort-warning { display: block; }
```

### The hover bug — worth knowing

There is a **Chrome and Safari bug** (not Firefox) where a hover style is applied
to whichever element now sits in the dragged element's old position.

Fix it with the `.sorting` body class:

```html
<div x-sort>
    <div x-sort:item class="[body:not(.sorting)_&]:hover:border">foo</div>
</div>
```

### Custom SortableJS config

```alpine
<ul x-sort x-sort:config="{ animation: 0 }">
<ul x-sort x-sort:config="{ ghostClass: 'opacity-50' }">
```

> Options you pass **overwrite** Alpine's defaults. Overwriting `handle`,
> `group`, `filter`, `onSort`, `onStart` or `onEnd` will break the plugin.

---

## Resize — `x-resize`

Wraps ResizeObserver. The expression gets `$width` and `$height`.

```alpine
<div x-data="{ width: 0, height: 0 }"
     x-resize="width = $width; height = $height">
    <p x-text="'Width: ' + width + 'px'"></p>
    <p x-text="'Height: ' + height + 'px'"></p>
</div>
```

`.document` observes the whole document instead of the element:

```alpine
<div x-resize.document="width = $width">…</div>
```

---

## Morph — `Alpine.morph()`

Morphs a live element into new HTML while preserving DOM and Alpine state. This
is the primitive behind Livewire and Phoenix LiveView.

```js
Alpine.morph(el, newHtml, options)
```

| Parameter | Meaning |
|---|---|
| `el` | The live DOM element |
| `newHtml` | HTML string to morph toward |
| `options` | Lifecycle hooks and config (optional) |

```js
Alpine.morph(el, `
    <div x-data="{ message: '...' }">
        <h2>See how new elements have been added</h2>
        <input type="text" x-model="message">
        <span x-text="message"></span>
    </div>
`)
```

The input's value and the component's state survive.

### Lifecycle hooks

| Hook | When |
|---|---|
| `updating(el, toEl, childrenOnly, skip)` | Before patching `el` |
| `updated(el, toEl)` | After patching |
| `removing(el, skip)` | Before removing an element |
| `removed(el)` | After removing |
| `adding(el, skip)` | Before adding a new element |
| `added(el)` | After adding |
| `key(el)` | How to key elements — defaults to the `key=""` attribute |
| `lookahead` | Boolean. Look ahead to *move* an element rather than remove it. Default `false` |

Parameters worth knowing:

- **`el`** — the real element on the page that will be patched.
- **`toEl`** — a *template* element representing the target. It never lives on
  the page; use it for reference only.
- **`childrenOnly()`** — skip this element, patch only its children.
- **`skip()`** — skip this element and its children entirely.

```js
Alpine.morph(el, newHtml, {
    updating(el, toEl, childrenOnly, skip) {},
    updated(el, toEl) {},
    removing(el, skip) {},
    removed(el) {},
    adding(el, skip) {},
    added(el) {},
    key(el) { return el.id },
    lookahead: true,
})
```

### Keys

Without keys, a reorder looks like a series of content changes:

```html
<!-- live -->            <!-- new -->
<ul>                     <ul>
    <li>Mark</li>            <li>Travis</li>
    <li>Tom</li>             <li>Mark</li>
    <li>Travis</li>          <li>Tom</li>
</ul>                    </ul>
```

Morph concludes "Mark became Travis, Travis became Tom" and destroys elements it
should have moved. Keys fix it:

```html
<li key="1">Mark</li>
<li key="2">Tom</li>
<li key="3">Travis</li>
```

### Alpine.morphBetween()

Morphs a **range** of nodes between two markers, when there is no single root
element to target.

```js
Alpine.morphBetween(startMarker, endMarker, newHtml, options)
```

`startMarker` and `endMarker` are typically comment nodes. `newHtml` may be a
string or a DOM element. Options are the same as `Alpine.morph()`.

---

## Which to use inside Livewire

Three plugins have a Livewire counterpart. Inside a Livewire component the
Livewire version wins, because it wires straight to a component action:

| Task | Alpine | Prefer in Livewire |
|---|---|---|
| Viewport intersection | `x-intersect` | `wire:intersect` |
| Drag-and-drop sorting | `x-sort` | `wire:sort` |
| Teleporting markup | `x-teleport` | `@teleport` |
| DOM morphing | `Alpine.morph()` | Livewire does it for you |

The rest — mask, persist, collapse, focus, anchor, resize — have no Livewire
equivalent. Use them directly.
