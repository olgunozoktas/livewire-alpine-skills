# Properties, data binding, actions, events, lifecycle

---

## Initializing properties

```php
new class extends Component {
    public $todos = [];
    public $todo = '';

    public function mount()
    {
        $this->todos = ['Buy groceries', 'Walk the dog'];
    }
};
```

Bulk assignment with `fill()`:

```php
public function mount(Post $post)
{
    $this->post = $post;

    $this->fill(
        $post->only('title', 'description'),
    );
}
```

### Resetting and pulling

```php
$this->reset('todo');                  // one property
$this->reset(['title', 'content']);    // several
$this->reset();                        // all

$this->pull('todo');                   // reset AND return the old value
$this->pull(['title', 'content']);     // returns a key-value array
$this->pull();                         // all — same as all() + reset()
```

> `reset()` restores a property to its state **before `mount()` ran**. If you set
> the value in `mount()`, reset it by hand.

Other helpers: `$this->only([...])`, `$this->all()`.

---

## Supported property types

Every public property is serialized to JSON between requests (*dehydrate*) and
rebuilt into PHP on the next one (*hydrate*).

**Primitives:** `Array`, `String`, `Integer`, `Float`, `Boolean`, `Null`.

**Common PHP/Laravel objects:**

| Type | Class |
|---|---|
| BackedEnum | `BackedEnum` |
| Collection | `Illuminate\Support\Collection` |
| Eloquent Collection | `Illuminate\Database\Eloquent\Collection` |
| Model | `Illuminate\Database\Eloquent\Model` |
| DateTime | `DateTime` |
| Carbon | `Carbon\Carbon` |
| Stringable | `Illuminate\Support\Stringable` |

### Two traps with Eloquent properties

**Query constraints are not preserved.** A property holding
`->select(['title', 'content'])->get()` loses the `select` on the next request,
because Livewire re-runs the query from the serialized keys.

**Large collections re-query on every hydrate.** That is a real performance cost.

Both are solved the same way — use a computed property instead:

```php
#[Computed]
public function todos()
{
    return Auth::user()->todos()->select(['title', 'content'])->get();
}
```

### Custom types — `Wireable`

```php
use Livewire\Wireable;

class Customer implements Wireable
{
    public function __construct(protected $name, protected $age) {}

    public function toLivewire()
    {
        return ['name' => $this->name, 'age' => $this->age];
    }

    public static function fromLivewire($value)
    {
        return new static($value['name'], $value['age']);
    }
}
```

For global or package-level type support, write a **Synthesizer** instead
(`/docs/4.x/synthesizers`).

---

## `wire:model`

Two-way binding between an input and a property.

```blade
<input type="text" wire:model="title">
```

**By default no network request is sent while typing.** The value syncs to the
server when an action runs (`wire:click`, `wire:submit`, …). This is deliberate —
it keeps Livewire fast.

### Modifiers

| Modifier | Description |
|---|---|
| `.live` | Send updates to the server as they happen |
| `.blur` | Only sync on blur |
| `.change` | Only sync on the change event |
| `.enter` | Only sync on the Enter key |
| `.lazy` | Update on change and send a request (v3-compatible) |
| `.debounce.Xms` | Debounce updates (use with `.live`) |
| `.throttle.Xms` | Throttle updates (use with `.live`) |
| `.number` | Cast to `int` on the server |
| `.boolean` | Cast to `bool` on the server |
| `.fill` | Take the initial value from the HTML `value` attribute |
| `.deep` | Also listen to events bubbling from child elements |
| `.renderless` | Skip re-rendering after a live model update |
| `.preserve-scroll` | Maintain scroll position during updates |

### The v4 change that breaks v3 code

In v3, `.blur` and `.change` controlled **network timing only** — the client-side
value in `$wire.property` always updated as the user typed.

In v4 they control **client-side sync too**. That unlocks inputs that do not
update state until the user commits, but it changes existing behavior:

| v3 | v4 equivalent |
|---|---|
| `wire:model.blur` | `wire:model.live.blur` |
| `wire:model.change` | `wire:model.live.change` |

`.lazy` is unchanged and needs no migration.

New patterns this enables — no network request, just delayed client state:

```blade
<input wire:model.blur="width">          {{-- update $wire.width on tab-away --}}
<input wire:model.blur.enter="search">   {{-- on Enter or blur --}}
```

Default debounce with `.live` is 150 ms. Override with `.debounce.250ms`.

### Nested properties

Dot and bracket notation both work and can be mixed:

```blade
<input wire:model="address.city">
<input wire:model="items.0.name">
<input wire:model="form.title">
<input wire:model="address['city']">
<input wire:model="items[0].name">
```

