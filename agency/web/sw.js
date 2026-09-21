/* Service worker: l'app shell deve aprirsi anche senza rete.
 *
 * Strategia deliberatamente diversa per tipo di risorsa:
 *  - shell (html/js/manifest/icona): cache-first, e' statica e deve essere istantanea;
 *  - stato (index.json): network-first, perche' un dato vecchio spacciato per fresco
 *    e' peggio di un dato dichiaratamente offline.
 */
'use strict';

const CACHE = 'agency-v1';
const SHELL = ['./', './index.html', './app.js', './manifest.webmanifest', './icon.svg'];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  // Le chiamate a GitHub non si cachano mai: sono scritture e letture live.
  if (url.hostname === 'api.github.com') return;

  if (url.pathname.endsWith('index.json')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put(request, copy));
          return response;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  event.respondWith(
    caches.match(request).then(cached => cached || fetch(request))
  );
});
