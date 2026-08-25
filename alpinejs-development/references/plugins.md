# Alpine plugins

**Livewire bundles every Alpine plugin below.** In a Livewire app they work with
no install step. The one exception is `@alpinejs/ui` (headless Alpine
Components), which Livewire does **not** bundle — add it from a CDN if you need
it.

Outside Livewire, each plugin is a separate `<script>` tag or npm package.

---

## x-mask — input formatting

Formats a text input as the user types.

```alpine
<input x-mask="99/99/9999" placeholder="MM/DD/YYYY">
<input x-mask="(999) 999-9999">
<input x-mask="aaa-999">
```

| Wildcard | Matches |
|---|---|
| `*` | Any character |
| `a` | Alpha only (a–z, A–Z) |
| `9` | Numeric only (0–9) |

Any other character is a literal separator.

### Dynamic masks

`x-mask:dynamic` takes an expression re-evaluated on every keystroke, with the
current value available as `$input`:

```alpine
<input x-mask:dynamic="$money($input)">
<input x-mask:dynamic="$money($input, ',')">          <!-- decimal separator -->
<input x-mask:dynamic="$money($input, '.', ' ')">     <!-- thousands separator -->
<input x-mask:dynamic="$money($input, '.', ',', 4)">  <!-- decimal precision -->

<input x-mask:dynamic="creditCardMask">
```

`$money($input, decimalSeparator, thousandsSeparator, precision)` is the built-in
currency helper.

---

## x-intersect — react to the viewport

Wraps IntersectionObserver.

```alpine
<div x-intersect="shown = true">…</div>
<div x-intersect:enter="loadMore">…</div>
<div x-intersect:leave="pauseVideo">…</div>
```

| Modifier | Effect |
|---|---|
| `.once` | Fire only the first time |
| `.half` | Wait until 50% visible |
| `.full` | Wait until 100% visible |
| `.threshold.[0-100]` | Custom visibility percentage |
| `.margin.[value]` | Grow/shrink the observed box (`.margin.200px`, `.margin.10%`) |
| `.parent` | Observe against the parent element rather than the viewport |

> Livewire has its own `wire:intersect` with the same modifier set. Inside a
> Livewire component prefer `wire:intersect` when the handler is a component
> action, and `x-intersect` when it is pure client-side state.

---

## x-persist — survive page loads

`$persist()` stores a property in `localStorage` and restores it.

```alpine
<div x-data="{ count: $persist(0) }">
    <button @click="count++">Increment</button>
    <span x-text="count"></span>
</div>
```

```alpine
$persist(0).as('other-key')          <!-- custom storage key -->
$persist(0).using(sessionStorage)    <!-- session instead of local -->
$persist(0).using(cookieStorage)     <!-- cookies -->
$persist({ value: 0 })               <!-- objects work -->
```

> Not a substitute for `#[Session]` or `#[Url]` in Livewire. `$persist` keeps the
> value in the **browser** only; the server never sees it.

---

## x-collapse — animated expand and collapse

Pairs with `x-show`. Animates height rather than fading.

```alpine
<div x-data="{ expanded: false }">
    <button @click="expanded = ! expanded">Toggle</button>

    <div x-show="expanded" x-collapse>
        Content...
    </div>
</div>
```

```alpine
<div x-show="expanded" x-collapse.duration.1000ms>
<div x-show="expanded" x-collapse.min.50px>   <!-- keep 50px visible collapsed -->
```

`.min` gives you a "read more" teaser without extra markup.

---

## x-trap — focus management

Traps focus inside an element. Essential for accessible modals and dialogs.

```alpine
<div x-data="{ open: false }">
    <button @click="open = true">Open</button>

    <div x-show="open" x-trap="open">
        <input type="text">
        <button @click="open = false">Close</button>
    </div>
</div>
```

