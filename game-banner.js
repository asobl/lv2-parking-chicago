(function () {
  // Don't show on the homepage — it already has full today info
  var path = window.location.pathname;
  if (path === '/' || path === '/index.html') return;

  // Don't show if dismissed this session
  if (sessionStorage.getItem('game_banner_dismissed')) return;

  var todayLocal = new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD in local time

  fetch('/data/today.json')
    .then(function (r) { return r.json(); })
    .then(function (d) {
      // Only show when LV2 is actually active today and data is current
      if (!d.lv2Active || d.date !== todayLocal) return;

      // Build label from first event, fall back to generic
      var label = 'Wrigley event today';
      if (d.events && d.events.length) {
        var ev = d.events[0];
        var icon = ev.type === 'game' ? '\u26be' : '\u{1F3B5}';
        label = icon + '\u00a0' + (ev.name || 'Event') + (ev.time ? ', ' + ev.time : '');
      }

      var banner = document.createElement('div');
      banner.id = 'game-day-banner';
      banner.innerHTML =
        '<div class="gdb-inner">' +
          '<span class="gdb-label">' + label + '</span>' +
          '<span class="gdb-sep">\u2014</span>' +
          '<span class="gdb-msg">LV2 no parking after 5\u202fPM</span>' +
          '<a class="gdb-link" href="/">See today\'s status \u2192</a>' +
          '<button class="gdb-close" aria-label="Dismiss">\u00d7</button>' +
        '</div>';

      banner.querySelector('.gdb-close').addEventListener('click', function () {
        banner.remove();
        sessionStorage.setItem('game_banner_dismissed', '1');
        if (typeof gtag !== 'undefined') gtag('event', 'game_banner_dismissed');
      });

      // Insert before the top-bar (first child of body, or before .top-bar)
      var topBar = document.querySelector('.top-bar');
      if (topBar) {
        document.body.insertBefore(banner, topBar);
      } else {
        document.body.prepend(banner);
      }

      if (typeof gtag !== 'undefined') gtag('event', 'game_banner_shown');
    })
    .catch(function () { /* silently ignore network errors */ });
})();
