// nexus_sw.js — Service Worker NEXUS by Simplex
// Habilita instalación PWA + cache offline básico

const CACHE_NAME = 'nexus-v2026-1';
const CACHE_STATIC = [
  '/dashboard',
  '/static/nexus_manifest.json',
];

// Instalar — cachear assets básicos
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(CACHE_STATIC).catch(() => {});
    })
  );
  self.skipWaiting();
});

// Activar — limpiar caches viejos
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch — network first, cache fallback para pages
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  // Solo manejar mismo origen
  if (url.origin !== location.origin) return;
  // API calls — siempre network, nunca cache
  if (url.pathname.startsWith('/api/')) return;
  event.respondWith(
    fetch(event.request)
      .then(response => {
        if (response.ok && event.request.method === 'GET') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

// Push notifications (para futuras alertas de pedidos)
self.addEventListener('push', event => {
  if (!event.data) return;
  const data = event.data.json();
  self.registration.showNotification(data.title || 'NEXUS', {
    body: data.body || '',
    icon: '/static/uploads/nexus_icon_192.png',
    badge: '/static/uploads/nexus_icon_192.png',
    tag: data.tag || 'nexus',
    data: { url: data.url || '/dashboard' },
  });
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data?.url || '/dashboard')
  );
});
