// Global htmx setup + small page helpers.
document.addEventListener('DOMContentLoaded', function () {
  document.body.addEventListener('htmx:configRequest', function (evt) {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) evt.detail.headers['X-CSRFToken'] = meta.content;
  });

  // Give blog post art a stable per-post gradient hue.
  function paintArt(root) {
    (root || document).querySelectorAll('.post-art[data-hue]').forEach(function (el) {
      var hue = (parseInt(el.dataset.hue, 10) * 47) % 360;
      el.style.background =
        'linear-gradient(135deg, hsl(' + hue + ', 70%, 55%), hsl(' + ((hue + 60) % 360) + ', 70%, 45%))';
    });
  }
  paintArt(document);
  document.body.addEventListener('htmx:afterSwap', function (evt) {
    paintArt(evt.detail.target || document);
  });

  // Quota and validation errors from htmx endpoints arrive as plain-text 4xx
  // responses; show them as a temporary toast.
  var toastTimer = null;
  document.body.addEventListener('htmx:responseError', function (evt) {
    var status = evt.detail.xhr.status;
    if (status < 400 || status >= 500) return;
    var toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = evt.detail.xhr.responseText || 'That change was not saved.';
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.hidden = true; }, 6000);
  });
});
