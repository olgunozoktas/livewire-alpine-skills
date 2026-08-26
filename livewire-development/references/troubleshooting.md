# Troubleshooting — symptom to cause to fix

Start here when something is broken. Find the symptom, not the feature.

---

## Triage table

| Symptom | Most likely cause | Fix |
|---|---|---|
| `Component already initialized` | Missing `wire:key` in a loop | Add `wire:key` to the first element inside every `@foreach` |
| `Snapshot missing on Livewire component with id: …` | Same | Same — including on nested components *deep* inside a loop |
| Rows show the wrong data after a sort or filter | Missing or non-unique `wire:key` | Prefix keys: `post-{{ $id }}`, `author-{{ $id }}` |
| `Detected multiple instances of Alpine running` | Alpine included twice | Remove the CDN tag / `Alpine.start()` — Livewire bundles it |
| `Alpine Expression Error: $wire is not defined` | Same | Same |
| `Uncaught Alpine: no element provided to x-anchor` | `@alpinejs/ui` is the one plugin Livewire does not bundle | Add that plugin from a CDN |
| Input does not update as I type | `wire:model` is deferred by default | Add `.live` — and consider `.blur` or `.debounce` first |
| `wire:model.blur` stopped sending requests after upgrading | v4 changed its meaning | Write `wire:model.live.blur` |
| A dependent `<select>` keeps stale options | Child select has no key | `wire:key="cities-{{ $stateId }}"` on the second select |
| Event listener silently never fires (Echo) | `broadcastAs()` name needs a leading dot | `#[On('echo:scores,.score.submitted')]` |
| Every row's spinner lights up when one button is pressed | `wire:target` is not scoped to the parameters | `wire:target="remove({{ $post->id }})"` |
| Validation error appears and the button disappears | Morph mis-paired a conditional sibling | Wrap the conditional in an always-present element |
| Alpine state resets on every Livewire update | Something forces a replace | Check for `wire:replace.self`; morphing normally preserves it |
| Third-party JS widget breaks after any update | Livewire is morphing DOM the library owns | `wire:ignore` around it |
| Web component keeps stale internal state | Morph reused the element | `wire:replace` |
| `Livewire JavaScript 404` | Nginx blocks `/livewire-{hash}/`, or routes are cached | See "404 on the JS asset" below |
| Blank component, no error | No single root element, or a PHP syntax error | Check the root element; read `storage/logs/laravel.log` |
| `Component [x] not found` | Path, dot notation, or namespace mismatch | `php artisan view:clear`, verify the file path |
| `Unable to locate file in Vite manifest` | Asset not built | Build assets; unrelated to Livewire |
| Query constraints vanish between requests | Eloquent property re-queried from keys | Use a `#[Computed]` property, not a public property |
| A `select(...)` returns full models on the 2nd request | Same | Same |
| Async action increments once for five clicks | Parallel requests each start from the same snapshot | Never mutate rendered state in `#[Async]` |
| `CorruptComponentPayloadException` | Snapshot checksum failed — tampering, or a shared cache mismatch | Do not disable it; find what mutated the snapshot |
| Property changes from DevTools and the action still runs | Property is not locked or authorized | `#[Locked]`, or a model property, plus `$this->authorize()` |
| `wire:stream` does nothing | Laravel Octane | `wire:stream` is not compatible with Octane |
| Island errors on a variable that exists | Islands cannot read template scope | Move the value onto the component, use `$this->` |
| Island inside `@foreach` does not work | Islands cannot go in control structures | Put the loop *inside* the island |
| Transitions do nothing in Firefox | Firefox has no transition **types** | Expected — falls back to untyped |
| Transitions do nothing for one user | `prefers-reduced-motion` | Expected and correct |
| `@script` needed or not? | Depends on component format | Class-based needs it; SFC/MFC must not use it |
| `import.meta.env.DEV` gating breaks a build | It means "dev server running", not "development" | Not a Livewire issue — see the project's own notes |

---

## The big three, in detail

### 1. Missing `wire:key`

By far the most common Livewire bug, and the error message never says "key".

```blade
@foreach ($posts as $post)
    <div wire:key="{{ $post->id }}">…</div>
@endforeach

@foreach ($posts as $post)
    <livewire:show-post :$post :wire:key="$post->id" />
@endforeach
```

Three cases people miss:

1. **A component nested deep inside a loop** still needs its own key, even when
   an ancestor already has one.
