---
name: livewire-security
description: 'Use for Livewire security work. Covers what a public property publishes, snapshot serialization, #[Locked], the persistent middleware gap, model class and key disclosure, and response-level leak detection. Use it before you ship a component on a public route. Use it before you put a model on a public property. Use it when a security review must prove that its own checks can fail. Keywords: livewire security, wire:snapshot, dehydrate, hydrate, #[Locked], CannotUpdateLockedPropertyException, ModelSynth, morphMap, PersistentMiddleware, livewire update endpoint, public property leak, IDOR, Livewire::test, canary test, PII, primary key disclosure.'
---

# Livewire security

The Livewire threat model is different from the Laravel threat model. One keyword
causes most of the difference.

**Provenance.** This skill comes from `livewire/livewire` v4.4.2. The author read
the code in `vendor/` and ran it. Every statement about the framework is
verified by execution. The text names a version when the version is important.

Use the `livewire-reference` skill for all other Livewire work.

---

## The one rule that causes the others

> **A `public` property on a Livewire component is published to the browser. The
> browser can also change it.**

`Drawer\BaseUtils::getPublicPropertiesDefinedOnSubclass()` selects properties by
`isPublic()` only. `HandleComponents::dehydrateProperties()` puts the result in
the snapshot. Livewire writes that snapshot into a `wire:snapshot` attribute.

A public property is therefore in the page source. Any person who opens the page
can read it. Any crawler can read it. The property also returns on the next
update request, and the browser can change the value first.

`public` does not mean this in other PHP code. This difference causes most
Livewire defects.

---

## The six rules

### 1 · Do not put an Eloquent model or collection on a public property

A model does not publish all of its attributes. `SupportModels\ModelSynth`
publishes this:

```json
{"class": "App\\Models\\User", "key": 42}
```

This is the full class name and the primary key. The class name shows the
internal structure. The primary key shows how many rows the table holds, and the
order of creation.

An **array or plain object built from a model** does publish every value.
`ArraySynth` and `StdClassSynth` do this. An **unsaved** model also publishes
every value.

A `public array $props = []` that holds a record is the most dangerous shape.
Livewire publishes all of it, and the browser can change all of it.

`Relation::enforceMorphMap()` replaces the class name with an alias. It does not
change the key.

### 2 · A public property can hold the viewer's own input, and no other person's data

This rule prevents the previous rule from becoming a habit without a reason.

A checkout form holds the buyer's own email address. Livewire publishes it into
that buyer's snapshot, in that buyer's session, in that buyer's browser. The
buyer typed it. This is disclosure to the owner of the data.

Another person's identity on a public property is different. Livewire publishes
it to every person who opens the page.

Write this distinction into the check that enforces it. Without it, the exception
list becomes a place for real defects.

### 3 · Use `#[Locked]` for a value the client must not change

A client write to a locked property throws
`Livewire\Features\SupportLockedProperties\CannotUpdateLockedPropertyException`.

The namespace is **not** `Livewire\Exceptions\`. People assume that namespace.
The test then never matches the exception.

An assigned Eloquent model locks its key automatically. Read rule 1 first.

`#[Locked]` stops the client. Server code can still write a bad value.

### 4 · A public method is callable, and a directive is not necessary

`wire:click="delete(5)"` accepts any argument from the browser console. A method
that no template calls is also callable. The caller needs a valid snapshot only.

- Authorize inside the method. Authorize against the record that the method
  resolves.
- Make each helper `protected` or `private`. A public helper is an endpoint.
- Livewire lifecycle hooks such as `updatedFoo()` must stay public. The browser
  can call them directly. These hooks usually run queries. The application
  usually throttles the action and does not throttle the hook.

### 5 · Route middleware does not all run again on the update endpoint

Component actions use one general endpoint. Livewire runs only the middleware on
its persistent list.
`Mechanisms\PersistentMiddleware\PersistentMiddleware` contains `Authenticate`,
`Authorize`, `SubstituteBindings`, and the Sanctum and Jetstream entries.

The Spatie `permission:` and `role:` middleware are not on that list.
`password.confirm` is not on that list. The results are:

- A component behind `permission:manage billing` does not check that permission
  again on a later action.
- A snapshot from a confirmed step-up window stays usable after the window ends.

Call the check inside the component. Or register the middleware with
`Livewire::addPersistentMiddleware()`. Do not rely on the route.

### 6 · Keep page properties in a private property

Some applications render every page with one component. That component receives
a merged property bag.

A public property publishes the full bag on every page. The bag usually contains
the authenticated user, because the layout adds it.

A private property stays out of the snapshot. The serializer reads public
properties only. A private property does not survive to the next request. Use
this pattern for a page that renders one time.

**Write a test for the keyword.** No other test fails when a person changes it.

---

## The rest of the surface

`references/attack-surface.md` covers the features that carry their own risk. Read
it before a component handles money, identity or another person's data.

The most serious item is first. **`#[Computed(cache: true)]` is keyed on the
component name and the method name only.** The key holds no user and no tenant,
so the first request writes a value that every later request reads, for one hour
by default. A computed property that reads `auth()` therefore serves one person's
data to every person. `bin/scan.php` reports this shape.

The file also covers event listeners, which a browser can call directly through
`__dispatch`. It covers the file-upload defaults, which include a throttle and no
`auth`, and accept any file type to 12 MB. It covers `wire:navigate`, which keeps
the JavaScript runtime across a page change. It covers `#[Url]`, and the change to
parent access in v4.

---

## Detect a leak in the response, and not at the source

An allow-list looks correct. An allow-list is **not** a boundary in Livewire.
Four paths avoid it:

