# Full API reference — attributes, directives, config, troubleshooting

---

## PHP attributes

All live in `Livewire\Attributes\`. Import them — a missing import is a common
silent failure, because PHP treats an unresolvable attribute as an error only when
it is reflected.

| Attribute | Target | Purpose |
|---|---|---|
| `#[Async]` | method | Run in parallel, bypassing the request queue |
| `#[Authorize]` | method | Gate check before the action runs |
| `#[Computed]` | method | Memoized derived property |
| `#[Defer]` | class | Load immediately after page load |
| `#[Isolate]` | class | Never bundle this component's requests |
| `#[Js]` | method | Method returns JavaScript to run client-side |
| `#[Json]` | method | Action returns JSON to JavaScript, skips render |
| `#[Layout]` | class | Layout for a page component |
| `#[Lazy]` | class | Load when scrolled into view |
| `#[Locked]` | property | Refuse client-side modification |
| `#[Modelable]` | property | Bindable from a parent via `wire:model` |
| `#[On]` | method | Event listener |
| `#[Reactive]` | property | Prop updates when the parent changes it |
| `#[Renderless]` | method | Skip the render phase |
| `#[Session]` | property | Persist in the session across page loads |
| `#[Title]` | class | Page title |
| `#[Transition]` | method | View-transition behavior for an action |
| `#[Url]` | property | Sync with the URL query string |
| `#[Validate]` | property | Validation rules |
| `#[Rule]` | property | **Deprecated** alias for `#[Validate]` |

Class-level attributes go between `new` and `class`:

```php
new #[Layout('layouts::app')] class extends Component { };
new #[Title('Create post')] class extends Component { };
new #[Isolate] class extends Component { };
```

### Parameters

```php
#[Computed(
    bool $persist = false,     // cache across requests for this component instance
    int $seconds = 3600,       // cache duration
    bool $cache = false,       // cache across ALL component instances
    ?string $key = null,       // custom cache key
    mixed $tags = null,        // cache tags (needs a tag-capable driver)
)]

#[Url(
    ?string $as = null,        // query parameter alias
    bool $history = false,     // push to browser history
    bool $keep = false,        // keep when navigating away
    mixed $except = null,      // value(s) to omit from the URL
    mixed $nullable = null,    // value when the parameter is absent
)]

#[Validate(
    mixed $rule = null,
    ?string $attribute = null, // custom attribute name for messages
    ?string $as = null,        // friendly name in messages
    mixed $message = null,     // custom message(s)
    bool $onUpdate = true,     // validate on property update
    bool $translate = true,    // run messages through trans()
)]

#[Lazy(bool|null $bundle = null)]
#[Defer(bool|null $bundle = null)]
#[Layout(string $name, array $params = [])]
#[Title(string $content)]
#[Session(?string $key = null)]
#[On(string $event)]

#[Authorize(                       // repeatable
    \UnitEnum|string $ability,
    array|string|null $argument = null,
)]

#[Transition(
    ?string $type = null,          // e.g. 'forward', 'backward'
    bool $skip = false,            // skip the transition entirely
)]
```

`#[Authorize]` names a gate/policy ability, with an optional argument — a property
name resolves to that property's value:

```php
#[Authorize('update', 'post')]
public function save() { $this->post->save(); }
```

It throws a 403 when the check fails, before the action body runs.

`#[Locked]`, `#[Reactive]`, `#[Renderless]`, `#[Async]`, `#[Modelable]`, `#[Js]`
and `#[Json]` take no parameters.

---

## `wire:` directives

### Actions

```blade
wire:click="methodName"
wire:click="methodName(param1, param2)"
wire:submit="save"
wire:keydown.enter="search"
wire:mouseenter="…"
wire:{any-browser-event}="…"
```

**Modifiers shared by every event directive** (Alpine's, plus Livewire's):

| Modifier | Effect |
|---|---|
| `.prevent` | `preventDefault()` (automatic on `wire:submit`) |
| `.stop` | `stopPropagation()` |
| `.self` | Only if the event originated on this element |
| `.once` | Fire at most once |
| `.debounce` / `.debounce.500ms` | Debounce (default 250 ms) |
| `.throttle` / `.throttle.500ms` | Throttle (default 250 ms) |
| `.window` | Listen on `window` |
| `.document` | Listen on `document` |
| `.outside` | Clicks outside the element |
| `.passive` | Do not block scrolling |
| `.capture` | Capturing phase |
| `.camel` | `wire:custom-event` → `customEvent` |
| `.dot` | `wire:custom-event` → `custom.event` |
| `.renderless` | Skip re-rendering after the action |
| `.preserve-scroll` | Keep scroll position |
| `.async` | Run in parallel instead of queued |

