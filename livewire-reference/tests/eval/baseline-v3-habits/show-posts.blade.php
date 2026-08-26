<?php
use Livewire\Component;
use App\Models\Post;

new class extends Component {
    public $posts = [];
    public $postId;
    public $search = '';

    public function mount()
    {
        $this->posts = Post::all();
    }

    public function reset()
    {
        $this->search = '';
    }

    public function delete($id)
    {
        $post = Post::find($id);
        $post->delete();
    }
};
?>
<div>
    <input wire:model.defer="search">

    @foreach ($posts as $post)
        <div>
            {{ $post->title }}
            <button wire:click="delete({{ $post->id }})">Delete</button>
        </div>
    @endforeach

    <div wire:transition.opacity.duration.500ms>Fading</div>
    <livewire:post-stats>
</div>
