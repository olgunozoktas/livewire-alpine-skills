# Alpine directives — all 18

---

## x-data

Declares a component and its reactive state. Everything else in Alpine needs an
`x-data` ancestor.

```alpine
<div x-data="{ open: false }">
    <button @click="open = ! open">Toggle</button>
    <div x-show="open">Content...</div>
</div>
```

### Scope

Scope flows **down** to all children, including nested `x-data` blocks. An inner
property of the same name shadows the outer one.

```alpine
<div x-data="{ foo: 'bar' }">
    <span x-text="foo"></span>                <!-- "bar" -->

    <div x-data="{ bar: 'baz' }">
        <span x-text="foo"></span>            <!-- "bar" — inherited -->

        <div x-data="{ foo: 'bob' }">
            <span x-text="foo"></span>        <!-- "bob" — shadowed -->
        </div>
    </div>
</div>
```

### Methods

The object is evaluated as a normal JavaScript object with a `this` context.

```alpine
<div x-data="{ open: false, toggle() { this.open = ! this.open } }">
    <button @click="toggle()">Toggle</button>
    <button @click="toggle">Toggle</button>     <!-- parens optional -->
</div>
```

### Getters

JavaScript getters act like computed properties — **not cached**, unlike Vue's.

```alpine
<div x-data="{
    open: false,
    get isOpen() { return this.open },
    toggle() { this.open = ! this.open },
}">
    <div x-show="isOpen">Content...</div>
</div>
```

### Data-less and single-element components

```alpine
<div x-data="{}">          <!-- empty object -->
<div x-data>               <!-- same thing, shorter -->

<button x-data="{ open: true }" @click="open = false" x-show="open">
    Hide Me
</button>
```

### Reusable data

Extract with `Alpine.data()` — see `magics-globals.md`.

```alpine
<div x-data="dropdown">
    <button @click="toggle">Toggle</button>
    <div x-show="open">Content...</div>
</div>
```

---

## x-init

Runs code when an element initializes. Works on **any** element, inside or
outside an `x-data` block.

```alpine
<div x-init="console.log('initializing')"></div>

<div x-data="{ posts: [] }" x-init="posts = await (await fetch('/posts')).json()"></div>
```

`$nextTick` waits until Alpine has finished rendering — the equivalent of
`useEffect(…, [])` or Vue's `mounted`:

```alpine
<div x-init="$nextTick(() => { /* DOM is ready */ })"></div>
```

### An `init()` method runs automatically

```alpine
<div x-data="{ init() { console.log('called automatically') } }">
```
```js
Alpine.data('dropdown', () => ({
    init() { /* runs when each dropdown initializes */ },
}))
```

**Ordering:** the `x-data` `init()` method runs **before** the `x-init`
directive.

---

## x-show

Toggles `display: none`. The element stays in the DOM.

```alpine
<div x-show="open">Dropdown Contents...</div>
```

`.important` forces `display: none !important`, for when a CSS rule with
`!important` would otherwise win:

```alpine
<div x-show.important="open">…</div>
```

> If the initial state is hidden, add `x-cloak` or the element flashes before
> Alpine loads.

Works with `x-transition`. `x-if` does not.

---

## x-bind / `:`

Sets an attribute from an expression.

```alpine
<input x-bind:placeholder="placeholderText">
<input :placeholder="placeholderText">          <!-- shorthand -->
```

### Binding classes

```alpine
<div :class="open ? '' : 'hidden'">
<div :class="open || 'hidden'">        <!-- short-circuit, equivalent -->
<div :class="closed && 'hidden'">      <!-- inverse -->
<div :class="{ 'hidden': ! show }">    <!-- object syntax -->
```

**`class` behaves specially.** For any other attribute, a binding overwrites the
existing value. For `class`, Alpine **preserves** existing classes:

```alpine
<div class="opacity-50" :class="hide && 'hidden'">

<!-- hide === true  -->  <div class="opacity-50 hidden">
<!-- hide === false -->  <div class="opacity-50">
```

Object syntax is the exception — it does **not** preserve the original class, so
it is the only way to have a class applied before Alpine loads *and* toggled by
Alpine:

```alpine
<div class="hidden" :class="{ 'hidden': ! show }">
```

### Binding styles

```alpine
<div :style="{ color: 'red', display: 'flex' }">
<!-- renders: style="color: red; display: flex;" -->

<div x-bind:style="true && { color: 'red' }">     <!-- conditional -->

<div style="padding: 1rem;" :style="{ color: 'red' }">
<!-- renders: style="padding: 1rem; color: red;" — merges -->

<div x-data="{ styles: { color: 'red' } }">
    <div :style="styles">
</div>
```

### Binding a whole object of directives

