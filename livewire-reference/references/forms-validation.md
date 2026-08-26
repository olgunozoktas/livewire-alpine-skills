# Forms, validation, uploads, pagination, URL state

---

## A basic form

```php
<?php // resources/views/components/post/⚡create.blade.php

use Livewire\Attributes\Validate;
use Livewire\Component;
use App\Models\Post;

new class extends Component {
    #[Validate('required|min:5')]
    public $title = '';

    #[Validate('required|min:5')]
    public $content = '';

    public function save()
    {
        $this->validate();

        Post::create($this->only(['title', 'content']));

        session()->flash('status', 'Post created.');

        return $this->redirect('/posts');
    }
};
?>

<form wire:submit="save">
    <input type="text" wire:model="title">
    <div>@error('title') <span class="error">{{ $message }}</span> @enderror</div>

    <textarea wire:model="content"></textarea>
    <div>@error('content') <span class="error">{{ $message }}</span> @enderror</div>

    <button type="submit">Save</button>
</form>
```

---

## Validation

### `#[Validate]` on properties

```php
#[Validate('required|min:3')]
public $title = '';
```

Rules run **on every property update** as well as on `$this->validate()`. Still
call `$this->validate()` before persisting, so untouched properties are checked
too.

Parameters:

| Parameter | Type | Default | Effect |
|---|---|---|---|
| `$rule` | `mixed` | `null` | The rule(s) |
| `$attribute` | `?string` | `null` | Custom attribute name for messages |
| `$as` | `?string` | `null` | Friendly name in messages |
| `$message` | `mixed` | `null` | Custom message(s) |
| `$onUpdate` | `bool` | `true` | Run on property update |
| `$translate` | `bool` | `true` | Pass messages through `trans()` |

```php
#[Validate('required', as: 'date of birth')]
#[Validate('required', message: 'Please provide a post title')]
#[Validate('required|min:3', onUpdate: false)]
#[Validate('required', message: 'Please provide a title', translate: false)]
```

Different message per rule — use separate attributes:

```php
#[Validate('required', message: 'Please enter a title.')]
#[Validate('min:5', message: 'Your title is too short.')]
public $title = '';
```

Array syntax for a property and its children:

```php
#[Validate([
    'todos' => 'required',
    'todos.*' => ['required', 'min:3', new Uppercase],
])]
public $todos = [];
```

With messages and attributes:

```php
#[Validate([
    'titles' => 'required',
    'titles.*' => 'required|min:5',
], message: [
    'required' => 'The :attribute is missing.',
    'titles.required' => 'The :attribute are missing.',
    'min' => 'The :attribute is too short.',
], attribute: [
    'titles.*' => 'title',
])]
public $titles = [];
```

> **PHP attributes cannot hold runtime objects.** `Rule::unique(...)`,
> `Rule::password()` and similar need a `rules()` method.

### The `rules()` method

```php
protected function rules()
{
    return [
        'title' => ['required', Rule::unique('posts')->ignore($this->post)],
        'content' => 'required|min:5',
    ];
}

protected function messages()
{
    return ['content.required' => 'The :attribute are missing.'];
}

protected function validationAttributes()
{
    return ['content' => 'description'];
}
```

> `rules()` runs **only** on `$this->validate()` — not on property updates. To get
> real-time validation as well, add a bare `#[Validate]` (no arguments) to the
> property. It tells Livewire to run that property's `rules()` entry on update.

> Do not name a property or method `rules`, `messages`, `validationAttributes`, or
> `validationCustomValues` for anything else — they collide with Livewire.

### Inline rules

```php
$validated = $this->validate([
    'title' => 'required|min:3',
    'content' => 'required|min:3',
]);
```

### Real-time validation

No backend work beyond `#[Validate]`. Just make the input send updates:

```blade
<input type="text" wire:model.live.blur="title">
<div>@error('title') <span class="error">{{ $message }}</span> @enderror</div>
```

Each request validates before assigning. On failure the property is not updated
and the message renders.

### Manual error control

| Method | Effect |
|---|---|
| `$this->addError($key, $message)` | Add a message to the bag |
| `$this->resetValidation($key?)` | Clear one key, or all |
| `$this->getErrorBag()` | The underlying Laravel error bag |

Inside a **form object**, `addError()` keys are auto-prefixed with the form's
property name on the parent (`$data` → `data.key`).

### Accessing the validator

```php
public function boot()
{
    $this->withValidator(function ($validator) {
        $validator->after(function ($validator) {
            if (str($this->title)->startsWith('"')) {
                $validator->errors()->add('title', 'Titles cannot start with quotations');
            }
        });
    });
}
```

