#!/usr/bin/env python3
"""Refresh a provenance-preserving citation ledger and public GIS aggregates.

No credentials or full citation lists are shipped to the website. The excluded-
from-rendering directory is still readable in this public Git repository.
"""
from __future__ import annotations
import argparse
import csv
import copy
import hashlib
import html
import json
import math
import os
import re
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from citation_regions import complete_regions

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '_data/citations'
CACHE = BASE / 'cache'
OUT = BASE / 'current'
AUTHOR = 'A5087893108'
ORCID = '0000-0001-9856-2148'
DOIS = [
 '10.1109/TSG.2025.3601238','10.1016/j.eswa.2024.124508',
 '10.1109/TCSS.2023.3272330','10.23919/CCC52363.2021.9550182',
 '10.1016/j.eswa.2026.133261','10.1109/TSMC.2023.3344883',
 '10.1109/TASE.2023.3299185','10.1109/CDC49753.2023.10383316',
 '10.1016/j.ifacol.2023.10.581','10.23919/CCC52363.2021.9550267',
 '10.1109/TASE.2023.3236306','10.1109/TSMC.2023.3327450',
 '10.48550/arXiv.2603.23232','10.1007/s10489-026-07434-4',
 '10.1109/TSMC.2024.3373456',
]
WORK_FIELDS = 'id,doi,title,publication_year,publication_date,type,authorships,is_authors_truncated,primary_location,is_retracted'
LOCK = threading.Lock()
LAST = 0.0
OFFLINE = False
REQUESTS = []


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def sid(x):
    return (x or '').rstrip('/').rsplit('/', 1)[-1]


def doi(x):
    return re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:)', '', x or '', flags=re.I).lower().strip()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def request(path, **params):
    global LAST
    query = urllib.parse.urlencode(params)
    url = 'https://api.openalex.org' + path + ('?' + query if query else '')
    key = hashlib.sha256(url.encode()).hexdigest()
    cache = CACHE / (key + '.json')
    if OFFLINE:
        if not cache.exists():
            raise RuntimeError('Missing offline response: ' + url)
        envelope = json.loads(cache.read_text())
    else:
        headers = {'User-Agent': 'academic-citation-ledger/2.0', 'Accept': 'application/json'}
        if os.environ.get('OPENALEX_API_KEY'):
            headers['Authorization'] = 'Bearer ' + os.environ['OPENALEX_API_KEY']
        for attempt in range(5):
            with LOCK:
                delay = .16 - (time.monotonic() - LAST)
                if delay > 0:
                    time.sleep(delay)
                LAST = time.monotonic()
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=50) as response:
                    data = json.load(response)
                envelope = {'url': url, 'retrieved_at': now(), 'data': data}
                write_json(cache, envelope)
                break
            except (urllib.error.URLError, TimeoutError) as exc:
                if isinstance(exc, urllib.error.HTTPError) and exc.code not in (429, 500, 502, 503, 504):
                    raise
                if attempt == 4:
                    raise
                time.sleep(min(2**attempt, 8))
    with LOCK:
        REQUESTS.append({'url': url, 'retrieved_at': envelope['retrieved_at'], 'cache_file': cache.relative_to(BASE).as_posix()})
    return envelope['data']


def resolve_target(d):
    r = request('/works/doi:' + d, select=WORK_FIELDS + ',cited_by_count')
    r['requested_doi'] = d
    r['scope_basis'] = ('Publisher-deposited Crossref ORCID matches profile author; supplementary to Scholar list' if doi(d) == '10.1109/tsmc.2024.3373456' else 'Google Scholar profile publication list, verified DOI')
    return r