`x-bind` with no attribute name accepts an object of directives and attributes.
The keys are anything you would write as an attribute; values are strings, or
callbacks for dynamic directives.

```alpine
<div x-data="dropdown">
    <button x-bind="trigger">Open Dropdown</button>
    <span x-bind="dialogue">Dropdown Contents</span>
</div>
```
```js
Alpine.data('dropdown', () => ({
    open: false,
    trigger: {
        ['x-ref']: 'trigger',
        ['@click']() { this.open = true },
    },
    dialogue: {
        ['x-show']() { return this.open },
        ['@click.outside']() { this.open = false },
    },
}))
```

> When binding `x-for` this way, return a plain expression **string**:
> `['x-for']() { return 'item in items' }`

Reusable bind objects go in `Alpine.bind()` — see `magics-globals.md`.

---

## x-on / `@`

Runs code on a DOM event.

```alpine
<button x-on:click="alert('Hello World!')">Say Hi</button>
<button @click="alert('Hello World!')">Say Hi</button>       <!-- shorthand -->
```

### The event object

```alpine
<button @click="alert($event.target.getAttribute('message'))" message="Hi">…</button>
```

A method referenced **without parentheses** receives the event object:

```alpine
<button @click="handleClick">…</button>
```
```js
function handleClick(e) { /* e is the event */ }
```

> **Lowercase event names only.** HTML attributes are case-insensitive, so
> `@CLICK` listens for `click`. Use `.camel` for a camelCase custom event, or
> attach the listener via `x-bind`.

### Keyboard events

Any [`KeyboardEvent.key`] value in kebab-case works as a modifier:

```alpine
<input @keyup.enter="submit">
<input @keyup.shift.enter="submitAndStay">
<input @keyup.page-down="…">
<div @keyup.escape.window="close">
```

System keys: `.shift` `.ctrl` `.cmd` `.meta` `.alt`. Chain them freely.

### Custom events

```alpine
<div x-data @foo="alert('Fired!')">
    <button @click="$dispatch('foo')">Notify</button>
</div>
```

### All modifiers

| Modifier | Effect |
|---|---|
| `.prevent` | `event.preventDefault()` |
| `.stop` | `event.stopPropagation()` |
| `.outside` | Fire only on clicks **outside** the element |
| `.window` | Register the listener on `window` |
| `.document` | Register the listener on `document` |
| `.once` | Fire at most once |
| `.debounce` / `.debounce.500ms` | Wait for inactivity (default 250 ms) |
| `.throttle` / `.throttle.750ms` | Fire at most once per interval (default 250 ms) |
| `.self` | Only if the event originated on this element, not a child |
| `.camel` | `@custom-event.camel` listens for `customEvent` |
| `.dot` | `@custom-event.dot` listens for `custom.event` |
| `.passive` | Do not block scroll performance |
| `.passive.false` | Make a touch/wheel listener cancelable so `preventDefault()` works |
| `.capture` | Listen during the capturing phase |

```alpine
<form @submit.prevent="save" action="/foo">…</form>
<button @click.stop>Click Me</button>
<div x-show="open" @click.outside="open = false">…</div>
<input @input.debounce.500ms="fetchResults">
<div @scroll.window.throttle.750ms="handleScroll">…</div>
<button @click.self="handleClick">Click Me <img src="..."></button>
<div @touchstart.passive="…">…</div>
<div @touchmove.passive.false="$event.preventDefault()">…</div>
```

> `.outside` is only evaluated while the element is visible — otherwise the same
> click that opened a dropdown would immediately close it.

---

## x-text

Sets `textContent`.

```alpine
<div x-data="{ username: 'calebporzio' }">
    Username: <strong x-text="username"></strong>
</div>

<span x-text="1 + 2"></span>
```

---

## x-html

Sets `innerHTML`.

```alpine
<div x-data="{ username: '<strong>calebporzio</strong>' }">
    <span x-html="username"></span>
</div>
```

> **Only ever use on trusted content.** Rendering third-party HTML here is a
> direct XSS vector.

---

## x-model

Two-way binds an input to data. Works on `text`, `textarea`, `checkbox`,
`radio`, `select`, and `range`.

```alpine
<div x-data="{ message: '' }">
    <input type="text" x-model="message">
    <span x-text="message"></span>
</div>
```

It both gets **and** sets — changing the data updates the input.

### By input type

