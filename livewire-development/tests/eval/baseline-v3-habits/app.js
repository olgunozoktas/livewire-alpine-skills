import Alpine from 'alpinejs'
window.Alpine = Alpine
Alpine.start()

Livewire.hook('commit', ({ succeed }) => succeed(() => {}))
