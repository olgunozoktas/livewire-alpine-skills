# Changelog

The version in `VERSION` covers all four skills. They are released together,
because a reader who copies one usually copies the others.

`bin/check-update.sh` compares a local copy against this repository and reports
one line when a newer release exists. It stays silent in every other case.

---

## 1.2.0 — 2026-08-26

### Added — a fourth skill, `livewire-performance`

What one Livewire request costs, how to measure it, and which fix matches which
measurement. It refuses to give a list of tips, because which cost dominates
changes with the component.

- `references/measuring.md` — three numbers and the code that produces them:
  snapshot bytes, queries per update request, render milliseconds. One of them
  is a browser console paste that needs no package and no environment.
- `references/bottlenecks.md` — ten symptoms, each with its cause, the
  measurement that confirms it, and the fix.
- `bin/scan-performance.php` — 6 static checks, calibrated in both directions.
  A debounced live binding, a `.blur` binding, a select, an interval on the
  poll, and a `#[Locked]` array all stay silent.

Two costs in it are undocumented and were read in the source:

- **A model property is a query on every request, through the WRITE
  connection.** `ModelSynth.php:84` uses
  `newQueryForRestoration($key)->useWritePdo()->firstOrFail()`, so an
  application with read replicas sends every restoration to the primary.
- **On PHP 8.4 that query is deferred; below 8.4 it always runs.**
  `SupportModels/IsLazy.php:36` short-circuits `newLazyProxy` on older PHP. This
  is a measurable gain from a PHP upgrade with no code change.

### Added — two transport findings in `livewire-security`

- **The checksum-failure limiter is keyed on the client IP alone.**
  `Checksum.php:11,12,78` — ten bad snapshots answer 429 to every Livewire
  request from that address for ten minutes, and the check runs *before* the
  current request's own checksum. Behind NAT, CGNAT or an untrusted proxy, one
  address is many people. There is no setting: both values are
  `protected static`. **Undocumented.**
- **A snapshot is a bearer object with no owner and no expiry.** The HMAC key is
  the application key and nothing else is mixed in, so a validly signed snapshot
  is accepted from any client until the key rotates. The checksum DOES cover
  `memo.id` and `memo.name`, so a snapshot cannot be presented as a different
  component. Documented as integrity; the consequence is not stated.

### Verified safe, and recorded so nobody re-investigates

The checksum covers `data` and the whole `memo`, uses `hash_equals`, and the
`memo.children` exclusion is bounded by two regexes that permit only
alphanumerics and hyphens. All thirteen `runningUnitTests()` branches are
unreachable in production — with one deployment caveat: shipping with
`APP_ENV=testing` disables the checksum rate limiter and switches uploaded-file
mime, size and hash to client-supplied metadata. `SupportChecksumErrorDebugging`
begins with an unconditional `return;`, so it writes nothing. There is no
framework-introduced open redirect, and no path traversal in downloads.

### Added — the Octane finding, which is the largest one here

**Livewire ships no Octane integration, and the word appears once in 99
documentation files** — in `wire-stream.md`, saying `wire:stream` does not
support it.

About twenty feature classes hold request-scoped and user-scoped data in
`static` properties. One event clears them, `LivewireManager.php:293`, and
`flushState()` is called in exactly two places — **both the testing renderers**,
`SupportTesting/InitialRender.php:37` and `SubsequentRender.php:40`. The
production update path never calls it, and the package registers no Octane
listener.

Under PHP-FPM the process dies and nothing is wrong. Under Octane the worker is
reused, and two consequences follow, each traced to its property:

- `SupportScriptsAndAssets.php:11-17` keeps `$alreadyRunAssetKeys` so each
  `@assets` block is emitted once. On a later request in the same worker the
  block reads as already run and **the asset is omitted from another user's
  page**.
- `SupportRedirects.php:15` keeps `$atLeastOneMountedComponentHasRedirected`,
  and `:20-24` uses it to decide whether to clear the flash bag. Once any
  request redirects, the flag sticks and later requests **stop clearing flash
  data**.

**Verified in source, NOT verified against a running Octane worker.** Octane was
not installed where this was read, and the skill says so where the finding
appears.

### Added — four data-binding findings, one of which is the easiest to get wrong

- **Real-time `#[Validate]` does not gate the write, and the action still
  runs.** The value is set at `HandleComponents.php:451`; the validation
  callback runs after, at `:399-410`; the exception is deliberately swallowed
  (`Wrapped.php:22-34` with `SupportValidation.php:69-76` calling
  `stopPropagation()`); and `callMethods()` then runs at `:220-223`. One request
  carrying both an update and a call persists the invalid value. The docs say
  *"Property is validated every time it's updated"*, which is true and is not
  protection. **Documented; the consequence is not stated.**
- **`#[Reactive]` is enforced at dehydrate**, which is after the action.
  `BaseReactive.php:58-65`. The request aborts, but the side effect already
  happened. **Undocumented.**
- **`#[Locked]` cannot lock one key of an array** — it matches the whole subtree
  (`SupportAttributes.php:42`). A sensitive key beside a bound key in one array
  is writable. The blocking is documented; the granularity is not.
- **Publishing one `payload` limit silently disables the other three.**
  `mergeConfigFrom` is a shallow merge (`LivewireServiceProvider.php:65`), so
  `'payload' => ['max_size' => null]` replaces the array and leaves
  `max_nesting_depth`, `max_calls` and `max_components` undefined — which each
  guard reads as "off". None of the four appears in the documentation at all.

