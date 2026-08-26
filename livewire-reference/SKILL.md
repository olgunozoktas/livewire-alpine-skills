---
name: livewire-reference
version: 1.2.0
description: 'Use for all Laravel Livewire work. Covers Livewire v4 components, page routes, wire directives, PHP attributes, forms, validation, uploads, pagination, tables, modals, events, islands, performance, JavaScript, Alpine integration, Volt, Pest tests, upgrades, and debugging. Use it before you create, change, review, test, or optimize a Livewire component. It detects v2, v3, and v4 differences. Livewire v4 defaults differ from v2 and v3. Run bin/stack.sh first to load the paired Alpine skill map. Use Laravel Boost search-docs for facts newer than this snapshot. Keywords: livewire, wire:model, wire:click, wire:submit, wire:navigate, wire:poll, wire:loading, wire:key, wire:island, Livewire\Component, Route::livewire, #[Computed], #[Validate], #[Locked], #[On], #[Url], #[Lazy], #[Async], #[Authorize], $wire, Volt, SFC, form object, hydrate, morph, snapshot, Livewire::test.'
---

# Livewire v4

---

## Before you start: is this copy current?

Run once. It is cached for 24 hours, it fails open, and it prints nothing when
the copy is current.

From this skill's own directory:

```bash
bash bin/check-update.sh 2>/dev/null || true
```

If the output is `SKILL_UPDATE_AVAILABLE <local> <remote>`, tell the person one
line — the two versions and that `CHANGELOG.md` says what changed — then carry
on with their task. Do not stop, and do not upgrade anything without being
asked.

If there is no output, say nothing about versions.

Set `LW_SKILLS_NO_UPDATE_CHECK=1` to switch the check off.


Livewire builds dynamic, reactive interfaces in PHP. You write a class and a
Blade template; Livewire handles the AJAX, the DOM patching, and the state
serialization. It bundles Alpine.js, so Alpine is always available.

**Requirements:** Laravel 10+, PHP 8.1+. Install with `composer require livewire/livewire`.
Auto-discovery does the rest — there is no provider to register.

**Provenance:** written from all 98 files of `docs/` on `livewire/livewire@4.x`,
commit `81f35ea`. Audited clean **2026-08-26**. A few signatures the docs omit
(`#[Authorize]`, `#[Transition]`, `renderIsland()`, `streamIsland()`) were read
from the package source and are labelled where they appear.

**The recipes are executed, not merely written.** Every component in
`references/recipes.md` is rendered and exercised against a real Livewire
install — **14 tests, 54 assertions, all passing on livewire v4.4.2**, a
release newer than the snapshot above.

`verify-recipes.sh` catches what reading cannot — it is how the `reset()`
override and four missing `Auth` imports were found. `refresh.sh` reports
anything newly documented that this skill does not mention. Neither edits the
skill. When Livewire is newer than the date above, run both — or ask Laravel
Boost's `search-docs` (see below).

---

## This skill is the entry point for BOTH halves

Livewire bundles Alpine, so real work touches both. They are separate skills
because Alpine is also used with Rails, Django and Hotwire — but **from a Laravel
project, invoking this one is enough**:

```bash
bash bin/stack.sh          # locates the Alpine skill and prints both file maps
```

**Do this once at the start of any Livewire task.** It resolves the Alpine skill
whatever the layout — installed, public repo, or source tree, symlinks
included — and tells you which half answers which question. Then read from
either skill's `references/` directly; no second invocation needed.

If `stack.sh` reports Alpine as NOT FOUND, that skill is not installed. Fall back
to `references/alpine.md`, which covers Alpine **inside** Livewire (`$wire`,
morph vs Alpine state, entangle, which plugin to prefer) but **not** the Alpine
language itself.

**Rough split:** server state, `wire:` directives and PHP attributes are this
skill. `x-data`, `x-model`, `x-for`, `$refs`, `$store` and the plugins are the
Alpine skill. `$wire` and the morph interplay sit in `references/alpine.md`
here.

---

## Tools — run these, do not guess

This skill ships scripts. They read the real project and the real docs, so you
are never inferring what a static file cannot know.

```bash
bash bin/stack.sh               # load BOTH halves of the stack (run this first)
bash bin/detect.sh              # what does THIS project actually do?
bash bin/scaffold.sh post.create   # create in the project's own conventions
python3 bin/review.py <file>    # v3-isms, security holes, known traps
bash bin/verify-recipes.sh      # run every recipe against a real Livewire app
bash bin/refresh.sh             # re-audit against the current documentation
bash bin/eval.sh --compare      # score code quality objectively
```

