/**
 * Service Worker для офлайн-доступа к руководству Renault Symbol
 * Стратегия: Cache-First для статики, Network-First для страниц
 *
 * Все пути учитывают, что сайт развёрнут на GitHub Pages
 * в поддиректории /S-I_M_B_O_L/
 */

const CACHE_NAME = 'reno-symbol-v3';
const BASE_PATH = '/S-I_M_B_O_L';

const PRECACHE_URLS = [
  BASE_PATH + '/index.html',
  BASE_PATH + '/css/general.css',
  BASE_PATH + '/css/chrome.css',
  BASE_PATH + '/css/variables.css',
  BASE_PATH + '/theme/css/renault.css',
  BASE_PATH + '/theme/js/dtc-search.js',
  BASE_PATH + '/theme/js/service-tracker.js',
  BASE_PATH + '/theme/favicon.svg',
];

const ASSET_EXTENSIONS = [
  '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
  '.woff', '.woff2', '.ttf', '.eot',
  '.json', '.xml',
];

// Установка — кеширование предзагруженных ресурсов
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(PRECACHE_URLS).catch(err => {
        console.warn('[SW] Некоторые ресурсы не закешированы:', err);
      });
    })
  );
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

// Обработка сообщений от клиентов
self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Запросы — стратегии кеширования
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Только наш домен
  if (url.origin !== location.origin) return;

  // Не кешировать CDN-ресурсы
  if (url.hostname.includes('cdn.jsdelivr.net')) return;

  const pathname = url.pathname;

  // Ассеты (CSS, JS, изображения, шрифты) — Cache-First
  if (ASSET_EXTENSIONS.some(ext => pathname.endsWith(ext))) {
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
  if (pathname.endsWith('.html') || pathname === BASE_PATH + '/' || pathname === BASE_PATH || !pathname.includes('.')) {
    event.respondWith(
      fetch(request).then(response => {
        return caches.open(CACHE_NAME).then(cache => {
          cache.put(request, response.clone());
          return response;
        });
      }).catch(() => {
        return caches.match(request).then(cached => {
          return cached || caches.match(BASE_PATH + '/index.html');
        });
      })
    );
    return;
  }

  // Остальное — Network-Only
  event.respondWith(fetch(request));
});