2. **Two loops in one component** whose models share ids collide. Prefix:
   `post-{{ $id }}` and `author-{{ $id }}`.
3. **`@switch` / `@case`** need keys for the same reason `@foreach` does.

`'smart_wire_keys' => true` (the v4 default) generates keys for nested
components that lack them. **It does not remove the requirement in loops.**

### 2. Two copies of Alpine

Livewire bundles Alpine. A second copy breaks `$wire` everywhere.

```js
// resources/js/app.js — remove all three lines
import Alpine from 'alpinejs';
window.Alpine = Alpine;
Alpine.start();
```

```html
<!-- remove from the layout -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

Separate Alpine **plugin** tags can go too — Livewire bundles all of them except
`@alpinejs/ui`.

**On a page with no Livewire component**, Alpine is absent unless you include
`@livewireScripts` anyway.

### 3. Morph put state on the wrong element

The classic shape: a conditional that inserts a sibling **in the middle** of the
tree.

```blade
{{-- fragile --}}
<form wire:submit="save">
    <div><input wire:model="title"></div>

    @if ($errors->has('title'))
        <div>{{ $errors->first('title') }}</div>
    @endif

    <div><button>Save</button></div>
</form>
```

When the error appears, Livewire compares the second `<div>` in each tree,
concludes it is the same element with new content, and turns the **button** into
an error message — then appends a new element at the end.

```blade
{{-- robust: the conditional lives inside an element that is always there --}}
<form wire:submit="save">
    <div><input wire:model="title"></div>

    <div>
        @if ($errors->has('title'))
            <div>{{ $errors->first('title') }}</div>
        @endif
    </div>

    <div><button>Save</button></div>
</form>
```

Livewire mitigates this with a look-ahead pass and injected morph markers
(`'inject_morph_markers' => true`), but the structural fix is the reliable one.

---

## 404 on the JavaScript asset

Livewire serves from `/livewire-{hash}/livewire.js`, unique per installation.

**Nginx blocking it** — pass the pattern to Laravel:

```nginx
location ~ ^/livewire-[a-f0-9]+/ {
    try_files $uri $uri/ /index.php?$query_string;
}
```

**Route cache** — `php artisan route:clear`.

**Auto-injection disabled** — add `@livewireScripts` before `</body>`.

**Firewall or CDN rules** written for v3's `/livewire/` prefix need updating.

---

## Debugging tools

**From the browser console:**

```js
let $wire = Livewire.first()      // or Livewire.find(id) / Livewire.getByName('post.index')
$wire.count                       // read a property
$wire.increment()                 // call an action
$wire.__instance().snapshot       // the raw snapshot
```

**Log every request:**

```js
Livewire.interceptRequest(({ onSend, onSuccess, onError }) => {
    onSend(() => console.log('→', Date.now()))
    onSuccess(({ response }) => console.log('←', response.status))
    onError(({ response, body }) => console.error('✗', response.status, body))
})
```

**Watch a single component's actions:**

```js
$wire.intercept(({ action, onSuccess, onError }) => {
    console.log('action:', action.name, action.params)
    onSuccess(r => console.log('  →', r))
    onError(e => console.error('  ✗', e))
})
```

**From PHP** — `$this->js("console.log(…)")` runs after the response morphs.

---

## Reading the network tab

A Livewire request posts to `/livewire-{hash}/update` with:

```json
{ "snapshot": "…", "updates": { "title": "New" },
  "calls": [{ "method": "save", "params": [] }] }
```

and returns:

```json
{ "snapshot": "…", "effects": { "html": "…", "returns": [] } }
```

- **`updates` empty when you expected a value** → `wire:model` has no `.live`
  and no action ran.
- **`calls` empty** → the directive did not bind. Check for a typo in the method
  name, or a `wire:` directive on an element Livewire is ignoring.
- **`effects.html` missing** → the action was renderless (`#[Renderless]`,
  `.renderless`, `#[Json]`, or `skipRender()`).
- **419** → session expired. Handle it globally with an `interceptRequest`
  `onError`.
- **500 with an HTML body** → a normal Laravel exception. Read the log.

---

## Checks before asking anyone

```bash
php artisan view:clear
php artisan route:clear
php artisan cache:clear
php artisan optimize:clear
```

Confirm PHP 8.1+ and Laravel 10+, `@livewireStyles` in `<head>`,
`@livewireScripts` before `</body>`, and — most of all — **the Livewire major
version** (see `version-guide.md`). A v3 project given v4 code fails in ways
that read as unrelated bugs.