### Custom validators

Any `ValidationException` thrown inside a component is caught and surfaced to the
view, so `Validator::make(...)->validate()` works unchanged.

### Errors in JavaScript — `$errors`

```blade
<div wire:show="$errors.has('email')">
    <span wire:text="$errors.first('email')"></span>
</div>
```

| Method | Returns |
|---|---|
| `$errors.has('field')` | bool |
| `$errors.missing('field')` | bool |
| `$errors.first('field')` | first message |
| `$errors.get('field')` | all messages for a field |
| `$errors.all()` | all errors |
| `$errors.clear()` / `$errors.clear('field')` | clears |

In Alpine, reach it as `$wire.$errors`.

### Deprecated `#[Rule]`

`#[Rule]` was renamed to `#[Validate]` because it collided with Laravel's `Rule`
objects. Both work; use `#[Validate]`.

---

## Form objects

```shell
php artisan livewire:form PostForm     # app/Livewire/Forms/PostForm.php
```

Form objects are **always real classes** — never anonymous classes, even in a
single-file component.

```php
<?php

namespace App\Livewire\Forms;

use Livewire\Attributes\Validate;
use Livewire\Form;
use App\Models\Post;

class PostForm extends Form
{
    public ?Post $post;

    #[Validate('required|min:5')]
    public $title = '';

    #[Validate('required|min:5')]
    public $content = '';

    public function setPost(Post $post)
    {
        $this->post = $post;
        $this->title = $post->title;
        $this->content = $post->content;
    }

    public function store()
    {
        $this->validate();

        Post::create($this->only(['title', 'content']));

        $this->reset();
    }

    public function update()
    {
        $this->validate();

        $this->post->update($this->only(['title', 'content']));
    }
}
```

Use it:

```php
new class extends Component {
    public PostForm $form;

    public function mount(Post $post)
    {
        $this->form->setPost($post);
    }

    public function save()
    {
        $this->form->update();

        return $this->redirect('/posts');
    }
};
```

Template paths are prefixed with the property name:

```blade
<input type="text" wire:model="form.title">
<div>@error('form.title') <span class="error">{{ $message }}</span> @enderror</div>
```

Helpers on a form object: `all()`, `only([...])`, `except([...])`, `validate()`,
`reset()`, `pull()`.

> Computed properties are **not supported** on `Livewire\Form`.

---

## Live updates and network tuning

```blade
<input wire:model.live="title">                        {{-- every keystroke, 150ms debounce --}}
<input wire:model.live.debounce.150ms="title">         {{-- custom debounce --}}
<input wire:model.live.throttle.150ms="title">         {{-- fire every 150ms while typing --}}
<input wire:model.live.blur="title">                   {{-- on tab-away --}}
```

Debounce waits for a pause. Throttle fires on an interval regardless. Use throttle
for live search that should update during long typing.

### Real-time saving

```php
public function updated($name, $value)
{
    $this->post->update([$name => $value]);
}
```
```blade
<form wire:submit>
    <input wire:model.live.blur="title">
    <input wire:model.live.blur="content">
</form>
```

`#[Validate]` rules run before `updated()` fires, so an invalid value never
reaches the database.

### Dirty indicators

```blade
<input wire:model.live.blur="title" wire:dirty.class="border-yellow">

<input wire:model="title">
<div wire:dirty wire:target="title">Unsaved…</div>
```

`$dirty` is also an expression: `wire:show="$dirty"`, `$dirty('title')`,
`$dirty(['title', 'description'])`, and `$wire.$dirty()` in Alpine.

---

## Extracting form fields to Blade components

```blade
<!-- resources/views/components/input-text.blade.php -->
@props(['name'])

<input type="text" name="{{ $name }}" {{ $attributes }}>

<div>
    @error($name) <span class="error">{{ $message }}</span> @enderror
</div>
```
```blade
<x-input-text name="title" wire:model="title" />
```

`{{ $attributes }}` forwards `wire:model` and everything else onto the real input.

### Custom controls that accept `wire:model`

For a control with no native input, use Alpine's `x-modelable`:

```blade
<!-- resources/views/components/input-counter.blade.php -->
<div x-data="{ count: 0 }" x-modelable="count" {{ $attributes }}>
    <button x-on:click="count--">-</button>
    <span x-text="count"></span>
    <button x-on:click="count++">+</button>
</div>
```
```blade
<x-input-counter wire:model="quantity" />
<x-input-counter x-model="quantity" />   {{-- works in pure Alpine too --}}
```

---

## File uploads

