# Components, pages, and nesting

Covers the three component formats, rendering, props, page components, layouts,
component organization, nesting, reactive props, slots, and attribute forwarding.

---

## The three formats

The component **name** is identical in all three, so switching format never
touches a Blade tag, a route, or a test.

### Single-file (SFC) — the v4 default

```php
<?php // resources/views/components/post/⚡create.blade.php

use Livewire\Component;
use App\Models\Post;

new class extends Component {
    public $title = '';

    public function save()
    {
        Post::create(['title' => $this->title]);

        $this->redirect('/posts');
    }
};
?>

<div>
    <input wire:model="title" type="text">
    <button wire:click="save">Save Post</button>
</div>
```

Created by `php artisan make:livewire post.create`.

### Multi-file (MFC)

`php artisan make:livewire post.create --mfc` creates a directory:

```
resources/views/components/post/⚡create/
├── create.php          # PHP class
├── create.blade.php    # Blade template
├── create.js           # JavaScript (optional, --js)
├── create.css          # Scoped styles (optional, --css)
├── create.global.css   # Global styles (optional)
└── create.test.php     # Pest test (optional, --test)
```

Choose it for large components, better IDE navigation, or significant JavaScript.

### Class-based (the v3 shape)

`php artisan make:livewire CreatePost --class` creates two files:

```php
<?php // app/Livewire/CreatePost.php

namespace App\Livewire;

use Livewire\Component;

class CreatePost extends Component
{
    public function render()
    {
        return view('livewire.create-post');
    }
}
```

Plus `resources/views/livewire/create-post.blade.php`.

Class-based components are fully supported. They are the right choice when
migrating from v3 or when a team convention requires the separation. **They are
the only format that needs `@script` around `<script>` tags.**

Make it the default with:

```php
// config/livewire.php
'make_command' => [
    'type' => 'class',
    'emoji' => false,
],
```

### Converting

```shell
php artisan livewire:convert post.create        # auto-detect direction
php artisan livewire:convert post.create --mfc  # to multi-file
php artisan livewire:convert post.create --sfc  # to single-file
```

Converting **to** single-file deletes any test file — you are prompted first.

### `make:livewire` options

| Option | Effect |
|---|---|
| `--sfc` | Single-file (default) |
| `--mfc` | Multi-file |
| `--class` | Class-based |
| `--type=sfc\|mfc\|class` | Set type explicitly |
| `--emoji=true\|false` | Override the config emoji setting |
| `--test` | Include a Pest test file |
| `--js` | Include a JavaScript file (MFC only) |
| `--css` | Include CSS files (MFC only) |

---

## Rendering a component

```blade
<livewire:todos />                  {{-- resources/views/components/⚡todos.blade.php --}}
<livewire:post.create />            {{-- subdirectory, dot notation --}}
<livewire:pages::post.create />     {{-- namespaced --}}
```

**Tags must be closed.** `<livewire:foo>` without `/>` or a closing tag makes
Livewire read subsequent markup as slot content, and the component does not
render.

### Dynamic components

```blade
<livewire:dynamic-component :is="$current" :wire:key="$current" />
```

Useful for multi-step forms where the child is not known until runtime.

---

## Passing props

```blade
<livewire:post.create title="Initial Title" />   {{-- static string --}}
<livewire:post.create :title="$initialTitle" />  {{-- PHP expression --}}
<livewire:todo-count :$todos />                  {{-- shorthand, name matches --}}
<livewire:todo-count :todos="$todos" inline />   {{-- bare key = boolean true --}}
```

Receive them in `mount()`:

```php
new class extends Component {
    public $title;

    public function mount($title = null)
    {
        $this->title = $title;
    }
};
```

**Omit `mount()` when the property name matches the prop name** — Livewire assigns
it automatically:

```php
new class extends Component {
    public $title;   // set from the :title prop
};
```

> Props are **not reactive**. A later change to `$initialTitle` in the parent does
> not reach the child. Opt in with `#[Reactive]` — see below.

---

## Page components

### Routing

```php
Route::livewire('/posts/create', 'pages::post.create');
Route::livewire('/dashboard', Dashboard::class);   // class-based also works
```

`Route::livewire()` is **required** for single-file and multi-file components.
`Route::get('/x', Component::class)` still works for class-based components but is
no longer recommended.

Organize page components under the `pages::` namespace:

```shell
php artisan make:livewire pages::post.create
# → resources/views/pages/post/⚡create.blade.php
```

### Route parameters

```php
Route::livewire('/posts/{id}', 'pages::post.show');
```
```php
new class extends Component {
    public $postId;

    public function mount($id)          // name matches {id}
    {
        $this->postId = $id;
    }
};
```