1. **One general update endpoint.** Route classification cannot see a component,
   an action, or a property.
2. **The layout adds shared data after the controller returns.** The controller
   allow-list is not the final payload.
3. **Blade compiles `@include` with every variable in scope** (`CompilesIncludes`).
   A partial reads variables that no code passed to it.
4. **View composers, nested components, paginators, `makeVisible()`, `$appends`
   and Query Builder results.** `$hidden` does not apply to the query builder.

Test the response instead.

### The canary sweep

Write one unique value into every private column. Then request **every public
route from the real route collection**. Then assert that no response contains
those values.

```php
// Do not use a written list of paths. A list covers the pages that a person remembered.
foreach (Route::getRoutes()->getRoutes() as $route) { /* ... */ }
```

Five details decide whether the sweep works:

| Do this | Reason |
|---|---|
| Compare guard middleware by **exact class name** | `AuthenticateSession` is in the global `web` group. A substring test for `authenticate` marked a whole application as authenticated. The sweep then visited 7 routes and passed |
| Exclude middleware that cannot decide access | A global middleware for onboarding acts on an authenticated user only. It cannot decide that a route is public |
| Read the raw body **and** the HTML-entity-decoded body | The snapshot is JSON in an attribute. Each `"` arrives as `&quot;` |
| Give each fixture row a **six-figure primary key**, with one base value for each table | A new database gives the values 1, 2 and 3. The key sweep then reports the health endpoint as a leak. One shared base value turns one real defect into four reports that name four tables |
| Count a route as covered only after it **returns 200** | A route with a wrong parameter type returns 404. The sweep continues and reports no leak and no gap |

Search for integer keys in **attribute values only**. A page contains many small
integers as prices, counts and ranks. Attribute values contain the real keys.
Match a complete value, or a suffix such as `-42` in `wire:key="thing-42"`.

### Reflection over the components

This check is cheap. It finds a public property with a model type. It finds a
public property with an identity name. It finds a page-property bag that is no
longer private.

### Use `Livewire::test()` at least one time

A test suite without it never asserts the behaviour of a public method outside
its directive. It also never asserts that `#[Locked]` still works. The
application depends on both behaviours.

---

## Prove that the check can fail

**A check that is always silent looks the same as a broken check.**

Add the defect. See the test fail. Remove the defect. Do this every time.

One audit found three checks that could not fail:

- A test with the name *"no public page publishes an integer key"*. It compared
  against `'"id":<n>'`. The real defect was `wire:key="row-<n>"`. A second test
  asserted that the key **was** present, and held the defect in place.
- A `composer test:security` script that ran no privacy test.
- A doctor check that described an nginx `add_header` defect in its own text. It
  requested `/` only, so it could not observe that defect.

Run the self-test of each checker before you trust its silence.

---

## Traps that cost time

**Rector adds `use RuntimeException;` in the global namespace.** PHP reports this
statement as an unnecessary import. **paratest turns the report into a fatal
error.** The full `--parallel` run stops and reports no test results. This looks
like a broken test suite. Write `\RuntimeException` instead. Rector then makes no
change.

**Rector changes `toBe([])` and `toBe('')` to `toBeEmpty()`.** The failure
message becomes "failed asserting that an array is empty". The message no longer
names the defect. Throw the message first:

```php
if ($failures !== []) {
    throw new \RuntimeException("Leaked:\n  ".implode("\n  ", $failures));
}
```

**A test can inherit the configuration of a deployment.** This happens when the
application reads settings from the database at start. The route surface of the
sweep then changes with the test order. Set every switch that the test needs.

**A worktree is not the primary checkout.** The `composer install` of a worktree
can miss a path package. Every reference to a class in that package then looks
like a reference to a missing class. Old per-worker parallel databases turn one
new column into many failures. Reproduce a failure in the primary checkout before
you make a conclusion. Do this before you report a defect in another branch.

---

## The two tools

```bash
php bin/scan.php <path-to-app>          # 6 checks. Exit code is the finding count
php bin/scan.php --self-test            # prove that every rule fires

php bin/verify-facts.php <path-to-app>  # are the statements above still true?
php bin/verify-facts.php --help         # (any bad path prints the usage)
```

Both tools read source text. They need no bootstrap, no database and no
autoloader. They therefore run in CI, in a hook, and in a checkout without
installed dependencies. A reflection tool cannot run in those places.

### `scan.php`

It reports seven things. A public property with a model type or a collection
type. A public property with a protected field name. A page-property bag that is
not private. A public method with a mutator name and no authorization call. A
`#[Url]` property with an identifier name and no `#[Locked]`. A public property
with no type. A `#[Computed(cache: true)]` with no `key`.

The scanner skips `vendor` and `node_modules` at any depth. Livewire's own test
fixtures contain the shapes this scanner looks for, on purpose, and a report full
of them is a report that nobody reads a second time.

The scanner is a first check. The canary sweep is the boundary.

### `verify-facts.php`

This skill states facts about Livewire internals. It names an exception
namespace. It names the contents of a middleware list. It names the shape that a
model takes in a snapshot.

A fact can stop being true. A new release can move a class or change a list. The
skill then gives confident wrong advice, and no person notices.

This tool applies the rule above to the skill. It reads the installed
`vendor/livewire/livewire` and fails when a statement no longer holds. It checks
16 statements. Run it after a Livewire upgrade.

The most important check is the one for the persistent middleware list. The skill
tells a reader that a permission check does **not** run again on an update
request. A future release could add that middleware. The advice would then be
wrong in the dangerous direction.
