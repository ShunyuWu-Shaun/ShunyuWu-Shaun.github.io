"""Complete missing first-order regions from institution city coordinates."""
from __future__ import annotations
import hashlib
import json
import tempfile
import urllib.request
from pathlib import Path

SOURCE_SHA256 = '22d0e3ad85eb3e27f17cabf8ba2d50e554fbc27a87796ff891d958185da62fb5'
SOURCE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_10m_admin_1_states_provinces.geojson'

def inside_ring(x, y, ring):
    inside = False
    for p, q in zip(ring, ring[1:] + ring[:1]):
        if (p[1] > y) != (q[1] > y):
            cross = (q[0]-p[0]) * (y-p[1]) / (q[1]-p[1]) + p[0]
            if x < cross:
                inside = not inside
    return inside

def contains(x, y, rings):
    outer = rings[0]
    if not (min(p[0] for p in outer) <= x <= max(p[0] for p in outer)
            and min(p[1] for p in outer) <= y <= max(p[1] for p in outer)):
        return False
    return inside_ring(x,y,outer) and not any(inside_ring(x,y,h) for h in rings[1:])

def complete_regions(institutions, lookup_path, offline=False, polygon_path=None):
    saved = json.loads(lookup_path.read_text()) if lookup_path.exists() else {'source':SOURCE,'lookups':{}}
    overrides_path = lookup_path.with_name('region-overrides.json')
    overrides = json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
    pending = []
    for iid, inst in institutions.items():
        g = inst.get('geo') or {}
        inst['geo_original'] = dict(g)
        g['country_code'] = g.get('country_code') or inst.get('country_code')
        inst['region_basis'] = 'OpenAlex institution.geo.region' if g.get('region') else 'unresolved'
        override = overrides.get(iid)
        if override and all(g.get(k) == override[k] for k in ('latitude','longitude','country_code')):
            g['region'] = override['region']
            inst['region_basis'] = override['basis']
            inst['region_source'] = override['source']
        if g.get('region') or g.get('latitude') is None or g.get('longitude') is None:
            continue
        key = f"{g.get('country_code')}:{g['latitude']}:{g['longitude']}"
        if key not in saved['lookups']:
            pending.append((key, g))
    if pending:
        if offline:
            raise RuntimeError('Missing saved region lookups; run once online with --admin1-polygons')
        path = Path(polygon_path) if polygon_path else Path(tempfile.gettempdir())/'citation-admin1-v5.1.2.geojson'
        if not path.exists():
            urllib.request.urlretrieve(SOURCE, path)
        raw = path.read_bytes()
        saved['source_sha256'] = hashlib.sha256(raw).hexdigest()
        if saved['source_sha256'] != SOURCE_SHA256:
            raise RuntimeError('Admin-1 data do not match the verified Natural Earth v5.1.2 source hash')
        features = json.loads(raw)['features']
        by_country = {}
        for f in features:
            if not f.get('geometry'): continue
            cc = f['properties'].get('iso_a2')
            by_country.setdefault(cc, []).append(f)
        for key, g in pending:
            cc = g.get('country_code')
            candidates = by_country.get(cc, []) if cc else features
            matches = []
            for f in candidates:
                geom = f.get('geometry') or {}
                polys = geom.get('coordinates', []) if geom.get('type') == 'MultiPolygon' else [geom.get('coordinates', [])]
                if any(rings and contains(g['longitude'], g['latitude'], rings) for rings in polys):
                    matches.append(f['properties'])
            if len(matches) == 1:
                p = matches[0]
                # HK/MO city coordinates do not identify an author-specific district.
                name = p.get('admin') if cc in ('HK','MO') else p.get('name_en') or p['name']
                saved['lookups'][key] = {'region': name, 'country_code': cc or p['iso_a2'],
                    'country':g.get('country') or p.get('admin'), 'admin1_code':p.get('iso_3166_2'),
                    'polygon_name':p.get('name'), 'basis':'Natural Earth v5.1.2 point-in-polygon using institution city coordinates',
                    'jurisdiction_level_label':cc in ('HK','MO')}
            else:
                saved['lookups'][key] = {'region':None, 'basis':'No unique point-in-polygon match', 'matches':len(matches)}
        lookup_path.parent.mkdir(parents=True, exist_ok=True)
        lookup_path.write_text(json.dumps(saved, ensure_ascii=False, indent=2)+'\n')
    for inst in institutions.values():
        g=inst.get('geo') or {}
        if g.get('region') or g.get('latitude') is None or g.get('longitude') is None: continue
        key=f"{g.get('country_code')}:{g['latitude']}:{g['longitude']}"
        match=saved['lookups'].get(key,{})
        if match.get('region'):
            g.update({k:match[k] for k in ('region','country_code','country')})
            inst['region_basis']=match['basis']
            inst['region_source']=SOURCE
            inst['region_source_sha256']=saved['source_sha256']
            inst['region_admin1_code']=match.get('admin1_code')
        inst['geo']=g
    return saved