### Route model binding

```php
Route::livewire('/posts/{post}', 'pages::post.show');
```
```php
new class extends Component {
    public Post $post;   // resolved automatically — no mount() needed
};
```

The type-hint is what triggers binding. An explicit `mount(Post $post)` works too.

### Layouts

Default layout is `layouts::app` → `resources/views/layouts/app.blade.php`.
Generate it with `php artisan livewire:layout`:

```blade
<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <title>{{ $title ?? config('app.name') }}</title>

        @vite(['resources/css/app.css', 'resources/js/app.js'])

        @livewireStyles
    </head>
    <body>
        {{ $slot }}

        @livewireScripts
    </body>
</html>
```

Change the default globally:

```php
'component_layout' => 'layouts::dashboard',
```

Per component, with the attribute on the same line as `new`:

```php
new #[Layout('layouts::dashboard')] class extends Component { };
```

Or fluently, when it depends on state:

```php
public function render()
{
    return $this->view()->layout('layouts::dashboard');
}
```

### Page titles

```php
new #[Title('Create post')] class extends Component { };
```

Dynamic titles go through `render()`:

```php
public function render()
{
    return $this->view()->title("Edit {$this->post->title}");
}
```

The layout must render `{{ $title ?? config('app.name') }}`.

### Extra layout slots

Add a named slot to the layout:

```blade
<html lang="{{ str_replace('_', '-', $lang ?? app()->getLocale()) }}">
```

Fill it from the component, **outside** the root element:

```blade
<x-slot:lang>fr</x-slot>

<div>
    ...
</div>
```

This is the one sanctioned exception to the single-root-element rule.

---

## Passing data to the view

Three mechanisms, in increasing order of control.

**Public properties** — available bare in Blade.
```php
public $title = 'My Post';       // {{ $title }}
protected $apiKey = 'secret';    // {{ $this->apiKey }}, never sent to the client
```

**Computed properties** — memoized per request, accessed on `$this`.
```php
#[Computed]
public function posts()
{
    return Post::with('author')->latest()->get();
}
```
```blade
@foreach ($this->posts as $post)
    <article wire:key="{{ $post->id }}">{{ $post->title }}</article>
@endforeach
```

**From `render()`** — like a controller. Runs on every update, so avoid expensive
work here.
```php
public function render()
{
    return $this->view([
        'author' => Auth::user(),
        'currentTime' => now(),
    ]);
}
```

---

## Organizing components

### Namespaces

Two ship by default:

```php
'component_namespaces' => [
    'layouts' => resource_path('views/layouts'),
    'pages'   => resource_path('views/pages'),
],
```

Add your own, then use the prefix everywhere:

```php
'admin' => resource_path('views/admin'),
```
```shell
php artisan make:livewire admin::users-table
```
```blade
<livewire:admin::users-table />
```
```php
Route::livewire('/admin/users', 'admin::users-table');
```

### Extra locations

```php
'component_locations' => [
    resource_path('views/components'),
    resource_path('views/admin/components'),
],
```

The **first** entry is where `make:livewire` writes new files.

### Programmatic registration

For packages or conditional registration, in a provider's `boot()`:

```php
Livewire::addComponent(name: 'custom-button', viewPath: resource_path('views/ui/button.blade.php'));
Livewire::addLocation(viewPath: resource_path('views/admin/components'));
Livewire::addNamespace(namespace: 'ui', viewPath: resource_path('views/ui'));
```

Class-based equivalents use `class` / `classNamespace` instead:

```php
Livewire::addComponent(name: 'todos', class: \App\Livewire\Todos::class);
Livewire::addLocation(classNamespace: 'App\\Admin\\Livewire');
Livewire::addNamespace(
    namespace: 'admin',
    classNamespace: 'App\\Admin\\Livewire',
    classPath: app_path('Admin/Livewire'),
    classViewPath: resource_path('views/admin/livewire'),
);
```

### Custom stubs

```shell
php artisan livewire:stubs
```

Publishes `stubs/livewire-sfc.stub`, `livewire-mfc-{class,view,js,test}.stub`,
`livewire.stub`, `livewire.view.stub`, `livewire.attribute.stub`,
`livewire.form.stub`. Livewire uses them automatically once published.

---

## Nesting

> Before extracting a nested component, ask whether the content needs to be
> *live*. If not, use a Blade component. If you only want isolated re-rendering,
> use an island.

```blade
<div>
    <h1>Dashboard</h1>
    <livewire:todos />
</div>
```