def collect_citers(target):
    cursor = '*'
    works = {}
    pages = []
    seen = set()
    while cursor:
        if cursor in seen:
            raise RuntimeError('Repeated cursor for ' + target['id'])
        seen.add(cursor)
        p = request('/works', filter='cites:' + sid(target['id']), per_page=100,
                    cursor=cursor, select=WORK_FIELDS, corpus='all')
        records = p.get('results', [])
        for r in records:
            works[sid(r['id'])] = r
        pages.append({'count': p.get('meta', {}).get('count'), 'records': len(records)})
        if not records:
            break
        cursor = p.get('meta', {}).get('next_cursor')
    expected = pages[0]['count']
    if len(works) != expected:
        raise RuntimeError(f'Incomplete citing-work query for {target["id"]}: {len(works)} of {expected}')
    return {'target_id': sid(target['id']), 'expected': expected, 'retrieved': len(works), 'pages': pages, 'works': list(works.values())}


def write_csv(path, records, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
        w.writeheader()
        for r in records:
            row = {}
            for k in fields:
                value = r.get(k, '')
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                # Preserve source text and prevent spreadsheet formula execution.
                if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
                    value = "'" + value
                row[k] = value
            w.writerow(row)


def region_key(cc, name):
    slug = re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', name).encode('ascii','ignore').decode().lower()).strip('-')
    return cc + '-' + (slug or hashlib.sha256(name.encode()).hexdigest()[:10])


def valid_geo(g):
    lat, lon = g.get('latitude'), g.get('longitude')
    return (isinstance(lat,(int,float)) and isinstance(lon,(int,float)) and
            math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180)


def main():
    global OFFLINE
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--admin1-polygons', help='Optional local Natural Earth v5.1.2 original admin-1 GeoJSON')
    ap.add_argument('--offline', action='store_true', help='Rebuild deterministically from saved API responses')
    args = ap.parse_args()
    OFFLINE = args.offline
    started = now()
    with ThreadPoolExecutor(max_workers=4) as pool:
        targets = list(pool.map(resolve_target, DOIS))
    print(f'Resolved {len(targets)} publication targets', flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        queried = list(pool.map(collect_citers, targets))
    works = {}
    cited_targets = defaultdict(set)
    edges = []
    for q in queried:
        for w in q['works']:
            wid = sid(w['id'])
            works[wid] = w
            cited_targets[wid].add(q['target_id'])
            edges.append({'citing_work_id': wid, 'cited_work_id': q['target_id'], 'source': 'OpenAlex'})
    openalex_edges = len(edges)
    scholar_path = BASE/'sources/scholar-resolved.json'
    scholar = json.loads(scholar_path.read_text()) if scholar_path.exists() else {'records':[], 'new_works':[]}
    edge_index = {(e['citing_work_id'],e['cited_work_id']):e for e in edges}
    work_sources = defaultdict(set, {wid:{'OpenAlex'} for wid in works})
    for w in scholar.get('new_works', []):
        if sid(w['id']) not in works:
            wid = sid(w['id'])
            if re.fullmatch(r'W[0-9]+', wid):
                works[wid] = request('/works/' + wid, select=WORK_FIELDS)
                work_sources[wid].add('OpenAlex')
            else:
                works[wid] = copy.deepcopy(w)
                work_sources[wid].add(w.get('metadata_source', 'Publisher'))
    for record in scholar.get('records', []):
        wid, tid = record['work_id'], record['cited_work_id']
        if tid not in {sid(t['id']) for t in targets} or wid not in works:
            raise RuntimeError('Scholar record is outside the verified target/work scope')
        work_sources[wid].add('Google Scholar')
        cited_targets[wid].add(tid)
        pair = (wid, tid)
        if pair not in edge_index:
            e = {'citing_work_id':wid, 'cited_work_id':tid, 'source':'Google Scholar'}
            edge_index[pair]=e; edges.append(e)
        elif 'Google Scholar' not in edge_index[pair]['source']:
            edge_index[pair]['source'] += '; Google Scholar'
        edge_index[pair]['scholar_source_url'] = record['scholar_record']['source_page_url']
        edge_index[pair]['scholar_retrieved_at'] = record['scholar_record']['retrieved_at']
    print(f'Retrieved {len(edges)} citation edges from {len(works)} distinct citing works', flush=True)
    publisher_path = BASE/'sources/publisher-affiliations.json'
    if publisher_path.exists():
        patch = json.loads(publisher_path.read_text())
        w = works.get(patch['work_id'])
        if w:
            w['authorships_original'] = copy.deepcopy(w.get('authorships', []))
            for verified in patch['authors']:
                a = w['authorships'][verified['author_order']-1]
                if a['author']['display_name'].casefold() != verified['author_name'].casefold():
                    raise RuntimeError('Publisher author identity/order mismatch')
                a['raw_affiliation_strings'] = verified['raw_affiliation_strings']
                a['countries'] = [verified['country_code']]
                a['institutions'] = verified.get('institutions', [])
                a['affiliations'] = [{'raw_affiliation_string':v,'institution_ids':[i['id'] for i in a['institutions']]} for v in a['raw_affiliation_strings']]
                a['affiliation_source'] = patch['source']
                a['verified_region'] = verified['region']
            w['authorships_complete_verified'] = patch['authorships_complete_verified']
            work_sources[patch['work_id']].add('Publisher article')
    manual_path = BASE/'sources/manual-institutions.json'
    manual_institutions = {sid(i['id']):i for i in json.loads(manual_path.read_text())} if manual_path.exists() else {}
    institution_ids = sorted({sid(i['id']) for w in works.values() for a in w.get('authorships', []) for i in a.get('institutions', []) if i.get('id')})
    def get_inst(i):
        if i in manual_institutions: return copy.deepcopy(manual_institutions[i])
        return request('/institutions/' + i, select='id,ror,display_name,country_code,type,geo,lineage')
    with ThreadPoolExecutor(max_workers=5) as pool:
        institutions = {sid(i['id']): i for i in pool.map(get_inst, institution_ids)}
    print(f'Located {len(institutions)} institution records', flush=True)
    complete_regions(institutions, BASE/'sources/region-lookup.json', OFFLINE, args.admin1_polygons)
    affiliations = []
    citation_rows = []
    external = set()
    self_citers = set()
    non_research = set()
    external_records = set()
    all_map_work_regions = defaultdict(set)
    map_work_institutions = defaultdict(set)
    unresolved_works = set()
    excluded_sponsors = 0
    date_notes = {n['work_id']:n['note'] for n in scholar.get('new_work_metadata_notes', [])}
    for wid, w in sorted(works.items(), key=lambda pair: (-(pair[1].get('publication_year') or 0), pair[1].get('title') or '')):
        w['cited_target_ids'] = sorted(cited_targets[wid])
        w['sources'] = sorted(work_sources[wid])
        if wid in date_notes: w['publication_metadata_note'] = date_notes[wid]
        authors = w.get('authorships', [])
        author_ids = {sid(a.get('author',{}).get('id')) for a in authors if a.get('author',{}).get('id')}
        direct_self = AUTHOR in author_ids or any(sid(a.get('author',{}).get('orcid')) == ORCID for a in authors)
        w['is_direct_self_citation'] = direct_self
        w['has_coauthor_overlap_with_cited_targets'] = any(
            author_ids & {sid(a.get('author',{}).get('id')) for a in t.get('authorships',[]) if a.get('author',{}).get('id')}
            for t in targets if sid(t['id']) in cited_targets[wid])
        w['authorships_truncated'] = w.get('is_authors_truncated')
        w['is_non_research_record'] = w.get('type') == 'paratext'
        if w['is_non_research_record']: non_research.add(wid)
        if direct_self: self_citers.add(wid)
        else:
            external_records.add(wid)
            if not w['is_non_research_record']: external.add(wid)
        if not authors or w['authorships_truncated']:
            unresolved_works.add(wid)
        work_regions = set(); work_countries = set(); work_institutions = set()
        for author_index, a in enumerate(authors, 1):
            a_insts = a.get('institutions', [])
            raw = a.get('raw_affiliation_strings', [])
            countries = a.get('countries', [])
            has_education = any(i.get('type') == 'education' for i in a_insts)
            if not a_insts:
                unresolved_works.add(wid)
            for hydrated in a_insts or [{}]:
                iid = sid(hydrated.get('id'))
                inst = institutions.get(iid,{})
                geo = inst.get('geo') or {}
                cc = geo.get('country_code') or hydrated.get('country_code') or ''
                rn = geo.get('region') or ''
                name = inst.get('display_name') or hydrated.get('display_name') or ''
                # A ministry named inside a university laboratory address denotes
                # the sponsor/parent, not a second author workplace at its HQ.
                sponsor = has_education and bool(re.search(r'Ministry of Education', name, re.I))
                if sponsor:
                    status = 'excluded_sponsor_parent_with_university'
                    excluded_sponsors += 1
                elif not iid:
                    status = 'unresolved_institution'
                elif not rn:
                    status = 'region_unavailable'
                elif not valid_geo(geo):
                    status = 'coordinates_unavailable'
                else:
                    status = 'institution_geo'
                rid = region_key(cc, rn) if rn and cc else ''
                row = {'citing_work_id': wid, 'citing_doi': doi(w.get('doi')), 'citing_title': w.get('title'),
                       'publication_year': w.get('publication_year'), 'author_order': author_index,
                       'author_id': sid(a.get('author',{}).get('id')), 'author_name': a.get('author',{}).get('display_name'),
                       'author_orcid': a.get('author',{}).get('orcid'), 'author_position': a.get('author_position'),
                       'institution_id': iid, 'institution_name': name, 'institution_type': inst.get('type'),
                       'ror': inst.get('ror'), 'raw_affiliation_strings': raw,
                       'raw_affiliation_institution_links': a.get('affiliations', []),
                       'reported_country_codes': countries, 'country_code': cc, 'country': geo.get('country') or cc,
                       'state_province': rn, 'region_id': rid, 'city': geo.get('city'),
                       'latitude': geo.get('latitude'), 'longitude': geo.get('longitude'),
                       'geo_status': status, 'geo_source': inst.get('geo_source') or ('https://api.openalex.org/institutions/' + iid if iid else ''),
                       'affiliation_source': a.get('affiliation_source') or w.get('source_url') or w['id'],
                       'verified_region_text': a.get('verified_region'),
                       'region_basis': inst.get('region_basis'), 'region_source': inst.get('region_source'),
                       'region_admin1_code': inst.get('region_admin1_code'),
                       'coordinate_precision': inst.get('coordinate_precision','institution_city_point') if valid_geo(geo) else 'unavailable',
                       'is_direct_self_citation': direct_self,
                       'included_in_public_map': wid in external and status == 'institution_geo'}
                affiliations.append(row)
                if cc: work_countries.add(cc)
                if iid: work_institutions.add(name)
                if rid: work_regions.add(rn)
                if status == 'institution_geo':
                    if wid in external:
                        all_map_work_regions[wid].add(rid)
                        map_work_institutions[wid].add(iid)
                elif not sponsor:
                    unresolved_works.add(wid)
        w['affiliation_country_codes'] = sorted(work_countries)
        w['affiliation_regions'] = sorted(work_regions)
        w['geography_complete'] = wid not in unresolved_works
        citation_rows.append({'citing_work_id':wid,'title':w.get('title'),'doi':doi(w.get('doi')),
          'year':w.get('publication_year'),'publication_date':w.get('publication_date'),
          'publication_metadata_note':w.get('publication_metadata_note'),'type':w.get('type'),
          'authors':[a.get('author',{}).get('display_name') for a in authors],
          'institutions':sorted(work_institutions),'countries':sorted(work_countries),'states_provinces':sorted(work_regions),
          'cited_target_ids':w['cited_target_ids'],'is_direct_self_citation':direct_self,
          'has_coauthor_overlap':w['has_coauthor_overlap_with_cited_targets'],
          'is_non_research_record':w['is_non_research_record'],
          'authorships_truncated':w['authorships_truncated'],'geography_complete':w['geography_complete'],
          'is_retracted':w.get('is_retracted'), 'source':'; '.join(w['sources']), 'source_url':w.get('source_url') or (w['id'] if str(w['id']).startswith('https://') else (w.get('primary_location') or {}).get('landing_page_url'))})
    region_works=defaultdict(set); inst_works=defaultdict(set); region_insts=defaultdict(set); weights=Counter()
    for wid,rids in all_map_work_regions.items():
        for rid in rids:
            region_works[rid].add(wid); weights[rid] += 1/len(rids)
    for wid,iids in map_work_institutions.items():
        for iid in iids:
            inst_works[iid].add(wid)
            g=institutions[iid]['geo'];region_insts[region_key(g['country_code'],g['region'])].add(iid)
    public_insts=[]
    for iid,wids in inst_works.items():
        i=institutions[iid];g=i['geo']
        public_insts.append({'id':iid,'name':i['display_name'],'region_id':region_key(g['country_code'],g['region']),
                             'region':g['region'],'country_code':g['country_code'],'country':g['country'],
                             'city':g['city'],'latitude':g['latitude'],'longitude':g['longitude'],
                             'citing_work_count':len(wids)})
    regions=[]
    for rid,wids in region_works.items():
        representative=sorted(region_insts[rid], key=lambda i:(-len(inst_works[i]),i))[0]
        g=institutions[representative]['geo']
        regions.append({'id':rid,'name':g['region'],'country_code':g['country_code'],'country':g['country'],
          'latitude':g['latitude'],'longitude':g['longitude'],'citing_work_count':len(wids),
          'institution_count':len(region_insts[rid]),'fractional_count':round(weights[rid],6),
          'coordinate_basis':'most_cited_affiliation_institution','representative_institution_id':representative})
    mapped=set(all_map_work_regions)
    summary={'target_works':len(targets),'citation_edges':len(edges),'unique_citing_works':len(works),
             'openalex_citation_edges':openalex_edges, 'scholar_result_records':len(scholar.get('records',[])),
             'scholar_verified_edges':len({(r['work_id'],r['cited_work_id']) for r in scholar.get('records',[])}),
             'scholar_additional_edges':len(edges)-openalex_edges,
             'direct_self_citing_works':len(self_citers),'non_research_citing_records':len(non_research),
             'external_citing_records':len(external_records),'external_citing_works':len(external),
             'mapped_external_citing_works':len(mapped),'unmapped_external_citing_works':len(external-mapped),
             'partial_region_coverage_external_citing_works':len(mapped & unresolved_works),
             'regions':len(regions),'institutions':len(public_insts),
             'countries':len({r['country_code'] for r in regions}),
             'excluded_sponsor_parent_affiliation_rows':excluded_sponsors,
             'authorships_truncated_works':sum(w['authorships_truncated'] is True for w in works.values()),
             'authorship_truncation_status_unknown_works':sum(w['authorships_truncated'] is None for w in works.values())}
    summary['scholar_profile_scope_citation_edges'] = sum(e['cited_work_id'] != sid(next(t['id'] for t in targets if doi(t['doi']) == '10.1109/tsmc.2024.3373456')) for e in edges)
    retrieved_at=max([r['retrieved_at'] for r in REQUESTS] + [scholar.get('retrieved_at', '')])
    public={'updated_at':retrieved_at,'source':'Google Scholar, OpenAlex, and verified publisher metadata','summary':summary,
      'counting_method':'Unique external citing works per region or institution. One work can occur in multiple regions. Direct self-citations and paratext records are excluded only from the map.',
      'regions':sorted(regions,key=lambda r:(-r['citing_work_count'],r['id'])),
      'institutions':sorted(public_insts,key=lambda r:(-r['citing_work_count'],r['id'])),
      'unmapped_summary':{'external_works':len(external-mapped),'partially_mapped_external_works':len(mapped & unresolved_works)}}
    manifest={'started_at':started,'completed_at':now(),'data_retrieved_at':retrieved_at,'source':'Google Scholar, OpenAlex, and verified publisher metadata',
      'scholar_cross_check':{k:v for k,v in scholar.items() if k not in ('records','new_works')},
      'target_scope':'14 DOI-verified works on Google Scholar plus one publisher-ORCID-verified supplementary work',
      'authorship_truncation_note':'The current API omits is_authors_truncated. Unknown values remain null; no claim of independently verified author-list completeness is made.',
      'non_research_rule':'Retain type=paratext records in the retrieval ledger; exclude them from citing-paper and map counts.',
      'corpus':'all','coverage':'All cursor pages for each target. OpenAlex coverage is not identical to Google Scholar.',
      'summary':summary,'queries':[{k:v for k,v in q.items() if k!='works'} for q in queried],
      'requests':sorted(REQUESTS,key=lambda r:r['url']),
      'map_precision':'Institution city coordinates with state/province labels from OpenAlex institution.geo; missing regions are completed by point-in-polygon matching against Natural Earth v5.1.2, with source hashes and original geography retained. Regional symbols use a member institution point, not a state centroid.',
      'self_citation_definition':'The profile author OpenAlex ID or ORCID occurs among the citing authors. Coauthor-overlap is flagged separately and retained.',
      'affiliation_caveat':'Work-level affiliation strings are preserved. Institution geo describes the indexed institution/city, not a verified author-specific campus. Missing locations are not replaced by country capitals.',
      'sponsor_rule':'A Ministry of Education institution co-occurring with an education institution in one authorship is retained in the ledger but excluded as a sponsor/parent from geographical counts.'}
    scholar_targets = json.loads((BASE/'sources/scholar-targets.json').read_text())
    profile_counts = {doi(t['target_doi']):t['scholar_profile_cited_by_count'] for t in scholar_targets['targets']}
    target_queries = {q['target_id']:q for q in queried}
    target_coverage = []
    for t in targets:
        tid=sid(t['id']); target_edges=[e for e in edges if e['cited_work_id']==tid]
        target_coverage.append({'target_work_id':tid,'title':t['title'],'doi':doi(t['doi']),
          'scholar_profile_count':profile_counts.get(doi(t['doi'])),
          'scholar_retrieved_records':sum(r['cited_work_id']==tid for r in scholar.get('records',[])),
          'scholar_unique_edges':len({r['work_id'] for r in scholar.get('records',[]) if r['cited_work_id']==tid}),'openalex_retrieved_edges':target_queries[tid]['retrieved'],
          'union_retrieved_edges':len(target_edges),'non_research_record_edges':sum(e['citing_work_id'] in non_research for e in target_edges),
          'scope_basis':t['scope_basis']})
    manifest['scholar_profile_metrics_snapshot'] = {'metrics_text':scholar_targets['profile_metrics_text'],
      'retrieved_at':scholar_targets['retrieved_at'],'profile_url':scholar_targets['profile_url'],
      'completeness':'All 66 displayed Scholar citation result records enumerated through the actual browser, across 12 pages. Duplicate versions are retained in the Scholar sheet and deduplicated for the map.'}
    manifest['geography_completeness_definition'] = 'Location completeness of returned author affiliation records only; author-list completeness itself is not independently verified.'
    write_csv(OUT/'coverage-by-publication.csv', target_coverage, list(target_coverage[0]))
    write_json(OUT/'targets.json',targets)
    write_json(OUT/'citing-works.json',list(works.values()))
    write_json(OUT/'institutions.json',list(institutions.values()))
    write_json(OUT/'manifest.json',manifest)
    write_json(OUT/'author-affiliations.json',affiliations)
    write_csv(OUT/'citation-ledger.csv',citation_rows,list(citation_rows[0]) if citation_rows else ['citing_work_id','title'])
    write_csv(OUT/'citation-edges.csv',edges,['citing_work_id','cited_work_id','source','scholar_source_url','scholar_retrieved_at'])
    write_csv(OUT/'author-affiliations.csv',affiliations,list(affiliations[0]) if affiliations else ['citing_work_id','author_name'])
    citation_lookup = {r['citing_work_id']:r for r in citation_rows}
    scholar_rows=[]; first_result={}
    for n, record in enumerate(scholar.get('records',[]),1):
        r=record['scholar_record']; key=(record['work_id'],record['cited_work_id'])
        wid=record['work_id']; paper=citation_lookup[wid]
        result_id=r.get('scholar_result_id') or record.get('scholar_result_id')
        duplicate=first_result.get(key)
        scholar_rows.append({'row':n,'target_doi':record.get('target_doi'), 'cited_work_id':record['cited_work_id'],
          'scholar_result_id':result_id,'citing_work_id':wid,'title':paper['title'],'doi':paper['doi'],
          'year':paper['year'],'authors':paper['authors'],'institutions':paper['institutions'],
          'countries':paper['countries'],'states_provinces':paper['states_provinces'],
          'duplicate_of_result_id':duplicate,'is_direct_self_citation':paper['is_direct_self_citation'],
          'source_page_url':r['source_page_url'],'publication_url':r.get('publication_url'),
          'retrieved_at':r['retrieved_at']})
        first_result.setdefault(key,result_id)
    write_csv(OUT/'scholar-citations.csv',scholar_rows,list(scholar_rows[0]) if scholar_rows else ['row'])
    write_json(OUT/'scholar-citations.json',scholar_rows)
    write_json(ROOT/'assets/data/citation-geography.json',public)
    # Human-readable ledger stays excluded from Quarto rendering and resources.
    def md(value):
        return html.escape(str(value or '')).replace('|', '&#124;').replace('\n', ' ')
    report = ['# Citation ledger', '', f"Snapshot: {retrieved_at}", '',
      f"{len(edges)} verified citation relationships; {len(works)} distinct citing works; {len(self_citers)} direct self-citing works.", '',
      'All 66 Scholar result records are preserved separately in scholar-citations.csv. This merged ledger deduplicates versions and also retains additional OpenAlex records. See the parent README for scope and counting.', '']
    by_work = defaultdict(list)
    for row in affiliations: by_work[row['citing_work_id']].append(row)
    target_names = {sid(t['id']): doi(t['doi']) for t in targets}
    for n, row in enumerate(citation_rows, 1):
        report += [f"## {n}. {md(row['title'])}", '',
          f"Year: {row['year']} · DOI: {md(row['doi'])} · Direct self-citation: {row['is_direct_self_citation']} · Non-research record: {row['is_non_research_record']}", '',
          'Cites: ' + '; '.join(md(target_names[t]) for t in row['cited_target_ids']), '',
          f"Sources: {md(row['source'])} · [Metadata record]({row['source_url']})", '',
          '| Author | Affiliation | Country / region | Location status |',
          '|---|---|---|---|']
        for a in by_work[row['citing_work_id']]:
            name = a['institution_name'] or '; '.join(a['raw_affiliation_strings']) or 'Not reported in available metadata'
            place = ', '.join(str(a[k]) for k in ('country','state_province','city') if a.get(k)) or 'Unresolved'
            report.append('| ' + ' | '.join(md(v) for v in [a['author_name'],name,place,a['geo_status']]) + ' |')
        report += ['']
    (OUT/'citation-ledger.md').write_text('\n'.join(report).rstrip()+'\n')
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__': main()