```alpine
{{-- text / textarea --}}
<input type="text" x-model="message">

{{-- single checkbox → boolean --}}
<input type="checkbox" x-model="show">

{{-- multiple checkboxes → array --}}
<input type="checkbox" value="red" x-model="colors">
<input type="checkbox" value="blue" x-model="colors">

{{-- radio --}}
<input type="radio" value="yes" x-model="answer">
<input type="radio" value="no" x-model="answer">

{{-- select --}}
<select x-model="color">
    <option value="" disabled>Select A Color</option>
    <option>Red</option>
</select>

{{-- multiple select → array --}}
<select x-model="color" multiple>…</select>

{{-- dynamically populated --}}
<select x-model="color">
    <template x-for="color in ['Red', 'Orange']">
        <option x-text="color"></option>
    </template>
</select>

{{-- range --}}
<input type="range" x-model="range" min="0" max="1" step="0.1">
```

### Modifiers

| Modifier | Effect |
|---|---|
| `.lazy` | Sync on focus-out instead of every keystroke |
| `.change` | Sync on the native `change` event — functionally the same as `.lazy` |
| `.blur` | Sync on blur, whether or not the value changed |
| `.enter` | Sync when the user presses Enter |
| `.number` | Store as a JavaScript number instead of a string |
| `.boolean` | Store as a boolean — accepts `1`/`0` and `"true"`/`"false"` |
| `.debounce` / `.debounce.500ms` | Debounce updates (default 250 ms) |
| `.throttle` / `.throttle.500ms` | Throttle updates (default 250 ms) |
| `.fill` | Seed the property from the input's `value` attribute when the property is empty |

`.change`, `.blur` and `.enter` **combine**:

```alpine
<input x-model.blur.enter="search" placeholder="Press Enter or click away">
<input x-model.change.blur.enter="message">
```

> `.enter` does **not** prevent the default. Inside a `<form>`, the form still
> submits.

```alpine
<input x-model.number="age">
<select x-model.boolean="isActive">
    <option value="true">Yes</option>
    <option value="false">No</option>
</select>
<input x-model.fill="message" value="This is the default message.">
```

### Programmatic access — `_x_model`

An `x-model`ed element exposes `_x_model.get()` and `_x_model.set()`. Useful for
building utilities, or putting `x-model` on a non-input element.

```alpine
<div x-data="{ username: 'calebporzio' }">
    <div x-ref="div" x-model="username"></div>

    <button @click="$refs.div._x_model.set('phantomatrix')">Change</button>
    <span x-text="$refs.div._x_model.get()"></span>
</div>
```

---

## x-modelable

Exposes an inner property as the target of an outer `x-model`.

```alpine
<div x-data="{ number: 5 }">
    <div x-data="{ count: 0 }" x-modelable="count" x-model="number">
        <button @click="count++">Increment</button>
    </div>

    Number: <span x-text="number"></span>
</div>
```

This is how a server-rendered partial (a Blade or ERB component) accepts
`x-model` — or Livewire's `wire:model` — from outside as though it were a native
input.

> **It clones values as JSON**, keeping inner and outer state independent. So
> `File`, `FileList`, `Map`, `Set`, `Date`, class instances and DOM nodes do
> **not** survive the boundary — a `File` loses its name, size and type.
>
> For a control producing such a value, drop `x-modelable` and dispatch an
> `input` event instead. `x-model` reads the value off the event without cloning:
>
> ```alpine
> <div x-data="{ files: [] }">
>     <div x-model="files">
>         <input type="file" multiple
>             @change="$dispatch('input', Array.from($event.target.files))">
>     </div>
>
>     <template x-for="file in files" :key="file.name">
>         <p x-text="file.name"></p>
>     </template>
> </div>
> ```

---

## x-if

Adds and removes the element from the DOM.

```alpine
<template x-if="open">
    <div>Contents...</div>
</template>
```

**Two hard rules:**
1. `x-if` must be on a `<template>` tag.
2. That template must contain exactly **one** root element.

`x-if` does **not** support `x-transition`. Use `x-show` when you need one.

---

## x-for

Iterates a list. Same two `<template>` rules as `x-if`.

```alpine
<ul x-data="{ colors: ['Red', 'Orange', 'Yellow'] }">
    <template x-for="color in colors">
        <li x-text="color"></li>
    </template>
</ul>
```

Objects work too:

```alpine
<template x-for="(value, index) in car">
    <li><span x-text="index"></span>: <span x-text="value"></span></li>
</template>
```

### Keys — required for anything that reorders

```alpine
<template x-for="color in colors" :key="color.id">
    <li x-text="color.label"></li>
</template>
```

Without a key, Alpine cannot tell a move from a change, and elements are
destroyed and recreated instead of moved.

### Index and ranges

```alpine
<template x-for="(color, index) in colors">
    <li>
        <span x-text="index + ': '"></span>
        <span x-text="color"></span>
    </li>
</template>

<template x-for="(color, index) in colors" :key="index">

{{-- loop n times — "i" can be named anything --}}
<template x-for="i in 10">
    <li x-text="i"></li>
</template>
```

### The single-root rule, concretely