A nested component renders once on the parent's initial render. On subsequent
parent updates it is skipped — it is now an independent component on the page.

### Keys in loops are mandatory

```blade
@foreach ($todos as $todo)
    <livewire:todo-item :$todo :wire:key="$todo->id" />
@endforeach
```

This is stricter than Vue or Alpine, where a missing key only degrades reordering.
In Livewire a missing key breaks tracking outright. A nested component **deep**
inside a loop still needs its own key:

```blade
@foreach ($posts as $post)
    <div wire:key="{{ $post->id }}">
        <livewire:show-post :$post :wire:key="$post->id" />
    </div>
@endforeach
```

Prefix keys when two loops in one component could produce the same id:

```blade
<div wire:key="post-{{ $post->id }}">...</div>
<div wire:key="author-{{ $author->id }}">...</div>
```

`'smart_wire_keys' => true` (the v4 default) generates keys for nested components
that lack them, but **you still add `wire:key` in loops** — it does not remove the
requirement.

### Reactive props

```php
new class extends Component {
    #[Reactive]
    public $todos;

    #[Computed]
    public function count()
    {
        return $this->todos->count();
    }
};
```

Now a change in the parent updates the child. This costs a round trip per update —
add it only where the behavior is needed. If you are reaching for `#[Reactive]`
purely to keep an isolated region in sync, an island is usually the better tool.

### Binding to a child with `wire:model` — `#[Modelable]`

Parent:
```blade
<livewire:todo-input wire:model="todo" />
```

Child:
```php
new class extends Component {
    #[Modelable]
    public $value = '';
};
?>

<div>
    <input type="text" wire:model="value">
</div>
```

Only **one** `#[Modelable]` property per component is supported; the first wins.

### Slots

Parent passes content between the tags:

```blade
<livewire:comment :$comment :wire:key="$comment->id">
    <button wire:click="removeComment({{ $comment->id }})">Remove</button>
</livewire:comment>
```

Child renders it:

```blade
<div>
    <p>{{ $comment->author }}</p>
    <p>{{ $comment->body }}</p>

    {{ $slot }}
</div>
```

**Slots evaluate in the parent's context.** `removeComment()` above runs on the
parent, not the child.

Named slots:

```blade
<livewire:comment :$comment :wire:key="$comment->id">
    <livewire:slot name="actions">
        <button wire:click="removeComment({{ $comment->id }})">Remove</button>
    </livewire:slot>

    <span>Posted on {{ $comment->created_at }}</span>
</livewire:comment>
```
```blade
<div>
    @if ($slots->has('actions'))
        <div class="actions">{{ $slots['actions'] }}</div>
    @endif

    {{ $slot }}
</div>
```

### Attribute forwarding

```blade
<livewire:comment :$comment class="border-b" />
```
```blade
<div {{ $attributes->class('bg-white rounded-md') }}>
    ...
</div>
```

Attributes matching a public property name are consumed as props and excluded from
`$attributes`. Everything else — `class`, `id`, `data-*` — comes through.

### Child-to-parent communication

Three options, cheapest first.

**1. `$parent` magic — direct, no event indirection.**
```blade
<button wire:click="$parent.remove({{ $todo->id }})">Remove</button>
```

**2. Client-side dispatch — one network request.**
```blade
<button wire:click="$dispatch('remove-todo', { todoId: {{ $todo->id }} })">Remove</button>
```
```php
#[On('remove-todo')]
public function remove($todoId) { /* … */ }
```

**3. Server-side dispatch — two network requests.** Prefer 1 or 2.
```php
public function remove()
{
    $this->dispatch('remove-todo', todoId: $this->todo->id);
}
```

Listen for a specific child's events straight from the parent template:

```blade
<livewire:edit-post @saved="$refresh" />
<livewire:edit-post @saved="close($event.detail.postId)" />
```

### Islands vs nested components

| Need | Use |
|---|---|
| Only optimizing rendering | Island |
| Defer expensive content | Island (`lazy` / `defer`) |
| Several independent regions, shared state | Island |
| Reusable across the app | Nested component |
| Own `mount()` / `updated()` hooks | Nested component |
| Complex isolated state | Nested component |
| Part of a component library | Nested component |

Start with an island. Refactor to a nested component when you need the
encapsulation.

---

## Troubleshooting

**"Component [post.create] not found"** — check the file path, check dot notation
matches the directory structure, confirm the namespace is registered, then
`php artisan view:clear`.

**Blank render** — missing root element, or a PHP syntax error in the class block.
Check the Laravel log.

**Duplicate class name errors** — two single-file components with the same name in
different directories. Rename one, or namespace one of the directories.
