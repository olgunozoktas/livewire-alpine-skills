# The rest of the attack surface

`SKILL.md` covers properties, methods and middleware. This file covers the
features that carry their own risk.

Each statement names the file that proves it. The author read
`livewire/livewire` v4.4.2 in `vendor/`. Run `bin/verify-facts.php` after an
upgrade.

A statement marked **unverified** needs a test before you rely on it.

---

## 1 · A cached computed property can serve one user's data to every user

This is the most serious item in this file.

**The behaviour is documented. The consequence is not.**
`docs/computed-properties.md` says the value is cached "across all components in
your application", and that "every instance of this component in your
application will share the same cached value". That is accurate. But the example
caches `Post::query()->pluck('title', 'id')` — global data — and the page
presents `key:` only as a way to clear the cache by hand, never as a way to
scope it. No sentence says that a computed property reading `auth()` serves the
first person's data to everybody else.

`#[Computed]` accepts two different caching options. They use different keys.

`src/Features/SupportComputed/BaseComputed.php:145`:

```php
protected function generatePersistedKey()
{
    if ($this->key) return $this->key;

    return 'lw_computed.'.$this->component->getId().'.'.$this->getName();
}
```

`src/Features/SupportComputed/BaseComputed.php:152`:

```php
protected function generateCachedKey()
{
    if ($this->key) return $this->key;

    return 'lw_computed.'.$this->component->getName().'.'.$this->getName();
}
```

`persist: true` uses `getId()`. `src/Factory/Factory.php:27` gives each component
instance a random 20-character id. The key is therefore different for each
component instance.

`cache: true` uses `getName()`. This is the **component name**. The key contains
no user, no tenant, no team and no method parameter.

So this code is a data leak:

```php
#[Computed(cache: true)]
public function invoices()
{
    return auth()->user()->invoices; // one user's invoices...
}
```

The first request writes one user's invoices to `lw_computed.dashboard.invoices`.
Every later request for one hour reads that same key. Every user then receives
the first user's invoices. The default is 3600 seconds
(`BaseComputed.php:17`).

**Add the identity to the key.** The constructor accepts one:

```php
#[Computed(cache: true, key: 'invoices.'.auth()->id())]
```

Two more notes. `Cache::remember()` writes to the application cache, so the value
crosses requests and processes. A tagged cache uses `Cache::tags()` when the
driver supports tags (`BaseComputed.php:79`), and the tags do not add identity by
themselves.

**Check every `#[Computed(cache: true)]` in an application.** A computed property
that reads `auth()`, a tenant, a team or a request parameter needs an explicit
key.

---

## 2 · An event listener is an endpoint

People treat a listener as internal. They assume that only another component
dispatches the event. That assumption is wrong.

`src/Features/SupportEvents/SupportEvents.php:16` handles a method named
`__dispatch`. The browser can call it. Livewire then:

1. Checks that the event name is a registered listener on the component.
2. Checks that the resolved method is a public method on the subclass.
3. Runs the `#[Authorize]` attributes for that method.
4. Calls the method with the parameters from the request.

Step 3 exists for a reason. The source states it:

```php
// Run any authorization checks on the listener method since
// its normal "call" hook doesn't get run when the method
// is called as an event listener...
```

Livewire needed a special case for this path. That is evidence that the path is
real.

**Consequences.**

- `#[On('order-paid')] public function markPaid($orderId)` accepts any
  `$orderId` from the browser. Authorize inside the method.
- A listener is subject to the same rule as an action. Every public method is
  callable, and a listener is a public method with another name.
- A `protected` or `private` listener method is refused by step 2.

---

## 3 · File uploads

### The two routes are signed, and nothing else guards them by default

`src/Features/SupportFileUploads/FileUploadController.php:29` and
`FilePreviewController.php:20` both call
`abort_unless(request()->hasValidRelativeSignature(), 401)`.

The default middleware is a throttle only.
`src/Features/SupportFileUploads/FileUploadConfiguration.php:102`:

```php
return config('livewire.temporary_file_upload.middleware') ?: 'throttle:60,1';
```

There is no `auth` middleware in that default. A visitor who can load a page with
a file-upload component can obtain a signed URL and upload files. The limit is
60 requests each minute.

