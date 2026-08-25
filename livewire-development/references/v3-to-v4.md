# Upgrading Livewire v3 → v4

Most applications upgrade with few changes. The breaking changes are mostly
configuration and method signatures affecting advanced usage.

```bash
composer require livewire/livewire:^4.0
php artisan optimize:clear
```

Full diff: `github.com/livewire/livewire/compare/3.x...main`.
[Laravel Shift](https://laravelshift.com) automates part of it.

---

## v4.0 → v4.1

**`wire:model` modifier behavior changed again.** `.blur` and `.change` now control
client-side sync, not just network timing. To keep the previous behavior, add
`.live` before them: `wire:model.live.blur`. Details below.

---

## High impact

### Config keys

| v3 | v4 |
|---|---|
| `'layout' => 'components.layouts.app'` | `'component_layout' => 'layouts::app'` |
| `'lazy_placeholder' => 'livewire.placeholder'` | `'component_placeholder' => 'livewire.placeholder'` |

Changed default:
```php
'smart_wire_keys' => true,   // was false in v3
```
It generates keys for deeply nested components. **You still add `wire:key` in
loops** — it does not remove that requirement.

New keys:
```php
'component_locations' => [
    resource_path('views/components'),
    resource_path('views/livewire'),
],

'component_namespaces' => [
    'layouts' => resource_path('views/layouts'),
    'pages'   => resource_path('views/pages'),
],

'make_command' => [
    'type'  => 'sfc',   // 'sfc' | 'mfc' | 'class' — set 'class' for v3 behavior
    'emoji' => true,    // the ⚡ filename prefix
],

'csp_safe' => false,    // Alpine CSP build, avoids unsafe-eval
```

### Routing

```php
Route::get('/dashboard', Dashboard::class);          // v3 — still works
Route::livewire('/dashboard', Dashboard::class);     // v4 — recommended
Route::livewire('/dashboard', 'pages::dashboard');   // v4 — view-based components
```

`Route::livewire()` is **required** for single-file and multi-file components to
work as full pages.

### `wire:model` ignores child events

v3 responded to `input`/`change` bubbling up from children. That surprised anyone
with `wire:model` on a container — clearing an input inside a modal could close it.

v4 behaves as if `.self` were always applied. Restore the old behavior with
`.deep`:

```blade
<div wire:model.deep="value">
    <input type="text">
</div>
```

Standard input/select/textarea bindings are unaffected.

### `wire:scroll` → `wire:navigate:scroll`

```blade
@persist('sidebar')
    <div class="overflow-y-scroll" wire:navigate:scroll>
        …
    </div>
@endpersist
```

### Component tags must be closed

v3 rendered an unclosed tag anyway. With slots in v4, an unclosed tag makes
Livewire read the following markup as slot content and the component does not
render.

```blade
<livewire:component-name>     {{-- v3 --}}
<livewire:component-name />   {{-- v4 --}}
```

---

## Medium impact

### `wire:model` modifiers control client-side sync

| v3 | v4 equivalent |
|---|---|
| `wire:model.blur` | `wire:model.live.blur` |
| `wire:model.change` | `wire:model.live.change` |

`.lazy` is unchanged.

What this unlocks — delaying client state with no network request at all:

```blade
<input wire:model.blur="width">
<input wire:model.blur.enter="search">
```

### `wire:transition` uses the View Transitions API

Basic usage still fades. **All modifiers were removed.**

```blade
<div wire:transition>…</div>                    {{-- still works --}}
<div wire:transition.opacity>…</div>            {{-- gone --}}
<div wire:transition.scale.origin.top>…</div>   {{-- gone --}}
<div wire:transition.duration.500ms>…</div>     {{-- gone --}}
```

### Update hooks consolidate array replacement

Replacing a whole array from the frontend (`$wire.items = ['a','b']`) now fires
`updatingItems`/`updatedItems` **once** with the full new value — matching v2 —
instead of once per index plus `__rm__` removals.

Single-item changes (`wire:model="items.0"`) still fire granularly.

### `stream()` signature

```php
$this->stream(to: '#container', content: 'Hello', replace: true);   // v3
$this->stream(content: 'Hello', replace: true, el: '#container');   // v4

$this->stream('#container', 'Hello');       // v3 positional
$this->stream('Hello', el: '#container');   // v4
```

`to:` was renamed to `el:` and the positional order changed.

### `mount()` on LivewireManager (internal)

```php
public function mount($name, $params = [], $key = null)              // v3
public function mount($name, $params = [], $key = null, $slots = []) // v4
```

Only affects code extending `LivewireManager` or calling `mount()` directly.

### Performance (automatic, no code change)

- `wire:poll` no longer blocks other requests or is blocked by them.
- `wire:model.live` requests run in parallel — faster typing, quicker results.

---

## Low impact

### `wire:model` supports bracket notation

```blade
<input wire:model="foo['bar']['baz']">
<input wire:model="items[0].name">
```

Square brackets are now **property accessors**. In v3 they were literal
characters — rename any property key containing them.

### Asset and endpoint URLs carry a hash

```
/livewire/update        →  /livewire-{hash}/update
/livewire/upload-file   →  /livewire-{hash}/upload-file
/livewire/livewire.js   →  /livewire-{hash}/livewire.js
```

The hash derives from `APP_KEY`, so it is unique per installation. **Update
firewall rules, CDN config, and middleware that match `/livewire/`.**

If you use `setUpdateRoute`, take the new `$path` parameter to preserve it:

```php
Livewire::setUpdateRoute(function ($handle) {                 // v3
    return Route::post('/livewire/update', $handle);
});

Livewire::setUpdateRoute(function ($handle, $path) {          // v4
    return Route::post($path, $handle);
});
```

---

## JavaScript deprecations

All still work; migrate when convenient.

### `$wire.$js()` → property assignment

```js
$wire.$js('bookmark', () => {})   // deprecated
$js('bookmark', () => {})         // deprecated

$wire.$js.bookmark = () => {}     // new
this.$js.bookmark = () => {}      // new
```

### `commit` hook → `interceptMessage`

```js
// deprecated
Livewire.hook('commit', ({ component, commit, respond, succeed, fail }) => {
    respond(() => {})
    succeed(({ snapshot, effects }) => {})
    fail(() => {})
})

// new
Livewire.interceptMessage(({ component, message, onFinish, onSuccess, onError, onFailure }) => {
    onFinish(() => {})                    // was respond()
    onSuccess(({ payload }) => {})        // was succeed(); payload.snapshot, payload.effects
    onError(() => {})                     // was fail(), server errors
    onFailure(() => {})                   // was fail(), network errors
})
```

### `request` hook → `interceptRequest`

```js
// deprecated
Livewire.hook('request', ({ url, options, payload, respond, succeed, fail }) => {
    respond(({ status, response }) => {})
    succeed(({ status, json }) => {})
    fail(({ status, content, preventDefault }) => {})
})

// new
Livewire.interceptRequest(({ request, onResponse, onSuccess, onError, onFailure }) => {
    // request.uri, request.options, request.payload

    onResponse(({ response }) => {})                        // response.status
    onSuccess(({ response, responseJson }) => {})
    onError(({ response, responseBody, preventDefault }) => {})
    onFailure(({ error }) => {})
})
```

**What the new system adds:** network failures (`onFailure`) are separated from
server errors (`onError`); extra lifecycle hooks `onSync`, `onMorph`, `onMorphed`,
`onRender`; cancellation for messages and requests; and per-component scoping via
`$wire.intercept(...)`.

---

## Migrating from Volt

> **Volt is not gone.** Livewire v4 absorbed only Volt's **class-based** syntax.
> The **functional** API (`state()`, `computed()`, `$increment = fn () =>`) still
> lives in the `livewire/volt` package, which is still shipped and documented on
> the 4.x branch. Livewire's own wording: *"Volt is optional in Livewire v4 …
> most applications won't need Volt. Volt exists for developers who prefer a
> functional, closure-based syntax."*
>
> The steps below apply to **class-based Volt only**. If you use the functional
> API and want to keep it, keep the package and change nothing. See
> `references/volt.md`.

Livewire v4's single-file components use the same syntax as Volt class-based
components, so class-based Volt code moves over unchanged.

**1. Imports**
```php
use Livewire\Volt\Component;   // before
use Livewire\Component;        // after
```

**2. Routes**
```php
Volt::route('/dashboard', 'dashboard');            // before
Route::livewire('/dashboard', 'dashboard');        // after
```

**3. Tests**
```php
use Livewire\Volt\Volt;   →   use Livewire\Livewire;
Volt::test('counter')     →   Livewire::test('counter')
```

**4. Remove the service provider**
```bash
rm app/Providers/VoltServiceProvider.php
```
```php
// bootstrap/providers.php — remove the entry
return [
    App\Providers\AppServiceProvider::class,
];
```

**5. Remove the package**
```bash
composer remove livewire/volt
```

Then install Livewire v4. Existing Volt class-based components work as-is.

---

## New in v4 — what you can start using

### Component formats

```bash
php artisan make:livewire create-post        # single-file (default)
php artisan make:livewire create-post --mfc  # multi-file
php artisan livewire:convert create-post     # convert between them
```

Files are prefixed with `⚡`. Disable via `'make_command' => ['emoji' => false]`.

### Slots and attribute forwarding

```blade
<livewire:comment :$comment>
    <button wire:click="removeComment({{ $comment->id }})">Remove</button>
</livewire:comment>
```
```blade
<div {{ $attributes->class('bg-white') }}>
    {{ $slot }}
    {{ $slots['actions'] }}
</div>
```

### Bare `<script>` in view-based components

```blade
<script>
    this.count++       // $wire is bound as `this`
    $wire.save()
</script>
```

Served as separate cached files. Class-based components still need `@script`.

### Islands

```blade
@island(name: 'stats', lazy: true)
    <div>{{ $this->expensiveStats }}</div>
@endisland
```

Isolated regions that update independently — the performance of a child component
with none of the plumbing.

### Deferred and bundled loading

```blade
<livewire:revenue defer />
<livewire:revenue lazy.bundle />
<livewire:expenses defer.bundle />
```
```php
#[Defer]
#[Lazy(bundle: true)]
```

### Async actions

```blade
<button wire:click.async="logActivity">Track</button>
```
```php
#[Async]
public function logActivity() { }
```

### New directives

```blade
{{-- drag-and-drop sorting --}}
<ul wire:sort="updateOrder">
    <li wire:sort:item="{{ $item->id }}" wire:key="{{ $item->id }}">{{ $item->name }}</li>
</ul>

{{-- viewport intersection --}}
<div wire:intersect="loadMore">…</div>
<div wire:intersect.once="trackView">…</div>
<div wire:intersect:leave="pauseVideo">…</div>
<div wire:intersect.half="loadMore">…</div>
<div wire:intersect.margin.200px="loadMore">…</div>
<div wire:intersect.threshold.50="trackScroll">…</div>

{{-- element references --}}
<div wire:ref="modal">…</div>
```

### New modifiers

```blade
<button wire:click.renderless="trackClick">Track</button>
<button wire:click.preserve-scroll="loadMore">Load More</button>
```

### `data-loading`

Every element that triggers a request gets the attribute automatically:

```blade
<button wire:click="save" class="data-loading:opacity-50 data-loading:pointer-events-none">
    Save Changes
</button>
```

### `$errors` in the template

```blade
<div wire:show="$errors.has('email')">
    <span wire:text="$errors.first('email')"></span>
</div>
```

### `$intercept`

```blade
<script>
    this.$intercept('save', ({ … }) => { })
</script>
```

### Island targeting from the template

```blade
<button wire:click="loadMore" wire:island.append="stats">Load more</button>
```

---

## Post-upgrade checklist

- [ ] `composer require livewire/livewire:^4.0` and `php artisan optimize:clear`
- [ ] Rename `layout` → `component_layout`, `lazy_placeholder` → `component_placeholder`
- [ ] Decide `make_command.type` — `'sfc'` (new default) or `'class'` (v3 shape)
- [ ] Switch page routes to `Route::livewire()`
- [ ] Close every `<livewire:… />` tag
- [ ] `wire:model.blur` → `wire:model.live.blur` (same for `.change`)
- [ ] Add `.deep` to any `wire:model` on a container that needs child events
- [ ] `wire:scroll` → `wire:navigate:scroll`
- [ ] Remove `wire:transition` modifiers
- [ ] Update `$this->stream()` calls to `el:`
- [ ] Update firewall / CDN / middleware rules for `/livewire-{hash}/`
- [ ] Update `setUpdateRoute` / `setScriptRoute` to take `$path`
- [ ] Rename any property key containing `[` or `]`
- [ ] Migrate off `$wire.$js('name', cb)`, the `commit` hook, the `request` hook
- [ ] If on Volt: swap imports, routes, tests; remove provider and package
- [ ] Run the suite; smoke-test pages with loops for missing `wire:key`
