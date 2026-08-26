# Recipes — complete, working components

Each one is a whole component, not a fragment. All are v4 single-file
components; convert paths and format to match the project (see the top of
`SKILL.md`).

> **These are executed, not just written.** `bash bin/verify-recipes.sh`
> scaffolds a throwaway Laravel + Livewire 4 app, extracts every recipe below
> into a real component file, lints it, then renders it and exercises its
> actions with `Livewire::test()`. Last run: **14 tests, 54 assertions, all
> passing on livewire v4.4.2.** If you edit a recipe, re-run it.

---


## Fast idioms

Short patterns, moved here from `SKILL.md` so the entry point stays small.
The complete components follow below.

**Page component with a route.**
```php
Route::livewire('/posts/{post}', 'pages::post.show');
```
```php
<?php // resources/views/pages/post/⚡show.blade.php
use Livewire\Component;
use App\Models\Post;

new class extends Component {
    public Post $post;   // route model binding, no mount() needed
};
```

**Expensive query.** Never a public property — a `#[Computed]` method.
```php
#[Computed]
public function posts()
{
    return Auth::user()->posts()->latest()->get();
}
```
```blade
@foreach ($this->posts as $post)
    <div wire:key="{{ $post->id }}">{{ $post->title }}</div>
@endforeach
```
Memoized for one request only. `unset($this->posts)` busts it after a write.

**Search that survives a refresh.**
```php
#[Url]
public $search = '';
```
```blade
<input wire:model.live.debounce.250ms="search">
```

**Loading state, the v4 way.** Every element that triggers a request gets
`data-loading` automatically — no `wire:target` needed.
```blade
<button wire:click="save" class="data-loading:opacity-50">
    <span class="in-data-loading:hidden">Save</span>
    <span class="not-in-data-loading:hidden">Saving…</span>
</button>
```

**Defer an expensive region without a child component.**
```blade
@island(lazy: true)
    @placeholder
        <div class="animate-pulse h-32 bg-gray-200 rounded"></div>
    @endplaceholder

    <div>Revenue: {{ $this->revenue }}</div>
@endisland
```

**Fire-and-forget tracking.** `#[Async]` runs in parallel instead of queueing.
```php
#[Async]
public function trackClick() { Analytics::track(/* … */); }
```
Never mutate rendered state in an async action — parallel requests race and lose
updates.

---

---

## 1. CRUD create form with validation

```php
<?php // resources/views/components/post/⚡create.blade.php

use Illuminate\Support\Facades\Auth;
use Livewire\Attributes\Validate;
use Livewire\Component;
use App\Models\Post;

new class extends Component {
    #[Validate('required|min:5|max:255')]
    public string $title = '';

    #[Validate('required|min:10')]
    public string $content = '';

    public function save()
    {
        $this->validate();

        Auth::user()->posts()->create($this->only(['title', 'content']));

        session()->flash('status', 'Post created.');

        return $this->redirect('/posts', navigate: true);
    }
};
?>

<form wire:submit="save" class="space-y-4">
    <div>
        <input type="text" wire:model.live.blur="title" class="w-full">
        @error('title') <span class="text-red-600 text-sm">{{ $message }}</span> @enderror
    </div>

    <div>
        <textarea wire:model.live.blur="content" rows="8" class="w-full"></textarea>
        @error('content') <span class="text-red-600 text-sm">{{ $message }}</span> @enderror
    </div>

    <button type="submit" class="data-loading:opacity-50">
        <span class="in-data-loading:hidden">Save Post</span>
        <span class="not-in-data-loading:hidden">Saving…</span>
    </button>
</form>
```

`.live.blur` gives real-time validation on tab-away without a request per
keystroke. `data-loading` handles the button state with no `wire:target`.

---

## 2. Edit form, authorized