**Add `auth` for an application where only a signed-in person may upload.** Set
`livewire.temporary_file_upload.middleware`.

### The default rules accept any file type

`FileUploadConfiguration.php:116`:

```php
if (is_null($rules)) return ['required', 'file', 'max:12288'];
```

The default allows any type, to 12 MB. Your `#[Validate]` rule runs on the
component property, and the temporary upload has already happened by then. The
temporary disk therefore holds the file before your rule sees it.

**Set `livewire.temporary_file_upload.rules` for the temporary disk as well.**

### The original name and the extension come from the client

`TemporaryUploadedFile.php:215` stores the client name as base64 inside the
generated filename. `TemporaryUploadedFile.php:207` uses
`$file->getClientOriginalExtension()` for the stored extension.

**Never use `getClientOriginalName()` as a storage path.** Never trust the
extension.

### The mime type IS read from the file contents

`TemporaryUploadedFile.php:63` reads the filename only when
`app()->runningUnitTests()` returns true. In every other case it calls
`detectMimeTypeFromContents()`, which reads the stored stream.

This is correct behaviour. The note is here because the opposite is easy to
assume.

---

## 4 · `wire:navigate` keeps the JavaScript runtime

`wire:navigate` replaces the document without a browser reload. The events
`livewire:navigating`, `livewire:navigated`, `alpine:navigating` and
`alpine:navigated` exist in `dist/livewire.js`.

The consequence for security is the state that lives outside a component:

- An `Alpine.store()` value.
- A variable at module scope in your own script.
- An element inside a `@persist` block.

Each one survives a navigation. A navigation can move a person from a page under
one policy to a page under another policy. The state does not reset.

**Clear sensitive client state on `livewire:navigating`.** Do not hold a token, a
draft or another person's data in a store that outlives the page.

**Unverified:** whether a `@persist` block can hold a component from the previous
page in a way that survives an authorization change. Write a test before you
depend on either answer.

---

## 5 · Parent access changed in v4

`src/Features/SupportAccessingParent/` exists and is **empty** in v4.4.2. The
PHP-side parent accessor of earlier versions is not there.

`$parent` appears in `dist/livewire.js`, so the JavaScript side keeps a concept
of a parent component.

**Do not design an authorization boundary between a parent component and a child
component.** They render in one request, and the client addresses each of them
through the same endpoint. Authorize in each component that reads or writes data.

**Unverified:** the exact reach of `$wire.$parent` in v4.4.2. Read the current
official documentation before you use it.

---

## 6 · `#[Url]` writes the query string into a property

A `#[Url]` property takes its value from the query string. A link can therefore
set it, and a person can send that link to somebody else.

This is correct for a tab, a filter or a sort order.

It is a defect for an identifier. `#[Url] public $orderId` lets any link choose
the record that the component reads, and the value then returns in the snapshot.

Add `#[Locked]` when the property selects a record, or resolve the record from
the authenticated user instead.

`bin/scan.php` reports this shape. It matches identifier names only, because a
rule that reports every `#[Url]` property reports mostly correct code.
---

## 7 · A lazy component publishes its mount parameters

**Undocumented.** `docs/lazy.md` contains no security note.

`#[Lazy]`, or `lazy` on a component tag, defers the render. Livewire must carry
the mount parameters across that round trip, and it carries them **in the page**.

`src/Features/SupportLazyLoading/SupportLazyLoading.php:162` puts the parameters
on a throwaway component with two public properties, snapshots it, and then:

```php
$encoded = base64_encode(json_encode($snapshot));
```

Base64 is an encoding. It is not encryption. Any person who opens the page source
can decode every mount parameter of every lazy component.

The snapshot carries a checksum, so the values cannot be **changed** —
`HandleComponents::snapshot()` calls `Checksum::generate()`, which is an
HMAC-SHA256 over the snapshot. The parameters are therefore tamper-evident and
**not confidential**.

A component without `lazy` does not do this. `forMount` appears only in the lazy
feature.

**So this publishes a token:**

```blade
<livewire:invoice-panel :invoice="$invoice" :signed-url="$url" lazy />
```

**Pass an identifier that the component can authorize, and resolve the rest
inside `mount()`.** Never pass a secret, a signed URL, or a whole record to a
lazy component.

---

