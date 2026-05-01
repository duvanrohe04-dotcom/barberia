const CACHE_NAME = 'barberking-v50';
const urlsToCache = [
  '/',
  '/static/css/style.css?v=48',
  '/static/js/app.js?v=48',
  '/static/js/particles.js?v=47',
  '/static/js/utils.js?v=47'
];

self.addEventListener('install', event => {
  // Forzar activación inmediata sin esperar a que se cierren pestañas
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  // Ignorar requests que no sean GET o sean de extensiones
  if (event.request.method !== 'GET') return;
  if (event.request.url.startsWith('chrome-extension://')) return;
  if (event.request.url.includes('/api/')) return;

  event.respondWith(
    // Siempre intentar red primero, caché como fallback
    fetch(event.request)
      .then(response => {
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        // Guardar copia fresca en caché
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseClone));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Eliminando caché viejo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim()) // Tomar control inmediato de todas las pestañas
  );
});