**Key modifiers** for `keydown` / `keyup`: `.shift` `.enter` `.space` `.ctrl`
`.cmd` `.meta` `.alt` `.up` `.down` `.left` `.right` `.escape` `.tab` `.caps-lock`
`.equal` `.period` `.slash`. Chain to combine: `wire:keydown.shift.enter`.

### `wire:model`

```blade
wire:model="propertyName"
wire:model="property.nested"
wire:model="property['nested']"
wire:model="property[0]"
```

| Modifier | Effect |
|---|---|
| `.live` | Send updates to the server |
| `.blur` | Sync on blur |
| `.change` | Sync on change |
| `.enter` | Sync on Enter |
| `.lazy` | Update on change and request (v3-compatible) |
| `.debounce.Xms` | Debounce (with `.live`) |
| `.throttle.Xms` | Throttle (with `.live`) |
| `.number` | Cast to `int` server-side |
| `.boolean` | Cast to `bool` server-side |
| `.fill` | Take the initial value from the `value` attribute |
| `.deep` | Also listen to child element events |
| `.renderless` | Skip re-render after a live update |
| `.preserve-scroll` | Keep scroll position |

### Loading and state

```blade
wire:loading
wire:target="action" | "property" | .except="action"
wire:dirty
wire:offline
wire:cloak
```

`wire:loading` modifiers: `.remove`, `.class="name"`, `.class.remove="name"`,
`.attr="attribute"`, `.delay` (200 ms), `.delay.shortest|shorter|short` (50/100/150 ms),
`.delay.long|longer|longest` (300/500/1000 ms), and display hints `.inline-flex`
`.inline` `.block` `.table` `.flex` `.grid`.

`wire:dirty` modifiers: `.remove`, `.class="name"`. The `$dirty` expression works
in directives (`wire:show="$dirty"`), takes a property (`$dirty('title')`) or an
array (`$dirty(['title', 'description'])`), and is `$wire.$dirty()` in Alpine.

`wire:offline` modifiers: `.class="name"`, `.class.remove="name"`, `.attr="attribute"`.

### Rendering control

```blade
wire:key="unique-id"       {{-- mandatory in loops --}}
wire:ignore                {{-- exclude from morphing; .self for attributes only --}}
wire:replace               {{-- replace children rather than morph; .self includes the element --}}
wire:show="expression"
wire:text="expression"
wire:bind:{attribute}="expression"
wire:transition="name"     {{-- View Transitions API; no modifiers in v4 --}}
```

`wire:bind` takes any HTML attribute: `wire:bind:class`, `wire:bind:disabled`,
`wire:bind:href`, `wire:bind:data-state`.

`wire:transition` with no expression uses `match-element` as the transition name.

### Triggers

```blade
wire:init="action"                    {{-- run once when the component loads --}}
wire:poll                             {{-- .Ns .Nms .keep-alive .visible --}}
wire:intersect="action"               {{-- also :enter and :leave --}}
wire:confirm="message"                {{-- .prompt for "message|expected-input" --}}
```

`wire:intersect` modifiers: `.once`, `.half`, `.full`, `.threshold.[0-100]`,
`.margin.[value]` (e.g. `.margin.200px`, `.margin.10%`).

### Navigation

```blade
wire:navigate            {{-- .hover to prefetch after 60ms --}}
wire:navigate:scroll     {{-- preserve scroll in a container (was wire:scroll in v3) --}}
wire:current="classes"   {{-- .exact, .strict --}}
```

### Islands

```blade
wire:island="name"
wire:island.append="name"
wire:island.prepend="name"
```

### Sorting

```blade
<ul wire:sort="updateOrder">
    @foreach ($items as $item)
        <li wire:sort:item="{{ $item->id }}" wire:key="{{ $item->id }}">{{ $item->name }}</li>
    @endforeach
</ul>
```

Related: `wire:sort:group="name"`, `wire:sort:group-id="identifier"`,
`wire:sort:handle`, `wire:sort:ignore`. No modifiers.

### Streaming and references

```blade
wire:stream="name"     {{-- .replace to swap instead of append --}}
wire:ref="name"        {{-- reachable as $wire.$refs.name / this.$refs.name --}}
```

---

## Redirecting

A Livewire request is not a full browser request, so an HTTP redirect will not
work. Use the component helpers — Livewire performs the redirect on the client.

