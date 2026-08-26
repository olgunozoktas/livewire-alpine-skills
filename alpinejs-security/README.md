# alpinejs-security

What a browser can do to an Alpine component, and which of your assumptions
about client-side state are wrong.

Part of [livewire-alpine-skills](../README.md). Install the whole family, or
copy this directory alone.

## The idea

Alpine has **no security documentation page**. Across its 56 doc pages,
security is mentioned six times: a CSP page, and one XSS warning on `x-html`
repeated twice.

The gap that matters is not `x-html` — that one is warned about clearly. It is
that **an Alpine attribute is a JavaScript context**:

```blade
<div x-data="{ name: '{{ $displayName }}' }">   {{-- BROKEN --}}
```

Blade escapes the value correctly. The browser then decodes the entity back
before Alpine reads the attribute, Alpine compiles it with `new Function`, and a
quote in the data closes the string literal:

```
attacker display name : '+alert(document.cookie)+'
what getAttribute sees: { name: ''+alert(document.cookie)+'' }
```

HTML-escaping defends an HTML context. This is a JavaScript context. Use
`@js()` or pass the value through `data-*`.

## What is here

| | |
|---|---|
| `SKILL.md` | the two seams, the rules, what is safe |
| `references/attack-surface.md` | nine items, each with `file:line`, the docs status, and the fix |
| `bin/review-security.py` | 7 rules over Blade and HTML. Exit code is the error count |
| `bin/verify-facts.py` | 11 statements checked against a real Alpine checkout |
| `bin/check-update.sh` | tells you when a newer release exists |

## Use it

```bash
python3 bin/review-security.py resources/views/**/*.blade.php
python3 bin/review-security.py --self-test          # 26 checks
python3 bin/verify-facts.py node_modules/alpinejs   # or an Alpine checkout
```

The checker is calibrated in both directions. `@js()`, `Js::from()`, `data-*`
with `$el.dataset`, and Blade's own `:prop="$var"` component bindings all stay
silent — that last one is the false positive that makes a checker unusable, and
it is handled by telling PHP apart from JavaScript.

## What it will not tell you

The interpolation rule flags a **pattern**. Whether it is exploitable today
depends on where the value comes from: a hard-coded loop constant is latent, a
user-supplied field is live. Fix it either way — the pattern becomes a hole the
day the source changes, and nothing will flag that day.

## The other half

This skill is the client side. For the server side of a Livewire app — the
snapshot, `#[Locked]`, the persistent-middleware gap — use
[`livewire-security`](../livewire-security/).