```php
<?php // resources/views/components/post/⚡edit.blade.php

use Livewire\Attributes\Validate;
use Livewire\Attributes\Authorize;
use Livewire\Component;
use App\Models\Post;

new class extends Component {
    public Post $post;          // model property — key is locked automatically

    #[Validate('required|min:5|max:255')]
    public string $title = '';

    #[Validate('required|min:10')]
    public string $content = '';

    public function mount(Post $post)
    {
        $this->authorize('update', $post);

        $this->post = $post;

        $this->fill($post->only('title', 'content'));
    }

    #[Authorize('update', 'post')]
    public function save()
    {
        $this->validate();

        $this->post->update($this->only(['title', 'content']));

        session()->flash('status', 'Post updated.');
    }
};
?>

<form wire:submit="save">
    <input type="text" wire:model="title">
    @error('title') <span>{{ $message }}</span> @enderror

    <textarea wire:model="content"></textarea>
    @error('content') <span>{{ $message }}</span> @enderror

    <button type="submit">Update</button>

    <div wire:dirty>Unsaved changes…</div>
</form>
```

Authorized **twice** on purpose: `mount()` stops the page loading, `#[Authorize]`
stops the action being called directly from DevTools.

---

## 3. Search + filter + sort + paginate

The most-requested Livewire screen.

```php
<?php // resources/views/components/post/⚡index.blade.php

use Livewire\Attributes\Computed;
use Livewire\Attributes\Url;
use Livewire\WithPagination;
use Livewire\Component;
use App\Models\Post;

new class extends Component {
    use WithPagination;

    #[Url(as: 'q', except: '')]
    public string $search = '';

    #[Url]
    public string $status = 'all';

    #[Url]
    public string $sortBy = 'created_at';

    #[Url]
    public string $sortDirection = 'desc';

    // Reset to page 1 whenever a filter changes, or the user sits on
    // page 5 of a result set that now has two pages.
    public function updatedSearch() { $this->resetPage(); }
    public function updatedStatus() { $this->resetPage(); }

    public function sort($column)
    {
        if ($this->sortBy === $column) {
            $this->sortDirection = $this->sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            $this->sortBy = $column;
            $this->sortDirection = 'asc';
        }

        $this->resetPage();
    }

    #[Computed]
    public function posts()
    {
        return Post::query()
            ->when($this->search, fn ($q) => $q->where('title', 'like', "%{$this->search}%"))
            ->when($this->status !== 'all', fn ($q) => $q->where('status', $this->status))
            ->orderBy($this->sortBy, $this->sortDirection)
            ->paginate(15);
    }
};
?>

<div>
    <input type="search" wire:model.live.debounce.300ms="search" placeholder="Search posts…">

    <select wire:model.live="status">
        <option value="all">All</option>
        <option value="draft">Draft</option>
        <option value="published">Published</option>
    </select>

    <table>
        <thead>
            <tr>
                <th><button wire:click="sort('title')">Title</button></th>
                <th><button wire:click="sort('created_at')">Date</button></th>
            </tr>
        </thead>
        <tbody class="data-loading:opacity-50">
            @foreach ($this->posts as $post)
                <tr wire:key="post-{{ $post->id }}">
                    <td>{{ $post->title }}</td>
                    <td>{{ $post->created_at->diffForHumans() }}</td>
                </tr>
            @endforeach
        </tbody>
    </table>

    {{ $this->posts->links() }}
</div>
```

**Four things that make it correct:** a computed property (so the query runs
once and never becomes a stale serialized collection), `resetPage()` on every
filter change, `wire:key` on each row, and `debounce` on the search box.

---

## 4. Modal, accessible

Alpine handles the open/close with no round trip; Livewire handles the save.

