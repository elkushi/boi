/* Кеш игры: ассеты с хешем в имени - навсегда; index.html - из сети,
   при отсутствии сети - из кеша. Новая сборка = новое имя кеша. */
const CACHE = 'boi-e12aeb3f';
const ASSETS = ["assets/alisa-b92397aa.webp", "assets/arena-e5d19860.webp", "assets/moustafa-c19a7ad0.webp"];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS.concat(['./']))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (u.origin !== location.origin) return;                       // Firebase, шрифты - мимо
  if (u.pathname.includes('/assets/')) {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(res => {
      const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res; })));
  } else {
    e.respondWith(fetch(e.request).then(res => {
      const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res;
    }).catch(() => caches.match(e.request).then(r => r || caches.match('./'))));
  }
});
