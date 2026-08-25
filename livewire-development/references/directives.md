# Every `wire:` directive

---

## Action directives

### wire:click

Calls a component method when the element is clicked.

```blade
<button type="button" wire:click="download">Download Invoice</button>
<button wire:click="delete({{ $post->id }})">Delete</button>
```

> **On an `<a>` tag you must add `.prevent`**, or the browser follows the `href`:
> ```blade
> <a href="#" wire:click.prevent="show">View Details</a>
> ```

> **Never trust action parameters.** They are HTTP request input. Authorize
> ownership before touching the database.

### wire:submit

Intercepts a form submission.

```blade
<form wire:submit="save">
    <input type="text" wire:model="title">
    <textarea wire:model="content"></textarea>
    <button type="submit">Save</button>
</form>
```

Two behaviors unique to it:

- **`preventDefault()` is automatic.** No `.prevent` needed — there is almost no
  case where you would want the browser's full form post as well.
- **Livewire disables the form while submitting.** Submit buttons are disabled
  and every input is marked `readonly` until the response lands, so a form
  cannot be double-submitted.

### Any other browser event

`wire:` plus any event name: `wire:keydown`, `wire:keyup`, `wire:mouseenter`,
`wire:transitionend`, `wire:trix-change`, …

```blade
<input wire:model="query" wire:keydown.enter="searchPosts">
<input wire:keydown.shift.enter="…">
<div wire:custom-event.window="…"></div>
```

`$event` gives you the DOM event:

```blade
<input type="text" wire:keydown.enter="search($event.target.value)">
```

### Shared modifiers

Livewire's event directives use Alpine's event system, so all of Alpine's
modifiers apply, plus four of Livewire's own.

| Modifier | Effect |
|---|---|
| `.prevent` | `preventDefault()` — automatic on `wire:submit` |
| `.stop` | `stopPropagation()` |
| `.self` | Only if the event originated on this element |
| `.once` | Fire at most once |
| `.debounce` / `.debounce.500ms` | Debounce (default 250 ms) |
| `.throttle` / `.throttle.500ms` | Throttle (default 250 ms) |
| `.window` | Listen on `window` |
| `.document` | Listen on `document` |
| `.outside` | Clicks outside the element |
| `.passive` | Do not block scroll performance |
| `.capture` | Capturing phase |
| `.camel` | `wire:custom-event` → `customEvent` |
| `.dot` | `wire:custom-event` → `custom.event` |
| **`.renderless`** | Skip re-rendering after the action |
| **`.preserve-scroll`** | Keep scroll position through the update |
| **`.async`** | Run in parallel instead of queued |

**Key modifiers** for `keydown`/`keyup`: `.shift` `.enter` `.space` `.ctrl`
`.cmd` `.meta` `.alt` `.up` `.down` `.left` `.right` `.escape` `.tab`
`.caps-lock` `.equal` `.period` `.slash`. Chain to combine.

```blade
<button wire:click.renderless="trackClick">Track Event</button>
<button wire:click.preserve-scroll="loadMore">Load More</button>
<button wire:click.async="logActivity">Track</button>
```

---

## wire:model

Two-way binding. **No network request while typing** by default — the value
syncs when an action runs.

```blade
<input type="text" wire:model="title">
<input type="text" wire:model.live="title">
```

### Modifiers

| Modifier | Effect |
|---|---|
| `.live` | Send updates to the server |
| `.blur` | Sync on blur |
| `.change` | Sync on change |
| `.enter` | Sync on Enter |
| `.lazy` | Update on change and request — v3-compatible |
| `.debounce.Xms` | Debounce (with `.live`; default 150 ms) |
| `.throttle.Xms` | Throttle (with `.live`) |
| `.number` | Cast to `int` server-side |
| `.boolean` | Cast to `bool` server-side |
| `.fill` | Seed from the HTML `value` attribute |
| `.deep` | Also listen to events from child elements |
| `.renderless` | Skip re-render after a live update |
| `.preserve-scroll` | Keep scroll position |

### The v4 semantic change

In v3, `.blur` and `.change` controlled **network timing only** — client state
always updated on every keystroke. In v4 they control **client-side sync too**.

| v3 | v4 equivalent |
|---|---|
| `wire:model.blur` | `wire:model.live.blur` |
| `wire:model.change` | `wire:model.live.change` |

`.lazy` is unchanged.

New patterns this unlocks — delayed client state, no request at all:

```blade
<input wire:model.blur="width">
<input wire:model.blur.enter="search">
```

### Nested properties

Dot and bracket notation, freely mixed:

```blade
<input wire:model="address.city">
<input wire:model="items.0.name">
<input wire:model="form.title">
<input wire:model="address['city']">
<input wire:model="items[0].name">
```

