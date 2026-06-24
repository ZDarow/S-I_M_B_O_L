/**
 * Service Worker для офлайн-доступа к руководству Renault Symbol
 * Кеширует все HTML, CSS, JS, изображения, шрифты и MD-исходники
 * Стратегия: Cache-First для статики, Network-First для страниц
 */

const CACHE_NAME = 'reno-symbol-v1';

const PRECACHE_URLS = [
  '/',
  '/index.html',
];

const ASSET_EXTENSIONS = [
  '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
  '.woff', '.woff2', '.ttf', '.eot',
  '.json', '.xml', '.yaml', '.txt',
];

// Установка — кеширование предзагруженных ресурсов
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(PRECACHE_URLS);
    })
  );
  // Активировать сразу, не ждать закрытия вкладок
  self.skipWaiting();
});

// Активация — очистка старых кешей
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// Запрос — Cache-First для ассетов, Stale-While-Revalidate для страниц
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Только наш домен
  if (url.origin !== location.origin) return;

  // Не кешировать Mermaid (загружается с CDN)
  if (url.hostname.includes('cdn.jsdelivr.net')) return;

  // Ассеты (CSS, JS, изображения, шрифты) — Cache-First
  if (ASSET_EXTENSIONS.some(ext => url.pathname.endsWith(ext))) {
    event.respondWith(
      caches.match(request).then(cached => {
        return cached || fetch(request).then(response => {
          return caches.open(CACHE_NAME).then(cache => {
            cache.put(request, response.clone());
            return response;
          });
        });
      })
    );
    return;
  }

  // HTML-страницы — Network-First с падением на кеш
  if (url.pathname.endsWith('.html') || url.pathname === '/' || !url.pathname.includes('.')) {
    event.respondWith(
      fetch(request).then(response => {
        return caches.open(CACHE_NAME).then(cache => {
          cache.put(request, response.clone());
          return response;
        });
      }).catch(() => {
        return caches.match(request).then(cached => {
          return cached || caches.match('/');
        });
      })
    );
    return;
  }

  // Остальное — Network-Only
  event.respondWith(fetch(request));
});
