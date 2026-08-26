<?php

/**
 * Does Livewire's static state survive a completed request inside ONE process?
 *
 * That is the exact condition a Laravel Octane worker creates, and Livewire
 * clears this state only on a `flush-state` event that the production request
 * path never triggers.
 *
 * Run it against any Laravel app with Livewire installed:
 *
 *     php artisan tinker --execute="require 'path/to/octane-probe.php';"
 *
 * It writes nothing and flushes the state it touched before it exits.
 */
use Livewire\Features\SupportRedirects\SupportRedirects;

$flag = (new ReflectionClass(SupportRedirects::class))
    ->getProperty('atLeastOneMountedComponentHasRedirected');
$flag->setAccessible(true);

Livewire::component('octane-probe', new class extends \Livewire\Component {
    public function render() { return '<div>probe</div>'; }
});

$read = fn () => var_export($flag->getValue(), true);

echo "\n== 1. the TESTING renderer ==\n";
$flag->setValue(null, true);
echo "   before Livewire::test(): ".$read()."\n";
Livewire::test('octane-probe');
echo "   after  Livewire::test(): ".$read()."   <- SupportTesting calls flushState()\n";

echo "\n== 2. the PRODUCTION render path ==\n";
$flag->setValue(null, true);
echo "   before Livewire::mount(): ".$read()."\n";
Livewire::mount('octane-probe');
echo "   after  Livewire::mount(): ".$read()."   <- nothing flushed it\n";

echo "\n== 3. the call production never makes ==\n";
Livewire::flushState();
echo "   after  Livewire::flushState(): ".$read()."\n";

$survived = true;
$flag->setValue(null, true);
Livewire::mount('octane-probe');
$survived = ($flag->getValue() === true);
Livewire::flushState();

echo "\n".($survived
  ? "CONFIRMED. A completed production render leaves the flag set. On an Octane\n"
   ."worker the NEXT request reads it true, and SupportRedirects:20-24 then skips\n"
   ."clearing that visitor's flash data. Only flushState() clears it, and the\n"
   ."production path never calls it.\n"
  : "NOT CONFIRMED — the flag was reset. The finding is wrong.\n");
