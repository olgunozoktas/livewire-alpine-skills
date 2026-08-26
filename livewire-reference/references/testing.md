# Testing Livewire components

**Pest is the recommended framework for Livewire 4.** PHPUnit works identically —
every helper below is the same, only the assertion syntax differs.

---

## Setup

```shell
composer remove phpunit/phpunit
composer require pestphp/pest --dev --with-all-dependencies
./vendor/bin/pest --init
```

### Tests that live beside view-based components

Single-file and multi-file component tests sit in `resources/views`, not `tests/`.
Two edits make Pest find them.

`tests/Pest.php`:
```php
pest()->extend(Tests\TestCase::class)
    // ...
    ->in('Feature', '../resources/views');
```

`phpunit.xml`:
```xml
<testsuite name="Components">
    <directory suffix=".test.php">resources/views</directory>
</testsuite>
```

Generate a component with its test:
```shell
php artisan make:livewire post.create --test
```

For MFC that writes `resources/views/components/post/create.test.php`. For
class-based it writes `tests/Feature/Livewire/Post/CreateTest.php`.

---

## The basics

```php
use Livewire\Livewire;

it('renders successfully', function () {
    Livewire::test('post.create')
        ->assertStatus(200);
});
```

**Smoke test that a page contains a component:**
```php
it('component exists on the page', function () {
    $this->get('/posts/create')
        ->assertSeeLivewire('post.create');
});
```

These cost nothing to maintain and catch catastrophic breakage. Write them.

**Set properties, call an action, assert the result:**
```php
it('can create a post', function () {
    expect(Post::count())->toBe(0);

    Livewire::test('post.create')
        ->set('title', 'My new post')
        ->set('content', 'Post content here')
        ->call('save');

    expect(Post::count())->toBe(1);
});
```

**Pass mount parameters as the second argument:**
```php
Livewire::test('post.edit', ['post' => $post])
    ->assertSet('title', 'Existing post title');
```

**Authenticate:**
```php
Livewire::actingAs($user)
    ->test('show-posts')
    ->assertViewHas('posts', fn ($posts) => count($posts) === 3);
```

---

## Validation, redirects, events

```php
it('title field is required', function () {
    Livewire::test('post.create')
        ->set('title', '')
        ->call('save')
        ->assertHasErrors('title');
});

it('title must be at least 3 characters', function () {
    Livewire::test('post.create')
        ->set('title', 'ab')
        ->call('save')
        ->assertHasErrors(['title' => ['min:3']]);
});

it('redirects after creating', function () {
    Livewire::test('post.create')
        ->set('title', 'New post')
        ->call('save')
        ->assertRedirect('/posts');
});

it('dispatches an event when a post is created', function () {
    Livewire::test('post.create')
        ->set('title', 'New post')
        ->call('save')
        ->assertDispatched('post-created');
});
```

**Event communication between two components:**
```php
it('updates the count when an event is dispatched', function () {
    $badge = Livewire::test('post-count-badge')->assertSee('0');

    Livewire::test('post.create')
        ->set('title', 'New post')
        ->call('save')
        ->assertDispatched('post-created');

    $badge->dispatch('post-created')->assertSee('1');
});
```

**Event parameters:**
```php
->assertDispatched('notify', message: 'Post deleted');

->assertDispatched('notify', function ($event, $params) {
    return ($params['message'] ?? '') === 'Post deleted';
});
```

**Authorization:**
```php
Livewire::actingAs($user)
    ->test('post.edit', ['post' => $post])
    ->set('title', 'Hacked!')
    ->call('save')
    ->assertForbidden();
```

**Server-evaluated JavaScript:**
```php
->assertJs("alert('Post saved!')");
->assertNoJs();
```

---

## Browser testing

Pest v4 ships browser testing on Playwright.

```shell
composer require pestphp/pest-plugin-browser --dev
npm install playwright@latest
npx playwright install
```

```php
it('can create a new post', function () {
    Livewire::visit('post.create')
        ->type('[wire\:model="title"]', 'My first post')
        ->type('[wire\:model="content"]', 'This is the content')
        ->press('Save')
        ->assertSee('Post created successfully');
});
```

