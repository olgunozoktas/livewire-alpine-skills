---
name: livewire-development
description: Expert knowledge of Laravel Livewire v4 (livewire.laravel.com/docs/4.x). Use this skill for ANY Livewire work in a Laravel app — creating or editing components, wire:* directives, PHP attributes, forms, validation, file uploads, pagination, events, Laravel Echo broadcasting, lifecycle hooks, nesting, slots, islands, lazy/deferred loading, loading states, wire:navigate SPA mode, Alpine/$wire integration, JavaScript interceptors, scoped styles, synthesizers, component hooks, CSP, testing with Pest, Volt, or upgrading v3 to v4. Livewire v4 changed its DEFAULTS in ways that contradict v2/v3 training data — single-file components are the default, Route::livewire() replaces Route::get(), wire:model modifiers changed meaning, and only Volt's class-based half moved into core. Read this skill BEFORE writing any Livewire code. Keywords: livewire, wire:model, wire:click, wire:submit, wire:navigate, wire:poll, wire:loading, wire:key, wire:island, wire:sort, wire:intersect, wire:ref, wire:stream, wire:bind, wire:text, wire:current, Livewire\Component, mount(), #[Computed], #[Validate], #[Locked], #[On], #[Url], #[Lazy], #[Async], #[Json], #[Authorize], @island, @persist, @placeholder, @assets, @teleport, $wire, $refresh, $dispatch, data-loading, data-current, Volt, single-file component, SFC, MFC, form object, hydrate, dehydrate, morph, snapshot, synthesizer, Livewire::test.
---

# Livewire v4

Livewire builds dynamic, reactive interfaces in PHP. You write a class and a
Blade template; Livewire handles the AJAX, the DOM patching, and the state
serialization. It bundles Alpine.js, so Alpine is always available.

**Requirements:** Laravel 10+, PHP 8.1+. Install with `composer require livewire/livewire`.
Auto-discovery does the rest — there is no provider to register.

Source of truth: `livewire.laravel.com/docs/4.x` and the `docs/` directory of
`github.com/livewire/livewire` on branch `4.x`. This skill was written from that
branch at commit `81f35ea` (2026-08-24).

---

## STOP — v4 changed defaults your training data gets wrong

Most Livewire knowledge in circulation is v2 or v3. These twelve items are the
ones that produce broken or non-idiomatic code. Check them before writing.

| Topic | v2 / v3 (wrong for v4) | v4 |
|---|---|---|
| Default component format | Class in `app/Livewire/` + view in `resources/views/livewire/` | **Single-file component** at `resources/views/components/…/⚡name.blade.php` |
| Routing to a page | `Route::get('/x', Show::class)` | **`Route::livewire('/x', 'pages::show')`** — required for SFC/MFC |
| Volt | The way to get single-file components | **Only the class-based half moved into core.** Volt is still a separate, optional package for its *functional* API — see below |
| `<script>` in a template | Always needs `@script` … `@endscript` | Bare `<script>` in SFC/MFC. `@script` **only** for class-based components |
| `wire:model.blur` / `.change` | Controlled network timing only | Controls **client-side sync** too. For the old behavior write `wire:model.live.blur` |
| `wire:transition` | Alpine `x-transition` wrapper with `.opacity`, `.scale`, `.duration` modifiers | **View Transitions API.** All modifiers removed |
| Component tags | Unclosed `<livewire:foo>` rendered fine | **Must be closed** — `<livewire:foo />`. Otherwise later content is read as slot content |
| `wire:model` on a container | Caught `input`/`change` from children | Only listens on the element itself. Add **`.deep`** for the old behavior |
| Config layout key | `'layout' => 'components.layouts.app'` | **`'component_layout' => 'layouts::app'`** |
| Endpoint URLs | `/livewire/update`, `/livewire/livewire.js` | **`/livewire-{hash}/…`**, hash derived from `APP_KEY`. Update firewall/CDN rules |
| `$this->stream()` | `stream(to: '#el', content: '…')` | **`stream(content: '…', replace: true, el: '#el')`** — `to:` renamed to `el:` |
| JS actions | `$js('name', cb)` / `$wire.$js('name', cb)` | **`this.$js.name = () => {}`** (old forms still work, deprecated) |
| Scroll preservation across navigate | `wire:scroll` | **`wire:navigate:scroll`** |

