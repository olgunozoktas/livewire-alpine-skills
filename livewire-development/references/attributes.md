# Every PHP attribute

All live in `Livewire\Attributes\`. **Import them** — a missing import is a
common silent failure.

Class-level attributes sit between `new` and `class`:

```php
new #[Layout('layouts::app')] class extends Component { };
new #[Title('Create post')] class extends Component { };
new #[Isolate] class extends Component { };
```

| Attribute | Target | Purpose |
|---|---|---|
| `#[Async]` | method | Run in parallel, bypassing the queue |
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

---

## #[Computed]

Memoized derived property. Accessed as `$this->name` — **including in Blade**.

```php
use Livewire\Attributes\Computed;

#[Computed]
public function posts()
{
    return Auth::user()->posts;
}
```
```blade
@foreach ($this->posts as $post)
    <div wire:key="{{ $post->id }}">{{ $post->title }}</div>
@endforeach
```

**Memoized for one request only** — not across requests. An expensive query still
runs once per component update.

Bust the memo after a write with `unset()`:

```php
unset($this->posts);
```

### Parameters

```php
#[Computed(
    bool $persist = false,   // cache across requests, for this component instance
    int $seconds = 3600,     // cache duration
    bool $cache = false,     // cache across ALL component instances
    ?string $key = null,     // custom cache key
    mixed $tags = null,      // cache tags (needs a tag-capable driver)
)]
```

```php
#[Computed(persist: true)]
#[Computed(persist: true, seconds: 7200)]
#[Computed(cache: true)]
#[Computed(cache: true, key: 'homepage-posts')]
```

`unset()` clears both the memo **and** any persisted/cached value.

> **Laravel 13 caching caveat.** New Laravel 13 apps only unserialize explicitly
> allowed classes from cache. If Livewire cannot restore a cached object it
> re-evaluates the property, logging a warning in debug mode. Prefer caching
> scalars and arrays; to cache an object deliberately, list every class in its
> graph under `cache.serializable_classes`.

> Not supported on `Livewire\Form` objects.

---

## #[Validate]

```php
#[Validate('required|min:3')]
public $title = '';
```

Rules run on **every property update** and on `$this->validate()`.

```php
#[Validate(
    mixed $rule = null,
    ?string $attribute = null,  // custom attribute name for messages
    ?string $as = null,         // friendly name in messages
    mixed $message = null,      // custom message(s)
    bool $onUpdate = true,      // validate on property update
    bool $translate = true,     // run messages through trans()
)]
```

```php
#[Validate('required', as: 'date of birth')]
#[Validate('required', message: 'Please provide a post title')]
#[Validate('required|min:3', onUpdate: false)]
#[Validate('required', message: '…', translate: false)]
```

Separate attributes for a per-rule message:

```php
#[Validate('required', message: 'Please enter a title.')]
#[Validate('min:5', message: 'Your title is too short.')]
public $title = '';
```

Array syntax for a property and its children:

```php
#[Validate([
    'todos' => 'required',
    'todos.*' => ['required', 'min:3', new Uppercase],
])]
public $todos = [];
```

A **bare `#[Validate]`** with no arguments tells Livewire to run that property's
`rules()` entry on update — the way to get real-time validation while using
`Rule` objects.

> PHP attributes cannot hold runtime objects. `Rule::unique(...)` needs a
> `rules()` method. Full detail in `forms-validation.md`.

---

## #[Locked]

Refuses client-side modification. An attempt throws.

```php
use Livewire\Attributes\Locked;

#[Locked]
public $id;
```

No parameters.

**Model properties are locked automatically.** Storing the whole model is
usually better than locking an id:

```php
public Post $post;   // key cannot be tampered with
```

> `#[Locked]` stops **client** tampering only. Server code can still assign a
> bad value.

**Why not a protected property?** Livewire only persists public properties
between requests. Protected ones suit static, hard-coded values; anything set at
runtime must be public.

**Why is this not the default?** Livewire would have to parse every Blade
template to know whether a property is bound by `wire:model` — and could never
detect mutation from Alpine or custom JavaScript.

---

## #[Url]

Syncs a property with the URL query string.

```php
use Livewire\Attributes\Url;

#[Url]
public $search = '';
```

```php
#[Url(
    ?string $as = null,      // alias the parameter (?q= instead of ?search=)
    bool $history = false,   // push to browser history so Back works
    bool $keep = false,      // keep the parameter when navigating away
    mixed $except = null,    // value(s) to omit from the URL
    mixed $nullable = null,  // value to use when the parameter is absent
)]
```

- **`as`** — `#[Url(as: 'q')]` gives `?q=bob`.
- **`except`** — by default Livewire only writes a parameter once the value
  differs from its initialized value. If `mount()` sets a non-empty default,
  `except: ''` makes the empty string the only omitted value.
- **`keep`** — forces the parameter to appear on load even when empty:
  `?search=`.
- **`history`** — Livewire uses `history.replaceState()` by default, so Back
  leaves the page rather than stepping through search values. `history: true`
  switches to `pushState()`.

