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
- [ ] Each public method that reads or writes a record authorizes.
- [ ] `bin/scan.php` reports nothing, or reports only recorded exceptions.
- [ ] `bin/verify-facts.php` reports that every statement still holds.
