/* MARSCOPE offline shell. This is an offline review aid, not operational EVA software. */
const SHELL_CACHE = 'marscope-shell-v0.3.1';
const DATA_CACHE = 'marscope-reference-v0.3.1';
const SHELL = ['/', '/index.html', '/manifest.webmanifest'];
const REFERENCE_API = new Set([
  '/api/health', '/api/terrain', '/api/registry', '/api/data/catalog',
  '/api/science/evidence', '/api/observations'
]);

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => ![SHELL_CACHE, DATA_CACHE].includes(key)).map((key) => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;

  if (url.pathname.startsWith('/api/')) {
    if (!REFERENCE_API.has(url.pathname)) return;
    event.respondWith((async () => {
      const cache = await caches.open(DATA_CACHE);
      const cached = await cache.match(request);
      const refresh = fetch(request).then((response) => {
        if (response.ok) void cache.put(request, response.clone());
        return response;
      });
      if (cached) {
        event.waitUntil(refresh.catch(() => undefined));
        return cached;
      }
      try { return await refresh; }
      catch { return new Response(JSON.stringify({ offline: true, detail: 'No cached reference data is available.' }), { status: 503, headers: { 'Content-Type': 'application/json' } }); }
    })());
    return;
  }

  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(async () => (await caches.match('/index.html')) || Response.error()));
    return;
  }

  if (url.pathname.startsWith('/assets/')) {
    event.respondWith((async () => {
      const cache = await caches.open(SHELL_CACHE);
      const cached = await cache.match(request);
      if (cached) return cached;
      const response = await fetch(request);
      if (response.ok) void cache.put(request, response.clone());
      return response;
    })());
  }
});
