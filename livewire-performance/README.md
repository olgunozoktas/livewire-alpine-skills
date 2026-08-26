# livewire-performance

An [Agent Skill](https://agentskills.io/what-are-skills) for making Livewire
applications fast. It covers what one Livewire request actually costs, how to
measure it, and which fix matches which measurement.

It completes the family. `livewire-reference` is how Livewire works.
`livewire-security` is what a component publishes. This skill is what a component
costs.

---

## Measure first

The skill refuses to give a list of tips. Which cost dominates changes with the
component, and a person who optimises the wrong one has spent an hour for
nothing.

`references/measuring.md` gives three numbers — snapshot bytes, queries per
update request, render milliseconds — and the code that produces them. One of
them is a browser console paste that needs no package and no environment:

```js
[...document.querySelectorAll('[wire\\:snapshot]')]
  .map(el => ({
      name: JSON.parse(el.getAttribute('wire:snapshot')).memo.name,
      bytes: el.getAttribute('wire:snapshot').length,
  }))
  .sort((a, b) => b.bytes - a.bytes)
```

That answers "which component on this page is heavy" immediately, and it is
usually the right first step.

---

## What the skill establishes, from the source

Two costs are undocumented, and both were read in `livewire/livewire` v4.4.2.

**A model property is a database query on every request, through the WRITE
connection.** `ModelSynth.php:84` restores with
`newQueryForRestoration($key)->useWritePdo()->firstOrFail()`. An application with
read replicas therefore sends every Livewire model restoration to the primary.

**On PHP 8.4 the query is deferred; below it, the query always runs.**
`SupportModels/IsLazy.php:36`:

```php
if (PHP_VERSION_ID < 80400) {
    return $callback();                        // query now, every hydrate
}
$lazyModel = $reflector->newLazyProxy($callback);   // deferred until touched
```

That is a measurable performance gain from a PHP upgrade, with no code change.

**Any page mounting a component becomes uncacheable.**
`SupportDisablingBackButtonCache` runs on each component boot and sends
`Cache-Control: no-store, private`. Correct behind a login, surprising on a
marketing page a CDN was meant to hold.

---

## Layout

```
livewire-performance/
├── SKILL.md                          the cost model, and the order to work in
├── references/measuring.md           the three numbers, and how to get them
├── references/bottlenecks.md         ten symptoms, each with cause and fix
└── bin/scan-performance.php          6 static checks, with a self-test
```

---

## The scanner

```bash
php bin/scan-performance.php <path-to-app>   # exit code is the finding count
php bin/scan-performance.php --self-test     # prove that every rule fires
```

It reads source text — no bootstrap, no database, no autoloader — and finds
shapes that cost: a model or collection on a public property, an unlocked public
array, `wire:model.live` on a text input, `wire:poll` with no interval, a
computed property read in a loop, and `#[Reactive]`.

**A finding is a candidate, not a verdict.** The scanner cannot see how often a
component renders. That is why the skill puts measurement first.

Calibrated in both directions: a debounced live binding, a `.blur` binding, a
select, an interval on the poll, and a `#[Locked]` array all stay silent.

---

## Provenance

Read from `livewire/livewire` v4.4.2 in `vendor/`, and checked against the
official documentation. Where the documentation states a behaviour, the skill
says so. Where it does not, the skill says that too.

---

## License

MIT. This matches the rest of this repository.