```php
<?php // resources/views/components/post/⚡delete-modal.blade.php

use Livewire\Component;
use App\Models\Post;

new class extends Component {
    public Post $post;

    public function delete()
    {
        $this->authorize('delete', $this->post);

        $this->post->delete();

        $this->dispatch('post-deleted', postId: $this->post->id);
    }
};
?>

<div x-data="{ open: false }">
    <button @click="open = true">Delete</button>

    <template x-teleport="body">
        <div
            x-show="open"
            x-trap.inert.noscroll="open"
            @keyup.escape.window="open = false"
            @click.self="open = false"
            x-transition
            class="fixed inset-0 bg-black/50 grid place-items-center"
        >
            <div class="bg-white rounded p-6">
                <h2>Delete “{{ $post->title }}”?</h2>
                <p>This cannot be undone.</p>

                <button @click="open = false">Cancel</button>

                <button wire:click="delete" class="data-loading:opacity-50">
                    <span class="in-data-loading:hidden">Delete</span>
                    <span class="not-in-data-loading:hidden">Deleting…</span>
                </button>
            </div>
        </div>
    </template>
</div>
```

`x-teleport` escapes the parent's stacking context; `x-trap.inert.noscroll` is
what makes it accessible rather than merely visible.

---

## 5. File upload with preview and progress

```php
<?php // resources/views/components/⚡upload-avatar.blade.php

use Illuminate\Support\Facades\Auth;
use Livewire\Attributes\Validate;
use Livewire\WithFileUploads;
use Livewire\Component;

new class extends Component {
    use WithFileUploads;

    #[Validate('image|max:2048')]     // 2 MB
    public $photo;

    // NOTE: "upload" is a reserved name on a WithFileUploads component.
    public function save()
    {
        $this->validate();

        $path = $this->photo->store(path: 'avatars', options: 's3');

        Auth::user()->update(['avatar_path' => $path]);

        $this->reset('photo');

        session()->flash('status', 'Avatar updated.');
    }
};
?>

<form wire:submit="save"
    x-data="{ uploading: false, progress: 0 }"
    x-on:livewire-upload-start="uploading = true"
    x-on:livewire-upload-finish="uploading = false"
    x-on:livewire-upload-error="uploading = false"
    x-on:livewire-upload-cancel="uploading = false"
    x-on:livewire-upload-progress="progress = $event.detail.progress"
>
    <input type="file" wire:model="photo" accept="image/*">

    @error('photo') <span class="text-red-600">{{ $message }}</span> @enderror

    @if ($photo)
        <img src="{{ $photo->temporaryUrl() }}" class="w-32 h-32 object-cover rounded">
    @endif

    <div x-show="uploading">
        <progress max="100" x-bind:value="progress"></progress>
        <button type="button" wire:click="$cancelUpload('photo')">Cancel</button>
    </div>

    <button type="submit">Save</button>
</form>
```

`temporaryUrl()` only works for images — that restriction is deliberate.

---

## 6. Infinite scroll with an island

No child component, no props, no events.

```php
<?php // resources/views/components/⚡activity-feed.blade.php

use Livewire\Attributes\Computed;
use Livewire\Component;
use App\Models\Activity;

new class extends Component {
    public int $page = 1;

    public function loadMore()
    {
        $this->page++;
    }

    #[Computed]
    public function activities()
    {
        return Activity::latest()->forPage($this->page, 20)->get();
    }
};
?>

<div>
    @island(name: 'feed')
        @foreach ($this->activities as $activity)
            <div wire:key="activity-{{ $activity->id }}">{{ $activity->description }}</div>
        @endforeach
    @endisland

    <div wire:intersect="loadMore" wire:island.append="feed">
        <span class="not-data-loading:hidden">Loading more…</span>
    </div>
</div>
```

`wire:island.append` appends rather than replacing; `wire:intersect` fires when
the sentinel scrolls into view.

---

## 7. Multi-step wizard with directional transitions

