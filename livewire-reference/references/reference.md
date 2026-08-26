# Full API reference — attributes, directives, config, troubleshooting

---


## Artisan commands

```shell
php artisan make:livewire post.create           # single-file (default)
php artisan make:livewire post.create --mfc     # multi-file directory
php artisan make:livewire post.create --class   # v3-style class + view
php artisan make:livewire pages::post.create    # into the pages:: namespace
php artisan make:livewire post.create --test --js --css

php artisan livewire:convert post.create        # SFC <-> MFC, auto-detected
php artisan livewire:layout                     # resources/views/layouts/app.blade.php
php artisan livewire:config                     # publish config/livewire.php
php artisan livewire:form PostForm              # app/Livewire/Forms/PostForm.php
php artisan livewire:stubs                      # publish generator stubs
php artisan livewire:publish --assets           # publish JS to public/
```

Converting to single-file **deletes** a multi-file component's test file. You are
prompted first.

---

---

## PHP attributes and `wire:` directives

Both moved to dedicated files so each entry could be documented properly rather
than compressed into a modifier table:

- **`attributes.md`** — all 20 PHP attributes, every parameter, and the
  behaviors that are not obvious (`#[Authorize]`'s four-step argument
  resolution, `#[Json]`'s promise rejection shape, the three different ways to
  run JavaScript).
- **`directives.md`** — every `wire:` directive, every modifier, and
  `wire:target`'s four targeting forms.

Quick index:

**Attributes:** `#[Async]` `#[Authorize]` `#[Computed]` `#[Defer]` `#[Isolate]`
`#[Js]` `#[Json]` `#[Layout]` `#[Lazy]` `#[Locked]` `#[Modelable]` `#[On]`
`#[Reactive]` `#[Renderless]` `#[Session]` `#[Title]` `#[Transition]` `#[Url]`
`#[Validate]` — plus `#[Rule]`, deprecated.

**Directives:** `wire:click` `wire:submit` `wire:model` `wire:key` `wire:loading`
`wire:target` `wire:dirty` `wire:offline` `wire:cloak` `wire:confirm`
`wire:show` `wire:text` `wire:bind` `wire:ignore` `wire:replace`
`wire:transition` `wire:init` `wire:poll` `wire:intersect` `wire:navigate`
`wire:navigate:scroll` `wire:current` `wire:island` `wire:sort` `wire:stream`
`wire:ref`

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
