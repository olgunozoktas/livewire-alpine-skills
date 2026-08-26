# Measuring a Livewire request

**Do not optimise from a guess.** This file gives you the three numbers that
decide what to change, and a service provider that produces all three.

Every number here is one you collect from your own application. Nothing in this
file is a benchmark from somewhere else.

---

## The three numbers

| Number | What it tells you | A figure worth looking at |
|---|---|---|
| **Snapshot bytes** | how much state travels both ways on every request | over ~50 KB |
| **Queries per update request** | whether the component re-queries or N+1s | more than the page needs |
| **Render milliseconds** | whether the Blade render is the cost | over ~100 ms |

Collect all three before you change anything. One of them usually dominates, and
which one it is decides the fix.

---

## A service provider that reports all three

Copy this into `app/Providers/`. It logs one line for each Livewire update
request. Register it, exercise the slow component, then read the log.

```php
<?php

namespace App\Providers;

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\ServiceProvider;
use Livewire\Livewire;

class LivewireProfilingServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        // LOCAL ONLY. This logs a line for every update request, and it counts
        // every query. Neither belongs in production.
        if (! $this->app->environment('local')) {
            return;
        }

        $queries = 0;
        DB::listen(function () use (&$queries): void {
            $queries++;
        });

        $startedAt = microtime(true);

        Livewire::listen('component.dehydrate', function ($component, $response) use (&$queries, $startedAt): void {
            // The snapshot is what travels. Measuring the rendered HTML instead
            // would measure the wrong thing.
            $snapshot = method_exists($response, 'toArray') ? $response->toArray() : [];
            $bytes = strlen((string) json_encode($snapshot));

            Log::debug('livewire.profile', [
                'component' => $component->getName(),
                'snapshot_bytes' => $bytes,
                'queries' => $queries,
                'ms' => round((microtime(true) - $startedAt) * 1000, 1),
            ]);
        });
    }
}
```

**`Livewire::listen()` and the hook names differ between versions.** Confirm the
hook your version exposes before you rely on this — `Livewire\ComponentHook` and
the `on()` helper are the current mechanism, and a version that renamed the event
will simply log nothing. A silent profiler is worse than none, so check that the
first line appears before you draw a conclusion from an empty log.

---

## Reading the snapshot without any code

The snapshot is in the page. You can measure it from the browser console:

```js
[...document.querySelectorAll('[wire\\:snapshot]')]
  .map(el => ({
      name: JSON.parse(el.getAttribute('wire:snapshot')).memo.name,
      bytes: el.getAttribute('wire:snapshot').length,
  }))
  .sort((a, b) => b.bytes - a.bytes)
```

This needs no package and no environment. It answers "which component on this
page is heavy" in one paste, and it is usually the fastest first step.

The network tab answers the other half: open it, interact with the component,
and read the request and response sizes of the update calls. A text input that
sends a request for each keystroke is visible immediately.

---

## Counting queries for one interaction

Laravel Debugbar and Laravel Pulse both work on Livewire requests. Debugbar
shows the query list for an update request. Pulse's slow-query recorder catches
what runs in production.

Without either, `DB::listen` in a local service provider is enough, as above.

**What to look for:**

- **A query for each model property.** `ModelSynth` restores each one. On PHP
  8.4 and later the query is deferred until the property is touched; below 8.4
  it always runs. See `SKILL.md` item 2.
- **The same query on every update.** A `#[Computed]` memoizes for one request
  only. A value that does not change between requests wants `persist: true`, and
  a value shared by everybody wants `cache: true` **with an identity in `key:`**.
- **A query multiplied by a row count.** Eager-load in the computed property or
  in `render()`, exactly as you would outside Livewire.

---

## Confirming a re-render is the cost

Add a temporary marker to `render()`:

```php
public function render()
{
    Log::debug('rendered', ['component' => static::class]);

    return view('...');
}
```

If the log fills with renders for actions that change nothing on screen, the fix
is `#[Renderless]` or an island, not a faster query.

---

## After the change, measure again

The same three numbers. Write both figures down in the pull request. A change
that did not move a number is a change to revert, and a number nobody recorded
before the change cannot show that it moved.
