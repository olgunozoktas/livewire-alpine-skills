# JavaScript, `$wire`, interceptors, Alpine, scoped styles

---

## Scripts inside components

```blade
<div>
    ...
</div>

<script>
    // runs every time this component loads
</script>
```

Livewire runs these after the page loads but **before** the component renders, so
you never need `document.addEventListener('DOMContentLoaded', …)`. Lazily and
conditionally loaded components still get their scripts executed.

Inside the script, `$wire` is available, and `this` **is** `$wire`:

```blade
<script>
    this.count++      // same as $wire.count++
    $wire.save()
</script>
```

> **Class-based components must wrap scripts in `@script`:**
> ```blade
> @script
> <script>
>     this.$js.bookmark = () => { /* … */ }
> </script>
> @endscript
> ```
> Single-file and multi-file components must **not** use the wrapper.

In multi-file components, put JavaScript in `<name>.js` beside the class instead.

### Loading external assets — `@assets`

```blade
<div>
    <input type="text" data-picker>
</div>

@assets
<script src="https://cdn.jsdelivr.net/npm/pikaday/pikaday.js" defer></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pikaday/css/pikaday.css">
@endassets

<script>
    new Pikaday({ field: $wire.$el.querySelector('[data-picker]') })
</script>
```

`@assets` blocks load **once per page** however many component instances exist,
and Livewire waits for them before running component scripts. Component
`<script>` tags, by contrast, run once **per instance**.

### `@js` — embedding PHP data

```blade
<script>
    let posts = @js($posts)
</script>
```

---

## The `$wire` object

`$wire` is the JavaScript face of the component: every public property and public
method, plus the API below.

```js
$wire.count                 // read a property
$wire.count = 5             // write (syncs on the next request)
$wire.$get('count')
$wire.$set('count', 5)             // sends a request immediately
$wire.$set('count', 5, false)      // defer the request
$wire.$toggle('sortAsc')

$wire.save()                       // call an action
$wire.$call('increment')
await $wire.getPostCount()         // actions return a promise

$wire.$refresh()                   // re-render
$wire.$commit()                    // alias for $refresh()

$wire.$dispatch('post-created', { postId: 2 })
$wire.$dispatchTo('dashboard', 'post-created', { postId: 2 })
$wire.$dispatchSelf('post-created')
$wire.$on('post-created', (event) => event.detail.postId)
$wire.$hook('message.sent', () => {})

$wire.$el                          // root DOM element
$wire.$id                          // component id
$wire.$parent                      // parent component's $wire
$wire.$refs.modal                  // elements marked with wire:ref
$wire.$errors                      // validation error bag

$wire.$watch('content', (value, old) => {})

$wire.$js.bookmark = () => {}      // define a JS action
$wire.$island('feed', { mode: 'append' }).loadMore()

$wire.$upload(name, file, finish, error, progress)
$wire.$uploadMultiple(name, files, finish, error, progress)
$wire.$removeUpload(name, tmpFilename, finish, error)

$wire.intercept(cb)                // see Interceptors
$wire.interceptMessage(cb)
$wire.interceptRequest(cb)

$wire.__instance()                 // the underlying component object
```

`$wire.$entangle(name)` is **deprecated** — read and write `$wire` properties
directly.

### JavaScript actions

```blade
<button wire:click="$js.bookmark">Bookmark</button>

<script>
    this.$js.bookmark = () => {
        $wire.bookmarked = ! $wire.bookmarked   // optimistic UI, no request
        $wire.bookmarkPost()                    // then persist
    }
</script>
```

Call from Alpine: `x-on:click="$wire.$js.bookmark()"`.

Call from PHP after an action completes:
```php
$this->js('onPostSaved');
```

The old `$js('name', cb)` and `$wire.$js('name', cb)` forms still work but are
deprecated.

### `#[Js]` — PHP methods that return JavaScript

```php
use Livewire\Attributes\Js;

#[Js]
public function resetForm()
{
    return <<<'JS'
        $wire.title = ''
        $wire.content = ''
    JS;
}
```

Callable from the template with no server request.

