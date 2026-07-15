// Outline editor: click a bullet to edit; Enter/Tab/Shift+Tab/Backspace drive
// server-side outline operations via htmx; text autosaves on blur and idle.
(function () {
  var busy = false;          // an outline-mutating request is in flight
  var suppressBlur = false;  // ignore the blur that fires when we swap the outline
  var saveTimer = null;

  function csrf() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
  }

  function autoGrow(input) {
    input.style.height = 'auto';
    input.style.height = input.scrollHeight + 'px';
  }

  function enterEdit(row) {
    var input = row.querySelector('.node-input');
    var display = row.querySelector('.node-display');
    if (!input || !display) return;
    display.hidden = true;
    input.hidden = false;
    autoGrow(input);
    input.focus();
    var len = input.value.length;
    try { input.setSelectionRange(len, len); } catch (e) { /* not focusable yet */ }
  }

  function exitEdit(row) {
    var input = row.querySelector('.node-input');
    var display = row.querySelector('.node-display');
    if (!input || !display) return;
    input.hidden = true;
    display.hidden = false;
  }

  function saveSilent(input) {
    clearTimeout(saveTimer);
    var row = input.closest('.node-row');
    var display = row && row.querySelector('.node-display');
    return fetch(input.dataset.saveUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf(), 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ text: input.value }),
    })
      .then(function (r) { return r.text(); })
      .then(function (html) {
        if (display) {
          display.innerHTML = html;
          display.classList.toggle('node-empty', input.value.trim() === '');
        }
      })
      .catch(function () { /* keep editing; next save retries */ });
  }

  function op(input, url, sendText) {
    if (busy) return;
    busy = true;
    suppressBlur = true;
    clearTimeout(saveTimer);
    var values = sendText === false ? {} : { text: input.value };
    htmx.ajax('POST', url, {
      target: '#outline',
      swap: 'outerHTML',
      values: values,
      headers: { 'X-CSRFToken': csrf() },
    }).finally(function () {
      busy = false;
      suppressBlur = false;
    });
  }

  function visibleRows() {
    return Array.prototype.slice.call(document.querySelectorAll('#outline .node-row'));
  }

  function moveFocus(row, delta) {
    var rows = visibleRows();
    var idx = rows.indexOf(row);
    var next = rows[idx + delta];
    if (!next) return;
    var input = row.querySelector('.node-input');
    saveSilent(input);
    exitEdit(row);
    enterEdit(next);
  }

  document.addEventListener('click', function (evt) {
    var display = evt.target.closest('.node-display');
    if (!display) return;
    if (evt.target.closest('a')) return; // let refs/tags navigate
    enterEdit(display.closest('.node-row'));
  });

  document.addEventListener('keydown', function (evt) {
    var input = evt.target.closest && evt.target.closest('.node-input');
    if (!input) return;
    var row = input.closest('.node-row');

    if (evt.key === 'Enter' && !evt.shiftKey) {
      evt.preventDefault();
      op(input, input.dataset.createUrl);
    } else if (evt.key === 'Tab') {
      evt.preventDefault();
      op(input, evt.shiftKey ? input.dataset.outdentUrl : input.dataset.indentUrl);
    } else if (evt.key === 'Backspace' && input.value === '') {
      var node = row.closest('.node');
      var hasChildren = node.querySelector('.node-children .node-row') !== null;
      if (!hasChildren) {
        evt.preventDefault();
        op(input, input.dataset.deleteUrl, false);
      }
    } else if (evt.key === 'ArrowUp') {
      evt.preventDefault();
      moveFocus(row, -1);
    } else if (evt.key === 'ArrowDown') {
      evt.preventDefault();
      moveFocus(row, 1);
    } else if (evt.key === 'Escape') {
      input.blur();
    }
  });

  document.addEventListener('input', function (evt) {
    var input = evt.target.closest && evt.target.closest('.node-input');
    if (!input) return;
    autoGrow(input);
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function () { saveSilent(input); }, 1500);
  });

  document.addEventListener('focusout', function (evt) {
    var input = evt.target.closest && evt.target.closest('.node-input');
    if (!input || suppressBlur) return;
    saveSilent(input);
    exitEdit(input.closest('.node-row'));
  });

  document.addEventListener('htmx:afterSwap', function () {
    var outline = document.getElementById('outline');
    if (!outline) return;
    var focusId = outline.getAttribute('data-focus');
    if (!focusId) return;
    outline.removeAttribute('data-focus');
    var row = outline.querySelector('.node-row[data-id="' + focusId + '"]');
    if (row) enterEdit(row);
  });
})();
