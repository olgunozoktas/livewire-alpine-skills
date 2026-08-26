# The bottleneck catalogue

Each entry names the symptom, the cause, the measurement that confirms it, and
the fix. Take the measurement before the fix. `measuring.md` explains how.

---

## 1 · The page is slow to load, and the HTML is enormous

**Cause.** A public property holds a large value. Every public property is
serialized into `wire:snapshot` in the page.

**Confirm.** The browser console snippet in `measuring.md` sorts every component
on the page by snapshot bytes.

**Fix.** Move the value out of a public property.

- A list only the view reads → `render()` view data, or `#[Computed]`.
- A value derived from other state → `#[Computed]`.
- A value the client never sends back → not a public property.

`#[Locked]` does **not** reduce the payload. It stops the browser changing the
value. The bytes still travel.

---

## 2 · Every keystroke makes a request

**Cause.** `wire:model.live` on a text input.

**Confirm.** Open the network tab and type. One update request per keystroke.

**Fix.** Choose the binding that matches the interaction:

- `wire:model` — send on submit.
- `wire:model.blur` — send when the field loses focus.
- `wire:model.live.debounce.500ms` — send after 500 ms of quiet.

A search field usually wants the debounce. A form field usually wants `.blur` or
plain `wire:model`.

---

## 3 · The component queries the database on every request, and nothing changed

**Cause A — a model property.** `ModelSynth` restores each model property with
`newQueryForRestoration($key)->useWritePdo()->firstOrFail()`.

**On PHP 8.4 and later the query is deferred** until something touches the model
(`SupportModels/IsLazy.php:36`, `ReflectionClass::newLazyProxy`). **Below PHP
8.4 it runs on every hydrate**, touched or not.

**Cause B — a computed property.** `#[Computed]` memoizes for ONE request. The
same query therefore runs again on the next request.

**Confirm.** Count queries for one interaction. A query for each model property,
or a repeated identical query across requests.

**Fix.**

- Upgrade to PHP 8.4 if you hold model properties. It removes a query per
  untouched property per request, with no code change.
- Hold an identifier and resolve the record in a `#[Computed]`, so the query
  happens when it is needed rather than on every hydrate.
- `#[Computed(persist: true)]` for a value that does not change between requests
  for this component instance.
- `#[Computed(cache: true, key: '...')]` for a value shared by everybody —
  **with an identity in the key** if the value depends on the viewer. Without
  one, the first person's value is served to everybody. See the
  `livewire-security` skill.

---

## 4 · Every Livewire request goes to the primary database

**Cause.** `ModelSynth.php:84` calls `useWritePdo()` on the restoration query.

An application with read replicas sends every model restoration to the primary
connection. The Livewire surface therefore does not benefit from read scaling.

**Confirm.** Read the query log on the primary and look for
`select * from ... where id = ?` on each Livewire update.

**Fix.** There is no setting for this in Livewire. Hold an identifier rather than
a model property, and resolve it yourself in a `#[Computed]`, where your own
connection choice applies.

**Undocumented.** Nothing in the Livewire documentation mentions the write
connection.

---

## 5 · An action that changes nothing on screen still re-renders

**Cause.** Every update request runs `render()` again.

**Confirm.** Log inside `render()` and exercise the action.

**Fix.**

- `#[Renderless]` on the action, or `$this->skipRender()` inside it.
- An island (`@island`) to re-render one region.
- A nested component when the region has its own lifecycle.

---

## 6 · One slow region makes the whole page slow

**Cause.** The region renders with everything else, on the first paint.

**Fix.** `#[Lazy]`, so the page renders and the region loads after.

**Read the security note first.** A lazy component base64-encodes its mount
parameters into the page. Pass an identifier, never a secret or a whole record.
See the `livewire-security` skill.

---

## 7 · The server is busy with visitors who are not doing anything

**Cause.** `wire:poll` with no interval polls every 2 seconds, for every open
tab, forever. A page left open overnight is 43,200 requests.

**Fix.** Give it an interval — `wire:poll.30s` — and add `.visible` so a tab in
the background stops.

For a genuinely live surface, prefer broadcasting over polling.

---

## 8 · A download uses a lot of memory

**Cause.** `SupportFileDownloads.php:27-31` captures the response body with
`ob_start()` / `ob_get_clean()` and then `base64_encode`s the whole thing into
the JSON response. The file is held in memory and grows by about a third.

The documentation states that Livewire downloads "aren't truly streamed", so the
behaviour is documented; the memory arithmetic is not.

**Fix.** For a large file, do not download it through a Livewire action. Redirect
to a signed route that streams the response.

---

## 9 · A page that should be cached at the edge never is

**Cause.** `SupportDisablingBackButtonCache` runs on each component boot and adds
`Cache-Control: no-cache, must-revalidate, no-store, max-age=0, private`.

Any page that mounts one Livewire component becomes uncacheable by a CDN or a
reverse proxy. This is correct behaviour behind a login and surprising on a
marketing page.

**Confirm.** Read the response headers of the page.

**Fix.** Keep Livewire components off pages you intend to cache publicly, or
override the header at the edge for those routes — knowing that you are turning
off the back-button protection for them.

**Undocumented.**

---

## 10 · The N+1 that is not Livewire's fault

A computed property that loops rows and touches a relation is an N+1, exactly as
it would be outside Livewire. Eager-load in the computed property.

Livewire makes it easier to miss, because the loop is in a property rather than
in a controller, and because the query runs again on every request while the
component stays mounted.

---

## What to do first

In order, because this order finds the biggest cost soonest:

1. Measure the snapshot bytes of every component on the page. One paste.
2. Open the network tab and interact. Count requests per interaction.
3. Count queries for one interaction.
4. Only then change code, and measure the same three numbers again.
