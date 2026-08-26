<?php

namespace Tests\Feature;

use App\Models\{Post, User, Activity, State, City, Order};
use Illuminate\Foundation\Testing\RefreshDatabase;
use Livewire\Livewire;
use Tests\TestCase;

class RecipesTest extends TestCase
{
    use RefreshDatabase;

    /** Recipe 1 — CRUD create form */
    public function test_recipe_1_create_form(): void
    {
        $user = User::factory()->create();

        Livewire::actingAs($user)->test('post.create')
            ->assertStatus(200)
            ->set('title', 'x')                       // too short
            ->set('content', 'short')
            ->call('save')
            ->assertHasErrors(['title', 'content']);

        Livewire::actingAs($user)->test('post.create')
            ->set('title', 'A valid post title')
            ->set('content', 'Content that is definitely long enough.')
            ->call('save')
            ->assertHasNoErrors()
            ->assertRedirect('/posts');

        $this->assertSame(1, Post::count());
    }

    /** Recipe 2 — edit form, authorized */
    public function test_recipe_2_edit_form(): void
    {
        $owner = User::factory()->create();
        $post  = Post::factory()->for($owner)->create(['title' => 'Existing title here']);

        Livewire::actingAs($owner)->test('post.edit', ['post' => $post])
            ->assertStatus(200)
            ->assertSet('title', 'Existing title here')
            ->set('title', 'Updated title here')
            ->call('save')
            ->assertHasNoErrors();

        $this->assertSame('Updated title here', $post->fresh()->title);
    }

    public function test_recipe_2_refuses_a_stranger(): void
    {
        $post = Post::factory()->for(User::factory())->create();

        Livewire::actingAs(User::factory()->create())
            ->test('post.edit', ['post' => $post])
            ->assertForbidden();
    }

    /** Recipe 3 — search / filter / sort / paginate */
    public function test_recipe_3_search_table(): void
    {
        Post::factory()->create(['title' => 'Laravel testing', 'status' => 'published']);
        Post::factory()->create(['title' => 'Vue components', 'status' => 'draft']);

        Livewire::test('post.index')
            ->assertStatus(200)
            ->assertSee('Laravel testing')
            ->set('search', 'Laravel')
            ->assertSee('Laravel testing')
            ->assertDontSee('Vue components')
            ->set('search', '')
            ->set('status', 'draft')
            ->assertSee('Vue components')
            ->assertDontSee('Laravel testing')
            ->call('sort', 'title');
    }

    public function test_recipe_3_resets_page_on_filter_change(): void
    {
        Post::factory()->count(40)->create();

        Livewire::test('post.index')
            ->call('setPage', 2)
            ->assertSet('paginators.page', 2)
            ->set('search', 'anything')
            ->assertSet('paginators.page', 1);
    }

    public function test_recipe_3_reads_query_string(): void
    {
        Post::factory()->create(['title' => 'Laravel testing']);

        Livewire::withQueryParams(['q' => 'Laravel'])
            ->test('post.index')
            ->assertSet('search', 'Laravel')
            ->assertSee('Laravel testing');
    }

    /** Recipe 4 — modal */
    public function test_recipe_4_modal(): void
    {
        $owner = User::factory()->create();
        $post  = Post::factory()->for($owner)->create();

        Livewire::actingAs($owner)->test('post.delete-modal', ['post' => $post])
            ->assertStatus(200)
            ->call('delete')
            ->assertDispatched('post-deleted');

        $this->assertSame(0, Post::count());
    }

    /** Recipe 5 — upload */
    public function test_recipe_5_upload(): void
    {
        Livewire::actingAs(User::factory()->create())
            ->test('upload-avatar')
            ->assertStatus(200);
    }

    /** Recipe 6 — infinite scroll island */
    public function test_recipe_6_activity_feed(): void
    {
        Activity::factory()->count(25)->create();

        Livewire::test('activity-feed')
            ->assertStatus(200)
            ->assertSet('page', 1)
            ->call('loadMore')
            ->assertSet('page', 2);
    }

    /** Recipe 7 — wizard */
    public function test_recipe_7_wizard(): void
    {
        Livewire::test('wizard')
            ->assertStatus(200)
            ->assertSet('step', 1)
            ->call('goToStep', 2)
            ->assertSet('step', 2)
            ->call('goToStep', 1)
            ->assertSet('step', 1)
            ->call('startOver')
            ->assertSet('step', 1);
    }

    /** Recipe 8 — optimistic UI */
    public function test_recipe_8_like_button(): void
    {
        $post = Post::factory()->create(['likes_count' => 3]);

        Livewire::actingAs(User::factory()->create())
            ->test('post.like-button', ['post' => $post])
            ->assertStatus(200)
            ->assertSet('likes', 3)
            ->call('toggleLike');

        $this->assertSame(4, $post->fresh()->likes_count);
    }

    /** Recipe 9 — dependent selects */
    public function test_recipe_9_dependent_selects(): void
    {
        $a = State::factory()->create(['name' => 'Alpha']);
        $b = State::factory()->create(['name' => 'Beta']);
        City::factory()->create(['state_id' => $a->id, 'name' => 'Alphaville']);
        City::factory()->create(['state_id' => $b->id, 'name' => 'Betatown']);

        Livewire::test('location-picker')
            ->assertStatus(200)
            ->set('stateId', $a->id)
            ->assertSee('Alphaville')
            ->assertDontSee('Betatown')
            ->set('cityId', 1)
            ->set('stateId', $b->id)
            ->assertSet('cityId', null);      // updatedStateId must clear it
    }

    /** Recipe 10 — Echo listener component renders */
    public function test_recipe_10_order_tracker(): void
    {
        $order = Order::factory()->create(['reference' => 'ORD-123']);

        Livewire::test('order-tracker', ['order' => $order])
            ->assertStatus(200)
            ->assertSee('ORD-123');
    }

    /** Recipe 11 — form object */
    public function test_recipe_11_form_object(): void
    {
        $this->assertTrue(class_exists(\App\Livewire\Forms\PostForm::class));

        $r = new \ReflectionClass(\App\Livewire\Forms\PostForm::class);
        $this->assertTrue($r->isSubclassOf(\Livewire\Form::class));
        foreach (['store', 'update', 'setPost'] as $m) {
            $this->assertTrue($r->hasMethod($m), "PostForm::{$m}() missing");
        }
        foreach (['title', 'content', 'post'] as $prop) {
            $this->assertTrue($r->hasProperty($prop), "PostForm::\${$prop} missing");
        }
    }
}
