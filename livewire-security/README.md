# livewire-security

An [Agent Skill](https://agentskills.io/what-are-skills) for the security half of
**Laravel Livewire v4**. It covers what a component publishes, what a browser can
change, and how to detect a leak in the response.

The `livewire-development` skill covers all other Livewire work. This skill is
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
├── SKILL.md          the six rules, the detection design, the traps
└── bin/scan.php      a static scanner with a self-test
```

---

## The tool

```bash
php bin/scan.php <path-to-app>      # report only. Exit code 1 for a finding
php bin/scan.php --self-test        # prove that every rule fires
```

The scanner reads source text. It needs no bootstrap, no database and no
autoloader. It therefore runs in CI, in a hook, and in a checkout without
installed dependencies. A reflection tool cannot run in those places.

It reports four things. A public property with a model type or a collection type.
A public property with a protected field name. A page-property bag that is not
private. A public method with a mutator name and no authorization call.

**The self-test found two real defects in the scanner.** On the first run every
rule reported "expected to fire". The test fixtures were single lines, and the
property patterns match the start of a line. On a real application the scanner
then reported three incorrect findings. The `updatedFoo()` lifecycle hooks
matched the `update` mutator prefix. An application guard method,
`$this->ensureAccess()`, was not in the authorization pattern. The scanner now
handles both cases, and the self-test covers both.

The exit code is the number of findings. The scanner can therefore gate a build.

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