## 8 · A model property rehydrates with global scopes disabled

**Undocumented in the Livewire documentation.**

`src/Features/SupportModels/ModelSynth.php:84` restores a model like this:

```php
(new $class)->newQueryForRestoration($key)->useWritePdo()->firstOrFail();
```

Laravel's `Model::newQueryForRestoration()` is:

```php
return $this->newQueryWithoutScopes()->whereKey($ids);
```

**Without scopes.** No tenant scope. No `published` scope. No soft-delete scope.

The checksum limits this. A browser cannot change the key, so this is not a way
to read any row by typing an id. Two cases remain, and both are real:

- **Authority that changed between requests.** A person removed from a team still
  holds a valid snapshot. Their next action rehydrates the model, and the tenant
  scope that would now exclude it does not run.
- **A row deleted between requests.** A soft-deleted model still rehydrates,
  because `SoftDeletingScope` is a global scope.

**Authorize in the action, against the rehydrated model.** Route middleware and a
global scope are both absent on this path.

---

## 9 · Spatie's `permission:` middleware cannot be made persistent

Item 5 of `SKILL.md` says that route middleware does not all run again. The
Livewire documentation covers the mechanism, and covers the limitation. The two
together are what matter, and neither page draws the conclusion.

`docs/security.md` presents persistent middleware as the protection:

> Persistent middleware protects you from scenarios where the authorization
> rules or user permissions have changed after the initial page-load.

It then tells you to register your own with
`Livewire::addPersistentMiddleware()`, and warns:

> **Middleware arguments are not supported.**
> ```php
> // Bad...
> Livewire::addPersistentMiddleware(AuthorizeResource::class.':admin');
> ```

Spatie's middleware takes the permission **as an argument**:
`permission:manage billing`. So the documented fix cannot express the common
case. Registering `PermissionMiddleware::class` persists a middleware with no
permission to check.

**Call the check inside the component.** That is the only form that survives an
update request.
---

## 10 · The checksum-failure limiter is keyed on the client IP

**Undocumented.** No page mentions checksum rate limiting, the 429, or its key.

Every Livewire update verifies the snapshot checksum, and a failure is counted
against the client IP. `src/Mechanisms/HandleComponents/Checksum.php`:

```php
:11   protected static $maxFailures = 10;
:12   protected static $decaySeconds = 600;     // ten minutes
:78   return 'livewire-checksum-failures:' . request()->ip();
```

`enforceRateLimit()` runs at the top of `verify()`, **before** the current
request's own checksum is checked. So ten bad snapshots from one address answer
429 to every Livewire request from that address for ten minutes.

The key is the raw IP and nothing else. Behind corporate NAT, campus NAT, CGNAT,
or a proxy where `TrustProxies` is not configured, that address belongs to many
people — or to everybody.

**Attacker sequence.** Send ten POSTs to the update route with a structurally
valid snapshot and a wrong checksum. Every Livewire interaction from that address
fails for ten minutes. Repeat every ten minutes. The cost is ten requests.

**There is no setting.** `$maxFailures` and `$decaySeconds` are `protected
static`. What you can do:

- Configure `TrustProxies` so `request()->ip()` is the real client and not your
  own load balancer.
- Rate-limit the update route at the edge on a key that includes the session.

## 11 · A snapshot is a bearer object, with no owner and no expiry

The checksum is `hash_hmac('sha256', json_encode($snapshot), $key)` where the key
is the application key — `Checksum.php:82`, `:89`. It uses `hash_equals`, so the
comparison is constant time.

It covers `data` and the whole `memo`, including `memo.id` and `memo.name`. A
snapshot therefore cannot be presented as a different component, and one
component's data cannot be re-signed as another's. That part is sound.

What it does **not** contain is a session id, a user id, a nonce or a timestamp.
A validly signed snapshot is accepted from any client, for as long as the
application key stays the same.

**Documented as integrity. The consequence is not stated.** `docs/security.md`
says the checksum verifies that "the snapshot hasn't changed", which is an
integrity claim. It does not say the snapshot is unbound and does not expire.

**Why this is defence in depth rather than a hole:** the documented model is that
you authorize every action. If you do, a replayed snapshot buys nothing. It
matters when a page leaks by an ordinary channel — a shared cache, a screenshot
of the source, a `Referer`, a log — and an action relies on state that was
authorized only at mount.

