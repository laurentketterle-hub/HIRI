// HIRI Web Service Worker — offline cache for device control
const CACHE = 'hiri-web-v1';
const PRE_CACHE = [
  '/',
  '/index.html',
  '/web-vi.html',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRE_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Network-first with cache fallback for API calls
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  // Cache API responses for offline device list
  if (url.pathname.startsWith('/devices') || url.pathname === '/stats' || url.pathname === '/areas') {
    event.respondWith(networkFirst(event.request));
  } else if (url.pathname === '/health') {
    event.respondWith(networkOnly(event.request));
  } else {
    event.respondWith(cacheFirst(event.request));
  }
});

async function networkFirst(request) {
  const cache = await caches.open(CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (e) {
    const cached = await cache.match(request);
    return cached || new Response(JSON.stringify({ error: 'offline', cached: false }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  return cached || fetch(request);
}

async function networkOnly(request) {
  return fetch(request);
}
