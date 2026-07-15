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

  // Drag a sidebar document onto a folder (or the Documents section, to
  // un-file it). Drops POST to the document's move endpoint, then reload.
  var draggedDocId = null;

  function clearDropHighlights() {
    document.querySelectorAll('.drop-hover').forEach(function (el) {
      el.classList.remove('drop-hover');
    });
  }

  document.addEventListener('dragstart', function (evt) {
    var doc = evt.target.closest && evt.target.closest('[data-doc-id]');
    if (!doc) return;
    draggedDocId = doc.dataset.docId;
    evt.dataTransfer.effectAllowed = 'move';
    try { evt.dataTransfer.setData('text/plain', draggedDocId); } catch (e) { /* IE quirk */ }
    doc.classList.add('dragging');
  });

  document.addEventListener('dragend', function (evt) {
    draggedDocId = null;
    clearDropHighlights();
    if (evt.target.classList) evt.target.classList.remove('dragging');
  });

  document.addEventListener('dragover', function (evt) {
    if (!draggedDocId) return;
    var target = evt.target.closest && evt.target.closest('[data-drop-folder]');
    if (!target) return;
    evt.preventDefault();
    evt.dataTransfer.dropEffect = 'move';
    document.querySelectorAll('.drop-hover').forEach(function (el) {
      if (el !== target) el.classList.remove('drop-hover');
    });
    target.classList.add('drop-hover');
  });

  document.addEventListener('drop', function (evt) {
    var target = evt.target.closest && evt.target.closest('[data-drop-folder]');
    if (!target || !draggedDocId) return;
    evt.preventDefault();
    var docId = draggedDocId;
    draggedDocId = null;
    clearDropHighlights();
    var meta = document.querySelector('meta[name="csrf-token"]');
    fetch('/d/' + docId + '/move/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': meta ? meta.content : '',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({ folder: target.dataset.dropFolder }),
    }).then(function () { window.location.reload(); });
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