**Treat "the checksum passed" as "this state is unmodified", never as "this
person owns this state".** Rotating the application key invalidates every
snapshot, which is the lever if one leaks.

---

## 12 · On Octane, Livewire's static state is never flushed between requests

**The most serious item in this file after the computed cache, and it is
undocumented.** Across all 99 documentation files the word "octane" appears
once, in `wire-stream.md`, saying `wire:stream` does not support it.

Livewire keeps request-scoped and user-scoped data in `static` properties across
about twenty feature classes. One event resets them —
`LivewireManager.php:293`:

```php
function flushState() { trigger('flush-state'); }
```

`flushState()` is called in exactly two places, and **both are the testing
renderers**: `SupportTesting/InitialRender.php:37` and
`SupportTesting/SubsequentRender.php:40`. The production update path,
`HandleRequests::handleUpdate()`, never calls it. The package registers no
Octane listener and no terminating callback. The only Octane mention in the
source is a comment.

Under PHP-FPM this costs nothing, because the process dies. **Under Laravel
Octane the worker is reused**, so the state survives into the next request and
the next user.

Two consequences, each traced to its property:

- **A page loses its JavaScript.** `SupportScriptsAndAssets.php:11-17` keeps
  `$alreadyRunAssetKeys`, which records the `@assets` and `@script` blocks
  already emitted so each is injected once. It is cleared only on
  `flush-state`. On a later request in the same worker the block reads as
  already run, and the required asset is **omitted from a different user's
  page**.
- **Flash data stops being cleared.** `SupportRedirects.php:15` holds
  `$atLeastOneMountedComponentHasRedirected`, and `:20-24` uses it on every
  response to decide whether to forget the flash bag. Once any request in that
  worker redirects, the flag stays true, and later requests skip the clearing —
  so a flash message persists into another request.

`$renderStack` and `$componentStack` (`HandleComponents.php:21-22`) are popped
with `tap()` rather than `try`/`finally`, so an exception mid-render leaves a
stale entry for the next request.

**No crafted payload is needed.** One user triggers a redirect or an assets
block; the next user routed to that worker gets the consequence.

**The fix, until Livewire wires it itself:**

```php
// config/octane.php
'listeners' => [
    RequestTerminated::class => [
        fn () => \Livewire\Livewire::flushState(),
    ],
],
```

**Verified in source, NOT verified against a running Octane worker.** Octane was
not installed where this was read. Confirm it in your own environment before you
rely on either the consequence or the fix.

## 13 · A valid Livewire request has no rate limit

`src/Features/SupportPolling/` is **empty**. The `wire:poll` throttling for a
background tab or an off-screen element is client-side JavaScript, and a script
that is not a browser ignores it.

The update route carries no `throttle` middleware
(`HandleRequests.php:26-30`). The only limiter in Livewire counts **checksum
failures** — see item 10 — and a request with a valid checksum is never counted.

Per-request caps do exist and are enforced: `max_size` 1 MB, `max_calls` 50,
`max_components` 200 (`config/livewire.php:276-280`). They bound one request,
never the rate.

**Attacker sequence.** Capture one valid snapshot from a page you are allowed to
see. POST it to the update route in a loop. Each request runs the full hydrate,
render and query cycle with no server-side throttle.

**Documented as a performance behaviour; the consequence is not stated.**
`polling.md` presents the throttling as a courtesy to the browser and never says
a malicious client bypasses it.

**Add `throttle` to a custom update route** with `Livewire::setUpdateRoute(...)`,
which `docs/security.md` already shows for other reasons.

## 14 · A nested component is addressable on its own

`HandleRequests::handleUpdate()` iterates `request('components')` and hydrates
each one independently (`:159-218`). There is no parent-to-child containment
check.

A child rendered inside a parent has its own `wire:id` and its own signed
snapshot, both in the page. A client can submit that child's snapshot alone and
call any of its public methods. **Middleware on the parent's route does not
protect the child.**

Forgery is still prevented by the checksum. The point is that a *legitimate*
child snapshot is independently replayable.

**Documented indirectly.** `understanding-nesting.md` establishes that each
component is independent with its own id and snapshot, and `nesting.md` shows
`$this->authorize()` inside child actions. The explicit warning is not written.