| Script | Use it when |
|---|---|
| **`stack.sh`** | **First, on any Livewire task.** Finds the `alpinejs-reference` skill in any layout and prints both file maps, so one invocation covers Livewire *and* Alpine |
| **`detect.sh`** | **First, always.** Prints the Livewire version, the component format already in use, the emoji setting, namespaces, routing style, whether Boost is installed, and whether Alpine is duplicated. Read-only |
| **`scaffold.sh`** | Creating a component. Infers the format from what is on disk and from `config/livewire.php`, and **refuses** a v4-only flag on a v3 project instead of producing broken output |
| **`review.py`** | Before handing back any component. Flags v3-isms, an unauthorized write, an `#[Async]` action mutating state, a `@foreach` with no `wire:key`, a method that overrides `Livewire\Component`. Exit code = error count, so it gates. `--self-test` proves all 41 checks still fire |
| **`verify-recipes.sh`** | After editing `references/recipes.md`. Scaffolds a throwaway app and runs every recipe |
| **`refresh.sh`** | When Livewire is newer than the provenance date below |
| **`eval.sh`** | Scoring a directory of components, or `--compare` for baseline-vs-skill |

> `review.py` is calibrated in both directions: **9 errors** on deliberately
> v3-style code, **0 findings** on the twelve verified recipes. A checker that
> fires on correct code is one people switch off.

---

## Preflight — two checks before you write anything

**1. Which Livewire version?** This skill documents **v4**. On v3 much of it is
wrong; on v2 nearly all of it is.

```bash
php -r '$l=json_decode(file_get_contents("composer.lock"),true);
foreach($l["packages"] as $p) if($p["name"]==="livewire/livewire") echo $p["version"],PHP_EOL;'
```

Quick tells: `app/Http/Livewire/` means **v2**. `app/Livewire/` with
`Route::get('/x', Foo::class)` and no `⚡` means **v3**. `Route::livewire(` or
`⚡` filenames mean **v4**. On anything but v4, read `references/version-guide.md`
first — it maps every difference and lists what does not exist yet.

**2. What are this project's conventions?** See directly below. They outrank
every default in this skill.

---

## Before anything: follow the project's existing conventions

**Inspect the project before applying any default in this skill.** Livewire v4's
defaults are what a *new* project gets — an existing codebase may deliberately
use something else, and matching it matters more than being idiomatic.

```bash
ls app/Livewire/ resources/views/livewire/ resources/views/components/
grep -n "make_command\|component_locations\|component_namespaces" config/livewire.php
```

- **A component format already in use wins.** If the app is class-based
  throughout, write class-based — do not introduce single-file components into
  it because v4 prefers them.
- **`make_command.emoji` may be `false`.** Then filenames carry **no** `⚡`
  prefix, and every path in this skill loses it.
- **`make_command.type`** may be `'class'` or `'mfc'`.
- **`component_locations` and `component_namespaces`** may put components
  somewhere other than `resources/views/components/`.
- **Check the installed version.** This skill is v4. On v3 or v2 much of it is
  wrong — check `composer.json`.

Only fall back to the defaults below when the project has established no
convention of its own.

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

### Working alongside Laravel Boost

Boost ships its own Livewire skill, named `livewire-development`
(`author: laravel`), installed into `.ai/skills/`. **This skill carried that same
name until 2026-08-26.** An identical name reads as a replacement for Boost's
skill, which was never the intent. Boost documents that a project-level skill of
the same name overrides its built-in one, so the old name broke nothing — it
simply said the wrong thing.

They are complementary, not rivals — use both:

```bash
ls .ai/skills/livewire-reference/ 2>/dev/null && echo "Boost skill present"
grep -q 'laravel/boost' composer.json && echo "Boost installed"
```

**If Boost is installed, use its `search-docs` MCP tool for anything this skill
does not cover, or anything you need to confirm against the current release.**
It queries a live, version-aware documentation index — it will be right about a
release newer than this skill's snapshot, and it beats guessing.

| Question | Best source |
|---|---|
| "What changed in the version released last week?" | Boost `search-docs` |
| "Which format does *this* project use?" | Boost — its skill reads your config |
| "Every modifier of `wire:target`" | This skill — `references/directives.md` |
| "Why did my morph put state on the wrong element?" | This skill — `references/troubleshooting.md` |
| "Full `#[Authorize]` argument resolution" | This skill — `references/attributes.md` |
| "A complete searchable, paginated table" | This skill — `references/recipes.md` |

If the two ever contradict each other on a fact, **prefer the live docs** —
via `search-docs`, or livewire.laravel.com — and treat this skill's snapshot
date as the tiebreaker.

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

**For anything more than these five rules, use the `livewire-security` skill.**
It covers the part this list does not: which middleware runs again on the update
endpoint and which does not, how to build detection that finds a leak whatever
produced it, and the traps that make a security check pass while it is broken.
Read it before a component goes on a public route, and during a security review.

```bash
php ../livewire-security/bin/scan.php <path-to-app>          # 4 static checks
php ../livewire-security/bin/verify-facts.php <path-to-app>  # are the framework facts still true?
```

---

## Artisan commands

Moved to `references/reference.md`, under **Artisan commands**. Every
`make:livewire` flag, the format converter, the layout and config publishers,
the form generator and the stub publisher.

