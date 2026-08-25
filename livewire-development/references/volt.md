# Volt — the functional API

> **Volt is optional in Livewire v4.** Livewire ships single-file components in
> the box, and most applications do not need Volt. It exists for developers who
> prefer a functional, closure-based syntax over class-based components.
>
> **Default to core Livewire v4 SFCs.** Reach for Volt only when the team has
> chosen the functional style, or when maintaining an app already built on it.

Volt is a separate package that compiles a functional API down to ordinary
Livewire class components, linked to the template in the same file.

```php
<?php

use function Livewire\Volt\{state};

state(['count' => 0]);

$increment = fn () => $this->count++;

?>

<div>
    <h1>{{ $count }}</h1>
    <button wire:click="increment">+</button>
</div>
```

---

## What changed in v4 — read this first

Livewire v4 absorbed **Volt's class-based syntax** into core. It did **not**
absorb the functional API.

| Volt feature | Status in Livewire v4 |
|---|---|
| Class-based SFC (`new class extends Component`) | **In core.** Use `Livewire\Component` — drop Volt for this |
| Functional API (`state()`, `computed()`, …) | **Still Volt only.** Requires the package |

So an app using **class-based Volt** should migrate off Volt entirely; an app
using the **functional API** keeps the package.

### Migrating class-based Volt to core

```php
use Livewire\Volt\Component;   // before
use Livewire\Component;        // after
```
```php
Volt::route('/dashboard', 'dashboard');       // before
Route::livewire('/dashboard', 'dashboard');   // after
```
```php
use Livewire\Volt\Volt;   →   use Livewire\Livewire;
Volt::test('counter')     →   Livewire::test('counter')
```
```bash
rm app/Providers/VoltServiceProvider.php
composer remove livewire/volt
```
Remove `App\Providers\VoltServiceProvider::class` from `bootstrap/providers.php`.

Class-based Volt components then work unchanged — the syntax is identical.

---

## Installation

```bash
composer require livewire/volt
php artisan volt:install
```

`volt:install` publishes a service provider naming the mounted directories. By
default it mounts `resources/views/livewire` and `resources/views/pages`;
customize them in the provider's `boot()`.

```bash
php artisan make:volt counter
php artisan make:volt counter --test --pest
php artisan make:volt counter --class
```

Any `.blade.php` file inside a mounted directory is a Volt component.

---

## State

```php
use function Livewire\Volt\{state};

state(['count' => 0]);
```

Wrap anything that hits the database, the container, or a model in a **closure**,
so it resolves lazily rather than on every definition:

```php
state(['count' => fn () => User::count()]);
state(['user' => fn () => $user]);          // Folio route model binding
```

Declare without a value when it comes from props or `mount()`:

```php
state(['count']);
```

### Modifiers

```php
state(['id'])->locked();        // #[Locked]
state(['todos'])->reactive();   // #[Reactive]
state(['form'])->modelable();   // #[Modelable]
state(['page' => 1])->url(as: 'p', history: true, keep: true);   // #[Url]
```

### Props

`state()` declares accepted props. Pass a closure to intercept the incoming
value:

```php
state('users');
state(['count' => fn ($users) => count($users)]);
```

---

## Actions

A closure assigned to a variable becomes an action named after the variable:

```php
$increment = fn () => $this->count++;
```

`$this` is bound to the underlying component, so everything on a normal component
is reachable:

```php
$increment = function () {
    $this->dispatch('count-updated');
};
```

Parameters and container dependencies both work:

```php
$delete = function (PostRepository $posts) {
    $posts->delete($this->postId);
};
```

**Renderless:**

```php
use function Livewire\Volt\{action};

$incrementViewCount = action(fn () => $this->viewCount++)->renderless();
```

**Protected helpers** — every Volt action is public and client-callable unless
wrapped:

```php
use function Livewire\Volt\{protect};

$ensurePostCanBeDeleted = protect(function () {
    // not callable from the browser
});
```

This is the functional equivalent of marking a method `protected`, and it matters
for the same security reason.

---

## Computed properties

```php
use function Livewire\Volt\{computed};

$count = computed(function () {
    return User::count();
});
```
```blade
<div>{{ $this->count }}</div>
```

The variable name becomes the property name. Access it as `$this->count`, exactly
like `#[Computed]`.

```php
$count = computed(fn () => User::count())->persist();
$count = computed(fn () => User::count())->persist(seconds: 10);
```

---

## Lifecycle hooks

```php
use function Livewire\Volt\{boot, booted, mount, hydrate, dehydrate, updating, updated};

boot(fn () => /* ... */);
booted(fn () => /* ... */);
mount(fn () => /* ... */);
hydrate(fn () => /* ... */);
hydrate(['count' => fn () => /* ... */]);
dehydrate(fn () => /* ... */);
dehydrate(['count' => fn () => /* ... */]);
updating(['count' => fn () => /* ... */]);
updated(['count' => fn () => /* ... */]);
```

