#!/usr/bin/env php
<?php

declare(strict_types=1);

/**
 * Check that the framework statements in SKILL.md are still true.
 *
 * This skill states facts about Livewire internals. It names an exception
 * namespace. It names the contents of a middleware list. It names the shape that
 * a model takes in a snapshot. People state each of these facts incorrectly, and
 * that is the reason the skill exists.
 *
 * A fact can stop being true. A new Livewire release can move a class or change
 * a list. The skill then gives confident wrong advice, and no person notices.
 *
 * This tool applies the skill's own rule to the skill. It reads the installed
 * `vendor/livewire/livewire` and fails when a statement no longer holds.
 *
 * It reads files only. It needs no bootstrap, no database and no autoloader.
 *
 * The exit code is the number of failed checks.
 */

/**
 * @return array{0: bool, 1: string}
 */
function checkFile(string $vendor, string $relative, string $must, string $claim): array
{
    $path = $vendor.'/'.$relative;

    if (! is_file($path)) {
        return [false, $claim.' — the file is absent: '.$relative];
    }

    $body = (string) file_get_contents($path);

    return str_contains($body, $must)
        ? [true, $claim]
        : [false, $claim.' — "'.$must.'" is no longer in '.$relative];
}

/**
 * @return array{0: bool, 1: string}
 */
function checkAbsent(string $vendor, string $relative, string $claim): array
{
    return is_file($vendor.'/'.$relative)
        ? [false, $claim.' — the file now EXISTS: '.$relative]
        : [true, $claim];
}

$root = rtrim($argv[1] ?? getcwd(), '/');
$vendor = $root.'/vendor/livewire/livewire';

if (! is_dir($vendor)) {
    fwrite(STDERR, "No Livewire install at {$vendor}\n");
    fwrite(STDERR, "Usage: php verify-facts.php <path-to-a-laravel-app>\n");

    exit(2);
}

$version = 'unknown';
$installed = $root.'/vendor/composer/installed.json';

if (is_file($installed)) {
    $data = json_decode((string) file_get_contents($installed), true);
    $packages = is_array($data) ? ($data['packages'] ?? $data) : [];

    foreach (is_array($packages) ? $packages : [] as $package) {
        if (is_array($package) && ($package['name'] ?? null) === 'livewire/livewire') {
            $version = is_string($package['version'] ?? null) ? $package['version'] : 'unknown';
        }
    }
}

$checks = [
    // RULE 1 — a public property is published, and the browser can change it.
    checkFile($vendor, 'src/Drawer/BaseUtils.php', 'isPublic',
        'A public property reaches the snapshot because BaseUtils filters on isPublic()'),
    checkFile($vendor, 'src/Mechanisms/HandleComponents/HandleComponents.php', 'dehydrateProperties',
        'HandleComponents::dehydrateProperties() still builds the snapshot data'),

    // RULE 1 — a model publishes its class and its key, and not every attribute.
    checkFile($vendor, 'src/Features/SupportModels/ModelSynth.php', 'morphMap',
        'ModelSynth still consults the morph map for the published class name'),
    checkFile($vendor, 'src/Features/SupportModels/ModelSynth.php', "'class'",
        'ModelSynth still publishes a class name'),

    // RULE 3 — the exception namespace that people guess incorrectly.
    checkFile($vendor, 'src/Features/SupportLockedProperties/CannotUpdateLockedPropertyException.php', 'class CannotUpdateLockedPropertyException',
        'The locked-property exception is in Features\\SupportLockedProperties'),
    checkAbsent($vendor, 'src/Exceptions/CannotUpdateLockedPropertyException.php',
        'The locked-property exception is NOT in Livewire\\Exceptions'),

    // RULE 5 — the persistent middleware list, which decides what runs again.
    checkFile($vendor, 'src/Mechanisms/PersistentMiddleware/PersistentMiddleware.php', 'Illuminate\Auth\Middleware\Authenticate::class',
        'Authenticate is persistent, so it runs again on an update request'),
    checkFile($vendor, 'src/Mechanisms/PersistentMiddleware/PersistentMiddleware.php', 'Illuminate\Routing\Middleware\SubstituteBindings::class',
        'SubstituteBindings is persistent'),
];

// RULE 5, the part that matters most. The skill tells a reader that a permission
// check does NOT run again. A future release could add these, and the advice
// would then be wrong in the dangerous direction.
$persistent = (string) @file_get_contents($vendor.'/src/Mechanisms/PersistentMiddleware/PersistentMiddleware.php');

foreach (['Spatie\Permission', 'RequirePassword', 'EnsureEmailIsVerified'] as $absent) {
    $checks[] = [
        ! str_contains($persistent, $absent),
        'The persistent list still excludes '.$absent.', so it does NOT run again on an update request',
    ];
}

$failed = 0;

printf("livewire-security verify-facts — livewire/livewire %s\n\n", $version);

foreach ($checks as [$ok, $claim]) {
    if (! $ok) {
        $failed++;
    }

    printf("  %s  %s\n", $ok ? ' ok ' : 'FAIL', $claim);
}

printf("\n%d/%d statements still hold\n", count($checks) - $failed, count($checks));

if ($failed > 0) {
    fwrite(STDERR, "\nSKILL.md states something that this Livewire version no longer does. Correct the skill.\n");
}

exit($failed);
