/**
 * sw.js — Service Worker do Portal da Igreja
 * Estratégia: Cache First para assets estáticos, Network First para páginas
 */

const CACHE_NAME    = 'portal-igreja-v1';
const STATIC_CACHE  = 'portal-static-v1';

// Assets que sempre ficam em cache (shell do app)
const SHELL_ASSETS = [
  '/',
  '/ebd/',
  '/eventos/',
  '/static/css/style.css',
  '/static/css/members.css',
  '/static/img/logo_icone.png',
  '/static/img/icon_192.png',
  '/static/img/icon_512.png',
  '/static/manifest.json',
];

// Página de fallback offline
const OFFLINE_PAGE = '/offline/';


// ── Install: pré-cachear o shell ──────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => {
      return cache.addAll(SHELL_ASSETS).catch(() => {
        // Falha silenciosa — alguns assets podem não existir ainda
      });
    }).then(() => self.skipWaiting())
  );
});


// ── Activate: limpar caches antigos ──────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k !== CACHE_NAME && k !== STATIC_CACHE)
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});


// ── Fetch: estratégia por tipo de recurso ────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorar requisições não-GET e de outros origens
  if (request.method !== 'GET') return;
  if (!url.origin.includes(self.location.origin)) return;

  // Assets estáticos → Cache First
  if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Páginas HTML → Network First com fallback offline
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirstWithFallback(request));
    return;
  }

  // Resto → Network First simples
  event.respondWith(networkFirst(request));
});


// ── Estratégias ──────────────────────────────────────────

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return cached || new Response('', { status: 408 });
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || new Response('', { status: 408 });
  }
}

async function networkFirstWithFallback(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    // Fallback para página offline
    const offline = await caches.match(OFFLINE_PAGE);
    return offline || new Response(
      `<!DOCTYPE html>
       <html lang="pt-BR">
       <head><meta charset="UTF-8"><title>Sem conexão</title>
       <meta name="viewport" content="width=device-width,initial-scale=1">
       <style>
         body{font-family:system-ui,sans-serif;display:flex;align-items:center;
              justify-content:center;min-height:100vh;margin:0;background:#FAF7F2;text-align:center;padding:2rem}
         h1{color:#1A2340;font-size:1.5rem}p{color:#6B6B6B}
         a{color:#C9A84C;font-weight:600}
       </style></head>
       <body>
         <div>
           <div style="font-size:3rem;margin-bottom:1rem">📡</div>
           <h1>Você está offline</h1>
           <p>Verifique sua conexão e tente novamente.</p>
           <a href="/" onclick="location.reload()">Tentar novamente</a>
         </div>
       </body></html>`,
      { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
    );
  }
}


// ── Push notifications (futuro) ──────────────────────────
self.addEventListener('push', event => {
  if (!event.data) return;
  const data = event.data.json();
  event.waitUntil(
    self.registration.showNotification(data.title || 'Portal da Igreja', {
      body:  data.body  || '',
      icon:  data.icon  || '/static/img/icon_192.png',
      badge: data.badge || '/static/img/icon_192.png',
      data:  { url: data.url || '/' },
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data?.url || '/')
  );
});