`mount()` receives the component's parameters, and resolves anything else from
the container:

```php
mount(function (UserCounter $counter, $users) {
    $counter->store('userCount', count($users));
});
```

---

## Validation

```php
use function Livewire\Volt\{rules};

rules(['name' => 'required|min:6', 'email' => 'required|email']);

$submit = function () {
    $this->validate();
};
```

Closure form, for runtime rules:

```php
rules(fn () => [
    'name'  => ['required', 'min:6'],
    'email' => ['required', 'email', 'not_in:'.Auth::user()->email],
]);
```

Messages and attributes chain on:

```php
rules(['name' => 'required|min:6', 'email' => 'required|email'])
    ->messages([
        'email.required' => 'The :attribute may not be empty.',
        'email.email'    => 'The :attribute format is invalid.',
    ])
    ->attributes([
        'email' => 'email address',
    ]);
```

---

## Forms

```php
use function Livewire\Volt\{form};
use App\Livewire\Forms\PostForm;

form(PostForm::class);

$save = function () {
    $this->form->store();
};
```

Custom property name:

```php
form(PostForm::class, 'postForm');
```

Form objects themselves stay ordinary classes extending `Livewire\Form`.

---

## Traits and interfaces

```php
use function Livewire\Volt\{uses, usesFileUploads, usesPagination};

uses([Sorting::class, WithSorting::class]);

usesFileUploads();                    // WithFileUploads
usesPagination();                     // WithPagination
usesPagination(theme: 'bootstrap');
```

File upload example:

```php
usesFileUploads();

state(['photo']);

$save = function () {
    $this->validate(['photo' => 'image|max:1024']);

    $this->photo->store('photos');
};
```

Pagination example:

```php
use function Livewire\Volt\{with, usesPagination};

usesPagination();

with(fn () => ['posts' => Post::paginate(10)]);
```

---

## Listeners

```php
use function Livewire\Volt\{on};

on(['eventName' => function () {
    //
}]);
```

Dynamic names, resolved from component data or the container:

```php
on(fn ($post) => [
    'event-'.$post->id => function () {
        //
    },
]);
```

Or dot notation against component data:

```php
on(['event-{post.id}' => function () {
    //
}]);
```

---

## Full-page components

```php
use Livewire\Volt\Volt;

Volt::route('/users', 'user-index');
```

```php
use function Livewire\Volt\{layout, title, state};

state('users');

layout('components.layouts.admin');

title('Users');

title(fn () => 'Users: ' . $this->users->count());   // dynamic
```

---

## Placeholders

```php
use function Livewire\Volt\{placeholder};

placeholder('<div>Loading...</div>');
```

---

## Class-based Volt components

Identical to a Livewire v4 SFC apart from the base class:

```blade
<?php

use Livewire\Volt\Component;

new class extends Component {
    public $count = 0;

    public function increment()
    {
        $this->count++;
    }
} ?>

<div>
    <h1>{{ $count }}</h1>
    <button wire:click="increment">+</button>
</div>
```

Class attributes go after `new`:

```blade
<?php

use Livewire\Attributes\{Layout, Title};
use Livewire\Volt\Component;

new
#[Layout('layouts.guest')]
#[Title('Login')]
class extends Component {
    public string $name = '';
```

**Extra view data** — `with()` rather than `render()`:

```php
new class extends Component {
    use WithPagination;

    public function with(): array
    {
        return ['posts' => Post::paginate(10)];
    }
}
```

**Modifying the view instance** — a `rendering()` method:

```php
public function rendering(View $view): void
{
    $view->title('Create Post');
}
```

> If you are writing class-based Volt in a v4 app, you are writing something core
> Livewire already does. Migrate — see the top of this file.

---

## Anonymous components — `@volt`

Turn part of an ordinary Blade view into a component without extracting a file:

```php
<?php

use function Livewire\Volt\{state};

state(['count' => 0]);

$increment = fn () => $this->count++;

?>

<x-app-layout>
    <x-slot name="header">
        Counter
    </x-slot>

    @volt('counter')
        <div>
            <h1>{{ $count }}</h1>
            <button wire:click="increment">+</button>
        </div>
    @endvolt
</x-app-layout>
```

View data passes straight through. Declaring the name is enough — Volt hydrates
the default from the proxied view data:

```php
Route::get('/counter', fn () => view('users.counter', [
    'count' => User::count(),
]));
```
```php
state('count');   // seeded from the view data
```

---

## Testing

```php
use Livewire\Volt\Volt;

it('increments the counter', function () {
    Volt::test('counter')
        ->assertSee('0')
        ->call('increment')
        ->assertSee('1');
});

Volt::test('users.stats');            // dot notation for nested
```

Everything in the standard Livewire testing API works.

For a page containing an anonymous `@volt` component:

```php
$this->get('/users')->assertSeeVolt('stats');
```
