#!/usr/bin/env php
<?php

declare(strict_types=1);

/**
 * A static security scan of Livewire components.
 *
 * The scanner reads source text. It needs no bootstrap, no database and no
 * autoloader. It therefore runs in CI, in a hook, and in a checkout without
 * installed dependencies. A reflection tool cannot run in those places.
 *
 * This scanner is a first check. The boundary is the canary sweep in the skill.
 * This scanner finds the shapes that are visible in the source text.
 *
 * The exit code is the number of findings. The scanner can therefore gate a
 * build.
 */

const RULES = [
    'model-on-public-property' => 'A public property typed as an Eloquent model or collection publishes its class name and primary key into wire:snapshot.',
    'identity-named-public-property' => 'A public property named for a protected field is published into wire:snapshot and is writable by the browser.',
    'public-page-props' => 'A page-prop property must be private, or every page publishes its whole prop bag.',
    'unauthorized-mutator' => 'A public method that looks like it mutates a record, with no authorize/policy/gate/can call. Every public method is callable from the browser.',
];

/** Field names that are somebody's identity, whatever the type says. */
const PROTECTED_NAMES = [
    'email', 'payerEmail', 'payerName', 'payerCompany', 'customerEmail',
    'firstName', 'lastName', 'surname', 'fullName', 'phone', 'phoneNumber',
    'ssn', 'taxId', 'apiKey', 'secret', 'token', 'password', 'accessToken',
];

/** Types that publish a class name and a primary key. */
const MODEL_HINTS = ['Model', 'Collection', 'EloquentCollection'];

function findings(string $file, string $source): array
{
    $out = [];

    if (! preg_match('/\bextends\s+(?:\\\\?Livewire\\\\)?Component\b/', $source)
        && ! str_contains($source, 'new class extends Component')) {
        return $out;
    }

    $lines = explode("\n", $source);

    foreach ($lines as $i => $line) {
        $number = $i + 1;

        // A public, non-static property declaration.
        if (preg_match('/^\s*public\s+(?:readonly\s+)?(\??[\w\\\\|]+)?\s*\$(\w+)/', $line, $m) === 1) {
            $type = trim((string) ($m[1] ?? ''), '?');
            $name = $m[2];
            $locked = $i > 0 && str_contains($lines[$i - 1], '#[Locked]');

            $short = $type === '' ? '' : substr((string) strrchr('\\'.$type, '\\'), 1);

            if ($short !== '' && in_array($short, MODEL_HINTS, true)) {
                $out[] = [$file, $number, 'model-on-public-property', trim($line)];
            }

            if (in_array($name, PROTECTED_NAMES, true)) {
                $out[] = [$file, $number, 'identity-named-public-property', trim($line)];
            }

            if (! $locked && preg_match('/^(pageProps|props|payload|data)$/', $name) === 1
                && preg_match('/\barray\b/i', $type) === 1) {
                $out[] = [$file, $number, 'public-page-props', trim($line)];
            }
        }

        // A LIFECYCLE HOOK IS NOT A MUTATOR.
        //
        // `updatedFoo()` must stay public, because Livewire calls it. The
        // `update` prefix matched every hook. A browser can call a hook
        // directly, so a person must review them. This rule is not the place.
        // The incorrect reports hid the one real finding. A person switches off
        // a check that reports incorrect findings.
        $isLifecycle = preg_match('/^\s*public\s+function\s+(updated|updating|mount|boot|booted|hydrate|dehydrate|rendering|rendered)/i', $line) === 1;

        // A public method whose name says it changes a record.
        if (! $isLifecycle && preg_match('/^\s*public\s+function\s+(delete|destroy|remove|update|save|store|approve|reject|refund|publish|unpublish|archive|restore|assign|revoke|impersonate)\w*\s*\(/i', $line, $m) === 1) {
            $body = implode("\n", array_slice($lines, $i, 40));

            // AN APPLICATION GUARD IS ALSO AUTHORIZATION.
            //
            // Applications wrap the check. Examples are
            // `$this->ensureAccess()` and `$this->guard()`. A scanner that
            // knows the Laravel functions only reports each wrapped guard as a
            // finding. On one real application this produced 1 of 3 findings,
            // and that method was correctly guarded.
            $authorized = preg_match('/\$this->authorize|Gate::|->can\(|->cannot\(|abort_unless|abort_if|::assert\(|policy\(|\$this->ensure\w*\(|\$this->guard\w*\(|::authorize\(/', $body) === 1;

            if (! $authorized) {
                $out[] = [$file, $number, 'unauthorized-mutator', trim($line)];
            }
        }
    }

    return $out;
}