Also new in v4 and worth reaching for: **islands**, `wire:sort`, `wire:intersect`,
`wire:ref`, `wire:bind`, `wire:text`, `#[Async]`, `#[Json]`, `#[Authorize]`, the
automatic `data-loading` and `data-current` attributes, the `$errors` magic
property, and **interceptors** (which replace the deprecated `commit` and
`request` hooks).

Full migration detail: `references/v3-to-v4.md`.

### The Volt situation, precisely

Livewire v4 absorbed **Volt's class-based syntax** into core. It did **not**
absorb Volt's *functional* API (`state()`, `computed()`, `$increment = fn () =>`).

| You are using | Do this |
|---|---|
| Class-based Volt (`new class extends Livewire\Volt\Component`) | Migrate to core — swap the import, `Volt::route()` → `Route::livewire()`, `Volt::test()` → `Livewire::test()`, remove the package |
| Volt's functional API | Keep `livewire/volt`. It is still shipped and documented |
| A new project | Use core Livewire v4 SFCs. Livewire's own docs: *"most applications won't need Volt"* |

Reference: `references/volt.md`.

### Name collision with Laravel Boost

Laravel Boost ships **its own skill also called `livewire-development`**, plus a
`volt-development` skill, installed into `.ai/skills/` when a project has
`livewire/livewire` in `composer.json`. Boost documents that a project-level
skill of the same name **overrides** its built-in one.

So in a Boost project both may exist. If Livewire guidance ever looks
contradictory, check which one is loaded — `.ai/skills/livewire-development/`
(Boost, project-level) or this skill (global).

---

## Component anatomy

A single-file component is one Blade file holding an anonymous class followed by
a template.

```php
<?php // resources/views/components/post/⚡create.blade.php

use Livewire\Attributes\Validate;
use Livewire\Component;
use App\Models\Post;

new class extends Component {
    #[Validate('required|max:255')]
    public string $title = '';

    #[Validate('required')]
    public string $content = '';

    public function save()
    {
        $this->validate();

        Post::create($this->only(['title', 'content']));

        return $this->redirect('/posts');
    }
};
?>

<form wire:submit="save">
    <input type="text" wire:model="title">
    @error('title') <span>{{ $message }}</span> @enderror

    <textarea wire:model="content"></textarea>
    @error('content') <span>{{ $message }}</span> @enderror

    <button type="submit">Save</button>
</form>
```

Rules this example encodes — each one breaks something if you skip it:

- **Open with `<?php`, close the PHP block with `};` then `?>`.** The `};` closes
  the anonymous class expression.
- **Exactly one root element in the template.** Two roots, or an HTML comment
  outside the root, throws. (Layout `<x-slot>` tags are the one exception.)
- **No `render()` method** unless you need to pass extra data or use a lifecycle
  hook. Livewire renders the template below the class by convention.
- **Public properties are available bare in Blade** (`{{ $title }}`). Computed
  properties need `$this->` (`{{ $this->posts }}`). Protected properties need
  `$this->` too and are never sent to the browser.

### The ⚡ in the filename

`make:livewire` prefixes view-based component files with a `⚡` character so they
stand out in an editor's file tree. It is part of the real filename — when you
create files by hand or glob for them, include it. The component **name** strips
it: `⚡create.blade.php` in `components/post/` is the component `post.create`.

Turn it off with `'make_command' => ['emoji' => false]` in `config/livewire.php`.

### File path to component name

| Format | Path | Name |
|---|---|---|
| Single-file | `resources/views/components/post/⚡create.blade.php` | `post.create` |
| Multi-file | `resources/views/components/post/⚡create/create.php` | `post.create` |
| Class-based | `app/Livewire/Post/Create.php` | `post.create` |
| Namespaced | `resources/views/pages/post/⚡create.blade.php` | `pages::post.create` |

The name is identical across formats, so converting a component never touches the
templates or routes that reference it.

---

## Mental model

