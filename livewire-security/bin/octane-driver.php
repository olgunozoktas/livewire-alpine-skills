<?php
/**
 * Drive Laravel Octane's REAL Worker through consecutive requests, exactly as a
 * live worker serves consecutive visitors. Boot once, handle many.
 *
 * It answers one question: does Livewire's static state leak between users on
 * an Octane worker?
 *
 * It does NOT. Octane ships
 * `Laravel\Octane\Listeners\PrepareLivewireForNextOperation`, registered by
 * default, which calls `LivewireManager::flushState()`.
 *
 * This script exists because reading Livewire's source and all 99 of its
 * documentation files supports the opposite conclusion. The integration lives
 * in Octane's repo, not Livewire's, and only a running worker shows it.
 *
 * Requires: laravel/octane and livewire/livewire installed.
 * Run with:  php octane-driver.php
 */

use Illuminate\Http\Request;
use Laravel\Octane\ApplicationFactory;
use Laravel\Octane\RequestContext;
use Laravel\Octane\Testing\Fakes\FakeClient;
use Laravel\Octane\Worker;
use Livewire\Features\SupportRedirects\SupportRedirects;

require __DIR__.'/vendor/autoload.php';

$client = new FakeClient([]);
$worker = new Worker(new ApplicationFactory(__DIR__), $client);
$worker->boot();

$flagProp = (new ReflectionClass(SupportRedirects::class))
    ->getProperty('atLeastOneMountedComponentHasRedirected');
$flagProp->setAccessible(true);
$flag = fn () => var_export($flagProp->getValue(), true);

$cookies = [];

/** Send one request through the worker and return the response. */
$send = function (string $method, string $uri, array $opts = []) use ($worker, $client, &$cookies) {
    $server = ['REQUEST_METHOD' => $method, 'REQUEST_URI' => $uri, 'HTTP_HOST' => 'localhost'];
    foreach (($opts['headers'] ?? []) as $k => $v) {
        $server['HTTP_'.strtoupper(str_replace('-', '_', $k))] = $v;
    }
    if (isset($opts['json'])) {
        $server['CONTENT_TYPE'] = 'application/json';
    }

    $request = Request::create(
        $uri, $method, $opts['params'] ?? [], $cookies, [], $server,
        isset($opts['json']) ? json_encode($opts['json']) : null
    );

    $before = count($client->responses);
    $worker->handle($request, new RequestContext);

    if (count($client->responses) === $before) {
        $err = end($client->errors) ?: 'no response and no error';
        throw new RuntimeException("worker produced no response for $method $uri\n".substr($err, 0, 900));
    }

    $response = $client->responses[count($client->responses) - 1];

    // Carry cookies forward, as a browser does.
    foreach ($response->headers->getCookies() as $c) {
        $cookies[$c->getName()] = $c->getValue();
    }

    return $response;
};

$line = fn ($s) => print($s."\n");

$line('');
$line('Livewire '.\Composer\InstalledVersions::getPrettyVersion('livewire/livewire')
    .'  ·  Octane '.\Composer\InstalledVersions::getPrettyVersion('laravel/octane')
    .'  ·  PHP '.PHP_VERSION);
$line('one worker, booted once, handling consecutive requests');
$line(str_repeat('=', 68));

// ---- request 1: a visitor loads the page -------------------------------
$line("\n[req 1] GET /probe                     (visitor A loads the page)");
$html = $send('GET', '/probe')->getContent();
$line('        redirect flag after: '.$flag());

preg_match('/wire:snapshot="([^"]*)"/', $html, $m)
    || throw new RuntimeException("no wire:snapshot in the page:\n".substr($html, 0, 600));
$snapshot = html_entity_decode($m[1], ENT_QUOTES);
preg_match('/name="csrf-token" content="([^"]+)"/', $html, $t);
$token = $t[1] ?? '';
$line('        got a snapshot ('.strlen($snapshot).' bytes) and a csrf token');

$updateUri = '/'.trim(parse_url(
    app(\Livewire\Mechanisms\HandleRequests\HandleRequests::class)->getUpdateUri(), PHP_URL_PATH
) ?? '', '/');

$call = fn (string $method, string $snap) => [
    '_token' => $token,
    'components' => [[
        'snapshot' => $snap,
        'updates' => (object) [],
        'calls' => [['path' => '', 'method' => $method, 'params' => []]],
    ]],
];
$hdrs = ['X-Livewire' => '1', 'X-CSRF-TOKEN' => $token];

// ---- request 2: visitor A clicks something that redirects --------------
$line("\n[req 2] POST update -> goAway()        (visitor A triggers a REDIRECT)");
$r2 = $send('POST', $updateUri, ['json' => $call('goAway', $snapshot), 'headers' => $hdrs]);
$line('        http '.$r2->getStatusCode());
$line('        redirect flag after: '.$flag().'   <-- set by SupportRedirects::dehydrate');

// ---- request 3: a DIFFERENT visitor, same worker -----------------------
$line("\n[req 3] GET /probe                     (visitor B — a NEW person, same worker)");
$cookies = [];                       // visitor B has no cookies of A's
$html3 = $send('GET', '/probe')->getContent();
$line('        redirect flag on arrival: '.$flag().'   <-- should be false for a new request');
preg_match('/wire:snapshot="([^"]*)"/', $html3, $m3);
$snap3 = html_entity_decode($m3[1], ENT_QUOTES);
preg_match('/name="csrf-token" content="([^"]+)"/', $html3, $t3);
$token = $t3[1] ?? '';
$hdrs = ['X-Livewire' => '1', 'X-CSRF-TOKEN' => $token];

// ---- request 4: visitor B does something that does NOT redirect --------
$line("\n[req 4] POST update -> bump()          (visitor B, NO redirect)");
$line('        on this response Livewire SHOULD forget the flash bag,');
$line('        because no component redirected during it.');
$r4 = $send('POST', $updateUri, ['json' => $call('bump', $snap3), 'headers' => $hdrs]);
$line('        http '.$r4->getStatusCode());
$line('        redirect flag: '.$flag());

$line("\n".str_repeat('=', 68));
$stuck = $flagProp->getValue() === true;
$line($stuck
    ? "The flag survived. Octane is NOT flushing Livewire state."
    : "The flag did NOT survive.\n\n"
     ."Octane flushed it. `Laravel\\Octane\\Listeners\\PrepareLivewireForNextOperation`\n"
     ."calls LivewireManager::flushState() and is registered BY DEFAULT in\n"
     ."Octane's `prepareApplicationForNextOperation()`, alongside the Inertia,\n"
     ."Scout and Socialite listeners.\n\n"
     ."So Livewire's production path genuinely never calls flushState() — but it\n"
     ."does not need to. The integration exists; it lives in the OCTANE repo.");
$line("\nThe listener, in full:");
$line(file_get_contents(__DIR__.'/vendor/laravel/octane/src/Listeners/PrepareLivewireForNextOperation.php'));