> Brackets became property accessors in v4. In v3 they were literal characters.
> Rename any property key containing `[` or `]`.

### Event propagation

`wire:model` only listens for events originating **on the element itself**. A
`wire:model` on a modal wrapper is no longer triggered by an input inside it. Add
`.deep` for the old behavior — sparingly.

### Input types

| Input | Notes |
|---|---|
| Text / textarea | Do not echo the value inside a `<textarea>` — Livewire fills it |
| Single checkbox | Binds a boolean |
| Multiple checkboxes | Bind several to one array property; `value` attrs collect into it |
| Radio | `value` on each input |
| Select | No manual `selected` needed. Placeholder = `<option disabled value="">` |
| Multi-select | `multiple` attribute binds to an array property |
| File | Needs the `WithFileUploads` trait — see `forms-validation.md` |

**Dependent selects need a `wire:key`** on the second select so it resets when the
first changes:

```blade
<select wire:model.live="selectedState">…</select>

<select wire:model.live="selectedCity" wire:key="{{ $selectedState }}">…</select>
```

---

## Computed properties

```php
use Livewire\Attributes\Computed;

#[Computed]
public function posts()
{
    return Auth::user()->posts;
}
```

Access as `$this->posts` — **in Blade too**, never bare `{{ $posts }}`.

**Memoized for one request only.** Not across requests. An expensive query inside
a computed property still runs once per component update.

Bust the memo after a write with `unset()`:

```php
public function createPost()
{
    Auth::user()->posts()->create(...);

    unset($this->posts);   // clears memo, and any persist/cache entry
}
```

### Caching across requests

```php
#[Computed(persist: true)]              // per component instance, 3600s default
#[Computed(persist: true, seconds: 7200)]
#[Computed(cache: true)]                // shared across ALL component instances
#[Computed(cache: true, key: 'homepage-posts')]
```

> **Laravel 13 caching caveat.** New Laravel 13 apps only unserialize explicitly
> allowed classes from cache. If Livewire cannot restore a cached object it
> re-evaluates the property (and logs a warning in debug mode). Prefer caching
> scalars and arrays. To cache an object deliberately, list every class in its
> graph under `cache.serializable_classes` in `config/cache.php`.

### When to prefer a computed property

- **Conditional access** — an expensive query behind `@if` only runs if reached.
- **Inline templates** — `render()` returns a heredoc with nowhere to pass data.
- **No `render()` method** — the common v4 case; computed properties are how the
  view gets data.
- **Constrained Eloquent queries** — see the trap above.

Not supported on `Livewire\Form` objects.

---

## Accessing properties from JavaScript

Livewire exposes `$wire` to Alpine and to component scripts.

```blade
<h2 x-text="$wire.todo.length"></h2>

<button x-on:click="$wire.todo = ''">Clear</button>

<button x-on:click="$wire.set('todo', '')">Clear</button>       {{-- sends a request --}}
<button x-on:click="$wire.set('todo', '', false)">Clear</button> {{-- defers the request --}}
```

---

## Actions

Public methods, callable from the template.

```blade
<form wire:submit="save">
<button wire:click="delete({{ $post->id }})">Delete</button>
```

### Parameters

Parameters are **untrusted user input**. Authorize every one.

Model binding works on action parameters, like route model binding:

```php
public function delete(Post $post)   // receives the model, not the id
{
    $this->authorize('delete', $post);
    $post->delete();
}
```

Dependency injection works too — type-hinted container bindings are resolved
before the passed parameters:

```php
public function delete(PostRepository $posts, $postId) { /* … */ }
```

### Event listeners

`wire:` plus any browser event name: `wire:click`, `wire:submit`, `wire:keydown`,
`wire:keyup`, `wire:mouseenter`, `wire:transitionend`, `wire:trix-change`, …

**Key modifiers:** `.shift` `.enter` `.space` `.ctrl` `.cmd` `.meta` `.alt` `.up`
`.down` `.left` `.right` `.escape` `.tab` `.caps-lock` `.equal` `.period` `.slash`.
Chain them: `wire:keydown.shift.enter="…"`.

**Handler modifiers:** `.prevent` `.stop` `.window` `.outside` `.document` `.once`
`.debounce[.Xms]` `.throttle[.Xms]` `.self` `.camel` `.dot` `.passive` `.capture`
`.renderless` `.preserve-scroll` `.async`.

`$event` gives you the DOM event:

```blade
<input wire:keydown.enter="search($event.target.value)">
```