**Nullable properties.** By default `?search=` becomes `''`. A nullable
type-hint makes it `null`, in both directions:

```php
#[Url]
public ?string $search;
```

**The `queryString()` method** is the alternative for dynamic options:

```php
protected function queryString()
{
    return ['search' => ['as' => 'q']];
}
```

And it has a trait hook:

```php
protected function queryStringWithSorting()
{
    return [
        'sortBy' => ['as' => 'sort'],
        'sortDirection' => ['as' => 'direction'],
    ];
}
```

---

## #[Session]

Persists a property in the session, without touching the URL.

```php
use Livewire\Attributes\Session;

#[Session]
public $search = '';

#[Session(key: 'post_search')]
public $search = '';
```

**Dynamic keys** interpolate other properties:

```php
public Author $author;

#[Session(key: 'search-{author.id}')]
public $search = '';
```

With `$author->id === 4` the key becomes `search-4` — a separate value per
author.

### Session vs Url

| | `#[Session]` | `#[Url]` |
|---|---|---|
| Survives a refresh | yes | yes |
| Survives sharing the URL | no | yes |
| Keeps the URL clean | yes | no |
| Visible to the user | no | yes |
| Shareable | no | yes |

Use `#[Session]` for user preferences, private filter state, and anything that
should not clutter or leak through a URL.

---

## #[On]

Event listener.

```php
use Livewire\Attributes\On;

#[On('post-created')]
public function updatePostList($title) { }
```

Dynamic names interpolate component state:

```php
#[On('post-updated.{post.id}')]
public function refreshPost() { }
```

Laravel Echo listeners use the `echo:` prefix — see `properties-actions.md`.

---

## #[Reactive]

Makes a prop update when the parent changes it. Props are **not** reactive by
default.

```php
use Livewire\Attributes\Reactive;

#[Reactive]
public $todos;
```

No parameters. Costs a round trip per update — add it only where the behavior is
needed. If you are reaching for it purely to keep an isolated region in sync, an
island is the better tool.

---

## #[Modelable]

Lets a parent bind to a child property with `wire:model`.

```blade
<livewire:todo-input wire:model="todo" />
```
```php
use Livewire\Attributes\Modelable;

#[Modelable]
public $value = '';
```

No parameters. **Only one `#[Modelable]` per component** — the first wins.

---

## #[Renderless]

Skips the render phase for an action with no visual effect.

```php
use Livewire\Attributes\Renderless;

#[Renderless]
public function incrementViewCount()
{
    $this->post->incrementViewCount();
}
```

No parameters. Two equivalents: `$this->skipRender()` for a conditional skip,
and the `.renderless` modifier in the template.

---

## #[Async]

Runs an action in parallel, bypassing Livewire's per-component queue.

```php
use Livewire\Attributes\Async;

#[Async]
public function logActivity()
{
    Activity::log('post-viewed', $this->post);
}
```

No parameters. The `.async` modifier does the same from the template.

**Use for pure side effects only** — analytics, logging, background jobs, or data
fetched purely for JavaScript.

> **Never mutate rendered state in an async action.** Parallel requests each
> start from the same snapshot, so updates are lost. Five rapid clicks on an
> async `$this->count++` can increment once.

---

## #[Authorize]

Runs a Gate check before the action body. Throws 403 on failure.

```php
use Livewire\Attributes\Authorize;

#[Authorize('update', 'post')]
public function save()
{
    $this->post->save();
}
```

```php
#[Authorize(
    \UnitEnum|string $ability,
    array|string|null $argument = null,
)]
```

### How the argument resolves

In this order:

1. **No argument** — a simple gate needing no model:
   `#[Authorize('view-dashboard')]`
2. **Class string** — for `create`, where no instance exists yet:
   `#[Authorize('create', Post::class)]`
3. **Method parameter** — resolved from the method's own parameters.
4. **Component property** — a property matching the argument name.

**A method parameter must be type-hinted**, or Livewire cannot resolve the model
and the check fails:

```php
#[Authorize('delete', 'comment')]
public function deleteComment(Comment $comment)
{
    $comment->delete();
}
```

### Extra policy arguments

An array passes the first element as the policy target and the rest as
parameters:

```php
public Post $post;

#[Authorize('create', [Comment::class, 'post'])]
public function createComment()
{
    $this->post->comments()->create(['body' => 'New comment']);
}
```

### Stacking

The attribute is **repeatable** — every check must pass:

```php
#[Authorize('create', Post::class)]
#[Authorize('update', 'post')]
public function save() { }
```

> **It protects the action, not the UI.** Still use `@can` in Blade to hide
> buttons the user may not press.

---

## #[Json]

Marks an action as a JSON endpoint returning data straight to JavaScript.

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
    <input x-model="query"
        x-on:input.debounce="$wire.search(query).then(data => posts = data)">

    <template x-for="post in posts">
        <li x-text="post.title"></li>
    </template>
