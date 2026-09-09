/* The map reads only aggregate geography. The citation ledger stays outside the site. */
(() => {
  'use strict';
  const number = new Intl.NumberFormat('en');
  const plural = (n, word) => `${number.format(n)} ${word}${n === 1 ? '' : 's'}`;
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[char]));
  const validPoint = p => Number.isFinite(p.latitude) && Number.isFinite(p.longitude) && Math.abs(p.latitude) <= 85 && Math.abs(p.longitude) <= 180;
  const byCount = (a, b) => b.citing_work_count - a.citing_work_count || a.name.localeCompare(b.name);
  const fetchJSON = async path => {
    const response = await fetch(path, {credentials: 'same-origin'});
    if (!response.ok) throw new Error(`Citation map resource ${response.status}: ${path}`);
    return response.json();
  };

  async function initialize(figure) {
    const canvas = figure.querySelector('.citation-map__canvas');
    const summary = figure.querySelector('.citation-map__summary');
    if (!window.L) throw new Error('Local Leaflet library did not load.');
    const [data, countries] = await Promise.all([
      fetchJSON(figure.dataset.source), fetchJSON('/assets/data/citation-world.geojson')
    ]);
    const regions = (data.regions || []).filter(validPoint).sort(byCount);
    const institutions = (data.institutions || []).filter(validPoint).sort(byCount);
    const stats = data.summary || {};
    const count = (key, fallback = 0) => Number.isFinite(stats[key]) ? stats[key] : fallback;
    const external = count('external_citing_works');
    summary.innerHTML = `<span class="citation-map__metric"><strong>${number.format(external)}</strong> external citing papers</span><span class="citation-map__sep">·</span><span class="citation-map__metric"><strong>${number.format(regions.length)}</strong> states / provinces</span><span class="citation-map__sep">·</span><span class="citation-map__metric"><strong>${number.format(institutions.length)}</strong> institutions</span>`;

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const worldBounds = L.latLngBounds([[-55, -169], [74, 178]]);
    const map = L.map(canvas, {
      attributionControl: true, zoomControl: false,
      minZoom: 0, maxZoom: 8, zoomSnap: .25, zoomDelta: .5,
      scrollWheelZoom: false, worldCopyJump: false,
      maxBounds: [[-85, -190], [85, 190]], maxBoundsViscosity: .8,
      zoomAnimation: !reducedMotion, fadeAnimation: !reducedMotion
    });
    map.attributionControl.setPrefix('<a href="https://leafletjs.com/">Leaflet</a>');
    map.attributionControl.addAttribution('Made with <a href="https://www.naturalearthdata.com/">Natural Earth</a> · <a href="https://www.geonames.org/">GeoNames</a>');
    L.control.zoom({position: 'topright'}).addTo(map);
    map.createPane('land').style.zIndex = 200;
    map.createPane('subdivisions').style.zIndex = 250;
    map.createPane('dots').style.zIndex = 450;
    L.geoJSON(countries, {pane:'land', interactive:false, style:{color:'#a9bdc8', weight:.65, opacity:.85, fillColor:'#e8f0f3', fillOpacity:1, smoothFactor:.6}}).addTo(map);
    let boundaries;
    let mode = 'regions';
    let automaticMode = true;
    let changedView = false;
    const dots = L.layerGroup().addTo(map);
    const modeButtons = [...figure.querySelectorAll('[data-map-mode]')];

    function home() {
      automaticMode = false;
      map.fitBounds(worldBounds, {animate:false, padding:[4, 4]});
      automaticMode = true;
      changedView = false;
      setMode('regions');
    }
    const getPlaces = () => mode === 'regions' ? regions : institutions;
    // Circle area is proportional to paper count; compact dots limit overlap.
    const radius = value => Math.sqrt(Math.max(1, value)) * 3;
    function pointLabel(place) {
      const location = mode === 'regions' ? place.country : [place.region, place.country].filter(Boolean).join(', ');
      return `${place.name}, ${location}: ${plural(place.citing_work_count, 'citing paper')}`;
    }
    function tooltipHTML(place) {
      return `<strong class="citation-map__tooltip-title">${escape(place.name)}</strong><span class="citation-map__tooltip-count">${plural(place.citing_work_count, 'citing paper')}</span>`;
    }
    function popupHTML(place, currentMode) {
      const location = currentMode === 'regions' ? place.country : [place.region, place.country].filter(Boolean).join(', ');
      let html = `<strong class="citation-map__popup-title">${escape(place.name)}</strong><span class="citation-map__popup-location">${escape(location)}</span><p class="citation-map__popup-count">${plural(place.citing_work_count, 'external citing paper')}</p>`;
      if (currentMode === 'regions') {
        const members = institutions.filter(p => p.region_id === place.id);
        html += `<span>${plural(place.institution_count ?? members.length, 'mapped institution')}</span>`;
        if (members.length) {
          html += '<ul class="citation-map__popup-list">' + members.slice(0, 5).map(p => `<li><span>${escape(p.name)}</span><b>${number.format(p.citing_work_count)}</b></li>`).join('') + '</ul>';
          if (members.length > 5) html += `<p class="citation-map__popup-note">${plural(members.length - 5, 'more institution')} in this region.</p>`;
          html += '<p class="citation-map__popup-note">Marker placed at the most-cited mapped institution in this region.</p><button class="citation-map__popup-button" type="button" data-show-institutions>Explore institutions</button>';
        }
      } else {
        html += '<p class="citation-map__popup-note">Affiliation location; it may represent a main campus or city.</p>';
      }
      return html;
    }
    function explore(place) {
      const members = institutions.filter(p => p.region_id === place.id);
      automaticMode = false;
      changedView = true;
      setMode('institutions');
      if (members.length > 1) map.fitBounds(members.map(p => [p.latitude, p.longitude]), {padding:[55, 55], maxZoom:7, animate:!reducedMotion});
      else map.setView([place.latitude, place.longitude], 6, {animate:!reducedMotion});
    }
    function draw() {
      dots.clearLayers();
      const places = getPlaces();
      // Large circles render first, leaving smaller nearby affiliations reachable.
      for (const place of places) {
        const marker = L.circleMarker([place.latitude, place.longitude], {
          pane:'dots', radius:radius(place.citing_work_count),
          color:'#336f92', weight:1.15, opacity:.92,
          fillColor:'#7caabf', fillOpacity:.62, bubblingMouseEvents:false
        });
        const single = place.citing_work_count === 1;
        marker.bindTooltip(tooltipHTML(place), {direction:'top', offset:[0, -4], opacity:1, className:`citation-map__tooltip${single ? ' citation-map__tooltip--single' : ''}`});
        marker.bindPopup(popupHTML(place, mode), {maxWidth:single ? 220 : 290, minWidth:single ? 140 : 210, autoPanPadding:[18,18], className:single ? 'citation-map__popup--single' : ''});
        marker.on('popupopen', event => {
          marker.closeTooltip();
          const button = event.popup.getElement().querySelector('[data-show-institutions]');
          if (button) button.addEventListener('click', () => explore(place), {once:true});
        });
        marker.addTo(dots);
        const path = marker.getElement();
        if (path) {
          path.setAttribute('tabindex', '0');
          path.setAttribute('role', 'button');
          path.setAttribute('aria-label', pointLabel(place));
          path.addEventListener('keydown', event => {
            if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); event.stopPropagation(); marker.openPopup(); }
            if (event.key === 'Escape') marker.closePopup();
          });
          path.addEventListener('focus', () => marker.openTooltip());
          path.addEventListener('blur', () => marker.closeTooltip());
        }
      }
      figure.dataset.mode = mode;
    }
    function setMode(next) {
      mode = next;
      modeButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.mapMode === mode)));
      draw();
    }
    modeButtons.forEach(button => button.addEventListener('click', () => {
      automaticMode = false;
      setMode(button.dataset.mapMode);
    }));
    figure.querySelector('[data-map-reset]').addEventListener('click', home);
    map.on('zoomend', () => {
      if (boundaries) boundaries.setStyle({opacity:map.getZoom() >= 3 ? .8 : .28, weight:map.getZoom() >= 4 ? .65 : .4});
      if (automaticMode) {
        const next = map.getZoom() >= 5 ? 'institutions' : 'regions';
        if (next !== mode) setMode(next);
      }
    });
    map.on('dragstart zoomstart', () => { changedView = true; });
    // Local boundaries are loaded after the country outline so the first view stays fast.
    fetchJSON('/assets/data/citation-admin1.geojson').then(data => {
      boundaries = L.geoJSON(data, {pane:'subdivisions', interactive:false, style:{color:'#a2b6c1', weight:.4, opacity:.28, fill:false, smoothFactor:.5}}).addTo(map);
      map.fire('zoomend');
    }).catch(error => {
      console.warn(error);
      const note = document.createElement('p');
      note.textContent = 'State and province boundaries could not be loaded; affiliation points are still shown.';
      note.setAttribute('role', 'status');
      figure.append(note);
    });
    home();
    if (window.ResizeObserver) new ResizeObserver(() => { map.invalidateSize({pan:false}); if (!changedView) home(); }).observe(canvas);
    figure.dataset.ready = 'true';
  }
  function start() {
    document.querySelectorAll('[data-citation-map]').forEach(figure => {
      const load = () => initialize(figure).catch(error => {
        console.error(error);
        figure.querySelector('.citation-map__summary').textContent = 'Citation geography is temporarily unavailable.';
        const canvas = figure.querySelector('.citation-map__canvas');
        canvas.classList.add('citation-map__error');
        canvas.textContent = 'The local map data could not be loaded. Reload this page to try again.';
        figure.dataset.ready = 'error';
      });
      if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(entries => {
          if (entries.some(entry => entry.isIntersecting)) { observer.disconnect(); load(); }
        }, {rootMargin:'350px'});
        observer.observe(figure);
      } else load();
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
})();
