# Advanced — internals, extension points, security mechanics

Hydration, morphing, synthesizers, component hooks, persistent middleware,
package development, CSP, and downloads.

---

## How a request actually works

1. `<livewire:counter />` renders. Livewire news up the class, calls `mount()`,
   renders the Blade, takes a **snapshot**, and embeds it as `wire:snapshot` on
   the root element alongside `wire:id`.
2. Livewire's JavaScript finds `wire:id` elements, parses the snapshot, and
   builds a client-side component object.
3. An interaction sends a **message** to `/livewire-{hash}/update`:
   `{ snapshot, updates, calls }`.
4. The server **hydrates** a fresh PHP object from the snapshot, applies the
   updates, runs the calls, re-renders, and returns
   `{ snapshot, effects: { html, returns } }`.
5. The client replaces the snapshot and **morphs** the new HTML into the DOM.

Each request is stateless. There is no long-running process holding your
component alive — the snapshot is the only continuity.

---

## Hydration and dehydration

**Dehydrate** = render HTML + serialize state to JSON.
**Hydrate** = rebuild the PHP object from that JSON.

A plain value serializes plainly:

```js
state: { count: 1 }
```

A non-primitive serializes as a **metadata tuple** — `[value, metadata]` — so
Livewire knows how to rebuild it:

```js
state: {
    todos: [
        ['first', 'second', 'third'],
        { s: 'clctn', class: 'Illuminate\\Support\\Collection' },
    ],
}
```

Tuples nest. A Stringable inside a Collection:

```js
todos: [
    ['first', 'second', ['third', { s: 'str' }]],
    { s: 'clctn', class: 'Illuminate\\Support\\Collection' },
]
```

The `s` key names the **synthesizer** that will rebuild the value.

### Snapshot shape

```js
{
    data: { count: 1 },
    memo: {
        id: '0qCY3ri9pzSSMIXPGg8F',
        name: 'counter',
        path: '/', method: 'GET', locale: 'en',
        children: [], lazyLoaded: false, errors: [],
    },
    checksum: '1bc274ee…',
}
```

### Snapshot checksums

Every snapshot carries a checksum. On the next request Livewire re-verifies it.
A mismatch throws `CorruptComponentPayloadException` and the request fails.

This is what stops a user editing the snapshot in DevTools to change a model id
or inject state. **It does not** stop them changing a property through legitimate
channels — that is what `#[Locked]` and authorization are for.

---

## Synthesizers — supporting custom property types

A Synthesizer teaches Livewire how to dehydrate and hydrate a type it does not
know. Here is Livewire's own Stringable synth:

```php
use Illuminate\Support\Stringable;

class StringableSynth extends Synth
{
    public static $key = 'str';

    public static function match($target)
    {
        return $target instanceof Stringable;
    }

    public function dehydrate($target)
    {
        return [$target->__toString(), []];
    }

    public function hydrate($value)
    {
        return str($value);
    }
}
```

- `$key` is the string written into the tuple's metadata (`{ s: 'str' }`).
- `match()` decides whether this synth handles a given value during dehydration.
- `dehydrate()` returns `[$jsonableValue, $metadata]`.
- `hydrate()` rebuilds the PHP value.

A custom example:

```php
use App\Dtos\Address;

class AddressSynth extends Synth
{
    public static $key = 'address';

    public static function match($target)
    {
        return $target instanceof Address;
    }

    public function dehydrate($target)
    {
        return [[
            'street' => $target->street,
            'city'   => $target->city,
            'state'  => $target->state,
            'zip'    => $target->zip,
        ], []];
    }

    public function hydrate($value)
    {
        $instance = new Address;

        $instance->street = $value['street'];
        $instance->city   = $value['city'];
        $instance->state  = $value['state'];
        $instance->zip    = $value['zip'];

        return $instance;
    }
}
```

Register it from a service provider:

```php
Livewire::propertySynthesizer(AddressSynth::class);
```

Add `get()` and `set()` methods to the synth to support `wire:model` binding into
the object's own properties (`wire:model="address.city"`).

**`Wireable` is the simpler option** for an app-level class — implement
`toLivewire()` and `fromLivewire()`. Reach for a Synthesizer when you need to
support a type you do not own, or you are writing a package.

---

## Morphing

Livewire **morphs** rather than replaces: it walks the old and new HTML trees
together and makes surgical changes. That preserves event listeners, focus state,
and input values, and it is faster than re-creating DOM.

### Where morphing fails

The root cause of almost every morph bug: **a conditional that inserts a sibling
in the middle of the tree.**

```blade
<form wire:submit="save">
    <div><input wire:model="title"></div>

    @if ($errors->has('title'))
        <div>{{ $errors->first('title') }}</div>
    @endif

    <div><button>Save</button></div>
</form>
```