For high-frequency third-party events, prefer setting state in Alpine over firing
a request per keystroke:

```blade
<trix-editor x-on:trix-change="$wire.content = $event.target.value"></trix-editor>
```

### Automatic form protection

Livewire disables the submit button and marks inputs `readonly` while a
`wire:submit` action is in flight. No double submits.

### Magic actions

| Magic | Use |
|---|---|
| `$refresh` | Re-render without calling a method. Pending `wire:model` values still sync |
| `$set('prop', value)` | Set a property from the template |
| `$toggle('prop')` | Flip a boolean |
| `$dispatch('event', {...})` | Dispatch an event client-side |
| `$dispatchTo('component', 'event', {...})` | Dispatch to a named component |
| `$parent.method()` | Call a parent action directly |
| `$event` | The triggering DOM event |
| `$js.name` | Call a registered JavaScript action |

All are available on `$wire` in Alpine too: `$wire.$refresh()`.

### Confirming

```blade
<button wire:click="delete" wire:confirm="Are you sure?">Delete post</button>
```

`.prompt` requires typed confirmation: `wire:confirm.prompt="Type DELETE|DELETE"`.

### Skipping the render

Three equivalent ways, for actions with no visible effect:

```php
#[Renderless]
public function incrementViewCount() { /* … */ }
```
```php
public function incrementViewCount()
{
    $this->post->incrementViewCount();
    $this->skipRender();          // conditional
}
```
```blade
<button wire:click.renderless="incrementViewCount">
```

### Parallel execution — `#[Async]`

By default actions on one component are **serialized**: an in-flight request
queues the next. `.async` / `#[Async]` bypasses the queue.

```blade
<button wire:click.async="logActivity">Track</button>
```
```php
#[Async]
public function logActivity() { Activity::log(/* … */); }
```

**Use for pure side effects only** — analytics, logging, background jobs, or data
fetched purely for JavaScript.

> **Never mutate rendered state in an async action.** Parallel requests each start
> from the same snapshot, so updates are lost. Five rapid clicks on an async
> `$this->count++` can increment once.

### Preserving scroll

```blade
<button wire:click.preserve-scroll="loadMore">Load More</button>
<select wire:model.live.preserve-scroll="category">…</select>
```

### JavaScript actions

Run entirely client-side, or optimistically update before a server call.

```blade
<button wire:click="$js.bookmark">Bookmark</button>

<script>
    this.$js.bookmark = () => {
        $wire.bookmarked = ! $wire.bookmarked   // instant feedback
        $wire.bookmarkPost()                    // then persist
    }
</script>
```

Call from Alpine: `x-on:click="$wire.$js.bookmark()"`.
Call from PHP after an action finishes: `$this->js('onPostSaved')`.

> Class-based components must wrap `<script>` in `@script` … `@endscript`.

---

## Events

### Dispatching

```php
$this->dispatch('post-created');
$this->dispatch('post-created', title: $post->title);
$this->dispatch('post-created')->to(component: Dashboard::class);
$this->dispatch('post-created')->to(self: true);
```

### Listening

```php
use Livewire\Attributes\On;

#[On('post-created')]
public function updatePostList($title) { /* … */ }
```

Dynamic names interpolate component state:

```php
$this->dispatch("post-updated.{$post->id}");
```
```php
#[On('post-updated.{post.id}')]
public function refreshPost() { /* … */ }
```

### From the template

```blade
<button wire:click="$dispatch('post-deleted')">Delete</button>
<button wire:click="$dispatchTo('posts', 'show-post-modal', { id: {{ $post->id }} })">Edit</button>
```

### From a specific child

```blade
<livewire:edit-post @saved="$refresh" />
<livewire:edit-post @saved="close($event.detail.postId)" />
```

### From JavaScript

Inside a component script:
```js
this.$on('post-created', (event) => { event.detail.refreshPosts })
this.$dispatch('post-created', { refreshPosts: true })
this.$dispatchSelf('post-created')
```

Globally:
```js
document.addEventListener('livewire:init', () => {
    let cleanup = Livewire.on('post-created', (event) => { /* … */ })
    // cleanup() removes the listener
})

Livewire.dispatch('post-created', { postId: 2 })
Livewire.dispatchTo('dashboard', 'post-created', { postId: 2 })
```

> Livewire events are plain browser events, so Alpine can listen
> (`x-on:post-created.window="…"`) and dispatch (`$dispatch('post-created')`).

> Unregister global listeners in an Alpine `destroy()` when using `wire:navigate`,
> or they accumulate on every page visit.

### Dispatching to a specific component instance — `ref:`

Give a component tag a `wire:ref`, then target it by name:

```blade
<livewire:modal wire:ref="modal">…</livewire:modal>
```
```php
$this->dispatch('close')->to(ref: 'modal');
```

This is more precise than `to(component: …)`, which reaches every instance of
that component on the page.

**You may not need events.** To call a parent action from a child, prefer
`wire:click="$parent.method()"`. To isolate a region, prefer an island.

---

## Real-time events with Laravel Echo

Requires Laravel Echo installed and `window.Echo` globally available.

Listen for a broadcast event by prefixing the listener with `echo:`:

```php
use Livewire\Attributes\On;

#[On('echo:orders,OrderShipped')]
public function notifyNewOrder()
{
    $this->showNewOrderNotification = true;
}
```

The format is `echo:<channel>,<EventName>`.

### Dynamic channel names

Interpolate component state with the same `{property.path}` syntax as ordinary
dynamic events:

```php
#[On('echo:orders.{order.id},OrderShipped')]
public function notifyNewOrder($event)
{
    $order = Order::find($event['orderId']);
}
```

Or build listeners at runtime with `getListeners()`:

```php
public function getListeners()
{
    return [
        "echo:orders.{$this->order->id},OrderShipped" => 'notifyShipped',
    ];
}
```

### Private and presence channels

```php
public function getListeners()
{
    return [
        'echo:orders,OrderShipped'          => 'notifyNewOrder',  // public
        'echo-private:orders,OrderShipped'  => 'notifyNewOrder',  // private
        'echo-presence:orders,OrderShipped' => 'notifyNewOrder',  // presence
        'echo-presence:orders,here'         => 'whoIsHere',
        'echo-presence:orders,joining'      => 'someoneJoined',
        'echo-presence:orders,leaving'      => 'someoneLeft',
    ];
}
```

Define the broadcast authorization callbacks in Laravel first.

### `broadcastAs()` needs a leading dot

If the event class overrides `broadcastAs()`, listen for the **custom name
prefixed with a dot** — an Echo convention that stops Laravel prepending the
`App\Events` namespace:

```php
public function broadcastAs(): string
{
    return 'score.submitted';
}
```
```php
#[On('echo:scores,.score.submitted')]          // note the leading dot
public function handleScoreSubmitted($event)
{
    $this->scores[] = $event['score'];
}

#[On('echo:scores.{game.id},.score.submitted')]   // with a dynamic channel
public function handleScoreSubmitted($event) { }
```

Getting this wrong is a silent failure — the listener simply never fires.

---

## Lifecycle hooks

| Hook | When |
|---|---|
| `mount()` | Component is first created. Receives props and route parameters |
| `hydrate()` | Start of every **subsequent** request |
| `boot()` | Start of **every** request, initial and subsequent |
| `updating($property, $value)` | Before a property updates |
| `updated($property, $value)` | After a property updates |
| `rendering($view, $data)` | Before the view renders |
| `rendered($view, $html)` | After the view renders |
| `dehydrate()` | End of every request |
| `exception($e, $stopPropagation)` | An exception was thrown |

All support dependency injection via type-hinted parameters.

`mount()` replaces `__construct()` because components are reconstructed on every
request and you only want initialization once.

`boot()` is the place for protected properties, which do not persist:

```php
#[Locked]
public $postId = 1;

protected Post $post;

public function boot()
{
    $this->post = Post::find($this->postId);
}
```

A computed property is usually better than this pattern.

### Targeted update hooks

```php
public function updatedUsername()
{
    $this->username = strtolower($this->username);
}
```

Arrays get a third `$key` argument, `null` when the whole array is replaced:

```php
public function updatedPreferences($value, $key) { /* $value='dark', $key='theme' */ }
```

> **v4 change:** replacing an entire array from the frontend now fires the hooks
> **once** with the full new value, instead of once per index plus `__rm__`
> removals. Single-index changes still fire granularly.

### Exception hook

```php
public function exception($e, $stopPropagation)
{
    if ($e instanceof NotFoundException) {
        $this->notify('Post is not found');
        $stopPropagation();
    }
}
```

### Hooks in traits

Suffix the hook with the camel-cased trait name so several traits can coexist:

```php
trait HasPostForm
{
    public function mountHasPostForm() { }
    public function bootHasPostForm() { }
    public function updatedHasPostForm() { }
    public function dehydrateHasPostForm() { }
    // hydrate*, updating*, rendering*, rendered* follow the same pattern
}
```

### Hooks in form objects

Form objects support `updating`, `updated`, and their per-property variants
(`updatingTitle`, `updatedTags($value, $key)`, …).