## 15 · Two smaller ones, recorded so nobody re-investigates

**Compiled component directories are created world-writable.**
`src/Compiler/CacheManager.php:118` and seven sibling lines use
`File::makeDirectory(..., 0777, true, true)`. The location is
`storage/framework/views/livewire`, which is not web-served, and this matches
Laravel's own compiled-Blade convention. The residual risk is local: on shared
hosting another local user could place a `.php` file that Livewire then
requires. Tighten to `0755` on a multi-tenant host. Undocumented.

**`#[Session]` is NOT the computed-cache bug.** Its default key is also built
from the component name and the property name only —
`SupportSession/BaseSession.php:45-52` — which looks identical to the computed
cache. The difference is the store: `#[Session]` writes through Laravel's
**per-user session**, so the same key resolves to a different value for each
person. Two instances of one component share a slot for the same user, which is
the documented feature. Checked because the key looked alarming.

---

## 16 · Real-time `#[Validate]` does not stop the write, and the action still runs

**The item on this page a developer is most likely to get wrong**, because the
documentation's own words invite it: `attribute-validate.md` calls it
*"Automatic validation — Property is validated every time it's updated"*.

That sentence is true and it is not protection. The order in
`HandleComponents.php:399-410` is: set the value, **then** run the validation
callbacks.

```php
// updateProperty() has already written the value at :451
foreach ($finishes as $finish) { $finish(); }   // validateOnly runs here
```

The `ValidationException` it raises is then **swallowed on purpose**.
`Wrapped.php:22-34` triggers the exception hook and rethrows only if
propagation is still on, and `SupportValidation.php:69-76` calls
`$stopPropagation()`. The error reaches the error bag and nothing else.

Control returns to `update()`, which calls `callMethods()` at `:220-223`. **The
action runs, with the invalid value on the component.**

**Attacker sequence.** The component has
`#[Validate('required|email')] public $email` and a `save()` that trusts it. One
request carries both:

```json
{ "updates": { "email": "anything at all" },
  "calls": [ { "method": "save", "params": [] } ] }
```

The property is set. `validateOnly` throws and is swallowed. `save()` persists
it.

**Call `$this->validate()` at the top of every action that acts on the data.**
Treat the attribute as a user-experience aid. The docs do say "You still call
`$this->validate()` before saving" — framed as completeness, never as the gate.

**Documented; the consequence is not stated.**

## 17 · `#[Reactive]` is enforced at dehydrate, after the action has run

A child may not persist a change to a `#[Reactive]` prop. The check is in
`BaseReactive.php:58-65`, and `dehydrate()` is the **end** of the request.

The order is again updateProperties, callMethods, dehydrate
(`HandleComponents.php:220-234`). So a client that sends
`updates: {"amount": 1}` with `calls: [{"method":"charge"}]` gets `charge()` run
with `amount = 1`. The request then aborts with
`CannotMutateReactivePropException` — **after** the charge.

**Do not read a `#[Reactive]` prop as a trusted value inside an action.**
Re-derive it from server state.

**Undocumented.** Neither `attribute-reactive.md` nor `nesting.md` carries a
mutation warning.

## 18 · `#[Locked]` cannot lock one key of an array

The attribute matches the whole subtree — `SupportAttributes.php:42` tests
`$fullPath === $name` or `startsWith($name . '.')` — so it is all or nothing for
the property.

That is a problem when one key of an array is bound and a sibling key is not:

```php
public $settings = ['theme' => 'dark', 'is_admin' => false];
```

The view binds `wire:model="settings.theme"`, so `#[Locked]` on `$settings`
would break the binding. Without it, `updates: {"settings.is_admin": true}`
writes the key — `ArraySynth::set()` is `$target[$key] = $value`
(`ArraySynth.php:36-38`), with no key allow-list below the top-level public
property check.

**Never keep a sensitive key in the same array as a bound key.** Give it its own
`#[Locked]` scalar, or re-authorize where it is used.

The refusal itself is correctly placed: it throws during `trigger('update')` at
`HandleComponents.php:441`, **before** the value is written at `:451`. Unlike
items 16 and 17, a locked write never lands.

**The blocking is documented. The granularity is not.**

