# Which Livewire version is this project on?

**This skill documents v4.** On v3 or v2, a large part of it is wrong. Establish
the version before writing anything.

---

## Detect it

```bash
composer show livewire/livewire 2>/dev/null | head -3
grep -n '"livewire/livewire"' composer.json
php artisan --version
```

Or from the lockfile, which is the authoritative answer:

```bash
php -r '$l=json_decode(file_get_contents("composer.lock"),true);
foreach($l["packages"] as $p) if($p["name"]==="livewire/livewire") echo $p["version"],PHP_EOL;'
```

**Corroborating signals**, useful when the lockfile is absent:

| You see | Version |
|---|---|
| `resources/views/components/**/⚡*.blade.php` | v4 |
| `Route::livewire(` in `routes/` | v4 |
| `'component_layout' =>` in `config/livewire.php` | v4 |
| `'layout' => 'components.layouts.app'` in config | v3 |
| `app/Livewire/` + `Route::get('/x', Foo::class)` and no `⚡` | v3 |
| `app/Http/Livewire/` | **v2** |
| `wire:model` behaving live by default | **v2** |

The namespace move from `App\Http\Livewire` to `App\Livewire` is the cleanest
v2-vs-v3+ tell.

---

## If the project is on v3

Most of this skill's *concepts* hold — components, properties, actions,
lifecycle hooks, events, validation, uploads, pagination. The **defaults and
several APIs differ**. Read this table before applying anything.

| Topic | v3 (what to write) | v4 (what this skill says) |
|---|---|---|
| `make:livewire CreatePost` | `app/Livewire/CreatePost.php` **+** `resources/views/livewire/create-post.blade.php` | single file at `resources/views/components/⚡create-post.blade.php` |
| Component format | Class-based only | SFC / MFC / class |
| Page routing | **`Route::get('/x', CreatePost::class)`** | `Route::livewire('/x', 'pages::create-post')` |
| Layout config key | **`'layout' => 'components.layouts.app'`** | `'component_layout' => 'layouts::app'` |
| Placeholder config key | **`'lazy_placeholder'`** | `'component_placeholder'` |
| `<script>` in a view | **always** needs `@script` … `@endscript` | bare `<script>` in SFC/MFC |
| `wire:model.blur` / `.change` | network timing only | also controls client-side sync |
| `wire:model.defer` | **exists** | removed — deferred is the default |
| `wire:transition` | Alpine wrapper, `.opacity` `.scale` `.duration` `.origin` | View Transitions API, no modifiers |
| `wire:model` on a container | catches child events | element only (`.deep` restores) |
| Component tags | unclosed tag renders | must be closed |
| Endpoints | `/livewire/update` | `/livewire-{hash}/update` |
| `$this->stream()` | `stream(to: …, content: …)` | `stream(content: …, name:/el:/ref: …)` |
| JS actions | `$wire.$js('name', fn)` | `$wire.$js.name = fn` |
| JS hooks | `Livewire.hook('commit'\|'request', …)` | `interceptMessage()` / `interceptRequest()` |
| Scroll across navigate | `wire:scroll` | `wire:navigate:scroll` |
| `smart_wire_keys` | default `false` | default `true` |

### Not available in v3 at all

Do not write these into a v3 project — they do not exist:

`@island` / `wire:island` · `wire:sort` · `wire:intersect` · `wire:ref` ·
`wire:bind` · the automatic `data-loading` attribute · the automatic
`data-current` attribute · `#[Async]` / `.async` · `#[Json]` · `#[Authorize]` ·
`defer` and `lazy.bundle` · slots and `{{ $attributes }}` forwarding · the
`$errors` and `$intercept` magics · `.renderless` and `.preserve-scroll`
modifiers · single-file and multi-file component formats · `livewire:convert`

**`lazy` does exist in v3.** So does `#[Lazy]`, `wire:poll`, `wire:navigate`,
`#[Computed]`, `#[Validate]`, `#[Locked]`, `#[On]`, `#[Url]`, `#[Session]`,
`#[Reactive]`, `#[Modelable]`, `#[Renderless]`, `#[Isolate]`, `#[Layout]`,
`#[Title]`, form objects, `wire:stream`, `wire:current`, `wire:dirty`,
`wire:cloak`, `wire:confirm`, `wire:replace`, `wire:show`, `wire:text` and
`wire:offline`.

### Volt on v3

On v3, `livewire/volt` is how you get single-file components at all — both the
functional API **and** the class-based one. Migrating a v3 Volt app to v4 means
only the class-based half moves into core. See `volt.md`.

---

## If the project is on v2

**This skill does not cover v2, and neither does the current documentation.**
Do not apply it. The differences are structural, not cosmetic:

- Components live in **`app/Http/Livewire/`**, not `app/Livewire/`.
- The namespace is `App\Http\Livewire`.
- `wire:model` is **live by default** — v3 inverted this, making deferred the
  default. Applying v3/v4 habits to v2 produces a component that fires a request
  on every keystroke *or* one that never syncs, depending on direction.
- `emit()` / `emitTo()` / `emitSelf()` instead of `dispatch()`.
- `$listeners` array instead of `#[On]`.
- `protected $rules` instead of `#[Validate]`.
- Alpine is **not bundled** — v2 projects include it separately, and that is
  correct there. Do not "fix" it.

If you must work in v2, read `livewire.laravel.com/docs/2.x` and treat this
skill as inapplicable. Upgrading v2 → v3 → v4 is two separate migrations.

---

## Reporting the version you assumed

When the version is ambiguous — no lockfile, conflicting signals — **say which
you assumed and why** before writing code. A component written for the wrong
major version fails in ways that read as unrelated bugs: a missing `⚡` file, a
route that 404s, or a form that silently never syncs.
