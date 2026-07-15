// ezmemory service worker: receive push messages and open the app on click.
self.addEventListener('push', function (event) {
  var data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { /* non-JSON push */ }
  event.waitUntil(
    self.registration.showNotification(data.title || 'ezmemory', {
      body: data.body || '',
      icon: '/static/img/icon.svg',
      data: { url: data.url || '/' },
    })
  );
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  var url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (windows) {
      for (var i = 0; i < windows.length; i++) {
        if ('focus' in windows[i]) { windows[i].navigate(url); return windows[i].focus(); }
      }
      return clients.openWindow(url);
    })
  );
});
