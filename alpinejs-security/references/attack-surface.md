# What a browser can do to an Alpine component

Every item verified in Alpine v3 source. Each carries `file:line`, whether
Alpine's own docs cover it, and the fix.

**The docs status matters more than the finding.** Alpine's 56 documentation
pages mention security six times: a CSP page, and one XSS warning on `x-html`
repeated twice. Where a page already warns you, this file says so and moves on.

---

## The two seams, once more

| | Seam A — the VALUE | Seam B — the EXPRESSION |
|---|---|---|
| Sink | `innerHTML`, `setAttribute` | `new AsyncFunction` |
| Encode for | HTML, URL scheme | **JavaScript** |
| Alpine warns? | yes, on `x-html` | **no** |

Alpine documents the lesser risk and is silent on the greater one. That
inversion is the single most useful thing in this file.

---

## 1 · Server data in an Alpine attribute is code — and HTML-escaping does not stop it

**The most important item here.**

`x-data`, `x-init`, `x-on`, `x-effect`, `x-show`, `x-if`, `x-text` and the rest
all compile their attribute text:

```js
new AsyncFunction(["__self","scope"],
  `with (scope) { __self.result = ${expression} }; …`)
```

`evaluator.js:94-96`. The `expression` is the element's **decoded** attribute
value — `directives.js:198`, read from `.value` at `:38,62-65`.

Decoded is the word that matters. Measured with a real HTML parser:

```
1. attacker display name : '+alert(document.cookie)+'
2. after Blade {{ }}     : &#039;+alert(document.cookie)+&#039;
3. rendered HTML         : <div x-data="{ name: '&#039;+alert(…)+&#039;' }">
4. what getAttribute sees: { name: ''+alert(document.cookie)+'' }
```

The parser turns `&#039;` back into `'` before any script runs. Alpine compiles
line 4, the quote closes the literal, and the call executes at init with no
interaction.

**Blade is not broken.** An HTML encoder was applied to a JavaScript context.

### The fixes, both verified

```blade
<div x-data="@js(['name' => $displayName])">
```

emits `JSON.parse('{"name":"'+alert(…)+'"}')`. `'` is a
JavaScript escape, not an HTML entity, so the parser leaves it alone and Alpine
compiles one string literal.

```blade
<div data-name="{{ $displayName }}" x-data="{ name: $el.dataset.name }">
```

is safe for a different reason: the value lands in Seam A and never enters
compiled code.

**Docs status: DOCUMENTED BUT THE CONSEQUENCE IS NOT STATED.** `data.md:50`
says *"x-data is evaluated as a normal JavaScript object"*. True, and it never
says that interpolating into it is a code-injection sink. No escaping guidance
exists for this seam anywhere in the docs.

---

## 2 · `x-*` is an execution sink that a deny-list sanitiser will miss

Alpine watches the whole document:

```js
observer.observe(document, { subtree: true, childList: true,
                             attributes: true, attributeOldValue: true })
```

`mutation.js:49,54`. Added nodes are collected (`:139-152`) and their directives
processed (`:210`). So HTML that reaches the page by **any** route — another
library, a different `innerHTML`, an htmx swap — has its `x-*` attributes
compiled and run.

That gives an XSS payload with no `<script>` in it:

```html
<div x-init="location='//evil'"></div>
```

**Whether your sanitiser stops it depends on its shape, and this is where a
common claim is wrong:**

| Sanitiser | `x-*` survives? |
|---|---|
| Strict allow-list — **DOMPurify's default** | **No.** Unknown attributes are dropped |
| Allow-list widened with `ADD_ATTR` | depends what was added |
| Deny-list — "strip `<script>` and `on*`" | **Yes.** The dangerous shape |
| Hand-rolled regex | **Yes**, nearly always |

DOMPurify admits an attribute only if it is in a 369-entry allow-list or matches
`/^data-[\-\w.·-￿]+$/` or `/^aria-[\-\w]+$/`. `x-init` matches none of
the three, so **DOMPurify strips Alpine directives by default.** Do not repeat
the claim that it does not — verified in `purify.ts:2284-2299`.

