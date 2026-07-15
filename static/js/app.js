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
  // un-file it), and drag folders into folders to nest them. Drops POST to
  // the matching move endpoint, then reload.
  var drag = null; // {kind: 'doc'|'folder', id, el}

  function clearDropHighlights() {
    document.querySelectorAll('.drop-hover').forEach(function (el) {
      el.classList.remove('drop-hover');
    });
  }

  function validTarget(evt) {
    if (!drag) return null;
    var target = evt.target.closest && evt.target.closest('[data-drop-folder]');
    if (!target) return null;
    if (drag.kind === 'folder') {
      // A folder can't drop onto itself or anything inside its own subtree.
      var ownBox = drag.el.closest('.sidebar-folder');
      if (ownBox && (target === ownBox || ownBox.contains(target))) return null;
    }
    return target;
  }

  document.addEventListener('dragstart', function (evt) {
    if (!evt.target.closest) return;
    var doc = evt.target.closest('[data-doc-id]');
    var folder = doc ? null : evt.target.closest('[data-folder-id]');
    if (!doc && !folder) return;
    drag = doc
      ? { kind: 'doc', id: doc.dataset.docId, el: doc }
      : { kind: 'folder', id: folder.dataset.folderId, el: folder };
    evt.dataTransfer.effectAllowed = 'move';
    try { evt.dataTransfer.setData('text/plain', drag.id); } catch (e) { /* IE quirk */ }
    drag.el.classList.add('dragging');
  });

  document.addEventListener('dragend', function () {
    if (drag) drag.el.classList.remove('dragging');
    drag = null;
    clearDropHighlights();
  });

  document.addEventListener('dragover', function (evt) {
    var target = validTarget(evt);
    if (!target) return;
    evt.preventDefault();
    evt.dataTransfer.dropEffect = 'move';
    document.querySelectorAll('.drop-hover').forEach(function (el) {
      if (el !== target) el.classList.remove('drop-hover');
    });
    target.classList.add('drop-hover');
  });

  document.addEventListener('drop', function (evt) {
    var target = validTarget(evt);
    if (!target) return;
    evt.preventDefault();
    var kind = drag.kind, id = drag.id;
    drag = null;
    clearDropHighlights();
    var meta = document.querySelector('meta[name="csrf-token"]');
    var url = kind === 'doc' ? '/d/' + id + '/move/' : '/folders/' + id + '/move/';
    var field = kind === 'doc' ? 'folder' : 'parent';
    var body = {};
    body[field] = target.dataset.dropFolder;
    fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': meta ? meta.content : '',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams(body),
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