</div>
```

**It applies two behaviors automatically:**
1. **Skips rendering** — the response is consumed by JavaScript.
2. **Runs asynchronously** — in parallel, without blocking other requests.

### Promise semantics

Resolves with the return value; **rejects on validation failure**:

```js
let data = await $wire.search('query')

try {
    let data = await $wire.save()
} catch (e) {
    e.status   // 422
    e.errors   // { name: ['The name field is required.'] }
}
```

**Rejection shape:**

```js
{ status: 422, body: null, json: null, errors: {...} }    // validation
{ status: 500, body: '<html>...</html>', json: null, errors: null }   // HTTP error
```

Prefer `#[Json]` over a plain action whenever the result is only for JavaScript.

---

## #[Js]

A PHP method that **returns JavaScript**, executed on the client with no server
request.

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
```blade
<button type="button" @click="$wire.resetForm()">Reset</button>
```

`$wire` is in scope inside the expression.

**Use it for:** clearing form fields with no server overhead, triggering
animations, updating client state without re-rendering, reusable JavaScript
called from several places, third-party library integration.

### Three ways to run JavaScript — the distinction

| Mechanism | Defined in | Runs |
|---|---|---|
| `#[Js]` method | PHP, returns JS | Client-side, no request |
| `$js.name` action | JavaScript, in a `<script>` | Client-side, no request |
| `$this->js('…')` | PHP, called inside an action | Client-side, **after** the response |

`$this->js()` is the one to use when the JavaScript must run *after* a server
action completes:

```php
public function save()
{
    Post::create(['title' => $this->title]);

    $this->js("alert('Post saved successfully!')");
}
```

---

## #[Lazy] and #[Defer]

Control when a component loads.

```php
use Livewire\Attributes\Lazy;
use Livewire\Attributes\Defer;

new #[Lazy] class extends Component { };    // loads when scrolled into view
new #[Defer] class extends Component { };   // loads right after page load
```

```php
#[Lazy(bool|null $bundle = null)]
#[Defer(bool|null $bundle = null)]
```

`bundle: true` sends multiple lazy/deferred loads as **one** request instead of
parallel ones.

Override per usage:

```blade
<livewire:revenue lazy />
<livewire:revenue defer />
<livewire:revenue lazy.bundle />
<livewire:revenue :lazy="false" />
```

And per route:

```php
Route::livewire('/dashboard', 'pages::dashboard')->lazy();
Route::livewire('/dashboard', 'pages::dashboard')->defer();
Route::livewire('/dashboard', 'pages::dashboard')->lazy(enabled: false);
```

> `isolate: false` is the legacy spelling of `bundle: true`.

---

## #[Isolate]

Stops a component's requests being bundled with other components'.

```php
new #[Isolate] class extends Component {
    public function refreshStats() { /* expensive */ }
};
```

No parameters. Useful when several components poll or listen for the same event
and one is slow enough to hold up the rest.

Bundling is otherwise the default, and it is what makes reactive props and
modelable props work across components.

---

## #[Layout] and #[Title]

For page components.

```php
#[Layout(string $name, array $params = [])]
#[Title(string $content)]
```

```php
new #[Layout('layouts::dashboard')] class extends Component { };
new #[Title('Create post')] class extends Component { };
```

Dynamic values go through `render()` instead:

```php
public function render()
{
    return $this->view()
        ->layout('layouts::dashboard')
        ->title("Edit {$this->post->title}");
}
```

The layout must render `{{ $title ?? config('app.name') }}`.

---

## #[Transition]

Configures view-transition behavior for an action.

```php
#[Transition(
    ?string $type = null,   // e.g. 'forward', 'backward'
    bool $skip = false,     // disable transitions for this action
)]
```

```php
use Livewire\Attributes\Transition;

#[Transition(type: 'forward')]
public function next() { $this->step++; }

#[Transition(type: 'backward')]
public function previous() { $this->step--; }

#[Transition(skip: true)]
public function reset() { $this->step = 1; }
```

`skip: true` suits "reset" and "cancel" actions that should update instantly.

**The type is targeted in CSS** with `:active-view-transition-type()`:

```blade
<div wire:transition="content">Step {{ $step }}</div>
```
```css
html:active-view-transition-type(forward) {
    &::view-transition-old(content) {
        animation: 300ms ease-out both slide-out-left;
    }
    &::view-transition-new(content) {
        animation: 300ms ease-in both slide-in-right;
    }
}

html:active-view-transition-type(backward) {
    &::view-transition-old(content) {
        animation: 300ms ease-out both slide-out-right;
    }
    &::view-transition-new(content) {
        animation: 300ms ease-in both slide-in-left;
    }
}
```

That is the wizard pattern — the same markup animating in opposite directions
depending on which way the user moved.

For a type computed at runtime, use the `transition()` method instead of the
attribute.

---

## #[Rule] — deprecated

Renamed to `#[Validate]` because it collided with Laravel's `Rule` objects. Both
work; use `#[Validate]`.