When the error appears, Livewire compares the second `<div>` in each tree, thinks
it is the same element with changed content, and turns the **button** into an
error message — then appends a new element at the end. The button is destroyed
and recreated instead of moved.

Symptoms: lost event listeners, state on the wrong element, duplicated or reset
Livewire components, lost Alpine state.

### The three mitigations

1. **Look-ahead** — Livewire checks subsequent elements before changing one.
   Automatic.
2. **Morph markers** — Livewire wraps `@if`, `@class` and `@foreach` in HTML
   comments (`<!--[if BLOCK]><![endif]-->`) as guides. Automatic, controlled by
   `'inject_morph_markers' => true`. It parses templates by regex, so it can
   occasionally misfire; setting it to `false` disables it.
3. **Wrap conditionals in an always-present element.** This is the reliable fix:

```blade
<form wire:submit="save">
    <div><input wire:model="title"></div>

    <div>                                    {{-- always present --}}
        @if ($errors->has('title'))
            <div>{{ $errors->first('title') }}</div>
        @endif
    </div>

    <div><button>Save</button></div>
</form>
```

### Opting out

- **`wire:ignore`** — Livewire does not touch this subtree. Use around
  third-party libraries that own their own DOM. `.self` ignores attribute changes
  on the element only.
- **`wire:replace`** — replace children wholesale instead of morphing. Use for
  web components with shadow DOM, or when element reuse corrupts internal state.
  `.self` replaces the element itself too.

```blade
<div wire:replace>
    <json-viewer>@json($someProperty)</json-viewer>
</div>

<div x-data="{ open: false }" wire:replace.self>
    {{-- "open" resets to false on every render --}}
</div>
```

---

## Component hooks — behavior for every component

A `ComponentHook` attaches to the lifecycle of **every** component in the app,
without touching the component classes or a trait.

```php
use Livewire\ComponentHook;

class MyComponentHook extends ComponentHook
{
    public static function provide()
    {
        // Once at application boot. Register services here.
    }

    public function mount($params, $parent) { }

    public function hydrate($memo) { }

    public function boot() { }

    public function update($property, $path, $value)
    {
        // before the property updates...
        return function () {
            // after it updates...
        };
    }

    public function call($method, $params, $returnEarly)
    {
        // before the method runs...
        return function ($returnValue) {
            // after it runs...
        };
    }

    public function render($view, $data)
    {
        // after render() is called, before Blade renders...
        return function ($html) {
            // after the view renders...
        };
    }

    public function dehydrate($context) { }

    public function exception($e, $stopPropagation) { }
}
```

Register from a service provider:

```php
Livewire::componentHook(MyComponentHook::class);
```

The worked example in the docs: intercept any action that returns a `Csv` object
and turn it into a file download, app-wide.

---

## Persistent middleware

When a component loads on a route carrying authorization middleware, Livewire
**re-applies that middleware to every subsequent update request**:

```php
Route::livewire('/post/{post}', App\Livewire\UpdatePost::class)
    ->middleware('can:update,post');
```

This closes the window where a user loads a page, loses permission, and then
triggers an update.

Persisted by default:

```php
\Laravel\Sanctum\Http\Middleware\EnsureFrontendRequestsAreStateful::class,
\Laravel\Jetstream\Http\Middleware\AuthenticateSession::class,
\Illuminate\Auth\Middleware\AuthenticateWithBasicAuth::class,
\Illuminate\Routing\Middleware\SubstituteBindings::class,
\App\Http\Middleware\RedirectIfAuthenticated::class,
\Illuminate\Auth\Middleware\Authenticate::class,
\Illuminate\Auth\Middleware\Authorize::class,
```

Add your own from a service provider:

```php
Livewire::addPersistentMiddleware([
    App\Http\Middleware\EnsureUserHasRole::class,
]);
```

> **Middleware arguments are not supported here.** Register
> `AuthorizeResource::class`, never `AuthorizeResource::class.':admin'`.

To apply middleware to **every** Livewire update request, register the update
route yourself:

```php
Livewire::setUpdateRoute(function ($handle, $path) {
    return Route::post($path, $handle)
        ->middleware(App\Http\Middleware\LocalizeViewPaths::class);
});
```

---

## File downloads

Return any Laravel download response from an action. Behind the scenes Livewire
Base64-encodes the file, sends it to the client, and decodes it there.

```php
public function download()
{
    return response()->download($this->invoice->file_path, 'invoice.pdf');
}

public function download()
{
    return Storage::disk('invoices')->download('invoice.csv');
}

public function download()
{
    return response()->streamDownload(function () {
        echo '...';
    }, 'invoice.pdf');
}
```

> "Streaming" downloads are not truly streamed — the download does not begin
> until the whole body has been collected and delivered.

Test them:

```php
->assertFileDownloaded('invoice.pdf');
->assertNoFileDownloaded();
```

---

## Package development

Register components from your package's service provider `boot()`.