**The action is to check your sanitiser's shape**, not to distrust DOMPurify.
If it is a deny-list, add `x-*`, `@*` and `:*`. Use `x-ignore` on any region
that will hold untrusted HTML.

**Docs status: UNDOCUMENTED.** `x-html`'s own warning is clear
(`html.md:10-11`), but nothing describes the general case that any injected
`x-*` is executed.

---

## 3 · `x-html` assigns `innerHTML` and re-runs Alpine over the result

`x-html.js:12` — `el.innerHTML = value ?? ''`, then `initTree(el)` at `:15`. No
sanitisation. `<script>` inserted this way is inert per HTML5, but
`<img src=x onerror=…>` fires, and any `x-*` in the injected markup is compiled.

The CSP build removes the directive outright — it throws *"Using the x-html
directive is prohibited in the CSP build"*.

**Docs status: DOCUMENTED, clearly.** `html.md:10-11` — *"Only use on trusted
content and never on user-provided content."* **Not a finding.** Use `x-text`.

---

## 4 · `x-bind` on a URL applies no scheme filter

`bind.js:97-112` — a plain `setAttribute`. So `:href="userUrl"` with
`userUrl = "javascript:alert(1)"` produces a live `javascript:` URL.

**Docs status: UNDOCUMENTED.** Validate the scheme server-side, or test it in
the expression.

---

## 5 · Nothing in the browser is a control

State is an expando on the DOM node — `node._x_dataStack`, `scope.js:7` — and
the CDN build assigns `window.Alpine` (`builds/cdn.js:3`). Stores are one module
object, readable and writable with no guard (`store.js:4,10-14`).

From the console:

```js
Alpine.store('cart').total = 0
Alpine.$data($0).isAdmin = true
```

Both work. There is no API that hides Alpine state — a grep of the core for
`private|hidden|secret` returns nothing, and `installation.md:64` presents the
window global as a **feature** for devtools.

**So a role, a price, an entitlement or an id in `x-data` is a suggestion.** It
is also public: the whole initial state is in view-source and in every cache and
crawler copy.

**Docs status: DOCUMENTED BUT THE CONSEQUENCE IS NOT STATED.**
`alpine-store.md:60-66` documents external access and even shows
`Alpine.store('darkMode').toggle()` from outside. No page says a visitor can
rewrite any store, or that a store must not gate anything.

---

## 6 · Three specific things developers mistake for guarantees

**`x-model.number` does not guarantee a number.** `x-model.js:273-277` —
`safeParseNumber` returns `isNumeric(number) ? number : rawValue`. Input `"abc"`
stays the string `"abc"`. `model.md:378` says the modifier will *"force Alpine
to store the value as a JavaScript number"*. **The doc claim is stronger than
the code.**

`x-model` also exposes a direct bypass: `el._x_model.set(value)`
(`x-model.js:148-157`), with a source comment saying it exists to allow
programmatic override. It skips input events, so it skips any event-level check
a developer added.

**`$persist` is plain-text `localStorage`.** `persist/src/index.js:7` — the
default store; `:90` — `JSON.stringify`, no transform; `:21` — the key is
`` `_x_${path}` ``, the property path only. Readable by any script on the
origin, shared across pages, and it survives logout. It re-reads that storage
through an unguarded `JSON.parse` (`:76`), so a hand-edited value throws during
init and breaks the component. Never persist a token, a role or PII;
`.using(sessionStorage)` at least dies with the tab.

**A mask is presentation.** `@alpinejs/mask` reformats the displayed value
(`mask/src/index.js:102-129`) and constrains nothing that reaches the server.

---

## 7 · `x-teleport` moves content out of its form

`x-teleport.js:13` clones the template's children; `:75-84` resolves the target
with `document.querySelector`; `:36-47` relocates it; `:53` re-inits Alpine
there.

A control authored inside `<template x-teleport="body">` ends up outside the
`<form>`, so **it is no longer submitted** — DOM ancestry decides form
association. Developers hit this building modals to escape a stacking context.

