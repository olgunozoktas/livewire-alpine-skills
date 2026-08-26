---
name: livewire-performance
version: 1.2.2
description: 'Use for Livewire performance work. Covers what one Livewire request actually costs, the snapshot that travels both ways on every request, model properties that re-query through the write connection, computed property caching, render and poll frequency, persistent workers (Octane, FrankenPHP, Swoole, RoadRunner), and how to MEASURE before you change anything. Use it when a component feels slow, when a page makes too many requests, when the payload is large, or before you optimise anything. Keywords: livewire performance, slow component, wire:snapshot size, payload, N+1, wire:model.live debounce, wire:poll, #[Computed] cache persist, #[Renderless], #[Lazy], islands, wire:navigate, useWritePdo, newQueryForRestoration, morph, re-render, bottleneck, profiling, octane, frankenphp, swoole, roadrunner, worker memory leak, flushState.'
---

# Livewire performance

## Before you start: is this copy current?

Run once. It is cached for 24 hours, it fails open, and it prints nothing when
the copy is current.

From this skill's own directory:

```bash
bash bin/check-update.sh 2>/dev/null || true
```

If the output is `SKILL_UPDATE_AVAILABLE <local> <remote>`, tell the person one
line — the two versions and that `CHANGELOG.md` says what changed — then carry
on with their task.

Set `LW_SKILLS_NO_UPDATE_CHECK=1` to switch the check off.

---

## Measure first. Always.

**Do not optimise a Livewire component from a guess.** The costs below are real,
and which one dominates changes with the component. A person who removes a model
property from a component that renders one time a day has spent an hour for
nothing.

`references/measuring.md` gives the recipe: snapshot bytes per component, queries
per request, and render time, with a service provider you can copy. Read it
before you change code.

---

## What one Livewire request costs

A Livewire update request is not a page load. It is smaller in some ways and
larger in others, and the differences are where the cost hides.

### 1 · The snapshot travels BOTH ways, every time

Every public property is serialized into the `wire:snapshot` attribute, sent to
the browser, and sent back on every update request.

A `public array $rows` holding 500 records is therefore in the HTML, in every
request body, and in every response. It is paid on each keystroke if a text
input is bound with `wire:model.live`.

**The fix is the smallest one that works.** Ask whether the value must survive
the round trip at all:

| The value | Where it belongs |
|---|---|
| A list only the view reads | `render()` view data, or a `#[Computed]` |
| An identifier the client must send back | a public property, with `#[Locked]` |
| A value the client types | a public property |
| Anything derived | `#[Computed]` |

`#[Locked]` does not remove a value from the snapshot. It stops the browser
changing it. Only moving the value out of a public property removes the cost.

### 2 · A model property is a database query on every request

`SupportModels\ModelSynth.php:84` restores a model like this:

```php
(new $class)->newQueryForRestoration($key)->useWritePdo()->firstOrFail();
```

Two costs, and the documentation states neither.

**A query for each model property, for each request.** `SupportModels/IsLazy.php:36`
decides when:

```php
if (PHP_VERSION_ID < 80400) {
    return $callback();          // the query runs NOW, on every hydrate
}
$lazyModel = $reflector->newLazyProxy($callback);   // deferred until first access
```

**On PHP 8.4 and later the query is deferred** until something touches the model.
A component that holds `public Post $post` and does not read it in that request
pays nothing. **Below PHP 8.4 the query always runs.** This is a real reason to
upgrade PHP.

**`useWritePdo()` sends the query to the WRITE connection.** An application with
read replicas sends every Livewire model restoration to the primary. That
defeats read scaling for the whole Livewire surface, and nothing in the
documentation mentions it.

### 3 · Every request re-renders, unless you say otherwise

An update request runs the component's `render()` again. That is usually correct
and sometimes waste. Three ways to stop it, in order of how much they change:

- **`#[Renderless]`** on an action, or `$this->skipRender()` inside one, when the
  action changes nothing the view shows.
- **An island** (`@island`), to re-render one region rather than the component.
- **A nested component**, when the region has its own lifecycle.

A parent re-render does **not** re-render its children. `#[Reactive]` on a child
property is what makes it, and that is the cost the attribute buys.

### 4 · Request frequency is a design decision

`wire:model.live` on a text input is one request per keystroke. The modifiers
are the fix, and they are not equivalent:

| Binding | Sends |
|---|---|
| `wire:model` | on submit only |
| `wire:model.blur` | when the field loses focus |
| `wire:model.change` | on the `change` event |
| `wire:model.live` | on every input event |
| `wire:model.live.debounce.500ms` | after 500ms of quiet |

`wire:poll` with no modifier polls **every 2 seconds, for every open tab,
forever**. Give it an interval, and consider `wire:poll.visible`.

### 5 · A cached computed property is the cheapest cache and the most dangerous

`#[Computed]` memoizes for one request. `persist: true` caches per component
instance. `cache: true` caches across the whole application.

**`cache: true` is keyed on the component name and the method name only.** It
holds no user and no tenant, so a computed property that reads `auth()` serves
the first person's data to everybody. Use `key:` to add the identity.

The `livewire-security` skill covers that consequence in full. It is repeated
here because the fastest option is the one a person reaches for while optimising.

### 6 · Every page with a component becomes uncacheable

`SupportDisablingBackButtonCache` runs on each component boot and adds:

```
Cache-Control: no-cache, must-revalidate, no-store, max-age=0, private
```

This is correct for a page behind a login, and it is applied to **every** page
that mounts a component. A marketing page you wanted a CDN to hold will not be
held if it contains one Livewire component. Nothing in the documentation
mentions this.

---

## The catalogue

`references/bottlenecks.md` lists each symptom, the cause, the measurement that
confirms it, and the fix. Read it when you have a measurement and need the
remedy.

`references/measuring.md` is how you get the measurement.

**Running a persistent worker?** Item 11 covers Octane, FrankenPHP, Swoole and
RoadRunner: what Livewire retains between requests and who clears it (Octane
does, by default — you wire nothing), the `#[Computed]` listener leak that was
real and is fixed, why `wire:stream` cannot move to a worker, and the one extra
number to watch. Read it before you move a Livewire app onto one.

---

## The scanner

```bash
php bin/scan-performance.php <path-to-app>   # 6 checks. Exit code is the finding count
php bin/scan-performance.php --self-test     # prove that every rule fires
```

It reads source text. It needs no bootstrap, no database and no autoloader.

It finds SHAPES that cost: a model or collection on a public property, an
unlocked public array, `wire:model.live` on a text input, `wire:poll` with no
interval, a computed property read in a loop, and `#[Reactive]`.

**A finding is a candidate, not a verdict.** The scanner cannot see how often a
component renders. Measure before you act on one.
