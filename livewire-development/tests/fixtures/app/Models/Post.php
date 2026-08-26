<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Post extends Model
{
    use HasFactory;

    protected $guarded = [];

    public function user() { return $this->belongsTo(User::class); }

    public function likedBy(?User $user): bool { return false; }
    public function toggleLike(?User $user): void { $this->increment('likes_count'); }
}