The expression is a **selector**, not compiled code, so a server-interpolated
target is a destination-redirect, not code execution.

**The "escapes a CSP nonce scope" idea is wrong** — nonces validate scripts at
parse time and are not scoped by DOM subtree. Checked, and there is no such
path.

**Docs status: DOCUMENTED BUT THE CONSEQUENCE IS NOT STATED.**
`teleport.md:10-19` describes the move and says nothing about form association.

---

## 8 · Verified SAFE, so nobody re-investigates

**`x-text`.** `x-text.js:10` — `textContent`. Markup in the value becomes
literal text. Its **expression** is still Seam B.

**`x-ignore`.** `x-ignore.js:5-8` sets a flag and nothing else. It inserts
nothing and is a mitigation, not a surface.

**`wire:navigate`.** Same-origin is enforced three times, and the one that
matters is **after** the fetch: a same-origin URL that redirects off-origin is
re-checked against the final URL, the fetched body is discarded, and the browser
navigates natively. The source comment says so outright: *"The request may have
been redirected off to another origin. We can't swap that page into this
document."* Cross-origin HTML is never parsed or swapped.

**`Alpine.morph`.** Parses script-inert via `<template>.innerHTML`
(`morph.js:467-471`) and `insertAdjacentHTML` (`:43-48`). No `eval`, no
`new Function`, no `createContextualFragment`. It does not run `<script>`.
It also does not sanitise, so `<img onerror>` in a string you pass it still
fires once live — do not morph untrusted HTML.

**Query-string tracking** is opt-in per property and explicitly blocks
`__proto__`, `constructor` and `prototype`, building into `Object.create(null)`
with a comment naming the pollution risk.

**`$wire`.** The client is deliberately unprivileged — the proxy will send any
method name you type. Every gate is on the server: an HMAC checksum over the
snapshot, a public-method allow-list, a public-property allow-list, `#[Locked]`,
payload caps, and a failure rate-limit. See the `livewire-security` skill.

**`x-trap`.** Focus management for keyboard users, built on `focus-trap`, with
`allowOutsideClick: true` (`focus/src/index.js:105-109`). Focus leaves on a
mouse click, siblings stay in the DOM and stay script-reachable. Never a
security boundary.

---

## 9 · The CSP build, and what it is not

Default Alpine needs `'unsafe-eval'`, which weakens CSP for the **whole page**,
not only Alpine — any string reaching `eval` or `Function` anywhere then runs.

The CSP build replaces the evaluator with a tokenizer, parser and interpreter
that never construct a function from a string (`csp/src/parser.js`, whole file —
no `Function`, no `eval`). It blocks `constructor`, `prototype`, `__proto__`,
`insertAdjacentHTML` and `setAttribute*` (`parser.js:911-923`), captures every
value on `globalThis` at load and refuses any expression resolving to one
(`:4-9, 942-944`), and removes `x-html`.

It is a strict **subset**: no arrow functions, no template literals, no spread,
no destructuring. Anything unrecognised throws.

**Treat it as blast-radius reduction, not a proven sandbox.** Its boundary is a
blacklist plus a global-identity set, and it caches cleared values in a
`WeakMap` without re-checking (`parser.js:934-946`). Completeness is unverified.

**In Livewire, do not install it** — set `'csp_safe' => true`.

---

## A short checklist

- [ ] No server value is interpolated into an `x-*` expression. `@js()` or
      `data-*` instead.
- [ ] Nothing in `x-data` is relied on for authorization, price or identity.
- [ ] `x-html` is used only on server-trusted HTML, or replaced by `x-text`.
- [ ] The HTML sanitiser is an allow-list — or it strips `x-*`, `@*` and `:*`.
- [ ] `$persist` holds no credential and no PII.
- [ ] Every bound URL attribute has its scheme validated server-side.
- [ ] No teleported `<template>` contains a control the form needs.
- [ ] No client-side modifier (`.number`, a mask, `maxlength`) is treated as
      validation.
