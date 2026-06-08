/* Air-Gapped Latin Translator — main.js
   Operation status badge + form submission indicator.
   TTS playback controls are the only feature requiring JS.
   All core workflows (translation, PDF) function with JS disabled. */

(function () {
  'use strict';

  var badge = document.getElementById('status-badge');

  function showBadge(msg) {
    if (!badge) return;
    badge.textContent = msg || '⟳ Processing…';
    badge.hidden = false;
  }

  function hideBadge() {
    if (!badge) return;
    badge.hidden = true;
    badge.textContent = '';
  }

  /* Show status badge on form submit; hide on page load (response received). */
  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', function () {
      /* Don't show badge for feedback/level-switch forms */
      var action = form.getAttribute('action') || '';
      if (action.indexOf('/feedback') !== -1 || action.indexOf('/set-level') !== -1) return;
      showBadge('⟳ Processing…');
    });
  });

  /* Hide badge immediately — we're on a fresh page, operation completed. */
  hideBadge();
}());