> Brackets became **property accessors** in v4. In v3 they were literal
> characters — rename any property key containing them.

### Event propagation

`wire:model` listens only for events originating **on the element itself**. A
`wire:model` on a modal wrapper is no longer triggered by an input inside it.
`.deep` restores the old behavior — use it sparingly.

### By input type

| Input | Notes |
|---|---|
| Text / textarea | Do **not** echo the value inside `<textarea>` — Livewire fills it |
| Single checkbox | Binds a boolean |
| Multiple checkboxes | Bind several to one array property; `value` attrs collect into it |
| Radio | `value` on each input |
| Select | No manual `selected` needed. Placeholder = `<option disabled value="">` |
| Multi-select | `multiple` binds to an array |
| File | Needs the `WithFileUploads` trait |

**Dependent selects need `wire:key`** on the second select, so it resets when
the first changes:

```blade
<select wire:model.live="selectedState">…</select>
<select wire:model.live="selectedCity" wire:key="{{ $selectedState }}">…</select>
```

---

## State and feedback directives

### wire:loading

Hidden by default; shown while a request is in flight.

```blade
<div wire:loading>Saving post...</div>
<div wire:loading.remove>...</div>          {{-- inverse --}}
```

**Toggling classes and attributes:**

```blade
<button wire:loading.class="opacity-50">Save</button>
<button class="bg-blue-500" wire:loading.class.remove="bg-blue-500">Save</button>
<button type="button" wire:click="remove" wire:loading.attr="disabled">Remove</button>
```

`.attr` matters for non-submit buttons — Livewire's automatic form disabling
does not reach them.

**Targeting — `wire:target`.** Without it, `wire:loading` fires for *every*
request the component makes.

```blade
{{-- one action --}}
<div wire:loading wire:target="remove">Removing post...</div>

{{-- several, comma-separated --}}
<div wire:loading wire:target="save, remove">Updating post...</div>

{{-- a specific action call, by parameter --}}
@foreach ($posts as $post)
    <div wire:key="{{ $post->id }}">
        <button wire:click="remove({{ $post->id }})">Remove</button>
        <div wire:loading wire:target="remove({{ $post->id }})">Removing post...</div>
    </div>
@endforeach

{{-- a property update --}}
<div wire:loading wire:target="username">Checking availability...</div>

{{-- everything except one --}}
<div wire:loading wire:target.except="download">...</div>
```

Parameter targeting is what stops every row's spinner lighting up when one row's
button is pressed.

**Modifiers:**

| Modifier | Effect |
|---|---|
| `.remove` | Show by default, hide during loading |
| `.class="name"` | Add a class during loading |
| `.class.remove="name"` | Remove a class during loading |
| `.attr="attribute"` | Add an attribute during loading |
| `.delay` | Wait 200 ms before showing |
| `.delay.shortest` / `.shorter` / `.short` | 50 / 100 / 150 ms |
| `.delay.long` / `.longer` / `.longest` | 300 / 500 / 1000 ms |
| `.inline-flex` `.inline` `.block` `.table` `.flex` `.grid` | Display value to use |

> **Prefer the automatic `data-loading` attribute** in v4 — it needs no
> targeting, composes with utility classes, and works across component
> boundaries. See `islands-performance.md`.

### wire:dirty

Shows an element when client state has diverged from server state.

```blade
<div wire:dirty>Unsaved changes...</div>
<div wire:dirty.remove>The data is in-sync...</div>
<input wire:model.live.blur="title" wire:dirty.class="border-yellow-500">
```

Scope it with `wire:target`:

```blade
<div wire:dirty wire:target="title">Unsaved title...</div>
```

**The `$dirty` expression** works in directives and in Alpine:

```blade
<div wire:show="$dirty">You have unsaved changes</div>
<div wire:show="$dirty('title')">Title has been modified</div>
<div wire:show="$dirty('user.name')">Name has been modified</div>
<div wire:show="$dirty(['title', 'description'])">…</div>

<button x-on:click="$wire.$dirty('title') && $wire.save()">Save Title</button>
<input wire:model="email" :class="$wire.$dirty('email') && 'border-yellow-500'">
```

### wire:offline

Hidden by default; shown when the device loses its connection.

```blade
<div wire:offline>This device is currently offline.</div>
<div wire:offline.class="bg-red-300">
<div class="bg-green-300" wire:offline.class.remove="bg-green-300">
<button wire:offline.attr="disabled">Save</button>
```

Useful anywhere a user could draft something Livewire cannot save.

### wire:cloak

Hides an element until Livewire finishes initializing, preventing a flash of
uninitialized content.

```blade
<div wire:cloak>Hidden until Livewire loads</div>

{{-- both icons would flash without it --}}
<div wire:show="starred" wire:cloak><!-- yellow star --></div>
<div wire:show="!starred" wire:cloak><!-- gray star --></div>
```