```php
$this->redirect('/posts');
$this->redirect('/posts', navigate: true);          // SPA-style, no full reload
$this->redirectRoute('profile');
$this->redirectRoute('profile', ['id' => 1]);
$this->redirectIntended('/default/url');            // back where they came from
$this->redirectAction([UserController::class, 'index']);
$this->redirectAction([UserController::class, 'show'], ['id' => 1]);
```

Flash data works exactly as in Laravel:

```php
session()->flash('status', 'Post successfully updated.');

$this->redirect('/posts');
```

`'render_on_redirect' => false` (the default) skips the final `render()` before
redirecting. Set it to `true` if you need the view rendered once more.

---

## Blade directives

| Directive | Purpose |
|---|---|
| `@livewireStyles` | Livewire CSS, in `<head>` |
| `@livewireScripts` | Livewire + Alpine JS, before `</body>` |
| `@livewireScriptConfig` | Config only — use when bundling Livewire yourself |
| `@island(…)` … `@endisland` | Isolated update region |
| `@placeholder` … `@endplaceholder` | Loading content for a lazy component or island |
| `@persist('name')` … `@endpersist` | Keep an element across `wire:navigate` visits |
| `@teleport('#selector')` … `@endteleport` | Move HTML elsewhere in the DOM |
| `@assets` … `@endassets` | Load scripts/styles once per page |
| `@script` … `@endscript` | Wrap `<script>` — **class-based components only** |
| `@js($data)` | Serialize PHP data into a JS expression |
| `@error('field')` … `@enderror` | Laravel's validation error block |

> `@teleport` only moves HTML **outside** the component. It cannot teleport into
> another component.

---

## Config — `config/livewire.php`

Publish with `php artisan livewire:config`. Livewire is zero-config; you only need
this file to change something.

```php
return [
    // Where view-based components are discovered. make:livewire writes to the FIRST.
    'component_locations' => [
        resource_path('views/components'),
        resource_path('views/livewire'),
    ],

    // Namespace prefixes: <livewire:pages::dashboard />
    'component_namespaces' => [
        'layouts' => resource_path('views/layouts'),
        'pages'   => resource_path('views/pages'),
    ],

    // Default layout for Route::livewire() page components.
    'component_layout' => 'layouts::app',

    // Default lazy-loading placeholder view.
    'component_placeholder' => null,   // e.g. 'placeholders::skeleton'

    'make_command' => [
        'type'  => 'sfc',   // 'sfc' | 'mfc' | 'class'
        'emoji' => true,    // the ⚡ filename prefix
        'with'  => ['js' => false, 'css' => false, 'test' => false],
    ],

    'class_namespace' => 'App\\Livewire',
    'class_path'      => app_path('Livewire'),
    'view_path'       => resource_path('views/livewire'),

    'temporary_file_upload' => [
        'disk'          => env('LIVEWIRE_TEMPORARY_FILE_UPLOAD_DISK'),
        'rules'         => null,   // default ['required','file','max:12288'] (12MB)
        'directory'     => null,   // default 'livewire-tmp'
        'middleware'    => null,   // default 'throttle:60,1'
        'preview_mimes' => ['png','gif','bmp','svg','wav','mp4','mov','avi','wmv',
                            'mp3','m4a','jpg','jpeg','mpga','webp','wma'],
        'max_upload_time' => 5,
        'cleanup'         => true,
    ],

    // Run render() once more before redirecting.
    'render_on_redirect' => false,

    // v2-style direct model binding via wire:model. Off by design.
    'legacy_model_binding' => false,

    // Auto-inject JS/CSS into pages containing components.
    'inject_assets' => true,

    'navigate' => [
        'show_progress_bar'  => true,
        'progress_bar_color' => '#2299dd',
    ],

    // HTML comment markers around @if/@class/@foreach to guide morphing.
    'inject_morph_markers' => true,

    // Generate keys for nested components inside keyed loops. Default true in v4.
    'smart_wire_keys' => true,

    // Alpine CSP build — avoids unsafe-eval, restricts expression complexity.
    'csp_safe' => false,
];
```

### To restore v3 conventions

```php
'make_command' => [
    'type'  => 'class',
    'emoji' => false,
],
```

### CSP-safe mode

`'csp_safe' => true` switches to the [Alpine CSP build](https://alpinejs.dev/advanced/csp),
removing `unsafe-eval`. The cost: complex expressions in directives stop working —
no `wire:click="addToCart($event.detail.productId)"`, no `window.location`
references. Plan for it before enabling.

---

## Advanced installation

### Manually bundling Livewire and Alpine

Needed when you want to register Alpine plugins or control init order.

Swap `@livewireScripts` for `@livewireScriptConfig` in the layout, then:

```js
// resources/js/app.js
import { Livewire, Alpine } from '../../vendor/livewire/livewire/dist/livewire.esm';
import Clipboard from '@ryangjchandler/alpine-clipboard'

Alpine.plugin(Clipboard)

Livewire.start()
```

Rebuild assets (`npm run build`) after every Composer update of Livewire.

### Custom endpoints

Livewire serves from `/livewire-{hash}/…` where `{hash}` derives from `APP_KEY`.
Override in a provider's `boot()` when route prefixes (localization,
multi-tenancy) require it:

