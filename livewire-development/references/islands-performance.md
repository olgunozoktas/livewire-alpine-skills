# Islands, lazy loading, loading states, polling, navigate

Everything in this file is about **not blocking the page** and **not re-rendering
more than you need**.

---

## Islands

An island is an isolated region *inside* a component that re-renders on its own.
It gives you the performance isolation of a child component with none of the
props, events, or extra files.

```blade
<?php // resources/views/components/⚡dashboard.blade.php

use Livewire\Attributes\Computed;
use Livewire\Component;
use App\Models\Revenue;

new class extends Component {
    #[Computed]
    public function revenue()
    {
        return Revenue::yearToDate();   // expensive
    }
};
?>

<div>
    @island
        <div>
            Revenue: {{ $this->revenue }}

            <button type="button" wire:click="$refresh">Refresh</button>
        </div>
    @endisland

    <div>
        <!-- Other content — untouched when the island refreshes -->
    </div>
</div>
```

Clicking Refresh re-renders only the island. Because `revenue()` is a computed
property, the query only runs when the island renders — but islands **do** render
on initial page load unless you make them `lazy`, `defer`, or `skip`.

### Parameters

```blade
@island(
    ?string $name = null,
    bool $lazy = false,
    bool $defer = false,
)
```

The guide also documents two more, used the same way:

| Parameter | Effect |
|---|---|
| `name` | A name so `wire:island` can target it |
| `lazy` | Render after page load, when scrolled into view |
| `defer` | Render immediately after page load, regardless of viewport |
| `always` | Re-render whenever the parent component re-renders |
| `skip` | Do not render initially — show the placeholder until triggered |

### Lazy and deferred islands

```blade
@island(lazy: true)     {{-- loads when scrolled into view --}}
@island(defer: true)    {{-- loads immediately after page load --}}
```

With a custom loading state:

```blade
@island(lazy: true)
    @placeholder
        <div class="animate-pulse">
            <div class="h-32 bg-gray-200 rounded"></div>
        </div>
    @endplaceholder

    <div>Revenue: {{ $this->revenue }}</div>
@endisland
```

### Named islands and `wire:island`

```blade
@island(name: 'revenue')
    <div>Revenue: {{ $this->revenue }}</div>
@endisland

<button type="button" wire:click="$refresh" wire:island="revenue">
    Refresh revenue
</button>
```

`wire:island` works alongside `wire:click`, `wire:submit`, and the other action
directives — it scopes their update to that island.

**Islands sharing a name render as a group.** Two `@island(name: 'revenue')`
blocks in different places both update when either is triggered.

### Append and prepend

Perfect for infinite scroll and feeds:

```blade
@island(name: 'feed')
    @foreach ($this->activities as $activity)
        <x-activity-item wire:key="{{ $activity->id }}" :$activity />
    @endforeach
@endisland

<button type="button" wire:click="loadMore" wire:island.append="feed">
    Load more
</button>
```

`wire:island.append` adds to the end, `wire:island.prepend` to the beginning.

### Nested islands

An outer island's re-render **skips** inner islands by default:

```blade
@island(name: 'revenue')
    <div>
        Total: {{ $this->revenue }}

        @island(name: 'breakdown')
            <div>{{ $this->monthlyBreakdown }}</div>
            <button wire:click="$refresh">Refresh breakdown</button>
        @endisland

        <button wire:click="$refresh">Refresh revenue</button>
    </div>
@endisland
```

`always: true` on an inner island makes it follow its parent instead.

### Skip initial render

```blade
@island(skip: true)
    @placeholder
        <button type="button" wire:click="$refresh">Load revenue details</button>
    @endplaceholder

    <div>Revenue: {{ $this->revenue }}</div>
@endisland
```

### Island polling

`wire:poll` inside an island scopes the poll to that island:

```blade
@island(skip: true)
    <div wire:poll.3s>
        Revenue: {{ $this->revenue }}
    </div>
@endisland
```

### Triggering from JavaScript — `$wire.$island()`

`wire:island` only pairs with Livewire action directives. From Alpine or plain JS:

