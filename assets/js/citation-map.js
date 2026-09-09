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
    const mapped = count('mapped_external_citing_works');
    const missing = count('unmapped_external_citing_works', Math.max(0, external - mapped));
    const partial = count('partial_region_coverage_external_citing_works');
    summary.innerHTML = `<span class="citation-map__metric"><strong>${number.format(external)}</strong> external citing papers</span><span class="citation-map__sep">·</span><span class="citation-map__metric"><strong>${number.format(regions.length)}</strong> states / provinces</span><span class="citation-map__sep">·</span><span class="citation-map__metric"><strong>${number.format(institutions.length)}</strong> institutions</span>`;
    const date = new Date(data.updated_at);
    const dateText = Number.isNaN(date.valueOf()) ? String(data.updated_at || '') : date.toLocaleDateString('en', {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'});
    figure.querySelector('[data-map-coverage]').innerHTML = `${number.format(mapped)} of ${number.format(external)} external citing papers have at least one mapped affiliation.${missing ? ` ${plural(missing, 'paper')} could not be located.` : ''}${partial ? ` Additional affiliations remain unresolved for ${plural(partial, 'mapped paper')}.` : ''} Updated <time datetime="${escape(data.updated_at)}">${escape(dateText)}</time>.`;

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
    const land = L.geoJSON(countries, {pane:'land', interactive:false, style:{color:'#a9bdc8', weight:.65, opacity:.85, fillColor:'#e8f0f3', fillOpacity:1, smoothFactor:.6}}).addTo(map);
    let boundaries;
    let mode = 'regions';
    let automaticMode = true;
    let changedView = false;
    const dots = L.layerGroup().addTo(map);
    const markers = new Map();
    const modeButtons = [...figure.querySelectorAll('[data-map-mode]')];
    const locationSelect = figure.querySelector('[data-map-location]');

    function home() {
      automaticMode = false;
      map.fitBounds(worldBounds, {animate:false, padding:[4, 4]});
      automaticMode = true;
      changedView = false;
      setMode('regions');
    }
    const getPlaces = () => mode === 'regions' ? regions : institutions;
    // Circle area is proportional to paper count; a single paper has radius 4.
    const radius = value => Math.sqrt(Math.max(1, value)) * 4;
    function pointLabel(place) {
      const location = mode === 'regions' ? place.country : [place.region, place.country].filter(Boolean).join(', ');
      return `${place.name}, ${location}: ${plural(place.citing_work_count, 'citing paper')}`;
    }
    function popupHTML(place, currentMode, short = false) {
      const location = currentMode === 'regions' ? place.country : [place.region, place.country].filter(Boolean).join(', ');
      let html = `<strong class="citation-map__popup-title">${escape(place.name)}</strong><span class="citation-map__popup-location">${escape(location)}</span><p class="citation-map__popup-count">${plural(place.citing_work_count, 'external citing paper')}</p>`;
      if (currentMode === 'regions') {
        const members = institutions.filter(p => p.region_id === place.id);
        html += `<span>${plural(place.institution_count ?? members.length, 'mapped institution')}</span>`;
        if (!short && members.length) {
          html += '<ul class="citation-map__popup-list">' + members.slice(0, 5).map(p => `<li><span>${escape(p.name)}</span><b>${number.format(p.citing_work_count)}</b></li>`).join('') + '</ul>';
          if (members.length > 5) html += `<p class="citation-map__popup-note">${plural(members.length - 5, 'more institution')} in this region.</p>`;
          html += '<p class="citation-map__popup-note">Marker placed at the most-cited mapped institution in this region.</p><button class="citation-map__popup-button" type="button" data-show-institutions>Explore institutions</button>';
        }
      } else if (!short) {
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
      markers.clear();
      const places = getPlaces();
      // Large circles render first, leaving smaller nearby affiliations reachable.
      for (const place of places) {
        const marker = L.circleMarker([place.latitude, place.longitude], {
          pane:'dots', radius:radius(place.citing_work_count),
          color:'#336f92', weight:1.15, opacity:.92,
          fillColor:'#7caabf', fillOpacity:.62, bubblingMouseEvents:false
        });
        marker.bindTooltip(popupHTML(place, mode, true), {direction:'top', offset:[0, -6], opacity:1, className:'citation-map__tooltip'});
        marker.bindPopup(popupHTML(place, mode), {maxWidth:290, minWidth:210, autoPanPadding:[18,18]});
        marker.on('popupopen', event => {
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
        markers.set(String(place.id), marker);
      }
      const maximum = Math.max(1, ...places.map(p => p.citing_work_count));
      const sizes = [...new Set([1, Math.max(1, Math.round(maximum / 3)), maximum])];
      figure.querySelector('.citation-map__legend').innerHTML = sizes.map(n => `<span class="citation-map__legend-item"><span class="citation-map__legend-dot" style="width:${radius(n) * 2}px;height:${radius(n) * 2}px"></span>${number.format(n)}</span>`).join('') + '<span>citing papers</span>';
      const options = [...places].sort((a,b) => a.name.localeCompare(b.name));
      locationSelect.replaceChildren(new Option(mode === 'regions' ? 'Choose a state or province' : 'Choose an institution', ''), ...options.map(place => new Option(`${place.name}, ${place.country} (${number.format(place.citing_work_count)})`, String(place.id))));
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
    locationSelect.addEventListener('change', () => {
      const place = getPlaces().find(p => String(p.id) === locationSelect.value);
      if (!place) return;
      automaticMode = false;
      changedView = true;
      const marker = markers.get(String(place.id));
      map.setView([place.latitude, place.longitude], mode === 'regions' ? 4.75 : 6.5, {animate:!reducedMotion});
      marker.openPopup();
    });
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
      figure.querySelector('figcaption').append(note);
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