Add the `WithFileUploads` trait, then use `wire:model` on a file input.

```php
use Livewire\Attributes\Validate;
use Livewire\WithFileUploads;
use Livewire\Component;

new class extends Component {
    use WithFileUploads;

    #[Validate('image|max:1024')]   // 1 MB
    public $photo;

    public function save()
    {
        $this->validate();

        $this->photo->store(path: 'photos');
    }
};
```
```blade
<form wire:submit="save">
    <input type="file" wire:model="photo">
    @error('photo') <span class="error">{{ $message }}</span> @enderror
    <button type="submit">Save photo</button>
</form>
```

> **`upload` is a reserved name.** A component using `WithFileUploads` cannot have
> a method or property called `upload`. Name the action `save`.

### What happens under the hood

1. Livewire requests a temporary signed upload URL from the component.
2. JavaScript uploads to that URL, into a temporary directory.
3. A final request sets the public property to the temporary file.
4. The property now holds a `TemporaryUploadedFile`, ready to validate or store.

### Storing

```php
$this->photo->store(path: 'photos');
$this->photo->store(path: 'photos', options: 's3');
$this->photo->storeAs(path: 'photos', name: 'avatar');
$this->photo->storeAs(path: 'photos', name: 'avatar', options: 's3');
$this->photo->storePublicly(path: 'photos', options: 's3');
$this->photo->storePubliclyAs(path: 'photos', name: 'avatar', options: 's3');
```

`$this->photo->getClientOriginalName()` returns the original filename.

### Multiple files

```php
#[Validate(['photos.*' => 'image|max:1024'])]
public $photos = [];
```
```blade
<input type="file" wire:model="photos" multiple>
@error('photos.*') <span class="error">{{ $message }}</span> @enderror
```

### Previews

```blade
@if ($photo)
    <img src="{{ $photo->temporaryUrl() }}">
@endif
```

`temporaryUrl()` only works for image MIME types, by design.

> Validation rules that inspect file contents fail when uploading directly to S3
> unless the object is publicly accessible.

### Configuration

```php
'temporary_file_upload' => [
    'disk' => env('LIVEWIRE_TEMPORARY_FILE_UPLOAD_DISK'),  // default: 'default'
    'rules' => null,          // default: ['required', 'file', 'max:12288']  (12 MB)
    'directory' => null,      // default: 'livewire-tmp'
    'middleware' => null,     // default: 'throttle:60,1'
    'preview_mimes' => ['png', 'gif', 'bmp', 'svg', 'wav', 'mp4', 'mov', 'avi',
                        'wmv', 'mp3', 'm4a', 'jpg', 'jpeg', 'mpga', 'webp', 'wma'],
    'max_upload_time' => 5,   // minutes before an upload is invalidated
    'cleanup' => true,        // purge temp uploads older than 24h
],
```

### Progress indicators

Every upload dispatches events on the `<input>` element:

| Event | Fires |
|---|---|
| `livewire-upload-start` | Upload begins |
| `livewire-upload-finish` | Upload succeeded |
| `livewire-upload-cancel` | Upload cancelled early |
| `livewire-upload-error` | Upload failed |
| `livewire-upload-progress` | Progress; percentage in `$event.detail.progress` |

```blade
<div
    x-data="{ uploading: false, progress: 0 }"
    x-on:livewire-upload-start="uploading = true"
    x-on:livewire-upload-finish="uploading = false"
    x-on:livewire-upload-cancel="uploading = false"
    x-on:livewire-upload-error="uploading = false"
    x-on:livewire-upload-progress="progress = $event.detail.progress"
>
    <input type="file" wire:model="photo">

    <div x-show="uploading">
        <progress max="100" x-bind:value="progress"></progress>
    </div>
</div>
```

Simple loading state works too:

```blade
<input type="file" wire:model="photo">
<div wire:loading wire:target="photo">Uploading…</div>
<div class="not-data-loading:hidden">Uploading…</div>
```

### Cancelling

```blade
<button type="button" wire:click="$cancelUpload('photo')">Cancel Upload</button>
<button type="button" x-on:click="$wire.cancelUpload('photo')">Cancel Upload</button>
```

The request aborts and the file input clears, so the user can try another file.

### JavaScript upload API

For third-party upload libraries that need more control than a file input:

```blade
<script>
    let file = $wire.el.querySelector('input[type="file"]').files[0]

    $wire.upload('photo', file,
        (uploadedFilename) => { /* success */ },
        () => { /* error */ },
        (event) => { event.detail.progress /* 1–100 */ },
        () => { /* cancelled */ },
    )

    $wire.uploadMultiple('photos', [file], success, error, progress, cancelled)
    $wire.removeUpload('photos', uploadedFilename, success)
    $wire.cancelUpload('photos')
</script>
```