```alpine
{{-- broken: two roots --}}
<template x-for="color in colors">
    <span>The next color is </span><span x-text="color">
</template>

{{-- fine --}}
<template x-for="color in colors">
    <p>
        <span>The next color is </span><span x-text="color">
    </p>
</template>
```

---

## x-effect

Re-runs an expression whenever any property it reads changes. A watcher that
infers its own dependencies.

```alpine
<div x-data="{ label: 'Hello' }" x-effect="console.log(label)">
    <button @click="label += ' World!'">Change Message</button>
</div>
```

Runs immediately, then again on every change.

**`x-effect` vs `$watch`:**

| | `x-effect` | `$watch` |
|---|---|---|
| Runs immediately | Yes | No — lazy, waits for the first change |
| Dependencies | Inferred from the expression | You name one property |
| Old value | Not available | Passed as the second argument |

---

## x-ref

Names an element for `$refs`. A scoped replacement for `getElementById` /
`querySelector`.

```alpine
<button @click="$refs.text.remove()">Remove Text</button>

<span x-ref="text">Hello</span>
```

> **v3 limitation:** `$refs` only resolves **statically declared** refs.
> `:x-ref="item.name"` inside an `x-for` does not work — `$refs` gets the
> literal string `'item.name'`.

---

## x-cloak

Hides an element until Alpine initializes, preventing a flash of uninitialized
content. Alpine removes the attribute once loaded.

```alpine
<span x-cloak x-show="false">This will not blip onto screen</span>
<span x-cloak x-text="message"></span>
```

**It needs this CSS to exist**, or it does nothing:

```css
[x-cloak] { display: none !important; }
```

An alternative that avoids the global style, exploiting `<template>` being
hidden by default:

```alpine
<template x-if="true">
    <span x-text="message"></span>
</template>
```

---

## x-ignore

Stops Alpine initializing a subtree.

```alpine
<div x-data="{ label: 'From Alpine' }">
    <div x-ignore>
        <span x-text="label"></span>     <!-- stays empty -->
    </div>
</div>
```

---

## x-teleport

Renders part of the template somewhere else in the DOM. Must be on a
`<template>`.

```alpine
<body>
    <div x-data="{ open: false }">
        <button @click="open = ! open">Toggle Modal</button>

        <template x-teleport="body">
            <div x-show="open">Modal contents...</div>
        </template>
    </div>
</body>
```

The selector is anything `document.querySelector()` accepts — `body`,
`#modal-root`, `.container`.

### Events still reach the original location

Alpine watches for listeners on the `<template x-teleport>` element, stops those
events propagating past the teleported element, and re-dispatches a copy from
the template. So you can listen where the markup is authored, not where it
renders.

### Nesting

Nested modals authored as children render as **siblings** on the page, which is
the whole point — no inherited stacking context, so backdrops behave.

```alpine
<div x-data="{ open: false }">
    <template x-teleport="body">
        <div x-show="open">
            Modal contents...

            <div x-data="{ open: false }">
                <template x-teleport="body">
                    <div x-show="open">Nested modal contents...</div>
                </template>
            </div>
        </div>
    </template>
</div>
```

> Custom directives run **after** `x-teleport` by default. See
> `extending.md` → Custom order.

---

## x-transition

Animates an element as `x-show` toggles it.

```alpine
<div x-show="open" x-transition>Hello</div>
```

Defaults: fade **and** scale, 150 ms entering, 75 ms leaving.

### Helper modifiers

```alpine
<div x-transition.duration.500ms>
<div x-transition.delay.50ms>
<div x-transition.opacity>                 <!-- fade only -->
<div x-transition.scale>                   <!-- scale only -->
<div x-transition.scale.80>                <!-- scale to 80% -->
<div x-transition.scale.origin.top>        <!-- top | bottom | left | right -->
<div x-transition.scale.origin.top.right>  <!-- combine two -->

<div x-transition:enter.duration.500ms
     x-transition:leave.duration.400ms>

<div x-transition:enter.scale.80
     x-transition:leave.scale.90>
```

### Transition classes

Full control, six hooks. Usually Tailwind utilities.

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

| Hook | Applied |
|---|---|
| `:enter` | Throughout the entering phase |
| `:enter-start` | Before insertion; removed one frame after |
| `:enter-end` | One frame after insertion; removed when the transition finishes |
| `:leave` | Throughout the leaving phase |
| `:leave-start` | Immediately when leaving begins; removed after one frame |
| `:leave-end` | One frame after leaving begins; removed when the transition finishes |

> Works with `x-show` only, never `x-if`.

---

## x-id

Declares an "id scope" so repeated components generate non-colliding ids. Pairs
with the `$id()` magic.

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

Scopes nest, and inner scopes get their own numbering. See `magics-globals.md`
→ `$id` for keyed ids inside loops.