```php
<?php // resources/views/components/⚡wizard.blade.php

use Livewire\Component;

new class extends Component {
    public int $step = 1;
    public array $data = [];

    public function goToStep(int $step)
    {
        $this->transition(type: $step > $this->step ? 'forward' : 'backward');

        $this->step = $step;
    }

    // NOTE: do NOT name this reset() — that would override
    // Livewire\Component::reset(), breaking $this->reset('field') everywhere
    // in this component. Same applies to validate(), fill(), pull(), only(),
    // all(), dispatch(), redirect(), render(), mount(), js() and stream().
    public function startOver()
    {
        $this->skipTransition();

        $this->step = 1;
        $this->data = [];
    }
};
?>

<div>
    {{-- x-wizard.* are your own Blade partials — create them, or inline the steps --}}
    <div wire:transition="content">
        @if ($step === 1) <x-wizard.account />
        @elseif ($step === 2) <x-wizard.profile />
        @else <x-wizard.confirm />
        @endif
    </div>

    <button wire:click="goToStep({{ $step - 1 }})" @disabled($step === 1)>Back</button>
    <button wire:click="goToStep({{ $step + 1 }})" @disabled($step === 3)>Next</button>
    <button wire:click="startOver">Start over</button>
</div>
```

```css
html:active-view-transition-type(forward) {
    &::view-transition-old(content) { animation: 300ms ease-out both slide-out-left; }
    &::view-transition-new(content) { animation: 300ms ease-in both slide-in-right; }
}
html:active-view-transition-type(backward) {
    &::view-transition-old(content) { animation: 300ms ease-out both slide-out-right; }
    &::view-transition-new(content) { animation: 300ms ease-in both slide-in-left; }
}
```

> Firefox supports view transitions but **not transition types**, so it falls
> back to an untyped transition. Nothing breaks.

---

## 8. Optimistic UI — instant feedback, background persist

```php
<?php // resources/views/components/post/⚡like-button.blade.php

use Illuminate\Support\Facades\Auth;
use Livewire\Attributes\Renderless;
use Livewire\Component;
use App\Models\Post;

new class extends Component {
    public Post $post;
    public int $likes = 0;
    public bool $liked = false;

    public function mount()
    {
        $this->likes = $this->post->likes_count;
        $this->liked = $this->post->likedBy(Auth::user());
    }

    #[Renderless]
    public function toggleLike()
    {
        $this->post->toggleLike(Auth::user());
    }
};
?>

<div>
    <button wire:click="$js.toggle">
        <span wire:text="liked ? '♥' : '♡'"></span>
        <span wire:text="likes"></span>
    </button>
</div>

<script>
    this.$js.toggle = () => {
        // instant, client-side
        $wire.liked = ! $wire.liked
        $wire.likes += $wire.liked ? 1 : -1

        // then persist, without re-rendering
        $wire.toggleLike()
    }
</script>
```

`wire:text` updates from client state with no round trip; `#[Renderless]` stops
the server response undoing the optimistic change.

---

## 9. Dependent selects

```php
<?php // resources/views/components/⚡location-picker.blade.php

use Livewire\Attributes\Computed;
use Livewire\Component;
use App\Models\{State, City};

new class extends Component {
    public ?int $stateId = null;
    public ?int $cityId = null;

    public function updatedStateId()
    {
        $this->cityId = null;         // clear the stale child selection
    }

    #[Computed]
    public function states()
    {
        return State::orderBy('name')->get();
    }

    #[Computed]
    public function cities()
    {
        return $this->stateId
            ? City::where('state_id', $this->stateId)->orderBy('name')->get()
            : collect();
    }
};
?>

<div>
    <select wire:model.live="stateId">
        <option value="">Select a state…</option>
        @foreach ($this->states as $state)
            <option value="{{ $state->id }}" wire:key="state-{{ $state->id }}">{{ $state->name }}</option>
        @endforeach
    </select>

    {{-- wire:key is REQUIRED here, or the select keeps the old options --}}
    <select wire:model.live="cityId" wire:key="cities-{{ $stateId }}">
        <option value="">Select a city…</option>
        @foreach ($this->cities as $city)
            <option value="{{ $city->id }}" wire:key="city-{{ $city->id }}">{{ $city->name }}</option>
        @endforeach
    </select>
</div>
```