**View-based (SFC/MFC):**

```php
Livewire::addNamespace(
    namespace: 'mypackage',
    viewPath: __DIR__ . '/../resources/views/livewire',
);
```

```blade
<livewire:mypackage::counter />
<livewire:mypackage::users.table />
```

**Class-based** needs more, plus registering the views with Laravel:

```php
Livewire::addNamespace(
    namespace: 'mypackage',
    classNamespace: 'MyVendor\\MyPackage\\Livewire',
    classPath: __DIR__ . '/Livewire',
    classViewPath: __DIR__ . '/../resources/views/livewire',
);

$this->loadViewsFrom(__DIR__ . '/../resources/views', 'my-package');
```

```php
public function render()
{
    return view('my-package::livewire.counter');
}
```

> **Do not use the ⚡ prefix in a package.** It causes problems with Composer when
> publishing. Name the file `counter.blade.php`.

---

## Content Security Policy

`'csp_safe' => true` switches Livewire and Alpine to a CSP-safe expression
evaluator, removing the need for `'unsafe-eval'`.

By default both use `new Function()` to compile expressions from HTML attributes,
which violates a strict CSP.

**Enabling it affects all Alpine in your app**, and that is where the limits bite
— Alpine expressions are usually more complex than Livewire ones.

**Works:**
```blade
<button wire:click="increment">+</button>
<button wire:click="updateUser('John', 25)">Update</button>
<button wire:click="saveData({ name: 'John', age: 30 })">Save</button>
<input wire:model="user.name">
<button wire:click="$set('user.active', true)">Activate</button>
<div wire:show="user.role === 'admin'">Admin Panel</div>
<div x-data="{ count: 0 }"><button x-on:click="count++"></button></div>
```

**Does not work:**
```blade
<button wire:click="items.filter(i => i.active).length">…</button>
<div wire:show="users.some(u => u.role === 'admin')">…</div>
<div x-text="`Hello ${name}`">…</div>
<div x-data="{ ...defaults }">…</div>
<button x-on:click="() => doSomething()">…</button>
<div wire:show="user[dynamicProperty]">…</div>
<button wire:click="this[methodName]()">…</button>
```

Work around it by moving logic into `Alpine.data()` getters, or into component
methods:

```blade
<div x-data="users">
    <div x-show="hasActiveAdmins">Admin panel available</div>
    <span x-text="activeUserCount">0</span>
</div>

<script nonce="[nonce]">
    Alpine.data('users', () => ({
        users: [],
        get hasActiveAdmins() {
            return this.users.filter(u => u.active && u.role === 'admin').length > 0
        },
        get activeUserCount() {
            return this.users.filter(u => u.active).length
        },
    }))
</script>
```

Matching headers:

```
Content-Security-Policy: default-src 'self';
                         script-src 'nonce-[random]' 'strict-dynamic';
                         style-src 'self' 'unsafe-inline';
```

Cost: slightly slower expression parsing, slightly larger bundle. Runtime is
comparable.

---

## Streaming

```php
$this->stream(content: 'Hello', replace: true, name: 'count');
$this->stream(content: 'Hello', replace: true, el: '#container');
$this->stream(content: 'Hello', replace: true, ref: 'output');
```

```blade
<span wire:stream="count">{{ $start }}</span>
```

The real signature is:

```php
stream($content = null, $replace = false, $name = null, $el = null, $ref = null, $to = null)
```

Three ways to target: `name:` matches `wire:stream="name"`, `el:` takes a CSS
selector, `ref:` takes a `wire:ref` name. **`to:` is the legacy v3 parameter and
maps to `name:`** — it still works, but `content` is now the first positional
argument, so any positional v3 call must be rewritten.

> `wire:stream` does **not** work with Laravel Octane.

Everything streams inside a single request, so a `sleep()` loop between
`stream()` calls drives a live countdown or a token-by-token AI response.

---

## Bundling

Component updates that happen at the same moment are **bundled into one request**
by default. Fewer connections, less server load — and it is what makes reactive
props and modelable props work across components.

Opt a component out with `#[Isolate]`:

```php
new #[Isolate] class extends Component {
    public function refreshStats() { /* expensive */ }
};
```

Useful when several components poll or listen for the same event and one of them
is slow enough to hold up the rest.

Lazy and deferred loads are **isolated by default** (parallel, so each appears as
soon as it is ready). Bundle them with `bundle: true` / `lazy.bundle`.

> `#[Lazy(isolate: false)]` is the legacy spelling of `#[Lazy(bundle: true)]`.

---

## Global JavaScript events

```js
document.addEventListener('livewire:init', () => {
    // Livewire loaded, not yet initialized. Register directives and hooks here.
})

document.addEventListener('livewire:initialized', () => {
    // Initialization complete.
})
```

Navigation adds three more — see `islands-performance.md`.