Note the escaped colon in the selector: `[wire\:model="title"]`.

> Browser tests are slow. Use them for critical user flows and complex
> interactions. `Livewire::test()` covers most component behavior faster.

---

## Full method reference

### Setup

| Method | Effect |
|---|---|
| `Livewire::test('post.create')` | Test a component by name |
| `Livewire::test(UpdatePost::class, ['post' => $post])` | With `mount()` parameters |
| `Livewire::actingAs($user)` | Authenticate |
| `Livewire::withQueryParams(['search' => '…'])` | Simulate `?search=…` |
| `Livewire::withCookie('name', 'value')` | Set a cookie |
| `Livewire::withCookies(['color' => 'blue'])` | Set several |
| `Livewire::withHeaders(['X-Header' => 'value'])` | Custom headers |
| `Livewire::withoutLazyLoading()` | Render lazy components immediately |
| `Livewire::visit('post.create')` | Browser test (Pest v4) |

### Interaction

| Method | Effect |
|---|---|
| `set('title', '…')` | Set a property |
| `set(['title' => '…', 'content' => '…'])` | Set several |
| `toggle('sortAsc')` | Flip a boolean |
| `call('save')` | Call an action |
| `call('remove', $postId)` | With parameters |
| `refresh()` | Trigger a re-render |
| `dispatch('post-created')` | Dispatch an event at the component |
| `dispatch('post-created', postId: $post->id)` | With parameters |

### Assertions

| Method | Asserts |
|---|---|
| `assertSet('title', '…')` | Property equals |
| `assertNotSet('title', '…')` | Property does not equal |
| `assertCount('posts', 3)` | Property holds 3 items |
| `assertSee('…')` / `assertDontSee('…')` | Rendered text |
| `assertSeeHtml('<div>…</div>')` / `assertDontSeeHtml(…)` | Raw HTML |
| `assertSeeInOrder(['first', 'second'])` | Text order |
| `assertDispatched('post-created')` / `assertNotDispatched(…)` | Events |
| `assertHasErrors('title')` | Validation failed |
| `assertHasErrors(['title' => ['required', 'min:6']])` | Specific rules failed |
| `assertHasNoErrors('title')` | No errors for a property |
| `assertRedirect()` / `assertRedirect('/posts')` | Redirect happened |
| `assertRedirectToRoute('posts.index')` | Redirect to a named route |
| `assertNoRedirect()` | No redirect |
| `assertViewHas('posts')` | Data passed to the view |
| `assertViewHas('postCount', 3)` | With a value |
| `assertViewHas('posts', fn ($posts) => …)` | With a closure |
| `assertViewIs('livewire.show-posts')` | Which view rendered |
| `assertJs("alert('…')")` / `assertNoJs()` | Server-evaluated JS |
| `assertFileDownloaded()` / `assertFileDownloaded($filename)` | Download triggered |
| `assertNoFileDownloaded()` | No download triggered |
| `assertUnauthorized()` | 401 |
| `assertForbidden()` | 403 |
| `assertStatus(500)` | Any status |
| `assertSeeLivewire('post.create')` | On an HTTP response, not the component |

---

## PHPUnit

```php
<?php

namespace Tests\Feature\Livewire;

use Livewire\Livewire;
use App\Models\Post;
use Tests\TestCase;

class CreatePostTest extends TestCase
{
    public function test_can_create_post()
    {
        $this->assertEquals(0, Post::count());

        Livewire::test('post.create')
            ->set('title', 'My new post')
            ->set('content', 'Post content')
            ->call('save');

        $this->assertEquals(1, Post::count());
    }
}
```

---

## Conventions

- **Test files are always real classes/plain Pest files** — never anonymous
  component classes.
- **Test what a failure would tell you.** Property contracts, authorization,
  validation, and events are worth testing. "A component was renamed" is not.
- **Prefer `Livewire::test()` over browser tests** unless the behavior genuinely
  needs a browser.
- Use `withoutLazyLoading()` when testing a component that is normally lazy, so
  its real content renders.