### Verified sound, and recorded so nobody re-investigates

An update can never choose its own synthesizer or class — `HandleSynths.php`
pairs every untrusted value with meta from the authenticated snapshot, with the
trust boundary written out in comments at `:98-100` and `:113-117`. Base-class
internals are not writable (`BaseUtils.php:28-39`), so `$id` is safe. There are
exactly four magic actions and the server treats them as no-ops
(`SupportMagicActions.php:11-27`) — the real boundary is the public-property and
public-method check, never that list. `#[Session]` looks like the computed-cache
bug and is not: the key omits the user in the same way, but the store is the
per-user session (`BaseSession.php:45-52`). Islands cannot be forged — the token
is compiled into the parent view and a client-supplied name is filtered against
the component's server-known list. `#[Async]`, `#[Isolate]` and `#[Renderless]`
carry identical auth. Lifecycle hooks are not directly callable
(`SupportLifecycleHooks.php:98-134`).

### Changed

- `verify-facts.php` holds 27 statements, up from 19.
- Self-tests total 124, up from 111.

---

## 1.1.0 — 2026-08-26

Three findings, each read in the Livewire source and each checked against the
official documentation before it was written down.

### Added to `livewire-security/references/attack-surface.md`

- **A lazy component publishes its mount parameters.** `SupportLazyLoading.php`
  base64-encodes them into the page. Base64 is an encoding, not encryption, so
  any reader of the page source can decode them. The snapshot checksum makes
  them tamper-evident and does not make them confidential. A component without
  `lazy` does not do this. **Undocumented** — `docs/lazy.md` carries no security
  note.
- **A model property rehydrates with global scopes disabled.**
  `ModelSynth.php` restores through `newQueryForRestoration()`, which Laravel
  defines as `newQueryWithoutScopes()->whereKey($ids)`. No tenant scope, no
  soft-delete scope. The checksum bounds it: a browser cannot change the key.
  Two cases remain — authority that changed between requests, and a row
  soft-deleted between requests. **Undocumented** in the Livewire documentation.
- **Spatie's `permission:` middleware cannot be made persistent.** The Livewire
  documentation presents persistent middleware as the protection against changed
  permissions, and separately warns that middleware **arguments** are not
  supported. Spatie carries the permission as an argument, so the documented fix
  cannot express the common case. Both halves are documented; the conclusion is
  not drawn on either page.

### Changed

- The cached-computed item now states the documentation position. The behaviour
  IS documented — "across all components in your application" — while the
  security consequence is not, and `key:` is presented only as a way to clear
  the cache by hand rather than to scope it. The documented example caches
  global data.
- `bin/verify-facts.php` holds 19 statements, up from 16. The three new ones
  cover the lazy encoding, the restoration query, and the checksum that bounds
  both.

---

## 1.0.0 — 2026-08-26

The first numbered release. Everything before this shipped without a version.

### Added

- **`livewire-security`**, a third skill. It covers what a Livewire component
  publishes, what a browser can change, and how to detect a leak in the
  response.
  - `bin/scan.php` — 7 static checks, no bootstrap and no database.
  - `bin/verify-facts.php` — checks 16 statements the skill makes against the
    installed `livewire/livewire`, and fails when one stops being true.
  - `references/attack-surface.md` — cached computed properties, event
    listeners, file uploads, `wire:navigate`, `#[Url]`, parent access.
- **`bin/check-update.sh`** — reports a newer release. It fails open on every
  path, caches for 24 hours, sends one unauthenticated GET, and honours
  `LW_SKILLS_NO_UPDATE_CHECK=1`.
- **`VERSION`** and this file.

### Changed — two renames

- **`livewire-development` is now `livewire-reference`.** Laravel Boost ships
  its own Livewire skill named `livewire-development` with `author: laravel`.
  The names were identical. Boost documents that a project-level skill of the
  same name overrides its built-in one, so the old name broke nothing — it read
  as a replacement for Boost's skill, which was never the intent.
- **`alpinejs-development` is now `alpinejs-reference`**, so the three names
  form one family. Alpine had no collision; this rename is for consistency
  alone, and it keeps the `js` because `alpine` on its own also names a Linux
  distribution.

**To update a copy you installed:**

```bash
rm -rf ~/.claude/skills/livewire-development ~/.claude/skills/alpinejs-development
cp -R livewire-reference alpinejs-reference livewire-security ~/.claude/skills/
```

No stub remains at either old name. A stub at `livewire-development` would
restore the exact collision that the rename removes.

### Changed — a smaller entry point

`livewire-reference/SKILL.md` went from 565 lines to 490. Two sections moved
into references, and **no content was removed**:

- `Fast recipes` → `references/recipes.md`, under **Fast idioms**.
- `Artisan commands` → `references/reference.md`.

Only `SKILL.md` loads when a skill is invoked. The `references/` files are read
on demand through the routing table, and `bin/` is executed rather than read.
The repository line count measures coverage, not context cost.

### Fixed

- A README line count had drifted. Every number is now produced by one method:
  every file except `README.md`.
- `bin/scan.php` walked into `packages/*/vendor`, where Livewire keeps test
  fixtures containing the shapes it looks for. One rule reported 49 findings on
  a real application, and most came from that directory. It now skips `vendor`,
  `node_modules` and `.git` at any depth.
