(function () {
  var globeLibPromise = null;

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

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.onload = resolve;
      script.onerror = function () {
        reject(new Error('script load failed: ' + src));
      };
      document.head.appendChild(script);
    });
  }

  function ensureGlobeLib() {
    if (window.Globe) {
      return Promise.resolve();
    }
    if (globeLibPromise) {
      return globeLibPromise;
    }

    globeLibPromise = loadScript('https://unpkg.com/globe.gl@2.45.0/dist/globe.gl.min.js');
    return globeLibPromise;
  }

  function renderGlobe(visitorPoint) {
    var containers = document.querySelectorAll('.visitor-globe');
    if (!containers.length) {
      return;
    }

    var points = [
      {
        lat: 31.2304,
        lng: 121.4737,
        size: 0.2,
        color: '#f472b6',
        label: 'Research base: Shanghai'
      }
    ];

    if (visitorPoint && typeof visitorPoint.lat === 'number' && typeof visitorPoint.lng === 'number') {
      points.push({
        lat: visitorPoint.lat,
        lng: visitorPoint.lng,
        size: 0.28,
        color: '#22b8a7',
        label: 'Current visitor: ' + visitorPoint.label
      });
    }

    ensureGlobeLib()
      .then(function () {
        containers.forEach(function (container) {
          container.innerHTML = '';

          var width = container.clientWidth || 420;
          var height = container.clientHeight || 320;

          var globe = window.Globe()(container)
            .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
            .backgroundImageUrl('https://unpkg.com/three-globe/example/img/night-sky.png')
            .backgroundColor('rgba(0,0,0,0)')
            .showAtmosphere(true)
            .atmosphereColor('#fda4af')
            .atmosphereAltitude(0.2)
            .pointsData(points)
            .pointLat('lat')
            .pointLng('lng')
            .pointAltitude('size')
            .pointRadius(0.35)
            .pointColor('color')
            .pointLabel('label')
            .width(width)
            .height(height);

          globe.pointOfView({ lat: 28, lng: 98, altitude: 1.95 }, 800);

          var controls = globe.controls();
          if (controls) {
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.45;
            controls.enablePan = false;
            controls.minDistance = 170;
            controls.maxDistance = 350;
          }

          var onResize = function () {
            globe.width(container.clientWidth || 420);
            globe.height(container.clientHeight || 320);
          };
          window.addEventListener('resize', onResize);
        });
      })
      .catch(function () {
        containers.forEach(function (container) {
          container.innerHTML = '<div class="globe-fallback">3D globe is temporarily unavailable.</div>';
        });
      });
  }

  function loadGeoHint() {
    var controller = new AbortController();
    var timeout = setTimeout(function () {
      controller.abort();
    }, 5000);

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
        } else {
          setText('visitor-geo', 'Unavailable');
        }

        var lat = parseFloat(data.latitude);
        var lng = parseFloat(data.longitude);
        if (!Number.isNaN(lat) && !Number.isNaN(lng)) {
          renderGlobe({ lat: lat, lng: lng, label: parts.join(', ') || 'Unknown region' });
        } else {
          renderGlobe(null);
        }
      })
      .catch(function () {
        clearTimeout(timeout);
        setText('visitor-geo', 'Unavailable');
        renderGlobe(null);
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