### wire:confirm

A confirmation dialog before any action directive.

```blade
<button wire:click="delete" wire:confirm="Are you sure you want to delete this post?">
    Delete post
</button>
```

`.prompt` requires typed confirmation. The expected input follows a `|` pipe and
is **case-sensitive**:

```blade
<button
    wire:click="delete"
    wire:confirm.prompt="Are you sure?\n\nType DELETE to confirm|DELETE"
>Delete account</button>
```

---

## Client-side reactive directives

These update the DOM without a server round trip — the basis of optimistic UI.

### wire:show

Toggles visibility with CSS `display`, not by removing the element. Unlike
`@if`, no round trip is needed.

```blade
<button x-on:click="$wire.showModal = true">New Post</button>

<div wire:show="showModal">
    <form wire:submit="save">…</form>
</div>
```

Combines with Alpine transitions, since it only touches `display`:

```blade
<div wire:show="showModal" x-transition.duration.500ms>…</div>
```

### wire:text

Sets text content from a property or expression, with no re-render.

```blade
<div>
    <button x-on:click="$wire.likes++" wire:click="like">❤️ Like</button>
    Likes: <span wire:text="likes"></span>
</div>
```

The count updates instantly while `wire:click` persists it in the background.
This is the canonical optimistic-UI pattern.

### wire:bind

Binds any HTML attribute to an expression, reactively, client-side. Equivalent
to Alpine's `x-bind`.

```blade
<input wire:model="message" wire:bind:class="message.length > 240 && 'text-red-500'">

<div wire:bind:style="{ 'color': textColor, 'font-size': fontSize + 'px' }">…</div>
<a wire:bind:href="url">Dynamic link</a>
<button wire:bind:disabled="isArchived">Delete</button>
<div wire:bind:data-count="count">…</div>
```

Any valid attribute name works: `class`, `style`, `href`, `disabled`, `data-*`.

---

## Rendering-control directives

### wire:key

**Mandatory** in any loop or switch. Livewire tracks elements and nested
components by key across requests.

```blade
@foreach ($posts as $post)
    <div wire:key="{{ $post->id }}">…</div>
@endforeach

@foreach ($posts as $post)
    <livewire:show-post :$post :wire:key="$post->id" />
@endforeach
```

A component nested **deep** inside a loop still needs its own key. Prefix keys
when two loops in one component could collide:

```blade
<div wire:key="post-{{ $post->id }}">…</div>
<div wire:key="author-{{ $author->id }}">…</div>
```

Missing keys produce "Component already initialized" and "Snapshot missing".

### wire:ignore

Excludes a subtree from Livewire's morphing. Essential around third-party
libraries that manage their own DOM.

```blade
<div wire:ignore>
    <input id="id-for-date-picker-library">
</div>

<div wire:ignore.self>…</div>
```

`.self` ignores attribute changes on the element only, not its contents.

### wire:replace

Replaces children wholesale instead of morphing them. For web components with
shadow DOM, or when element reuse corrupts internal state.

```blade
<div wire:replace>
    <json-viewer>@json($someProperty)</json-viewer>
</div>

<div x-data="{ open: false }" wire:replace.self>
    {{-- "open" resets to false on every render --}}
</div>
```

`.self` replaces the element itself as well as its children.

### wire:transition

Animates an element in and out.

```blade
<div wire:transition>…</div>
<div wire:transition="fade-name">…</div>
```

> **v4 rewrote this.** It now uses the browser's **View Transitions API** and
> accepts **no modifiers**. The v3 modifiers `.opacity`, `.scale`,
> `.duration.500ms` and `.origin.top` were all removed. With no expression it
> uses `match-element` as the transition name.
>
> Alpine's `x-transition` is unrelated and keeps its full modifier and class API.

---

## Trigger directives

### wire:init

Runs an action as soon as the component renders — useful when you do not want
slow data to hold up the page.

```blade
<div wire:init="loadPosts">…</div>
```

> Lazy loading is usually the better tool. See `islands-performance.md`.

### wire:poll

Polls the server on an interval. **Default 2.5 seconds.**

```blade
<div wire:poll>Subscribers: {{ $this->count }}</div>
<div wire:poll="refreshSubscribers">…</div>
<div wire:poll.15s>…</div>
<div wire:poll.15000ms>…</div>
```

| Modifier | Effect |
|---|---|
| `.Ns` / `.Nms` | Interval |
| `.keep-alive` | Keep polling while the tab is backgrounded |
| `.visible` | Only poll while the element is in the viewport |

**Background throttling is automatic** — a backgrounded tab drops to about **5%**
of the request rate until the user returns. `.keep-alive` opts out.