### `#[Json]` — actions consumed by JavaScript

Returns data by promise resolution, rejects on validation failure with structured
errors, and skips re-rendering.

```php
use Livewire\Attributes\Json;

#[Json]
public function search($query)
{
    return Post::where('title', 'like', "%{$query}%")->limit(10)->get();
}
```
```blade
<div x-data="{ query: '', posts: [] }">
    <input x-model="query" x-on:input.debounce="$wire.search(query).then(data => posts = data)">
</div>
```

Prefer `#[Json]` over a plain action whenever the result is only for JavaScript.

---

## Interceptors

Three levels, from most to least granular. All return an unsubscribe function.

```js
// Action — fires per method call
$wire.intercept(callback)
$wire.intercept('save', callback)
Livewire.interceptAction(callback)          // global

// Message — fires per component update (a message holds one or more actions)
$wire.interceptMessage(callback)
$wire.interceptMessage('save', callback)
Livewire.interceptMessage(callback)         // global

// Request — fires per HTTP request (may hold messages from several components)
$wire.interceptRequest(callback)
$wire.interceptRequest('save', callback)
Livewire.interceptRequest(callback)         // global
```

### Action interceptors

```js
$wire.intercept(({ action, onSend, onCancel, onSuccess, onError, onFailure, onFinish }) => {
    // action.name, action.params, action.component, action.cancel()

    onSend(({ call }) => {})            // call: { method, params, metadata }
    onCancel(() => {})
    onSuccess((result) => {})           // return value from the PHP method
    onError(({ response, body, preventDefault }) => { preventDefault() })
    onFailure(({ error }) => {})        // network error
    onFinish(() => {})                  // after morph, or on error/cancel
})
```

### Message interceptors

```js
$wire.interceptMessage(({ message, cancel, onSend, onCancel, onSuccess,
                         onSkipped, onError, onFailure, onStream, onFinish }) => {
    // message.component, message.actions, message.isSkipped()

    onSend(({ payload }) => {})         // payload: { snapshot, updates, calls }

    onSuccess(({ payload, onSync, onEffect, onMorph, onMorphed, onRender }) => {
        onSync(() => {})                // state merged
        onEffect(() => {})              // effects processed
        onMorph(async () => {})         // contribute awaited DOM work
        onMorphed(() => {})             // all morphs complete — read the DOM here
        onRender(() => {})              // next animation frame
    })

    onSkipped(() => {})                 // server skipped this message
    onStream(async ({ json }) => {})    // awaited before the next chunk
    onFinish(() => {})
})
```

**Order on success:** `onSuccess` → `onSync` → `onEffect` → `onMorph` →
`onMorphed` → `onFinish` → `onRender`.

For a skipped message (e.g. an unchanged reactive child) only `onSkipped` then
`onFinish` fire — no morph, no render, but action promises still resolve.

Action promises resolve at the same time as `onFinish`.

Use `onMorphed` to touch the updated DOM. `onMorph` is for contributing async work
that Livewire must wait for.

### Request interceptors

```js
$wire.interceptRequest(({ request, onSend, onCancel, onResponse, onParsed,
                         onSuccess, onError, onFailure, onStream,
                         onRedirect, onDump, onFinish }) => {
    // request.messages, request.cancel()

    onSend(({ responsePromise }) => {})
    onResponse(({ response }) => {})              // before body is read
    onParsed(({ response, body }) => {})          // body as string
    onSuccess(({ response, body, json }) => {})
    onError(({ response, body, preventDefault }) => {})
    onFailure(({ error }) => {})
    onRedirect(({ url, preventDefault }) => {})
    onDump(({ html, preventDefault }) => {})
    onFinish(() => {})
})
```

### Recipes

**Loading state for a component:**
```js
$wire.intercept(({ onSend, onFinish }) => {
    onSend(() => $wire.$el.classList.add('opacity-50'))
    onFinish(() => $wire.$el.classList.remove('opacity-50'))
})
```

**Confirm before a specific action:**
```js
$wire.intercept('delete', ({ action }) => {
    if (! confirm('Are you sure?')) action.cancel()
})
```