| Modifier | Effect |
|---|---|
| `.inert` | Mark everything outside as `inert` for screen readers |
| `.noscroll` | Prevent background scrolling while trapped |
| `.noreturn` | Do not restore focus to the trigger on close |

Combine them: `x-trap.inert.noscroll="open"` is the standard modal setup.

### $focus

The same plugin adds a `$focus` magic:

```alpine
<button @click="$focus.next()">Next</button>
<button @click="$focus.previous()">Previous</button>
<button @click="$focus.wrap()">Wrap around</button>
<button @click="$focus.within($refs.buttons).first()">First in group</button>
```

---

## x-anchor — position relative to another element

Powered by Floating UI. For dropdowns, popovers, tooltips and dialogs.

```alpine
<button x-ref="button">Toggle</button>

<div x-anchor="$refs.button">Positioned content</div>
<div x-anchor="document.getElementById('trigger')">…</div>
<div x-anchor="document.querySelector('.trigger')">…</div>
```

| Modifier | Effect |
|---|---|
| `.bottom` (and other placements) | Preferred side |
| `.offset.10` | Gap in pixels |
| `.no-flip` / `.noflip` | Do not flip to the opposite side when space runs out |
| `.fixed` | Use fixed positioning |

```alpine
<div x-anchor.bottom.offset.10="$refs.button">…</div>
<div x-anchor.noflip="$refs.button">…</div>
```

---

## x-sort — drag and drop

Powered by SortableJS.

```alpine
<ul x-sort>
    <li x-sort:item="1">foo</li>
    <li x-sort:item="2">bar</li>
    <li x-sort:item="3">baz</li>
</ul>
```

Pass a handler to persist the new order — it receives the item key and the new
position:

```alpine
<ul x-sort="handleSort($item, $position)">
```

| Attribute | Purpose |
|---|---|
| `x-sort:item="key"` | The sortable item and its identifier |
| `x-sort:group="name"` | Allow dragging between lists sharing the name |
| `x-sort:handle` | Restrict dragging to this child element |
| `x-sort:ignore` | Exclude a child from sorting |
| `x-sort:config="{...}"` | Raw SortableJS options |

```alpine
<ul x-sort x-sort:config="{ animation: 0 }">
<ul x-sort x-sort:config="{ ghostClass: 'opacity-50' }">
```

> Livewire ships its own `wire:sort` with `wire:sort:item`, `wire:sort:group`,
> `wire:sort:group-id`, `wire:sort:handle` and `wire:sort:ignore`. **Prefer
> `wire:sort` inside a Livewire component** — it calls a component action
> directly with `($id, $position)` and, for groups, the group id as a third
> argument.

---

## x-resize — react to size changes

Wraps ResizeObserver. The callback receives `$width` and `$height`.

```alpine
<div x-data="{ w: 0, h: 0 }" x-resize="w = $width; h = $height">
    <span x-text="`${w}px × ${h}px`"></span>
</div>
```

`.document` observes the document rather than the element:

```alpine
<div x-resize.document="w = $width">…</div>
```

---

## Alpine.morph — DOM morphing

Morphs an existing element into new HTML while preserving browser and Alpine
state. This is the primitive Livewire's own morphing is built on.

```js
Alpine.morph(el, newHtml)
```

You rarely call it directly in a Livewire app — Livewire does it for you. It is
useful when hand-rolling HTML-over-the-wire outside Livewire.

---

## Which to use inside Livewire

Three plugins have a Livewire counterpart. Inside a Livewire component, the
Livewire version wins because it wires straight to a component action:

| Task | Alpine | Livewire — prefer this |
|---|---|---|
| Viewport intersection | `x-intersect` | `wire:intersect` |
| Drag-and-drop sorting | `x-sort` | `wire:sort` |
| Teleporting markup | `x-teleport` | `@teleport` |

The rest — `x-mask`, `x-persist`, `x-collapse`, `x-trap`/`$focus`, `x-anchor`,
`x-resize` — have no Livewire equivalent. Use them directly.
