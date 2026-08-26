#!/usr/bin/env php
<?php

declare(strict_types=1);

/**
 * A static scan for Livewire performance costs.
 *
 * It reads source text. It needs no bootstrap, no database and no autoloader,
 * so it runs in CI and in a checkout without installed dependencies.
 *
 * It finds SHAPES that cost. It does not measure. Measurement needs a running
 * application, and `references/measuring.md` gives the recipe for that. A shape
 * this reports is a candidate, not a verdict: a model property on a component
 * that renders once per day costs nothing worth fixing.
 *
 * The exit code is the number of findings, so it can gate.
 */

const RULES = [
    'model-on-public-property' => 'A model or Eloquent collection on a public property. Livewire re-queries it on every request, through the WRITE connection.',
    'unbounded-public-array' => 'A public array with no #[Locked]. Every element travels to the browser and back on every request.',
    'live-binding-on-text' => 'wire:model.live on a text input sends one request per keystroke. Use .blur, .change, or .live.debounce.',
    'poll-without-interval' => 'wire:poll with no interval polls every 2 seconds, for every visitor, forever.',
    'computed-in-loop' => 'A computed property read inside a loop. It is memoized per request, so this is usually fine — check it is not a method call that queries.',
    'reactive-prop' => '#[Reactive] re-renders this child every time the parent renders. That is the cost it buys.',
];

/** @return list<array{0:string,1:int,2:string,3:string}> */
function findings(string $file, string $source): array
{
    $out = [];
    $isComponent = str_contains($source, 'extends Component')
        || str_contains($source, 'new class extends Component');
    $lines = explode("\n", $source);

    foreach ($lines as $i => $line) {
        $n = $i + 1;
        $above = ($i > 0 ? $lines[$i - 1] : '').($i > 1 ? $lines[$i - 2] : '');

        if ($isComponent && preg_match('/^\s*public\s+(\??[\w\\\\|]+)?\s*\$(\w+)/', $line, $m) === 1) {
            $type = trim((string) ($m[1] ?? ''), '?');
            $short = $type === '' ? '' : substr((string) strrchr('\\'.$type, '\\'), 1);
            $locked = str_contains($above, '#[Locked]');

            if (in_array($short, ['Model', 'Collection', 'EloquentCollection'], true)) {
                $out[] = [$file, $n, 'model-on-public-property', trim($line)];
            }

            if (! $locked && preg_match('/\barray\b/i', $type) === 1) {
                $out[] = [$file, $n, 'unbounded-public-array', trim($line)];
            }

            if (str_contains($above, '#[Reactive]')) {
                $out[] = [$file, $n, 'reactive-prop', trim($line)];
            }
        }

        // Blade-side costs.
        if (preg_match('/wire:model\.live(?!\.debounce)(?![\w.])/', $line) === 1
            && preg_match('/<(input|textarea)\b/i', $line.$above) === 1) {
            $out[] = [$file, $n, 'live-binding-on-text', trim($line)];
        }

        // `wire:poll` with no `.750ms` / `.5s` modifier.
        if (preg_match('/wire:poll(?![.\w])/', $line) === 1) {
            $out[] = [$file, $n, 'poll-without-interval', trim($line)];
        }
    }

    return $out;
}

function selfTest(): int
{
    $component = static fn (string $body): string => "<?php\n\nclass A extends Component\n{\n".$body."\n}\n";

    $cases = [
        ['model-on-public-property', true,  $component('    public Model $post;')],
        ['model-on-public-property', false, $component('    public string $title = \'\';')],
        ['unbounded-public-array',   true,  $component('    public array $rows = [];')],
        ['unbounded-public-array',   false, $component("    #[Locked]\n    public array \$rows = [];")],
        ['reactive-prop',            true,  $component("    #[Reactive]\n    public string \$filter = '';")],
        ['reactive-prop',            false, $component("    public string \$filter = '';")],
        // Blade. A debounced live binding is the FIX, so it must stay silent.
        ['live-binding-on-text',     true,  '<input type="text" wire:model.live="q">'],
        ['live-binding-on-text',     false, '<input type="text" wire:model.live.debounce.500ms="q">'],
        ['live-binding-on-text',     false, '<input type="text" wire:model.blur="q">'],
        // A select fires on change, not per keystroke, so it must stay silent.
        ['live-binding-on-text',     false, '<select wire:model.live="sort"></select>'],
        ['poll-without-interval',    true,  '<div wire:poll>'],
        ['poll-without-interval',    false, '<div wire:poll.30s>'],
        // Not a component: property rules stay silent.
        ['model-on-public-property', false, "<?php\n\nclass A\n{\n    public Model \$post;\n}\n"],
    ];

    $failed = 0;

    foreach ($cases as [$rule, $shouldFire, $source]) {
        $fired = false;

        foreach (findings('t.php', $source) as $f) {
            if ($f[2] === $rule) {
                $fired = true;
            }
        }

        if ($fired !== $shouldFire) {
            $failed++;
            printf("  FAIL  %-30s expected %s\n", $rule, $shouldFire ? 'to fire' : 'to stay silent');
        }
    }

    printf("scan-performance.php self-test — %d/%d checks passed\n", count($cases) - $failed, count($cases));

    return $failed === 0 ? 0 : 1;
}

$args = array_slice($argv, 1);

if (in_array('--self-test', $args, true)) {
    exit(selfTest());
}

$root = rtrim($args[0] ?? getcwd(), '/');

if (! is_dir($root)) {
    fwrite(STDERR, "Not a directory: {$root}\n");
    exit(2);
}

$all = [];

foreach ([$root.'/app', $root.'/resources/views', $root.'/packages'] as $dir) {
    if (! is_dir($dir)) {
        continue;
    }

    // Skip vendor and node_modules at any depth. A dependency's fixtures are
    // not this application's performance problem.
    $filter = new RecursiveCallbackFilterIterator(
        new RecursiveDirectoryIterator($dir, FilesystemIterator::SKIP_DOTS),
        static fn (SplFileInfo $e): bool => ! $e->isDir()
            || ! in_array($e->getFilename(), ['vendor', 'node_modules', '.git'], true),
    );

    foreach (new RecursiveIteratorIterator($filter) as $f) {
        if (! $f instanceof SplFileInfo || ! in_array($f->getExtension(), ['php'], true)) {
            continue;
        }

        $all = array_merge($all, findings(
            str_replace($root.'/', '', $f->getPathname()),
            (string) file_get_contents($f->getPathname()),
        ));
    }
}

foreach ($all as [$file, $line, $rule, $code]) {
    printf("%s:%d  [%s]\n      %s\n      %s\n\n", $file, $line, $rule, RULES[$rule], $code);
}

printf("%d finding(s)\n", count($all));

exit(count($all) === 0 ? 0 : 1);