**Global session-expiry handling:**
```js
Livewire.interceptRequest(({ onError }) => {
    onError(({ response, preventDefault }) => {
        if (response.status === 419) {
            preventDefault()
            if (confirm('Session expired. Refresh?')) window.location.reload()
        }
    })
})
```

**Toast on save:**
```js
$wire.intercept('save', ({ onSuccess, onError }) => {
    onSuccess(() => showToast('Saved!'))
    onError(() => showToast('Failed to save', 'error'))
})
```

> Component-level interceptors are cleaned up when the component is removed.
> Global ones live for the page lifetime — unregister them yourself if needed.

---

## The `Livewire` global object

Available as `window.Livewire`. Register extension points inside `livewire:init`.

```js
document.addEventListener('livewire:init', () => {
    // after Livewire loads, before it initializes
})

document.addEventListener('livewire:initialized', () => {
    // after initialization completes
})
```

### Finding components

```js
Livewire.first()            // $wire of the first component on the page
Livewire.find(id)           // by component id
Livewire.getByName(name)    // array of $wire objects
Livewire.all()              // every component's $wire
```

### Events

```js
Livewire.dispatch('post-created', { postId: 2 })
Livewire.dispatchTo('dashboard', 'post-created', { postId: 2 })
let cleanup = Livewire.on('post-created', ({ postId }) => {})
cleanup()
```

### Custom directives

```js
Livewire.directive('confirm', ({ el, directive, component, cleanup }) => {
    let content = directive.expression

    // for wire:click.prevent="deletePost(1)":
    //   directive.raw        = wire:click.prevent
    //   directive.value      = "click"
    //   directive.modifiers  = ['prevent']
    //   directive.expression = "deletePost(1)"

    let onClick = e => {
        if (! confirm(content)) {
            e.preventDefault()
            e.stopImmediatePropagation()
        }
    }

    el.addEventListener('click', onClick, { capture: true })

    cleanup(() => el.removeEventListener('click', onClick))
})
```

### Lifecycle hooks

```js
Livewire.hook('component.init',        ({ component, cleanup }) => {})
Livewire.hook('component.initialized', ({ component }) => {})
Livewire.hook('element.init',          ({ component, el }) => {})

Livewire.hook('morph.updating', ({ el, component, toEl, skip, childrenOnly }) => {})
Livewire.hook('morph.updated',  ({ el, component }) => {})
Livewire.hook('morph.removing', ({ el, component, skip }) => {})
Livewire.hook('morph.removed',  ({ el, component }) => {})
Livewire.hook('morph.adding',   ({ el, component }) => {})
Livewire.hook('morph.added',    ({ el }) => {})

Livewire.hook('morph',   ({ el, component }) => {})   // before children morph
Livewire.hook('morphed', ({ el, component }) => {})   // after
```

`component.initialized` runs after Livewire's initial effects (event listeners,
scripts, server-dispatched JS) are processed — use it for integrations that
depend on them.

> The `commit` and `request` hooks are **deprecated**. Use `interceptMessage` and
> `interceptRequest`. See `v3-to-v4.md` for the mapping.

---

## Server-side JavaScript evaluation

```php
$this->js("alert('Post saved!')");
$this->js('$wire.$refresh()');
$this->js('$wire.$dispatch("post-created", { id: ' . $post->id . ' })');
```

Runs on the client after the response's DOM morph completes. `$wire` is in scope.

---

## Streaming

```php
$this->stream(content: 'Hello', replace: true, name: 'count');   // wire:stream="count"
$this->stream(content: 'Hello', replace: true, el: '#container'); // CSS selector
$this->stream(content: 'Hello', replace: true, ref: 'output');    // wire:ref="output"
```
```blade
<span wire:stream="count">{{ $start }}</span>
```

`.replace` swaps contents instead of appending.

> **v3 → v4:** `content` is now the first positional argument, so any positional
> call must be rewritten. The legacy `to:` still works and maps to `name:`.
> `wire:stream` does not work with Laravel Octane. Full detail in
> `advanced.md` → Streaming.

---

## Common patterns

