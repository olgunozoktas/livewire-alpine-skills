# Extending Alpine — directives, magics, plugins, reactivity, CSP

---

## Where to register

Extensions must be registered **after** Alpine loads and **before** it
initializes the page.

**Script tag** — inside `alpine:init`:

```html
<html>
    <script src="/js/alpine.js" defer></script>

    <div x-data x-foo></div>

    <script>
        document.addEventListener('alpine:init', () => {
            Alpine.directive('foo', ...)
        })
    </script>
</html>
```

An external extension file must load **before** Alpine:

```html
<script src="/js/foo.js" defer></script>
<script src="/js/alpine.js" defer></script>
```

**Bundle** — between the import and `Alpine.start()`:

```js
import Alpine from 'alpinejs'

Alpine.directive('foo', ...)

window.Alpine = Alpine
Alpine.start()
```

---

## Alpine.directive()

```js
Alpine.directive('[name]', (el, { value, modifiers, expression }, { Alpine, effect, cleanup }) => {})
```

| Parameter | Meaning |
|---|---|
| `name` | Directive name. `"foo"` is consumed as `x-foo` |
| `el` | The element the directive is on |
| `value` | The part after a colon — `'bar'` in `x-foo:bar` |
| `modifiers` | Array of dot-separated additions — `['baz', 'lob']` from `x-foo.baz.lob` |
| `expression` | The attribute value — `law` from `x-foo="law"` |
| `Alpine` | The Alpine global |
| `effect` | Create a reactive effect that auto-cleans when the directive is removed |
| `cleanup` | Register a callback to run when the directive is removed |

### Simplest case

```js
Alpine.directive('uppercase', el => {
    el.textContent = el.textContent.toUpperCase()
})
```
```alpine
<div x-data>
    <span x-uppercase>Hello World!</span>
</div>
```

### Evaluating an expression

```js
Alpine.directive('log', (el, { expression }, { evaluate }) => {
    console.log(evaluate(expression))
})
```
```alpine
<div x-data="{ message: 'Hello World!' }">
    <div x-log="message"></div>
</div>
```

### Making it reactive — `evaluateLater` + `effect`

```js
Alpine.directive('log', (el, { expression }, { evaluateLater, effect }) => {
    let getThingToLog = evaluateLater(expression)

    effect(() => {
        getThingToLog(thingToLog => {
            console.log(thingToLog)
        })
    })
})
```

Three things are going on, each worth understanding:

1. **`evaluateLater(expression)`** compiles the string into a reusable function.
   Interpreting a string as a function is expensive — if you evaluate more than
   once, always compile first rather than calling `evaluate()` repeatedly.
2. **`effect(callback)`** runs the callback, records every reactive property it
   touched, and re-runs on change. This is the same mechanism as `x-effect`.
   **Use the `effect` passed into the directive, not `Alpine.effect()`** — the
   injected one cleans itself up when the directive leaves the DOM.
3. **The result arrives via a callback**, not a return value. That is what makes
   async expressions such as `await getMessage()` work.

### Cleaning up

```js
Alpine.directive('...', (el, {}, { cleanup }) => {
    let handler = () => {}

    window.addEventListener('click', handler)

    cleanup(() => {
        window.removeEventListener('click', handler)
    })
})
```

Runs when the directive or its element is removed.

### Custom order

New directives run **after** the standard ones, except `x-teleport`. Chain
`.before()` to run earlier:

```js
Alpine.directive('foo', (el, { value, modifiers, expression }) => {
    Alpine.addScopeToNode(el, { foo: 'bar' })
}).before('bind')
```

> Write the target name **without** the `x-` prefix.

---

## Alpine.magic()

```js
Alpine.magic('[name]', (el, { Alpine }) => {})
```

Registers a `$`-prefixed property available everywhere.

**A magic property** — a getter, evaluated on every access:

```js
Alpine.magic('now', () => {
    return (new Date).toLocaleTimeString()
})
```
```alpine
<span x-text="$now"></span>
```

**A magic function** — return a function from the getter:

```js
Alpine.magic('clipboard', () => {
    return subject => navigator.clipboard.writeText(subject)
})

// or, more briefly
Alpine.magic('clipboard', () => subject => {
    navigator.clipboard.writeText(subject)
})
```
```alpine
<button @click="$clipboard('hello world')">Copy</button>
```

---

## Writing a plugin

### For a script tag

```html
<script src="/js/foo.js" defer></script>
<script src="/js/alpine.js" defer></script>

<div x-data x-init="$foo()">
    <span x-foo="'hello world'">
</div>
```
```js
// foo.js
document.addEventListener('alpine:init', () => {
    window.Alpine.directive('foo', ...)
    window.Alpine.magic('foo', ...)
})
```

Loading order matters — the plugin script comes **first**.

### As a bundle module

Consumed like this:

```js
import Alpine from 'alpinejs'
import foo from 'foo'

Alpine.plugin(foo)

window.Alpine = Alpine
window.Alpine.start()
```

And authored like this:

```js
export default function (Alpine) {
    Alpine.directive('foo', ...)
    Alpine.magic('foo', ...)
}
```

`Alpine.plugin()` simply invokes your callback with the `Alpine` global, so a
consumer registers everything in one line instead of several.

Alpine publishes a `plugin-blueprint` package — clone it and run
`npm install && npm run build` to start.

---

## Reactivity

Alpine uses Vue's reactivity engine. Two functions do all the work.

### Alpine.reactive()

Wraps an object in a Proxy that intercepts get and set.

```js
let data = { count: 1 }
let reactiveData = Alpine.reactive(data)

console.log(data.count)          // 1
console.log(reactiveData.count)  // 1

reactiveData.count = 2

console.log(data.count)          // 2 — it is a thin wrapper
```

The behavior is identical to the plain object. The difference is that Alpine now
*knows* when the property is read or written.

### Alpine.effect()

Runs a callback, tracks every reactive property it read, and re-runs whenever one
changes.

```js
let data = Alpine.reactive({ count: 1 })

Alpine.effect(() => {
    console.log(data.count)
})

data.count = 2      // logs 2
```

### The two together, without any Alpine syntax

```alpine
<button>Increment</button>
Count: <span></span>
```
```js
let button = document.querySelector('button')
let span = document.querySelector('span')

let data = Alpine.reactive({ count: 1 })

Alpine.effect(() => {
    span.textContent = data.count
})

button.addEventListener('click', () => {
    data.count = data.count + 1
})
```

That is the entire mechanism behind every directive.

---

## Async

Alpine supports async functions almost everywhere it supports sync ones.

```js
async function getLabel() {
    let response = await fetch('/api/label')
    return await response.text()
}
```
```alpine
<span x-text="await getLabel()"></span>
<span x-text="getLabel"></span>     <!-- parens off: Alpine detects async -->
```

This is why custom directives receive results through a callback rather than a
return value.

---

## CSP build

Alpine compiles expressions with `Function` declarations, which violate a strict
`unsafe-eval` Content Security Policy. The CSP build swaps in a restricted
parser.

> It does not use `eval()` — `Function` is faster and safer — but both violate
> `unsafe-eval`.

### Installing

```html
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/csp@3.x.x/dist/cdn.min.js"></script>
```
```shell
npm install @alpinejs/csp
```
```js
import Alpine from '@alpinejs/csp'

window.Alpine = Alpine
Alpine.start()
```

> **In Laravel Livewire, do not install this.** Set `'csp_safe' => true` in
> `config/livewire.php`; it switches Livewire and Alpine together.

### What works

```alpine
<div x-data="{ user: { name: 'John' }, items: [1, 2, 3], count: 5 }">
    <span x-text="user.name"></span>
    <span x-text="items[0]"></span>
    <span x-text="count + 10"></span>
    <span x-text="count > 3"></span>
    <span x-text="count === 5 ? 'Yes' : 'No'"></span>
    <span x-text="'Hello ' + name"></span>
    <div x-show="!loading && count > 0"></div>

    <button x-on:click="count++">Increment</button>
    <button x-on:click="count = 0">Reset</button>
    <input x-model="user.name">

    <button x-on:click="items.push('c')">Add Item</button>
</div>
```

Object and array literals, basic operators, ternaries, comparisons, assignment
to a top-level property, increments, and method calls.

### What does not

```alpine
<button x-on:click="user.name = 'John'">      <!-- property assignment -->
<button x-on:click="() => console.log('hi')"> <!-- arrow functions -->
<div x-text="{ name } = user">                <!-- destructuring -->
<div x-text="`Hello ${name}`">                <!-- template literals -->
<div x-data="{ ...defaults }">                <!-- spread -->

<button x-on:click="console.log('hi')">       <!-- globals -->
<span x-text="document.title"></span>
<span x-text="window.innerWidth"></span>
<span x-text="Math.max(count, 100)"></span>
<span x-text="parseInt('123') + count"></span>
<span x-text="JSON.stringify({ value: count })"></span>

<span x-html="message"></span>                <!-- HTML injection -->
<span x-init="$el.insertAdjacentHTML('beforeend', message)"></span>
```

### Working around it

Move logic into `Alpine.data()` getters:

```alpine
<div x-data="userManager" x-show="hasActiveAdmins">
```
```html
<script nonce="...">
    Alpine.data('userManager', () => ({
        users: [],
        get hasActiveAdmins() {
            return this.users.filter(u => u.active && u.role === 'admin').length > 0
        },
    }))
</script>
```

More readable and testable anyway.

### Headers

```
Content-Security-Policy: default-src 'self'; script-src 'nonce-[random]' 'strict-dynamic';
```

The point is removing `'unsafe-eval'` from `script-src` while still permitting
your nonce-based scripts.

```html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self'; script-src 'nonce-a23gbfz9e'">
<script defer nonce="a23gbfz9e" src="https://cdn.jsdelivr.net/npm/@alpinejs/csp@3.x.x/dist/cdn.min.js"></script>
```