Livewire is **server-authoritative**. The browser holds a serialized *snapshot*
of the component's public properties plus a checksum. On each interaction it
sends a *message* (snapshot + property updates + method calls), the server
rebuilds the PHP object (*hydrate*), runs your code, re-renders the Blade, and
returns new HTML that Livewire *morphs* into the existing DOM.

Four consequences that explain most confusing behavior:

1. **Every public property crosses the wire in both directions.** Treat every one
   as untrusted user input, exactly like `$request->input()`. See Security below.
2. **Only serializable types work.** Primitives, arrays, `Collection`,
   `Model`, `BackedEnum`, `DateTime`, `Carbon`, `Stringable`. Anything else needs
   `Wireable` or a Synthesizer. Query constraints such as `select(...)` are **not**
   preserved across requests — use a `#[Computed]` property for constrained queries.
3. **Morphing needs stable identity.** Any `@foreach`, `@switch`, or nested
   component inside a loop needs `wire:key`. Missing keys cause
   "Component already initialized" and "Snapshot missing" errors.
4. **Every component is independent.** A parent re-render does not re-render its
   children, and props are not reactive unless you mark them `#[Reactive]`.

---

## Choosing the right tool

Reach in this order. Each step costs more than the one before it.

1. **A plain Blade component.** Livewire's own guidance: *"Start with extracting a
   Blade component first, then only do a Livewire component if you need to."*
   If the markup does not need to be live, it does not need Livewire.
2. **An island** (`@island`) — an isolated region *inside* one component that
   re-renders on its own. Use it when you only want performance isolation or
   deferred loading. No props, no events, no second file.
3. **A nested Livewire component** — use it when you need genuine encapsulation:
   reusability, its own lifecycle hooks, or its own isolated state.

Quick test: *"Am I only optimizing rendering?"* → island. *"Does this need its own
`mount()` or needs to be reused elsewhere?"* → nested component.

---

## Security — non-negotiable

Livewire's most common vulnerability is trusting a property or an action
parameter. Both are fully controllable from the browser DevTools.

1. **Authorize every action parameter.** `wire:click="delete({{ $post->id }})"`
   can be called with any id from the console.
   ```php
   public function delete($id)
   {
       $post = Post::findOrFail($id);
       $this->authorize('delete', $post);   // required
       $post->delete();
   }
   ```
2. **Authorize on the server, never by hiding the button.** `@if (auth()->user()->isAdmin())`
   around a button hides the UI, not the endpoint.
3. **Every `public` method is callable from the client**, whether a directive
   references it or not. Mark internal helpers `protected` or `private`.
4. **Lock or model-bind identifiers.** `#[Locked] public $postId;` throws if the
   client changes it. Assigning a whole Eloquent model (`public Post $post;`)
   locks its key automatically — prefer that.
5. **Property values leak class names.** A model property serializes as
   `{"type":"model","class":"App\\Models\\Post","key":1}`. Use
   `Relation::morphMap()` to publish an alias instead.

`#[Locked]` stops *client* tampering only. Server code can still assign a bad
value to a locked property.

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

## Reference files

Load the file that matches the task. Do not guess an API — these are transcribed
from the 4.x docs.