**Third-party library init:**
```blade
<div>
    <div id="map" style="height: 400px;"></div>
</div>

@assets
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_KEY"></script>
@endassets

<script>
    new google.maps.Map($wire.$el.querySelector('#map'), {
        center: { lat: {{ $latitude }}, lng: {{ $longitude }} },
        zoom: 12
    })
</script>
```

**Sync with localStorage:**
```blade
<script>
    if (localStorage.getItem('draft')) {
        $wire.content = localStorage.getItem('draft')
    }

    $wire.$watch('content', (value) => localStorage.setItem('draft', value))
</script>
```

**Element references — `wire:ref`:**
```blade
<div wire:ref="modal">…</div>

<button wire:click="$js.scrollToModal">Scroll to modal</button>

<script>
    this.$js.scrollToModal = () => this.$refs.modal.scrollIntoView()
</script>
```

---

## Alpine integration

Every Livewire component **is** an Alpine component. Alpine ships bundled — do not
add a second copy (see Troubleshooting in `reference.md`).

```blade
<h2 x-text="$wire.todo.length"></h2>
<button x-on:click="$wire.todo = ''">Clear</button>
<button x-on:click="$wire.save()">Save</button>
<div x-intersect="$wire.incrementViewCount()">…</div>
<span x-init="$el.innerHTML = await $wire.getPostCount()"></span>
<div x-on:post-created.window="notify($event.detail.title)"></div>
<button x-on:click="$dispatch('post-created', { title: 'Post Title' })">…</button>
```

Livewire's bundle includes every Alpine plugin **except `@alpinejs/ui`**. If you
use headless Alpine Components, add that plugin from a CDN.

To register your own Alpine plugins, bundle Livewire and Alpine yourself — see
`reference.md` → "Manually bundling".

---

## Scoped styles

Component styles are scoped automatically.

**Single-file:**
```blade
<div>
    <h1 class="title">Count: {{ $count }}</h1>
    <button class="btn" wire:click="increment">+</button>
</div>

<style>
.title { color: blue; font-size: 2rem; }
.btn { background: indigo; color: white; }
</style>
```

**Multi-file:** put them in `counter.css` beside the class.

Livewire wraps your CSS in a selector targeting the component's root, using CSS
nesting:

```css
/* you write */   .btn { background: blue; }
/* served as */   [wire\:name="counter"] { .btn { background: blue; } }
```

Target the root element itself with `&`:
```blade
<style>
& { border: 2px solid gray; padding: 1rem; }
</style>
```

**Global styles:** add the attribute, or use a `.global.css` file in MFC.
```blade
<style global>
body { font-family: system-ui, sans-serif; }
</style>
```

Styles are deduplicated — loaded once however many instances render.

> Scoping relies on CSS nesting: Chrome 120+, Firefox 117+, Safari 17.2+. For
> older browsers, precompile and load through `@assets`.

---

## Debugging

```js
let $wire = Livewire.first()
console.log($wire.count)
$wire.increment()

console.log(Livewire.first().__instance().snapshot)

Livewire.interceptRequest(({ onSend }) => {
    onSend(() => console.log('Request sent:', Date.now()))
})
```

---

## Internals reference

**Snapshot** — what the browser holds between requests:
```js
{
    data: { count: 0 },
    memo: {
        id: '0qCY3ri9pzSSMIXPGg8F',
        name: 'counter',
        path: '/', method: 'GET', locale: 'en',
        children: [], lazyLoaded: false, errors: [],
    },
    checksum: '1bc274ee…',   // tamper detection
}
```

**Message** — what goes to the server:
```js
{
    snapshot: { … },
    updates: { title: 'New' },
    calls: [ { method: 'increment', params: [] } ],
}
```

**Component object** (`$wire.__instance()`) — one layer below `$wire`: `el`, `id`,
`name`, `effects`, `canonical` (last server state), `ephemeral` (live client
state), `reactive` (Proxy Alpine watches), `$wire`, `children`, `snapshot`,
`snapshotEncoded`.

> Terminology: Livewire calls these **messages**, not commits. `$commit()` remains
> as an alias for `$refresh()`.
