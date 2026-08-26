---
name: alpinejs-security
version: 1.3.0
description: 'Use for Alpine.js security work. Covers the two injection seams — the VALUE a directive assigns, and the ATTRIBUTE EXPRESSION itself, which Alpine compiles with new Function. Explains why HTML-escaping a server value into x-data, x-on or x-init does NOT protect it, what x-* means for an HTML sanitiser, and what is user-controlled once state reaches the browser. Use it before you interpolate server data into any x-* attribute, before you use x-html, before you $persist anything, and when reviewing Blade or any server template that renders Alpine. Keywords: alpine security, alpinejs xss, x-data injection, x-html, x-on injection, x-init, new Function, unsafe-eval, CSP build, Alpine.evaluate, MutationObserver, sanitiser, DOMPurify, $persist localStorage, Alpine.store, x-model number, x-bind javascript url, x-teleport, $wire console.'
---

# Alpine.js security

Alpine runs in the browser, on the user's machine, in their debugger. Two
consequences follow, and this skill is about both.

1. **Nothing Alpine holds is secret, and nothing it enforces is enforced.**
2. **An Alpine attribute is a JavaScript context.** Server data interpolated
   into one is code, not data.

The second is the dangerous one, and Alpine's own documentation does not cover
it.

---

## The two seams

Every question in this skill is one of these. Tell them apart first.

| | **Seam A — the VALUE** | **Seam B — the EXPRESSION** |
|---|---|---|
| What it is | what a directive assigns at runtime | the attribute text Alpine compiles |
| Example | `x-html="body"` — what is in `body` | `x-data="{ n: '{{ $x }}' }"` — the attribute itself |
| Sink | `innerHTML`, `setAttribute` | `new AsyncFunction` |
| Encode for | HTML, or a URL scheme | **JavaScript** |
| Alpine's docs | warned about, clearly | **not covered** |

**Seam B is more severe and less known.** Start there.

---

## The rule that matters most

**HTML-escaping does not protect an Alpine attribute.**

```blade
<div x-data="{ name: '{{ $displayName }}' }">   {{-- BROKEN --}}
```

Blade escapes correctly. The browser then decodes the entity back before Alpine
reads the attribute, so Alpine compiles a real quote:

```
1. attacker display name : '+alert(document.cookie)+'
2. after Blade {{ }}     : &#039;+alert(document.cookie)+&#039;
3. what getAttribute sees: { name: ''+alert(document.cookie)+'' }
```

The quote closes the string literal and the call runs at init, with no
interaction. **This is not a Blade bug.** Blade applied an HTML encoder to a
JavaScript context, because that is what it was asked to do.

### Two fixes, both verified

```blade
<div x-data="@js(['name' => $displayName])">          {{-- encode for JS --}}

<div data-name="{{ $displayName }}"                    {{-- or pass by VALUE --}}
     x-data="{ name: $el.dataset.name }">
```

`@js()` emits `JSON.parse('…')` with `'` for the quote — a JavaScript
escape, not an HTML entity, so the parser leaves it alone. The `data-*` route
is safe because the value never enters compiled code.

**The same applies to `x-on`, `x-init`, `x-effect`, `x-show`, `x-if` and every
other expression directive.** `@click="buy('{{ $sku }}')"` has the identical
hole.

---

## What compiles, and when

Alpine builds a function from the attribute text:

```js
new AsyncFunction(["__self","scope"], `with (scope) { __self.result = ${expr} }…`)
```

`evaluator.js:94-96`. There is no sanitisation on that path and no escaping
helper anywhere in Alpine.

**It also compiles attributes on DOM it never parsed.** Alpine runs a
document-wide `MutationObserver` — `mutation.js:49,54`, with `subtree`,
`childList` and `attributes` all true. Any HTML that reaches the page by any
route has its `x-*` directives compiled and run.

So `x-init` is an XSS sink that does not involve `<script>`:

```html
<div x-init="location='//evil'"></div>
```

**Whether your sanitiser stops that depends on its shape:**