```php
Livewire::setUpdateRoute(function ($handle, $path) {
    return Route::post('/custom' . $path, $handle)->middleware(['web', 'auth']);
});

Livewire::setScriptRoute(function ($handle, $path) {
    return Route::get('/custom' . $path, $handle);
});
```

Keep `$path` in the result — it preserves the per-installation hash.

### Publishing assets to `public/`

```shell
php artisan livewire:publish --assets
```
```json
{
    "scripts": {
        "post-update-cmd": [
            "@php artisan vendor:publish --tag=livewire:assets --ansi --force"
        ]
    }
}
```

Rarely necessary. Only for CDN distribution or specific caching needs.

### Disabling auto-injection

```php
'inject_assets' => false,
```

You must then place `@livewireStyles` and `@livewireScripts` yourself.
`\Livewire\Livewire::forceAssetInjection()` re-enables it for one route.

---

## Troubleshooting

### "Component already initialized" / "Snapshot missing on Livewire component with id: …"

Almost always a missing `wire:key`.

```blade
@foreach ($posts as $post)
    <div wire:key="{{ $post->id }}">…</div>
@endforeach

@foreach ($posts as $post)
    <livewire:show-post :$post :wire:key="$post->id" />
@endforeach
```

A Livewire component nested **deep** inside a loop still needs its own key. And
prefix keys when two loops in one component could collide:

```blade
<div wire:key="post-{{ $post->id }}">…</div>
<div wire:key="author-{{ $author->id }}">…</div>
```

### "Detected multiple instances of Alpine running" / "$wire is not defined"

Two copies of Alpine. Livewire bundles its own — remove the other.

From a Breeze-style `resources/js/app.js`:
```js
import Alpine from 'alpinejs';   // remove
window.Alpine = Alpine;          // remove
Alpine.start();                  // remove
```

From a layout:
```html
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

You can also drop separate Alpine plugin tags — Livewire bundles all of them
except `@alpinejs/ui`.

### "Uncaught Alpine: no element provided to x-anchor"

`@alpinejs/ui` is the one plugin Livewire does not bundle. Add it from a CDN if
you use headless Alpine Components.

### Livewire JavaScript 404s

The asset path is `/livewire-{hash}/livewire.js`, unique per installation.

- **Nginx blocking it** — pass the pattern through to Laravel:
  ```nginx
  location ~ ^/livewire-[a-f0-9]+/ {
      try_files $uri $uri/ /index.php?$query_string;
  }
  ```
  Or bundle manually, or publish assets to `public/`.
- **Route cache** — `php artisan route:clear`.
- **Auto-injection disabled** — add `@livewireScripts` before `</body>`.

### Alpine unavailable on pages with no Livewire component

Alpine ships inside Livewire's bundle, so include `@livewireScripts` on those
pages too — or bundle Alpine yourself.

### Morphing puts state on the wrong element

The classic case: a conditional that inserts a sibling in the middle of the tree
(a validation error `<div>` appearing between an input and a button). The morph
algorithm can mistake the new element for a changed old one, destroying and
recreating elements that should have moved.

Livewire mitigates this with a look-ahead pass and by injecting HTML comment
markers around `@if`, `@class`, and `@foreach` (`'inject_morph_markers' => true`).

**The reliable fix is structural:** wrap conditionals and loops in an element that
is always present.

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

Symptoms of a morph bug: lost event listeners, state on the wrong element,
duplicated or reset Livewire components, lost Alpine state.

### Component renders blank

Missing root element (Livewire needs exactly one), or a PHP syntax error in the
class block. Check `storage/logs/laravel.log`.

### Reserved names

- **`upload`** — cannot be a method or property when using `WithFileUploads`.
- **`rules`, `messages`, `validationAttributes`, `validationCustomValues`** —
  reserved by the validation system unless you are deliberately overriding it.

### Other checks

```shell
php artisan view:clear
php artisan route:clear
php artisan cache:clear
php artisan optimize:clear
```

Confirm PHP 8.1+ and Laravel 10+, and that `@livewireStyles` is in `<head>` and
`@livewireScripts` before `</body>`.