In v4, polling is **non-blocking**: it neither blocks other requests nor is
blocked by them.

The main cost is scale — a thousand visitors at 2.5 s is a thousand requests
every 2.5 s. Lengthening the interval is the simplest lever.

### wire:intersect

Runs an action when an element enters or leaves the viewport.

```blade
<div wire:intersect="loadMore">…</div>
<div wire:intersect:enter="trackView">…</div>
<div wire:intersect:leave="pauseVideo">…</div>
```

| Modifier | Effect |
|---|---|
| `.once` | Fire only on the first intersection |
| `.half` | Wait until half the element is visible |
| `.full` | Wait until the whole element is visible |
| `.threshold.[0-100]` | Custom visibility percentage |
| `.margin.[value]` | Margin around the viewport (`.margin.200px`, `.margin.10%`) |

---

## Navigation directives

### wire:navigate

Turns a link into an SPA-style visit — Livewire fetches the page, then swaps the
URL, `<title>` and `<body>`.

```blade
<a href="/posts" wire:navigate>Posts</a>
<a href="/posts" wire:navigate.hover>Posts</a>
```

`.hover` prefetches after 60 ms of hovering. It increases server load, since not
every hovered link is clicked. Without it, Livewire already starts fetching on
mouse-*down*.

### wire:navigate:scroll

Preserves scroll position inside a scrollable container across navigations.

```blade
@persist('sidebar')
    <div class="overflow-y-scroll" wire:navigate:scroll>…</div>
@endpersist
```

> This was `wire:scroll` in v3.

### wire:current

Styles the link matching the current page.

```blade
<a href="/posts" wire:navigate wire:current="font-bold text-zinc-800">Posts</a>
<a href="/" wire:current.exact="font-bold">Dashboard</a>
<a href="/posts/" wire:current.strict="font-bold">Posts</a>
```

Matching is **partial** by default, so `/posts` matches on `/posts/1`.
`.exact` requires a full match. `.strict` stops trailing slashes being
normalized away.

> **Livewire adds `data-current` automatically** to every matching
> `wire:navigate` link, so you often need no directive at all —
> `class="data-current:font-bold"` is enough. `wire:current.ignore` opts a link
> out. `wire:current` adds the attribute *and* the classes.

> If it never matches: check the link has an `href`, and that the page has a
> Livewire component or a hardcoded `@livewireScripts`.

---

## Island directives

### wire:island

Scopes an action's update to a named `@island`.

```blade
<button wire:click="$refresh" wire:island="revenue">Refresh revenue</button>
<button wire:click="loadMore" wire:island.append="feed">Load more</button>
<button wire:click="loadMore" wire:island.prepend="feed">Load newer</button>
```

Works alongside `wire:click`, `wire:submit` and the other action directives.
From Alpine, use `$wire.$island('feed', { mode: 'append' }).loadMore()`.

---

## Sorting

### wire:sort

Drag-and-drop reordering, calling a component action.

```blade
<ul wire:sort="handleSort">
    @foreach ($list->tasks as $task)
        <li wire:key="{{ $task->id }}" wire:sort:item="{{ $task->id }}">
            {{ $task->title }}
        </li>
    @endforeach
</ul>
```
```php
public function handleSort($id, $position)
{
    // $position is zero-based. Persisting the order is your job.
}
```

| Attribute | Purpose |
|---|---|
| `wire:sort="method"` | The handler |
| `wire:sort:item="id"` | A sortable item and its identifier |
| `wire:sort:group="name"` | Allow dragging between lists sharing the name |
| `wire:sort:group-id="identifier"` | Passed as a third handler argument |
| `wire:sort:handle` | Restrict dragging to this child |
| `wire:sort:ignore` | Exclude a child from sorting |

No modifiers.

---

## Streaming and references

### wire:stream

Receives content streamed from the server before the request completes — the AI
chat-response case.

```blade
<h1>Count: <span wire:stream="count">{{ $start }}</span></h1>
```
```php
$this->stream(content: $this->start, replace: true, name: 'count');
```

`.replace` swaps the contents instead of appending.

> **Not compatible with Laravel Octane.**

### wire:ref

Names an element or component so it can be targeted.

```blade
<div wire:ref="modal">…</div>
<livewire:modal wire:ref="modal">…</livewire:modal>
```

Three uses:

```php
$this->dispatch('close')->to(ref: 'modal');                 // event to one instance
$this->stream(content: '…', ref: 'output');                 // stream to one element
```
```blade
<button wire:click="$js.scrollToModal">Scroll to modal</button>

<script>
    this.$js.scrollToModal = () => this.$refs.modal.scrollIntoView()
</script>
```

Cleaner than ids or classes, and scoped to the component.