function scanPath(string $root): array
{
    $all = [];
    $dirs = [$root.'/app', $root.'/resources/views', $root.'/packages'];

    foreach ($dirs as $dir) {
        if (! is_dir($dir)) {
            continue;
        }

        $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($dir, FilesystemIterator::SKIP_DOTS));

        foreach ($it as $f) {
            if (! $f instanceof SplFileInfo || ! in_array($f->getExtension(), ['php'], true)) {
                continue;
            }

            $source = (string) file_get_contents($f->getPathname());
            $all = array_merge($all, findings(str_replace($root.'/', '', $f->getPathname()), $source));
        }
    }

    return $all;
}

function selfTest(): int
{
    // EVERY RULE MUST FIRE, AND MUST NOT OVER-FIRE. A checker calibrated in one
    // direction only is the thing this skill warns about.
    // THESE FIXTURES USE SEVERAL LINES ON PURPOSE.
    //
    // The first fixtures used one line each. Every rule then reported
    // "expected to fire". The property and method patterns match the start of a
    // line. A single-line fixture puts the declaration in the middle of a line
    // that starts with `<?php class`.
    //
    // The self-test found this before any person trusted the scanner. This is
    // the reason to write a self-test.
    $component = static fn (string $body): string => "<?php\n\nclass A extends Component\n{\n".$body."\n}\n";
    $plain = static fn (string $body): string => "<?php\n\nclass A\n{\n".$body."\n}\n";

    $cases = [
        ['model-on-public-property', true, $component('    public Model $user;')],
        ['model-on-public-property', true, $component('    public Collection $rows;')],
        ['model-on-public-property', false, $component('    public string $name = \'\';')],
        ['identity-named-public-property', true, $component('    public string $payerEmail = \'\';')],
        ['identity-named-public-property', false, $component('    public string $title = \'\';')],
        ['public-page-props', true, $component('    public array $pageProps = [];')],
        ['public-page-props', false, $component('    private array $pageProps = [];')],
        ['unauthorized-mutator', true, $component("    public function deletePost(\$id)\n    {\n        Post::find(\$id)->delete();\n    }")],
        ['unauthorized-mutator', false, $component("    public function deletePost(\$id)\n    {\n        \$p = Post::findOrFail(\$id);\n        \$this->authorize('delete', \$p);\n        \$p->delete();\n    }")],
        // A lifecycle hook is not a mutator by name, however it is spelled.
        ['unauthorized-mutator', false, $component("    public function updatedTarget(): void\n    {\n        \$this->quote();\n    }")],
        // A project's own guard helper counts as authorization.
        ['unauthorized-mutator', false, $component("    public function deleteMessage(int \$id): void\n    {\n        \$this->ensureAccess();\n        Message::findOrFail(\$id)->delete();\n    }")],
        // Not a Livewire component at all: silent.
        ['model-on-public-property', false, $plain('    public Model $user;')],
        ['unauthorized-mutator', false, $plain("    public function deletePost(\$id)\n    {\n        Post::find(\$id)->delete();\n    }")],
    ];

    $failed = 0;

    foreach ($cases as [$rule, $shouldFire, $source]) {
        $fired = false;

        foreach (findings('test.php', $source) as $f) {
            if ($f[2] === $rule) {
                $fired = true;
            }
        }

        if ($fired !== $shouldFire) {
            $failed++;
            printf("  FAIL  %-32s expected %s\n", $rule, $shouldFire ? 'to fire' : 'to stay silent');
        }
    }

    printf("livewire-security scan.php self-test — %d/%d checks passed\n", count($cases) - $failed, count($cases));

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

$found = scanPath($root);

foreach ($found as [$file, $line, $rule, $code]) {
    printf("%s:%d  [%s]\n      %s\n      %s\n\n", $file, $line, $rule, RULES[$rule], $code);
}

printf("%d finding(s)\n", count($found));

exit(count($found) === 0 ? 0 : 1);