```blade
<button x-on:click="$wire.$island('feed').loadMore()">Load more</button>
<button x-on:click="$wire.$island('feed', { mode: 'append' }).loadMore()">Load more</button>
<button x-on:click="$wire.$island('revenue').$refresh()">Refresh</button>
```

Any `$wire` method chains off `$island()` — `$refresh()`, `$set()`, `$toggle()`,
and your own actions.

### Rendering an island from PHP

Two component methods drive an island from the server. **These come from the
package source (`HandlesIslands`), not the documentation** — the docs cover the
template and JavaScript sides only.

```php
public function renderIsland($name, $content = null, $mode = 'morph', $with = [], $mount = false)
public function streamIsland($name, $content = null, $mode = 'morph', $with = [])
```

`renderIsland()` re-renders a named island as part of the current response.
`streamIsland()` pushes island content down mid-request, the way
`$this->stream()` does for an element — useful for a feed that fills in as
results arrive.

`$mode` accepts the same values as the `wire:island` modifiers: `'morph'`
(default), `'append'`, `'prepend'`.

> Signatures read from source at commit `81f35ea`. Verify against your installed
> version before relying on them — undocumented API can change without a note in
> the upgrade guide.

### Constraints — read before using islands

**Islands cannot read template scope.** No `@php` variables, no loop variables.
Component properties and methods via `$this->` are fine.

```blade
@php $localVariable = 'nope'; @endphp

@island
    {{ $localVariable }}    {{-- errors --}}
    {{ $this->revenue }}    {{-- fine --}}
@endisland
```

**Islands cannot go inside `@foreach`, `@if`, or any control structure** — they
have no access to the surrounding context. Put the loop or conditional *inside*
the island instead:

```blade
{{-- Wrong --}}
@foreach ($items as $item)
    @island
        {{ $item->name }}
    @endisland
@endforeach

{{-- Right --}}
@island
    @foreach ($this->items as $item)
        {{ $item->name }}
    @endforeach
@endisland
```

**State can diverge.** Island requests run in parallel and both the island and the
root component can mutate the same properties. When several are in flight, the
last response wins.

### When islands earn their keep

- Expensive computations that should not block initial load
- Independent regions with their own interactions
- Real-time updates affecting part of the UI
- Performance bottlenecks in a large component

They are not worth it for static content, tightly coupled UI, or components that
already render fast.

---

## Lazy and deferred components

Same two strategies, applied to a whole component.

```blade
<livewire:revenue lazy />    {{-- loads when scrolled into view --}}
<livewire:revenue defer />   {{-- loads right after page load --}}
```

Or make it the component's own default:

```php
new #[Lazy] class extends Component { };
new #[Defer] class extends Component { };
```

`lazy="on-load"` is a legacy synonym for `defer`. Prefer `defer`.

### Placeholders

Without one, Livewire inserts an empty `<div></div>` and the component pops in.

**View-based components** use the directive:

```blade
@placeholder
    <div>
        <svg><!-- spinner --></svg>
    </div>
@endplaceholder

<div>
    Revenue this month: {{ $amount }}
</div>
```

**Class-based components** use the method:

```php
public function placeholder(array $params = [])
{
    return view('livewire.placeholders.skeleton', $params);
}
```

Props passed to the lazy component arrive in `$params`.

> **The placeholder's root element type must match the component's.** A `<div>`
> placeholder needs a `<div>` root in the component.

Set an app-wide default: `'component_placeholder' => 'placeholders::skeleton'`.

### Bundling

Lazy and deferred component loads are **isolated by default** — each one is its
own parallel request, which keeps them fast. Bundle them into a single request
when you would rather reduce connection count:

```blade
<livewire:revenue lazy.bundle />
<livewire:expenses defer.bundle />
```
```php
new #[Lazy(bundle: true)] class extends Component { };
new #[Defer(bundle: true)] class extends Component { };
```

### `#[Isolate]`

By default, several components updating at the same moment are **bundled** into
one request. That reduces server load and is what makes reactive props and
modelable props work across components.

