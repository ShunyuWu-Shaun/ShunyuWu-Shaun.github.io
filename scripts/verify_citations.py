#!/usr/bin/env python3
"""Independently reconcile the citation ledger, affiliations, and public map."""
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = root/'_data/citations/current'
read = lambda name: json.loads((base/name).read_text())
works = {w['id'].split('/')[-1]:w for w in read('citing-works.json')}
affiliations = read('author-affiliations.json')
public = json.loads((root/'assets/data/citation-geography.json').read_text())
summary = public['summary']
with (base/'citation-edges.csv').open(encoding='utf-8-sig') as f: edges=list(csv.DictReader(f))
assert len(edges)==len({(e['citing_work_id'],e['cited_work_id']) for e in edges})==summary['citation_edges']
assert len(works)==summary['unique_citing_works']
assert len({w['doi'] for w in works.values() if w.get('doi')})==sum(bool(w.get('doi')) for w in works.values())
assert len(affiliations)==sum(sum(max(1,len(a.get('institutions',[]))) for a in w.get('authorships',[])) for w in works.values())
external=set(); by_region=defaultdict(set); by_inst=defaultdict(set); by_work=defaultdict(list)
for wid,w in works.items():
    assert set(w['cited_target_ids']) == {e['cited_work_id'] for e in edges if e['citing_work_id']==wid}
    direct=any((a.get('author',{}).get('id') or '').endswith('/A5087893108') or (a.get('author',{}).get('orcid') or '').endswith('/0000-0001-9856-2148') for a in w.get('authorships',[]))
    assert direct == w['is_direct_self_citation']
    if not direct and w.get('type')!='paratext': external.add(wid)
    assert w['authorships_truncated']==w.get('is_authors_truncated')
for a in affiliations:
    wid=a['citing_work_id']; by_work[wid].append(a)
    included=wid in external and a['geo_status']=='institution_geo'
    assert a['included_in_public_map']==included
    source=works[wid]['authorships'][a['author_order']-1]
    assert a['raw_affiliation_strings']==source.get('raw_affiliation_strings',[])
    if included:
        assert -90<=a['latitude']<=90 and -180<=a['longitude']<=180
        by_region[a['region_id']].add(wid);by_inst[a['institution_id']].add(wid)
for wid,w in works.items():
    expected=bool(w.get('authorships')) and not w['authorships_truncated'] and all(a['geo_status'] in ('institution_geo','excluded_sponsor_parent_with_university') for a in by_work[wid])
    assert w['geography_complete']==expected,(wid,'geography completeness')
for kind, grouped in [('regions',by_region),('institutions',by_inst)]:
    assert {p['id'] for p in public[kind]}==set(grouped)
    for p in public[kind]: assert p['citing_work_count']==len(grouped[p['id']])
mapped=set().union(*by_region.values())
assert len(external)==summary['external_citing_works']
assert len(mapped)==summary['mapped_external_citing_works']
assert len(external-mapped)==summary['unmapped_external_citing_works']
assert math.isclose(sum(p['fractional_count'] for p in public['regions']),len(mapped),abs_tol=1e-4)
assert not any(p['id'] in ('IT-parma','MA-rabat-sale-zemmour-zaer') for p in public['regions'])
site=root/'_site'
if site.exists():
    assert not (site/'_data').exists()
    for path in site.rglob('*'):
        assert path.name not in ('citation-ledger.csv','citation-ledger.md','author-affiliations.csv','citing-works.json')
print(f"PASS: {len(works)} records, {len(edges)} citation edges, {len(affiliations)} author-affiliation rows; {len(mapped)}/{len(external)} external papers mapped across {len(by_region)} regions.")
