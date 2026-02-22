(function () {
  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) {
      el.textContent = value;
    }
  }

  function monitorBusuanzi() {
    var tries = 0;
    var timer = setInterval(function () {
      tries += 1;
      var pv = document.getElementById('busuanzi_value_site_pv');
      var uv = document.getElementById('busuanzi_value_site_uv');
      if (pv && uv && pv.textContent.trim() && uv.textContent.trim()) {
        setText('visitor-pv', pv.textContent.trim());
        setText('visitor-uv', uv.textContent.trim());
        clearInterval(timer);
        return;
      }
      if (tries > 25) {
        clearInterval(timer);
      }
    }, 800);
  }

  function loadGeoHint() {
    var controller = new AbortController();
    var timeout = setTimeout(function () {
      controller.abort();
    }, 4500);

    fetch('https://ipapi.co/json/', { signal: controller.signal })
      .then(function (res) {
        if (!res.ok) {
          throw new Error('geo request failed');
        }
        return res.json();
      })
      .then(function (data) {
        clearTimeout(timeout);
        var parts = [];
        if (data.city) parts.push(data.city);
        if (data.region) parts.push(data.region);
        if (data.country_name) parts.push(data.country_name);
        if (parts.length > 0) {
          setText('visitor-geo', parts.join(', '));
        }
      })
      .catch(function () {
        clearTimeout(timeout);
        setText('visitor-geo', 'Unavailable');
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      monitorBusuanzi();
      loadGeoHint();
    });
  } else {
    monitorBusuanzi();
    loadGeoHint();
  }
})();