`#[Isolate]` opts a component out, so its requests always go alone:

```php
new #[Isolate] class extends Component {
    public function refreshStats() { /* expensive */ }
};
```

Use it when one slow component would otherwise hold up everything bundled with it.

> `isolate: false` on `#[Lazy]`/`#[Defer]` is deprecated in favor of
> `bundle: true`.

---

## Loading states

**Every element that triggers a network request automatically gets a
`data-loading` attribute.** This is the v4 way — prefer it over `wire:loading`.

```blade
<button wire:click="save" class="data-loading:opacity-50">Save Changes</button>
```

It applies to actions, `wire:submit`, `wire:model.live` updates, and event
dispatches — **including events handled by a different component**. The button
that dispatched still shows loading.

### Tailwind v4 variants

```blade
{{-- style the element itself --}}
<button wire:click="save" class="data-loading:opacity-50">Save</button>

{{-- show only while loading --}}
<span class="not-data-loading:hidden">Saving…</span>

{{-- style children of a loading element --}}
<button wire:click="save">
    <span class="in-data-loading:hidden">Save</span>
    <span class="not-in-data-loading:hidden">Saving…</span>
</button>

{{-- style a parent that contains a loading child --}}
<div class="has-data-loading:opacity-50">
    <button wire:click="save">Save</button>
</div>

{{-- style a sibling --}}
<button wire:click="save" class="peer">Save</button>
<span class="peer-data-loading:opacity-50">Saving…</span>
```

Prefer `not-data-loading:hidden` over `hidden data-loading:block` — it works
whatever the element's display type is.

> `in-data-loading:` matches **any** ancestor with the attribute, however far up.
> Watch for surprises with nested loading states.

> `in-`, `has-`, `peer-`, and `not-` variants need **Tailwind v4+**. On v3 use the
> plain `data-loading:` variant or write CSS.

### Plain CSS

```css
[data-loading] { opacity: 0.5; }
button[data-loading] { background-color: #ccc; }
[data-loading] .loading-text { display: inline; }
```

### `wire:loading` (still supported)

```blade
<button wire:click="save">Save</button>
<span wire:loading wire:target="save">Saving…</span>
```

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

Target with `wire:target="action"`, `wire:target="property"`, or
`wire:target.except="action"`.

`data-loading` wins over `wire:loading` because it needs no targeting, composes
with utility classes, and works across component boundaries.

---

## Polling

```blade
<div wire:poll>...</div>              {{-- default interval --}}
<div wire:poll.5s>...</div>
<div wire:poll.500ms="refreshData">...</div>
```

| Modifier | Effect |
|---|---|
| `.Ns` / `.Nms` | Interval |
| `.keep-alive` | Keep polling while the tab is in the background |
| `.visible` | Only poll while the element is in the viewport |

In v4, polling is **non-blocking** — it neither blocks other requests nor is
blocked by them.

---

## `wire:navigate` — SPA mode

```blade
<nav>
    <a href="/" wire:navigate>Dashboard</a>
    <a href="/posts" wire:navigate>Posts</a>
</nav>
```

On click Livewire fetches the page in the background, shows a progress bar, then
swaps the URL, `<title>`, and `<body>`. Typically about twice as fast as a full
page load.

**Redirect through it:**
```php
return $this->redirect('/posts', navigate: true);
```

**Prefetching.** By default Livewire starts the request on mouse-*down* — often
enough time to load most of a page before the click completes. More aggressive:

```blade
<a href="/posts" wire:navigate.hover>Posts</a>
```

`.hover` prefetches after 60 ms of hover. It increases server load, because not
every hovered link is clicked.

**Persisting elements across visits:**
```blade
@persist('player')
    <audio src="{{ $episode->file }}" controls></audio>
@endpersist
```

Livewire reuses the existing DOM element when it finds a matching `@persist` on
the new page, preserving playback state.

**Preserving scroll inside a scrollable container:**
```blade
@persist('sidebar')
    <div class="overflow-y-scroll" wire:navigate:scroll>
        ...
    </div>
@endpersist
```

> This was `wire:scroll` in v3. Rename it.

