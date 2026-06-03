const CACHE_NAME = 'na-tuner-v1';
const ASSETS = [
  'index.html',
  'aron.html',
  'earlyfrench.html',
  'just.html',
  'kirnberger.html',
  'pytagorean.html',
  'rameau.html',
  'rousseau.html',
  'valotti.html',
  'violin.html',
  'werkmeister.html',
  'meantone4.html',
  'meantone6.html',
  'ozadje.jpg'
];

// Shranjevanje datotek v lokalni cache ob namestitvi
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Če kakšna datoteka s seznama še ne obstaja, se namestitev ne bo sesula
      return Promise.allSettled(
        ASSETS.map(asset => cache.add(asset))
      );
    })
  );
});

// Aktivacija in brisanje starih verzij
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    })
  );
});

// Mreža ali Cache (Offline delovanje)
self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((cachedResponse) => {
      return cachedResponse || fetch(e.request);
    })
  );
});