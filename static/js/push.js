// Client-side Web Push registration, used by the Settings page.
window.ezPush = (function () {
  function csrf() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
  }

  function urlBase64ToUint8Array(base64String) {
    var padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    var base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    var raw = atob(base64);
    var output = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; ++i) output[i] = raw.charCodeAt(i);
    return output;
  }

  function supported() {
    return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  }

  async function post(url, body) {
    var resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      body: JSON.stringify(body || {}),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }

  async function enable() {
    if (!supported()) throw new Error('This browser does not support push notifications.');
    var permission = await Notification.requestPermission();
    if (permission !== 'granted') throw new Error('Notification permission was not granted.');
    var registration = await navigator.serviceWorker.register('/sw.js');
    await navigator.serviceWorker.ready;
    var keyResp = await fetch('/push/key/');
    var key = (await keyResp.json()).key;
    var subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(key),
      });
    }
    return post('/push/subscribe/', subscription.toJSON());
  }

  async function disable() {
    var registration = await navigator.serviceWorker.getRegistration('/sw.js');
    var endpoint = '';
    if (registration) {
      var subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        endpoint = subscription.endpoint;
        await subscription.unsubscribe();
      }
    }
    return post('/push/unsubscribe/', { endpoint: endpoint });
  }

  async function test() {
    return post('/push/test/', {});
  }

  async function status() {
    if (!supported()) return 'unsupported';
    if (Notification.permission === 'denied') return 'denied';
    var registration = await navigator.serviceWorker.getRegistration('/sw.js');
    if (registration && (await registration.pushManager.getSubscription())) return 'enabled';
    return 'disabled';
  }

  return { supported: supported, enable: enable, disable: disable, test: test, status: status };
})();