The `wire:key` on the **second select**, keyed to the first's value, is the
whole trick. Without it the child select keeps stale options.

---

## 10. Real-time updates over Laravel Echo

```php
<?php // resources/views/components/⚡order-tracker.blade.php

use Livewire\Attributes\Computed;
use Livewire\Attributes\On;
use Livewire\Component;
use App\Models\Order;

new class extends Component {
    public Order $order;

    #[On('echo-private:orders.{order.id},OrderShipped')]
    public function onShipped($event)
    {
        unset($this->timeline);          // bust the computed memo

        $this->dispatch('notify', message: 'Your order has shipped.');
    }

    #[Computed]
    public function timeline()
    {
        return $this->order->events()->latest()->get();
    }
};
?>

<div>
    <h2>Order #{{ $order->reference }}</h2>

    @foreach ($this->timeline as $event)
        <div wire:key="event-{{ $event->id }}">{{ $event->description }}</div>
    @endforeach
</div>
```

`echo-private:` for a private channel. If the event class overrides
`broadcastAs()`, the listener needs a **leading dot** on the custom name —
`echo:orders,.order.shipped`. Omit it and the listener silently never fires.

---

## 11. Form object reused across create and edit

```php
<?php // app/Livewire/Forms/PostForm.php

namespace App\Livewire\Forms;

use Illuminate\Support\Facades\Auth;
use Livewire\Attributes\Validate;
use Livewire\Form;
use App\Models\Post;

class PostForm extends Form
{
    public ?Post $post = null;

    #[Validate('required|min:5|max:255')]
    public string $title = '';

    #[Validate('required|min:10')]
    public string $content = '';

    public function setPost(Post $post): void
    {
        $this->post = $post;
        $this->title = $post->title;
        $this->content = $post->content;
    }

    public function store(): Post
    {
        $this->validate();

        $post = Auth::user()->posts()->create($this->only(['title', 'content']));

        $this->reset();

        return $post;
    }

    public function update(): void
    {
        $this->validate();

        $this->post->update($this->only(['title', 'content']));
    }
}
```

```php
new class extends Component {
    public PostForm $form;

    public function mount(?Post $post = null)
    {
        if ($post?->exists) {
            $this->authorize('update', $post);
            $this->form->setPost($post);
        }
    }

    public function save()
    {
        $this->form->post ? $this->form->update() : $this->form->store();

        return $this->redirect('/posts', navigate: true);
    }
};
```

```blade
<input wire:model="form.title">
@error('form.title') <span>{{ $message }}</span> @enderror
```

Note the `form.` prefix in both the binding and the `@error` key.

---

## 12. Testing the search screen

```php
<?php // resources/views/components/post/index.test.php

use App\Models\{Post, User};
use Livewire\Livewire;

it('filters posts by search term', function () {
    Post::factory()->create(['title' => 'Laravel testing']);
    Post::factory()->create(['title' => 'Vue components']);

    Livewire::test('post.index')
        ->set('search', 'Laravel')
        ->assertSee('Laravel testing')
        ->assertDontSee('Vue components');
});

it('reads the search term from the query string', function () {
    Post::factory()->create(['title' => 'Laravel testing']);

    Livewire::withQueryParams(['q' => 'Laravel'])
        ->test('post.index')
        ->assertSet('search', 'Laravel')
        ->assertSee('Laravel testing');
});

it('resets to page one when the filter changes', function () {
    Post::factory()->count(40)->create();

    Livewire::test('post.index')
        ->call('setPage', 2)
        ->set('search', 'anything')
        ->assertSet('paginators.page', 1);
});

it('refuses to update another users post', function () {
    $post = Post::factory()->for(User::factory())->create();

    Livewire::actingAs(User::factory()->create())
        ->test('post.edit', ['post' => $post])
        ->set('title', 'Hacked')
        ->call('save')
        ->assertForbidden();
});
```

The last one is the test worth writing. "A component renders" tells you little;
"a stranger cannot edit this" is the assertion that catches a real defect.