## 19 · Publishing one payload limit silently disables the other three

Livewire caps a request in four ways, and all four are enforced:

| Key | Default | Enforced at |
|---|---|---|
| `max_size` | 1 MB | `HandleRequests.php:148-157` |
| `max_nesting_depth` | 10 | `HandleComponents.php:434-437` |
| `max_calls` | 50 | `HandleComponents.php:527-531` |
| `max_components` | 200 | `HandleRequests.php:176-180` |

None of the four appears anywhere in the 99 documentation files. They exist only
as comments in the published config — which is where the trap is.

`LivewireServiceProvider.php:65` uses `mergeConfigFrom`, and that merge is
**shallow**. A published config that overrides one key:

```php
'payload' => ['max_size' => null],
```

**replaces the whole `payload` array**. The other three keys are then undefined,
which reads back as `null`, and each guard is written `if ($max !== null)`. All
three are off, and nothing says so.

**Write every sub-key when you override one**, and confirm with
`config('livewire.payload')` after publishing.

## 20 · Class instantiation on hydrate is a denylist

`HandleSynths.php:68,91` calls `SecurityPolicy::validateClass()` on the class
named in the snapshot meta. The list is finite — console commands,
`Symfony\Component\Process\Process`, a few known gadgets — with an `is_a()`
inheritance check (`SecurityPolicy.php:12-52`).

Being a denylist, an unlisted gadget class passes. This matters only if the
checksum is ever bypassed, which the source comment says outright
(`SecurityPolicy.php:8-11`).

Add your own with `SecurityPolicy::denyClasses([...])`. It is defence in depth,
never the primary control — **that is the application key**.

## 21 · Three controls verified sound, so nobody re-checks them

**An update can never choose its own synthesizer or class.**
`HandleSynths::hydrateForUpdate()` and `hydratePropertyUpdate()`
(`:97-118`, `:121-153`) always pair the untrusted update value with meta taken
from the **authenticated** snapshot. The trust boundary is written out in
comments at `:98-100` and `:113-117`.

**Base-class internals are not writable.** `BaseUtils.php:28-39` admits only
public, non-static properties declared on the user's own subclass, excluding
`Livewire\Component` and `Volt\Component`. `$id` cannot be written.

**There are exactly four magic actions**, and the server treats them as no-ops:
`$refresh`, `$set`, `$sync`, `$commit` (`SupportMagicActions.php:11-27`).
`$toggle` and `$parent` are client-side only. The real mutation from `$set`
travels the ordinary `updates` path, so it meets the public-property check, the
`#[Locked]` check and type coercion. **The magic list is not a boundary** — the
public-property and public-method checks are.


---

## A short checklist

Read this before a Livewire component goes on a route that handles money,
identity or another person's data.

- [ ] No `#[Computed(cache: true)]` without an identity in `key`.
- [ ] Every `#[On]` listener authorizes inside the method.
- [ ] The upload middleware includes `auth` when only a member may upload.
- [ ] The upload rules restrict the file type on the temporary disk.
- [ ] No code uses `getClientOriginalName()` as a path.
- [ ] No sensitive client state survives `livewire:navigating`.
- [ ] Each `#[Url]` identifier is `#[Locked]`.
- [ ] No secret, signed URL or whole record is a mount parameter of a `lazy` component.
- [ ] Every action authorizes against the model it rehydrated, not against the route.
- [ ] Permission checks live inside the component, not only in `permission:` middleware.
- [ ] `TrustProxies` is configured, so the checksum limiter keys on a real client address.
- [ ] No action trusts state that was authorized only at mount.
- [ ] On Octane, `Livewire::flushState()` runs on `RequestTerminated`.
- [ ] The Livewire update route carries a `throttle`.
- [ ] Every nested component authorizes for itself, not through its parent's route.
- [ ] Every action that persists calls `$this->validate()` itself.
- [ ] No action trusts a `#[Reactive]` prop as a value.
- [ ] No sensitive key shares an array with a bound key.
- [ ] A published `livewire.payload` names all four sub-keys.
- [ ] Each public method that reads or writes a record authorizes.
- [ ] `bin/scan.php` reports nothing, or reports only recorded exceptions.
- [ ] `bin/verify-facts.php` reports that every statement still holds.