| Sanitiser | `x-*` survives? |
|---|---|
| Strict allow-list — DOMPurify's default | **No.** Unknown attributes are dropped |
| Allow-list widened with `ADD_ATTR` | depends what was added |
| Deny-list — "strip `<script>` and `on*`" | **Yes.** The dangerous one |
| Hand-rolled regex | **Yes**, nearly always |

DOMPurify admits an attribute only via a 369-entry allow-list plus
`/^data-…/` and `/^aria-…/`. `x-init` matches none, so it is stripped. **Verify
your sanitiser is an allow-list.** If it is a deny-list, add `x-*`, `@*` and
`:*`.

`x-ignore` stops Alpine initialising a subtree, and is the Alpine-side
mitigation for a region that will hold untrusted HTML.

---

## Nothing client-side is a control

State lives on the DOM node — `node._x_dataStack`, `scope.js:7` — and the CDN
build puts `Alpine` on `window`. So from the console a visitor can read and
write any component's scope and any store:

```js
Alpine.store('cart').total = 0
Alpine.$data($0).isAdmin = true
```

That is by design and Alpine documents the access. What it does not say is the
consequence: **a role, a price, an entitlement or an id in `x-data` is a
suggestion.** Re-derive every one of them on the server, on every request.

Three specific traps:

- **`x-model.number` does not guarantee a number.** `x-model.js:276` falls back
  to the raw string when the input is not numeric, so `"abc"` stays `"abc"`.
  The docs say it will *"force"* a number. It does not.
- **`$persist` is plain-text `localStorage`**, keyed `_x_<property>`, readable
  by any script on the origin, and it survives logout. Never persist a token,
  a role or PII. It re-reads that storage through an unguarded `JSON.parse`
  (`persist/src/index.js:76`), so a hand-edited value breaks the component.
- **A mask is presentation.** `@alpinejs/mask` reformats the displayed value
  and constrains nothing that reaches your server.

---

## What is SAFE, so you do not re-investigate it

| | Why |
|---|---|
| `x-text` | assigns `textContent` (`x-text.js:10`) — the value cannot become markup. Its **expression** is still Seam B |
| `wire:navigate` | same-origin checked three times, including **after** a redirect; a cross-origin result is discarded and the browser navigates natively |
| `Alpine.morph` | parses script-inert via `<template>.innerHTML`. It does not run `<script>` — but `<img onerror>` still fires once live, so do not morph untrusted HTML |
| `x-ignore` | inserts nothing; it is a mitigation |
| `$wire` | the client is deliberately unprivileged. The server verifies an HMAC on the snapshot, allows only public methods and public properties, enforces `#[Locked]`, and rate-limits failures |
| query-string tracking | opt-in per property, and it explicitly blocks `__proto__` / `constructor` / `prototype` |
| `x-trap` | focus management for keyboard users. `allowOutsideClick: true` — never a security boundary |

---

## The CSP build shrinks Seam B

Default Alpine requires `'unsafe-eval'`, and that weakens CSP for the whole
page, not just Alpine. The CSP build replaces the evaluator with a parser and
interpreter that never builds a function from a string. It blocks globals,
`constructor`, `prototype`, `__proto__`, and it removes `x-html` entirely.

It is a strict **subset** — no arrow functions, no template literals, no
spread. Treat it as blast-radius reduction, not as a proven sandbox: its guards
are a blacklist plus a global-identity set, and completeness is unverified.

**In Livewire, do not install it.** Set `'csp_safe' => true` instead.

---

## The tools

```bash
python3 bin/review-security.py <file>...   # exit code is the error count
python3 bin/review-security.py --self-test # prove every rule fires
```

It reads Blade, HTML and Vue-style templates and flags the seams above. It is
calibrated in both directions: `@js()`, `Js::from()`, `data-*` + `$el.dataset`,
and `x-text` on a plain property all stay silent.

---

## Reading order

| File | When |
|---|---|
| `references/attack-surface.md` | the full catalogue, every item with `file:line`, the docs status, and the fix |

For Alpine's mechanics use **`alpinejs-reference`**. For the server half of a
Livewire app use **`livewire-security`** — that one covers the snapshot,
`#[Locked]` and the persistent-middleware gap, which are a different boundary
from this skill's.
