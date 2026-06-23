// Service Worker для offline-доступа к руководству Renault Symbol
const CACHE_NAME = 'reno-symbol-v1';
const CACHE_URLS = [
  './',
  './index.html',
  './searchindex-5bf5d96f.js',
  './searcher-09f2665d.js',
  './book-c22b7243.js',
  './toc-e8962a39.js',
  './clipboard-1626706a.min.js',
  './highlight-abc7f01d.js',
  './mark-09e88c2c.min.js',
  './elasticlunr-ef4e11c1.min.js',
  './ayu-highlight-3fdfc3ac.css',
  './tomorrow-night-4c0ae647.css',
  './highlight-493f70e1.css',
  './css/general-0392ca55.css',
  './css/chrome-fc474251.css',
  './css/print-9e4910d8.css',
  './css/variables-8adf115d.css',
  './favicon-8114d1fc.png',
  './favicon-de23e50b.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(CACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request).then(fetchResponse => {
        return caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, fetchResponse.clone());
          return fetchResponse;
        });
      }))
  );
});
