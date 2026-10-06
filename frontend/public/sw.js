const CACHE_NAME = 'weibo-analytics-v2';
const STATIC_CACHE = 'static-v3';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/vite.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== STATIC_CACHE)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API 与 Socket.IO 一律不经过 SW：v1 曾对 /api/* networkFirst +
  // cache.put，把带鉴权的响应写进 CacheStorage，多用户共机会串数据，
  // 离线还会返回他人/过期的旧数据（#20）。浏览器默认行为（axios 统一
  // 处理 401/超时）比缓存更正确。
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/socket.io/')) {
    return;
  }

  if (request.method === 'GET') {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
  }
});

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // SPA 导航离线时回退到缓存的 index.html，而不是 503 白屏（#20）；
    // 静态资源本身带 hash 指纹，v2 起新名字会随发版自然更新。
    if (request.mode === 'navigate') {
      const shell = await caches.match('/index.html');
      if (shell) {
        return shell;
      }
    }
    return new Response('Offline', { status: 503 });
  }
}

self.addEventListener('push', (event) => {
  if (!event.data) return;
  
  const data = event.data.json();
  const options = {
    body: data.message || '您有新的预警信息',
    icon: '/logo.png',
    badge: '/vite.svg',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/alert-center'
    }
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || '舆情预警', options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});

self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});

async function syncData() {
  console.log('Background sync executed');
}