| File | Covers |
|---|---|
| `references/components.md` | Component formats, creating/rendering, props, `mount()`, route model binding, page components, layouts, titles, namespaces, nesting, reactive props, `#[Modelable]`, slots, attribute forwarding |
| `references/properties-actions.md` | Property types and serialization, `wire:model` and every modifier, `reset()`/`pull()`/`fill()`, actions, parameters, magic actions, `#[Async]`, `#[Renderless]`, events, lifecycle hooks |
| `references/forms-validation.md` | Forms, form objects, real-time validation, `#[Validate]` in full, `rules()`, custom messages, file uploads, pagination, URL query state, session properties |
| `references/islands-performance.md` | Islands in full, lazy vs deferred loading, placeholders, bundling, `#[Isolate]`, loading states and `data-loading`, polling, `wire:navigate`, `@persist` |
| `references/javascript.md` | Component scripts, `$wire` full API, JS actions, interceptors (action/message/request), `Livewire` global object, hooks, custom directives, `$this->js()`, scoped styles |
| `references/alpine.md` | Alpine **inside Livewire**: `$wire`, entangle, morph vs Alpine state, which plugin to prefer, event crossover, bundling plugins. For the Alpine language itself use the **`alpinejs-development`** skill |
| `references/testing.md` | Pest setup for view-based components, every `Livewire::test()` method and assertion, browser testing with `Livewire::visit()` |
| `references/advanced.md` | Hydration and snapshots, synthesizers, morphing in depth, component hooks, persistent middleware, downloads, package development, CSP, streaming, bundling |
| `references/directives.md` | Every `wire:` directive in full — every modifier, `wire:target`'s four targeting forms, the client-side reactive trio (`wire:show`/`wire:text`/`wire:bind`) |
| `references/attributes.md` | Every PHP attribute in full — parameters, `#[Authorize]`'s argument resolution, `#[Json]`'s promise semantics, the three ways to run JavaScript |
| `references/reference.md` | Redirects, every Blade directive, the full config file, advanced installation, troubleshooting |
| `references/volt.md` | The Volt functional API in full, and how to migrate class-based Volt to core |
| `references/v3-to-v4.md` | Complete upgrade guide and deprecations |

---

## Fast recipes

**Page component with a route.**
```php
Route::livewire('/posts/{post}', 'pages::post.show');
```
```php
<?php // resources/views/pages/post/⚡show.blade.php
use Livewire\Component;
use App\Models\Post;

new class extends Component {
    public Post $post;   // route model binding, no mount() needed
};
```

**Expensive query.** Never a public property — a `#[Computed]` method.
```php
#[Computed]
public function posts()
{
    return Auth::user()->posts()->latest()->get();
}
```
```blade
@foreach ($this->posts as $post)
    <div wire:key="{{ $post->id }}">{{ $post->title }}</div>
@endforeach
```
Memoized for one request only. `unset($this->posts)` busts it after a write.

**Search that survives a refresh.**
```php
#[Url]
public $search = '';
```
```blade
<input wire:model.live.debounce.250ms="search">
```

**Loading state, the v4 way.** Every element that triggers a request gets
`data-loading` automatically — no `wire:target` needed.
```blade
<button wire:click="save" class="data-loading:opacity-50">
    <span class="in-data-loading:hidden">Save</span>
    <span class="not-in-data-loading:hidden">Saving…</span>
</button>
```

**Defer an expensive region without a child component.**
```blade
@island(lazy: true)
    @placeholder
        <div class="animate-pulse h-32 bg-gray-200 rounded"></div>
    @endplaceholder

    <div>Revenue: {{ $this->revenue }}</div>
@endisland
```

**Fire-and-forget tracking.** `#[Async]` runs in parallel instead of queueing.
```php
#[Async]
public function trackClick() { Analytics::track(/* … */); }
```
Never mutate rendered state in an async action — parallel requests race and lose
updates.

---

## Things that bite

- **Missing `wire:key`** in a loop. The single most common cause of morph bugs.
  Prefix keys when two loops in one component could collide: `post-{{ $id }}`,
  `author-{{ $id }}`.
- **Islands cannot go inside `@foreach` or `@if`**, and cannot read `@php`
  variables or loop variables. Put the loop or conditional *inside* the island and
  read component state through `$this->`.
- **`upload` is a reserved name.** A component with `WithFileUploads` cannot have
  a method or property called `upload`. Name the action `save`.
- **Two copies of Alpine.** Livewire bundles Alpine. Remove any CDN tag or
  `Alpine.start()` in `resources/js/app.js`, or you get
  "Detected multiple instances of Alpine running".
- **`reset()` does not undo `mount()`.** It restores a property to its state
  *before* `mount()` ran.
- **Computed properties do not work on `Livewire\Form` objects.**
- **Conditionals that insert a sibling mid-tree** confuse the morph algorithm.
  Livewire injects markers and looks ahead, but the reliable fix is to wrap the
  conditional in an element that is always present.
- **A blank component** almost always means a missing root element or a PHP syntax
  error in the class block. Check the Laravel log.