**Config:**
```php
'navigate' => [
    'show_progress_bar' => true,
    'progress_bar_color' => '#2299dd',
],
```

### Highlighting the active link

Server-side `request()->is(...)` conditionals **do not work inside `@persist`**,
because the element is reused across pages.

Livewire adds a **`data-current` attribute automatically** to any `wire:navigate`
link matching the current page. This is the simplest approach and needs no
directive:

```blade
<nav>
    <a href="/dashboard" wire:navigate class="data-current:font-bold">Dashboard</a>
    <a href="/posts" wire:navigate class="data-current:font-bold">Posts</a>
</nav>
```
```css
[data-current] { font-weight: bold; color: #18181b; }
```

Opt one link out with `wire:current.ignore`.

The `wire:current` directive is the alternative — it adds the given classes *and*
the `data-current` attribute:

```blade
<a href="/posts" wire:navigate wire:current="font-bold text-zinc-800">Posts</a>
<a href="/" wire:current.exact="font-bold">Dashboard</a>
<a href="/posts/" wire:current.strict="font-bold">Posts</a>
```

Matching is **partial** by default, so `/posts` highlights on `/posts/1`.
`.exact` requires a full path match; `.strict` stops trailing slashes being
normalized away.

> If `wire:current` never matches, check that the link has an `href` and that the
> page has at least one Livewire component (or a hardcoded `@livewireScripts`).

### Navigation JavaScript hooks

Three events fire on **every** navigation, including `Livewire.navigate()`,
navigate-enabled redirects, and browser back/forward:

```js
document.addEventListener('livewire:navigate', (event) => {
    event.preventDefault()      // cancel the navigation

    event.detail.url            // URL object of the destination
    event.detail.history        // true if back/forward triggered it
    event.detail.cached         // true if a cached page will be used
})

document.addEventListener('livewire:navigating', (e) => {
    // new HTML is about to be swapped in

    e.detail.onSwap(() => {
        // after the swap, before scripts load —
        // the place for critical styles like dark mode, to avoid flicker
    })
})

document.addEventListener('livewire:navigated', () => {
    // final step of any navigation; also fires on initial page load
})
```

> **Listeners on `document` survive navigation.** Add the same listener on every
> page and it runs repeatedly; leave one behind and it may throw looking for
> elements that no longer exist. Use `{ once: true }` when a listener should run
> for one page only.

Navigate manually:

```js
Livewire.navigate('/new/url')
```

### Script evaluation rules

The browser never actually leaves the first page, so scripts behave differently.

- **`DOMContentLoaded` fires only on the first visit.** Replace it with
  `livewire:navigated`, which fires on the first load *and* every navigation.
  This is the usual place to initialize third-party libraries.
- **A `<script>` in `<head>` present on both pages runs once** — on the first
  visit only.
- **A `<script>` in `<head>` that is new on the destination page does run.**
- **Analytics needs care.** Google Analytics handles SPA navigation itself;
  Fathom needs `data-spa="auto"` on its script tag.

> Unregister global `Livewire.on(...)` listeners in an Alpine `destroy()` when
> using navigate, or they accumulate on every visit.

### Polling detail

`wire:poll` defaults to **2.5 seconds**. Livewire automatically throttles a
background tab, cutting requests by about **95%** until the user returns.
`.keep-alive` opts out of that; `.visible` polls only while the element is in the
viewport.

---

## Other performance levers

- **`wire:ignore`** — exclude a subtree from morphing. Essential around
  third-party libraries that manage their own DOM. `.self` ignores attribute
  changes on the element only, not children.
- **`wire:replace`** — replace children instead of morphing them. `.self` replaces
  the element itself too.
- **`#[Renderless]` / `.renderless`** — skip the render phase for actions with no
  visual effect.
- **`#[Async]` / `.async`** — run pure side effects in parallel. Never for state
  that renders.
- **`#[Computed]`** — memoize expensive work per request; `persist` or `cache` for
  longer.
- **`wire:model` without `.live`** — the default. Do not add `.live` unless the
  server genuinely needs each keystroke.
