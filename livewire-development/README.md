# livewire-development

An [Agent Skill](https://agentskills.io/what-are-skills) for **Laravel Livewire v4** —
written from all 98 files of the official documentation, with recipes that are
**executed against a real Livewire install** rather than only transcribed.

**This is the entry point for the whole stack.** Livewire bundles Alpine, so real
work touches both — `bash bin/stack.sh` locates the paired `alpinejs-development`
skill and prints both file maps, so one invocation covers Livewire *and* Alpine.

---

## Why it exists

Livewire v4 changed its defaults, and most model training data is v2 or v3. An
assistant working from memory writes code that no longer runs. The skill opens
with a twelve-row correction table — single-file components are now the default,
`Route::livewire()` replaces `Route::get()`, `wire:model.blur` changed meaning,
`wire:transition` is the View Transitions API, and only Volt's *class-based* half
moved into core.

---

## Layout

```
SKILL.md                    always loaded — preflight, corrections, mental model, routing
references/                 16 files, 8,315 lines
bin/                        seven scripts the agent RUNS
tests/                      the verification harness and eval baseline
```

### references/

| File | Covers |
|---|---|
| `recipes.md` | Twelve complete components, all executed |
| `troubleshooting.md` | Symptom → cause → fix, the three worst bugs in depth |
| `version-guide.md` | Detecting the version; every v3 difference; what does not exist before v4 |
| `directives.md` | Every `wire:` directive and modifier |
| `attributes.md` | Every PHP attribute and parameter |
| `components.md` | Formats, pages, layouts, namespaces, nesting, slots |
| `properties-actions.md` | Types, `wire:model`, actions, events, Echo, lifecycle hooks |
| `forms-validation.md` | Forms, validation, uploads, pagination, URL/session state |
| `islands-performance.md` | Islands, lazy/defer, `data-loading`, polling, navigate |
| `javascript.md` | `$wire`, interceptors, hooks, custom directives, scoped styles |
| `advanced.md` | Hydration, synthesizers, morphing, component hooks, middleware, CSP |
| `alpine.md` | Alpine **inside** Livewire |
| `testing.md` | Pest setup and every assertion |
| `reference.md` | Redirects, Blade directives, config, installation |
| `volt.md` | The Volt functional API and migrating off class-based Volt |
| `v3-to-v4.md` | The full upgrade guide |

### bin/

```bash
bash bin/detect.sh              # what does THIS project actually do?
bash bin/stack.sh               # load BOTH halves — this skill + Alpine
bash bin/scaffold.sh post.create   # create in the project's own conventions
python3 bin/review.py <file>    # 21 rules; exit code gates
bash bin/verify-recipes.sh      # run every recipe against a real install
bash bin/refresh.sh             # re-audit against current documentation
bash bin/eval.sh --compare      # score code quality objectively
```

**`stack.sh`** is what makes one invocation enough. Livewire bundles Alpine, so
real work touches both, but they are two skills. This locates the paired
`alpinejs-development` skill — in any layout, symlinks followed — and prints both
file maps with a table of which half answers which question. When Alpine is not
installed it says so and falls back to `references/alpine.md`, which covers the
integration but not the language.

**`detect.sh`** reports the Livewire version, the component format already on
disk, the emoji setting, namespaces, routing style, whether Boost is installed,
whether Alpine is duplicated, and whether this skill is older than the project's
Livewire. Read-only. **Run it first** — its answers outrank every default here.

**`scaffold.sh`** infers the format from what exists and from `config/livewire.php`,
and **refuses** `--sfc`/`--mfc`/namespaces on a v3 project instead of emitting
output that cannot work there.

**`review.py`** carries **21 rules** — 19 in the table plus two that need a
scanner rather than a pattern. It flags v3-isms, an unauthorized write, an
`#[Async]` action mutating state, a `@foreach` with no `wire:key`, a method that
overrides `Livewire\Component`, a template with more than one root element
(nesting-aware, not a regex), an unquoted Blade value inside JavaScript, a
duplicated Alpine. `--frontmatter` is a separate mode that validates a
`SKILL.md`'s own YAML.

It also **refuses a `.md` file**. Documentation holds many components, so a
whole-file rule compares across component boundaries — pointed at `recipes.md`,
the multi-root scanner counted roots from twelve different templates and reported
a defect that was not there. Extract first (`tests/extract-recipes.py`), then
review the real files. `--force-md` overrides and says its findings are not
trustworthy.

---

## Verified, not asserted

| Check | Result |
|---|---|
| `bin/verify-recipes.sh` | **14 tests, 54 assertions** — all pass on livewire v4.4.2 |
| `bin/review.py --self-test` | **53/53 cases**, covering all 21 rules |
| `review.py` on the twelve recipes | **0 findings** |
| `review.py` on deliberately v3-style code | **9 errors** |
| `bin/refresh.sh` | **CLEAN** — nothing documented is missing |
| `bin/eval.sh --compare` | v3 habits **46/100**, these recipes **100/100** |
| `bin/stack.sh` | resolves both skills in **all three layouts** |
| Independent check (Codex, evidence inline) | **12/12 supported, 0 contradicted** |

The recipes are rendered and exercised with `Livewire::test()` — no browser, no
dev server, under a second. That found two defects every text-level audit had
missed, because both fail at runtime: a `reset()` override that silently broke
`Livewire\Component::reset()`, and four blocks calling `Auth::user()` with no
facade import.

The self-tests earned their keep too. `review.py`'s caught three bugs in its own
rules — including one where the `//` in `https://` was parsed as a comment, so
the duplicated-Alpine check could never fire.

---

## Using it with Laravel Boost

Boost ships a skill with the **identical name**. Boost documents that a
project-level skill of that name overrides its built-in one, so both may exist.

**They are complementary — run both.** Boost knows your Livewire version and
reads your config; it is terse because it is paired with a live `search-docs`
index. This skill is the depth behind it.

| Question | Best source |
|---|---|
| "What changed in last week's release?" | Boost `search-docs` |
| "Every modifier of `wire:target`" | This skill |
| "Why did my morph put state on the wrong element?" | This skill |
| "A complete searchable, paginated table" | This skill |

If they disagree on a fact, **prefer the live docs** and treat this skill's
provenance date as the tiebreaker. `bin/detect.sh` warns when the project's
Livewire is newer than this skill's verification.

---

## Provenance

All 98 files of `docs/` on `livewire/livewire@4.x`, commit `81f35ea`. v3
differences read from the `3.x` branch. Signatures the docs omit
(`#[Authorize]`, `#[Transition]`, `renderIsland()`, `streamIsland()`) read from
package source and labelled where they appear.

**Audited clean and executed 2026-08-26, against livewire v4.4.2.**

Run `bash bin/refresh.sh` when Livewire moves.

---

## License

MIT. Content derived from the Livewire documentation, MIT licensed,
© Caleb Porzio and contributors.