## What do you want to do?

| Task | Go to |
|---|---|
| Build a CRUD form, search table, modal, wizard, upload, infinite scroll | **`references/recipes.md`** — complete working components |
| Something is broken | **`references/troubleshooting.md`** — symptom → cause → fix |
| The project is on v3 or v2 | **`references/version-guide.md`** |
| Look up a `wire:` directive or modifier | `references/directives.md` |
| Look up a PHP attribute | `references/attributes.md` |
| Create/organize components, pages, layouts, nesting, slots | `references/components.md` |
| Bind data, write actions, handle events, lifecycle hooks, Echo | `references/properties-actions.md` |
| Forms, validation, uploads, pagination, URL/session state | `references/forms-validation.md` |
| Make something faster, or load later | `references/islands-performance.md` |
| Write JavaScript, `$wire`, interceptors, scoped styles | `references/javascript.md` |
| Use Alpine with Livewire | `references/alpine.md` (language itself: `alpinejs-reference` skill) |
| Write tests | `references/testing.md` |
| Understand hydration, morphing, synthesizers, middleware, CSP | `references/advanced.md` |
| Upgrade v3 → v4 | `references/v3-to-v4.md` |
| Volt | `references/volt.md` |
| Config, redirects, Blade directives, installation | `references/reference.md` |

## Typical use cases

Concrete things this skill is for. Each names the file that answers it.

1. **"Build me a post editor with validation."** → `recipes.md` #1–2. Real-time
   validation on blur, `data-loading` button state, authorization in both
   `mount()` and the action.
2. **"Add search, filters, sorting and pagination to this table."** →
   `recipes.md` #3. The four things that make it correct: a computed property,
   `resetPage()` on filter change, `wire:key` per row, debounced search.
3. **"Why does my list show the wrong rows after sorting?"** →
   `troubleshooting.md`. Almost always a missing or colliding `wire:key`.
4. **"This page is slow to load."** → `islands-performance.md`. Islands, `lazy`,
   `defer`, and bundling, with the rule for choosing between them.
5. **"Make this feel instant."** → `recipes.md` #8. Optimistic UI with
   `wire:text` and `#[Renderless]`.
6. **"Upgrade this app from Livewire 3."** → `v3-to-v4.md`, then the checklist
   at its end.
7. **"Is this component secure?"** → the Security section below, then
   `attributes.md` → `#[Locked]` and `#[Authorize]`.
8. **"Add real-time updates."** → `recipes.md` #10 and
   `properties-actions.md` → Laravel Echo. Watch the leading dot on
   `broadcastAs()` names.
9. **"Write tests for this component."** → `testing.md` and `recipes.md` #12.
   Test authorization, not that a component renders.
10. **"Add a modal / dropdown / drag-and-drop."** → `recipes.md` #4, and
    `alpine.md` for which half belongs to Alpine.

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
| `references/alpine.md` | Alpine **inside Livewire**: `$wire`, entangle, morph vs Alpine state, which plugin to prefer, event crossover, bundling plugins. For the Alpine language itself use the **`alpinejs-reference`** skill |
| `references/testing.md` | Pest setup for view-based components, every `Livewire::test()` method and assertion, browser testing with `Livewire::visit()` |
| `references/advanced.md` | Hydration and snapshots, synthesizers, morphing in depth, component hooks, persistent middleware, downloads, package development, CSP, streaming, bundling |
| `references/directives.md` | Every `wire:` directive in full — every modifier, `wire:target`'s four targeting forms, the client-side reactive trio (`wire:show`/`wire:text`/`wire:bind`) |
| `references/attributes.md` | Every PHP attribute in full — parameters, `#[Authorize]`'s argument resolution, `#[Json]`'s promise semantics, the three ways to run JavaScript |
| `references/reference.md` | Redirects, every Blade directive, the full config file, advanced installation, troubleshooting |
| `references/volt.md` | The Volt functional API in full, and how to migrate class-based Volt to core |
| `references/v3-to-v4.md` | Complete upgrade guide and deprecations |
| `references/version-guide.md` | Detecting the installed version, and every v3 difference — plus what simply does not exist before v4 |
| `references/recipes.md` | Twelve complete components: CRUD, search/filter/sort/paginate, modal, upload, infinite scroll, wizard, optimistic UI, dependent selects, Echo, form objects, tests |
| `references/troubleshooting.md` | Symptom → cause → fix table, the three most common bugs in depth, debugging tools, reading the network tab |

---

## Fast recipes

Moved to `references/recipes.md`, under **Fast idioms** at the top of that
file. Six short patterns: a page component with a route, an expensive query,
search that survives a refresh, the v4 loading state, a deferred region, and
fire-and-forget tracking with `#[Async]`.

They live beside the twelve complete components rather than in this file,
because this file is read on every invocation and they are not needed on
every invocation.

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
