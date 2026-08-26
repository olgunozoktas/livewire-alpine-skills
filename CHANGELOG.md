# Changelog

The version in `VERSION` covers all three skills. They are released together,
because a reader who copies one usually copies the others.

`bin/check-update.sh` compares a local copy against this repository and reports
one line when a newer release exists. It stays silent in every other case.

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
