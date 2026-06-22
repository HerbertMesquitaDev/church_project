/**
 * sw.js — Service Worker do Portal da Igreja
 * Estratégia: Cache First para assets estáticos, Network First para páginas
 */

const CACHE_NAME    = 'portal-igreja-v2';
const STATIC_CACHE  = 'portal-static-v2';

// Assets que sempre ficam em cache (shell do app)
const SHELL_ASSETS = [
  '/',
  '/offline/',
  '/ebd/',
  '/eventos/',
  '/static/css/style.css',
  '/static/css/members.css',
  '/static/img/logo_icone.png',
  '/static/img/icon_192.png',
  '/static/img/icon_512.png',
  '/static/manifest.json',
  '/static/js/main.js',
];

// Página de fallback offline
const OFFLINE_PAGE = '/offline/';


// ── Install: pré-cachear o shell ──────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then(cache => {
        return cache.addAll(SHELL_ASSETS).catch(() => {
          console.log('[SW] Alguns assets não puderam ser cachados');
        });
      }),
      caches.open(CACHE_NAME).then(cache => {
        return cache.add(OFFLINE_PAGE).catch(() => {
          console.log('[SW] Página offline não pôde ser cachada');
        });
      })
    ]).then(() => self.skipWaiting())
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
<html lang="pt-BR" data-theme="">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="theme-color" content="#1A2340">
  <title>Sem conexão</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:system-ui,-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#FAF7F2;padding:2rem;text-align:center}
    [data-theme="dark"] body{background:#0E0E12}
    .card{max-width:480px;background:white;border-radius:12px;padding:3rem 2rem;box-shadow:0 8px 32px rgba(0,0,0,.08)}
    [data-theme="dark"] .card{background:#1E1E24;box-shadow:0 8px 32px rgba(0,0,0,.3)}
    .logo{width:52px;margin-bottom:1.5rem;opacity:.8}
    .icon-wrap{width:80px;height:80px;border-radius:50%;background:rgba(201,168,76,.12);display:flex;align-items:center;justify-content:center;margin:0 auto 1.75rem;font-size:2.5rem;animation:pulse 2s infinite}
    [data-theme="dark"] .icon-wrap{background:rgba(255,255,255,.05)}
    @keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.8;transform:scale(.95)}}
    h1{font-size:1.9rem;font-weight:600;color:#1A2340;margin-bottom:.75rem}
    [data-theme="dark"] h1{color:#E8E4DC}
    p{color:#6B6B6B;font-size:.95rem;line-height:1.7;margin-bottom:2rem}
    [data-theme="dark"] p{color:#B0ABA0}
    .actions{display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap;margin-bottom:2rem}
    .btn{padding:.65rem 1.75rem;border-radius:8px;font-size:.9rem;font-weight:500;cursor:pointer;text-decoration:none;border:none;font-family:inherit;display:inline-flex;align-items:center;gap:.5rem;transition:all .2s}
    .btn:active{transform:scale(.98)}
    .btn-primary{background:#1A2340;color:white}
    .btn-primary:hover{background:#0F1828;box-shadow:0 4px 12px rgba(26,35,64,.2)}
    [data-theme="dark"] .btn-primary:hover{background:#2A2A30}
    .btn-outline{border:1.5px solid #DDD8CC;color:#1A2340;background:none}
    [data-theme="dark"] .btn-outline{border-color:#4A4A50}
    .btn-outline:hover{background:rgba(26,35,64,.05);border-color:#1A2340}
    [data-theme="dark"] .btn-outline:hover{background:rgba(255,255,255,.05)}
    .note{font-size:.78rem;color:#6B6B6B;padding-top:1.5rem;border-top:1px solid rgba(201,168,76,.1)}
    [data-theme="dark"] .note{color:#B0ABA0;border-top-color:rgba(255,255,255,.1)}
  </style>
</head>
<body>
  <div class="card">
    <div style="font-size:2.5rem;margin-bottom:1rem">📡</div>
    <h1>Você está offline</h1>
    <p>Parece que sua conexão foi perdida.<br>Verifique e tente novamente.</p>
    <div class="actions">
      <button class="btn btn-primary" onclick="if(navigator.onLine){location.reload()}else{alert('Sem conexão')}">↺ Tentar</button>
      <a href="/" class="btn btn-outline">🏠 Início</a>
    </div>
    <p class="note">💾 Páginas visitadas podem estar disponíveis offline</p>
  </div>
  <script>
    (function(){var t=localStorage.getItem('church_theme')||'';if(t)document.documentElement.setAttribute('data-theme',t)})();
    window.addEventListener('online',function(){location.reload()});
  </script>
</body>
</html>`,
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
