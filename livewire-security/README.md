# livewire-security

An [Agent Skill](https://agentskills.io/what-are-skills) for the security half of
**Laravel Livewire v4**. It covers what a component publishes, what a browser can
change, and how to detect a leak in the response.

The `livewire-reference` skill covers all other Livewire work. This skill is
separate because a reader needs it at a different time. A reader needs it before
a component goes on a public route, and during a security review.

---

## Why it exists

> **A `public` property on a Livewire component is published to the browser. The
> browser can also change it.**

`Drawer\BaseUtils::getPublicPropertiesDefinedOnSubclass()` selects properties by
`isPublic()` only. `HandleComponents::dehydrateProperties()` puts the result into
the `wire:snapshot` attribute in the page source. The property returns on the
next request, and the browser can change the value first.

`public` does not mean this in other PHP code. This difference causes most
Livewire defects.

Two facts are often stated incorrectly. The author verified both by execution:

- **A model on a public property does not publish every attribute.**
  `SupportModels\ModelSynth` publishes `{"class":"App\\Models\\User","key":42}`.
  This is the class name and the primary key. An **array built from a model**
  does publish every value. An unsaved model also publishes every value.
- **A locked property throws
  `Livewire\Features\SupportLockedProperties\CannotUpdateLockedPropertyException`.**
  The namespace is not `Livewire\Exceptions\`. People assume that namespace, and
  the test then never matches.

One more fact is often assumed and is wrong. **Route middleware does not all run
again on the update endpoint.** Livewire runs only the middleware on its
persistent list. The Spatie `permission:` and `role:` middleware are not on that
list. `password.confirm` is not on that list. A component behind a permission
does not check that permission again on a later action.

---

## Layout

```
livewire-security/
├── SKILL.md                            the six rules, the detection design, the traps
├── references/attack-surface.md        computed caching, event listeners, uploads, navigate, #[Url]
├── bin/scan.php                        7 static checks, with a self-test
└── bin/verify-facts.php                checks that the skill's own facts are still true
```

### The most serious item in the reference

**`#[Computed(cache: true)]` is keyed on the component name and the method name
only** (`BaseComputed.php:152`). The key holds no user and no tenant. The first
request writes a value, and every later request reads it, for one hour by
default. A computed property that reads `auth()` therefore serves one person's
data to every person.

`#[Computed(persist: true)]` is different. It is keyed on the component instance
id (`BaseComputed.php:145`), and `Factory.php:27` makes that id random for each
instance.

The fix is an explicit key: `#[Computed(cache: true, key: 'invoices.'.auth()->id())]`.
`bin/scan.php` reports the shape, and `bin/verify-facts.php` fails if a future
Livewire release changes it.

---

## The tool

```bash
php bin/scan.php <path-to-app>      # report only. Exit code 1 for a finding
php bin/scan.php --self-test        # prove that every rule fires
```

The scanner reads source text. It needs no bootstrap, no database and no
autoloader. It therefore runs in CI, in a hook, and in a checkout without
installed dependencies. A reflection tool cannot run in those places.

It reports seven things. A public property with a model type or a collection
type. A public property with a protected field name. A page-property bag that is
not private. A public method with a mutator name and no authorization call. A
`#[Url]` property with an identifier name and no `#[Locked]`. A public property
with no type. A `#[Computed(cache: true)]` with no `key`.

**The self-test found two real defects in the scanner.** On the first run every
rule reported "expected to fire". The test fixtures were single lines, and the
property patterns match the start of a line. On a real application the scanner
then reported three incorrect findings. The `updatedFoo()` lifecycle hooks
matched the `update` mutator prefix. An application guard method,
`$this->ensureAccess()`, was not in the authorization pattern. The scanner now
handles both cases, and the self-test covers both.

The scanner skips `vendor` and `node_modules` at any depth. Livewire's own test
fixtures contain the shapes this scanner looks for, on purpose. Before that fix,
one rule reported 49 findings on a real application, and most came from that
directory.

The exit code is the number of findings. The scanner can therefore gate a build.

---

## The facts check their own age

```bash
php bin/verify-facts.php <path-to-a-laravel-app>
```

This skill states facts about Livewire internals. A fact can stop being true. A
new release can move a class or change a list. The skill then gives confident
wrong advice, and no person notices.

This tool applies the skill's own rule to the skill. It reads the installed
`vendor/livewire/livewire` and fails when a statement no longer holds. It checks
27 statements. Run it after a Livewire upgrade.

The tool was proved by injection. A copy of `vendor` received the Spatie
permission middleware in the persistent list, and the check failed. The same copy
received the locked-property exception in `Livewire\Exceptions\`, and that check
failed as well.

---

## Detection in the response, and not at the source

An allow-list looks correct. An allow-list is not a boundary in Livewire. Four
paths avoid it: the single general update endpoint, layout data that the
application adds after the controller returns, `@include` that inherits the full
variable scope, and view composers, paginators, `makeVisible()` and Query Builder
results.

The skill teaches a canary sweep instead. Write one unique value into every
private column. Request every public route from the real route collection. Assert
that no response contains those values.

The skill lists the five details that decide whether the sweep works.

One rule controls all of this work. **A check that is always silent looks the
same as a broken check.** Add the defect. See the test fail. Remove the defect.

---

## Provenance

This skill comes from `livewire/livewire` v4.4.2. The author read the code in
`vendor/` and ran it. The text names a version when the version is important.

The traps and the calibration notes come from a security audit of a production
Laravel and Livewire application.

---

## License

MIT. This matches the rest of this repository.
