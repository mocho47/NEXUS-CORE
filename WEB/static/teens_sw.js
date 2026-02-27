// NEXUS Teens — Service Worker v1
// Cachea la app para funcionar offline cuando la PC está apagada

const CACHE = 'nexus-teens-v1';
const SHELL = [
  '/teens',
  '/static/teens_manifest.json',
  '/static/uploads/teens_icon_192.png',
  '/static/uploads/teens_icon_512.png',
];

// Instalar: cachear shell
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

// Activar: limpiar caches viejos
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Fetch: estrategia por tipo de request
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // API del tutor: red primero, fallback offline amigable
  if (url.pathname === '/api/teens/tutor') {
    e.respondWith(
      fetch(e.request).catch(() =>
        new Response(JSON.stringify({
          ok: true,
          respuesta: '🔌 **Sin conexión** — la PC está apagada o sin internet.\n\nEl Tutor vuelve cuando se encienda. Mientras tanto:\n\n• Tu **diario** sigue funcionando ✅\n• Tus notas de **Mi Negocio** siguen guardadas ✅\n• **Mi Cabeza** funciona sin internet ✅\n\nAvísale a tu papá para que la encienda.'
        }), { headers: { 'Content-Type': 'application/json' }})
      )
    );
    return;
  }

  // Otras APIs: red primero, error silencioso
  if (url.pathname.startsWith('/api/')) {
    e.respondWith(
      fetch(e.request).catch(() =>
        new Response(JSON.stringify({ ok: false, error: 'offline' }),
          { headers: { 'Content-Type': 'application/json' }})
      )
    );
    return;
  }

  // Shell HTML/static: cache primero, actualiza en background
  e.respondWith(
    caches.match(e.request).then(cached => {
      const network = fetch(e.request).then(res => {
        if (res.ok && res.status < 400) {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      }).catch(() => cached);
      return cached || network;
    })
  );
});