### Uploading straight to S3

By default every upload passes through your application server into
`livewire-tmp/` on the default disk — even when the final destination is S3.

To bypass the app server entirely:

```env
LIVEWIRE_TEMPORARY_FILE_UPLOAD_DISK=s3
```

Then configure lifecycle cleanup once, from the environment using that bucket:

```shell
php artisan livewire:configure-s3-upload-cleanup
```

S3 will now purge temporary files older than 24 hours. Without S3, Livewire
handles cleanup itself and the command is unnecessary.

With S3 configured, `temporaryUrl()` returns a signed S3 URL, so previews do not
load through your server.

### Testing uploads

```php
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;

it('can upload a photo', function () {
    Storage::fake('avatars');

    $file = UploadedFile::fake()->image('avatar.png');

    Livewire::test('upload-photo')
        ->set('photo', $file)
        ->call('upload', 'uploaded-avatar.png');

    Storage::disk('avatars')->assertExists('uploaded-avatar.png');
});
```

---

## Pagination

```php
use Livewire\WithPagination;

new class extends Component {
    use WithPagination;

    #[Computed]
    public function posts()
    {
        return Post::paginate(10);
    }
};
```
```blade
<div>
    @foreach ($this->posts as $post)
        <div wire:key="{{ $post->id }}">{{ $post->title }}</div>
    @endforeach

    {{ $this->posts->links() }}
</div>
```

The trait is required. The current page is tracked in the query string as `?page=2`.

**Disable query-string tracking:**
```php
use Livewire\WithPagination;
use Livewire\WithoutUrlPagination;

class ShowPosts extends Component
{
    use WithPagination, WithoutUrlPagination;
}
```

**Scroll behavior:**
```blade
{{ $posts->links(data: ['scrollTo' => false]) }}
{{ $posts->links(data: ['scrollTo' => '#paginated-posts']) }}
```

### Page navigation methods

| Method | Effect |
|---|---|
| `$this->setPage($page)` | Jump to a page number |
| `$this->resetPage()` | Back to page 1 |
| `$this->nextPage()` | Forward one |
| `$this->previousPage()` | Back one |

Reset the page whenever a filter or sort changes, or the user stays on page 5 of
a result set that now has two pages:

```php
public function search()
{
    $this->resetPage();
}
```

### Multiple paginators on one page

Both Laravel and Livewire track the page in `?page=`, so two paginators collide.
Name the second one:

```php
#[Computed]
public function invoices()
{
    return Invoice::paginate(10, pageName: 'invoices-page');
}
```

URL becomes `?page=2&invoices-page=2`.

Every navigation method then needs the name too:

```php
$this->setPage(2, pageName: 'invoices-page');
$this->resetPage(pageName: 'invoices-page');
$this->nextPage(pageName: 'invoices-page');
$this->previousPage(pageName: 'invoices-page');
```

### Page update hooks

```php
public function updatingPage($page) { }   // before
public function updatedPage($page)  { }   // after
```

For a **named** paginator, name the hook after it:

```php
public function updatingInvoicesPage($page) { }
```

Or handle every paginator generically, receiving the name as a second argument:

```php
public function updatingPaginators($page, $pageName) { }
public function updatedPaginators($page, $pageName) { }
```

---

## URL query state — `#[Url]`

```php
use Livewire\Attributes\Url;

#[Url]
public $search = '';
```

The property reads its initial value from the query string on load, and writes
back on change: `https://example.com/users?search=bob`.

| Parameter | Type | Default | Effect |
|---|---|---|---|
| `$as` | `?string` | `null` | Alias the query parameter (`?q=` instead of `?search=`) |
| `$history` | `bool` | `false` | Push to browser history so Back works |
| `$keep` | `bool` | `false` | Keep the parameter when navigating away |
| `$except` | `mixed` | `null` | Value(s) to omit from the URL |
| `$nullable` | `mixed` | `null` | Value to use when the parameter is missing |

**Nullable handling.** By default `?search=` becomes `''`. A nullable type-hint
makes it `null` instead, in both directions:

```php
#[Url]
public ?string $search;
```

---

## Session state — `#[Session]`

Persists a value across page refreshes without putting it in the URL.

```php
use Livewire\Attributes\Session;

#[Session]
public $search = '';

#[Session(key: 'custom-key')]
public $filter = '';
```

Choose `#[Session]` over `#[Url]` when the value is user-specific and should not
be shareable or bookmarkable.
