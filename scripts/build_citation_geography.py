#!/usr/bin/env python3
"""Build the homepage citation-geography snapshot and static SVG map."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date
from fractions import Fraction
from pathlib import Path


OPENALEX_API = "https://api.openalex.org"
OPENALEX_AUTHOR_ID = "A5087893108"
NATURAL_EARTH_VERSION = "v5.1.2"
NATURAL_EARTH_BASE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    f"{NATURAL_EARTH_VERSION}/geojson/ne_110m_admin_0_countries.geojson"
)
NATURAL_EARTH_LABEL_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    f"{NATURAL_EARTH_VERSION}/geojson/ne_50m_admin_0_countries.geojson"
)
USER_AGENT = "shunyu-wu-citation-geography/1.0 (mailto:shunyuwu@sjtu.edu.cn)"

TARGET_DOIS = [
    "10.1109/TSG.2025.3601238",
    "10.1016/j.eswa.2024.124508",
    "10.1109/TCSS.2023.3272330",
    "10.23919/CCC52363.2021.9550182",
    "10.1016/j.eswa.2026.133261",
    "10.1109/TSMC.2023.3344883",
    "10.1109/TASE.2023.3299185",
    "10.1109/CDC49753.2023.10383316",
    "10.1016/j.ifacol.2023.10.581",
    "10.23919/CCC52363.2021.9550267",
]


def fetch_json(url: str, attempts: int = 5) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 and exc.code < 500:
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt == attempts - 1:
                raise
        time.sleep(2**attempt)
    raise RuntimeError(f"Unable to retrieve {url}")


def openalex_url(path: str, **params: object) -> str:
    query = {key: value for key, value in params.items() if value is not None}
    query["mailto"] = "shunyuwu@sjtu.edu.cn"
    return f"{OPENALEX_API}{path}?{urllib.parse.urlencode(query)}"


def openalex_short_id(value: str | None) -> str:
    return (value or "").rstrip("/").rsplit("/", 1)[-1]


def resolve_targets() -> list[dict]:
    targets = []
    for doi in TARGET_DOIS:
        record = fetch_json(
            openalex_url(
                f"/works/doi:{doi}",
                select="id,doi,title,publication_year,cited_by_count",
            )
        )
        targets.append(
            {
                "doi": doi,
                "openalex_id": openalex_short_id(record.get("id")),
                "title": record.get("title"),
                "publication_year": record.get("publication_year"),
                "openalex_cited_by_count": record.get("cited_by_count"),
            }
        )
    return targets


def citing_works(work_id: str) -> list[dict]:
    cursor = "*"
    records: list[dict] = []
    while cursor:
        page = fetch_json(
            openalex_url(
                "/works",
                filter=f"cites:{work_id}",
                corpus="core",
                per_page=100,
                cursor=cursor,
                select="id,doi,title,publication_year,authorships",
            )
        )
        records.extend(page.get("results", []))
        cursor = page.get("meta", {}).get("next_cursor")
    return records


def work_author_ids(work: dict) -> set[str]:
    return {
        openalex_short_id(authorship.get("author", {}).get("id"))
        for authorship in work.get("authorships", [])
        if authorship.get("author", {}).get("id")
    }


def work_country_codes(work: dict) -> set[str]:
    country_codes: set[str] = set()
    for authorship in work.get("authorships", []):
        country_codes.update(code for code in authorship.get("countries", []) if code)
        for institution in authorship.get("institutions", []):
            code = institution.get("country_code")
            if code:
                country_codes.add(code)
    return country_codes


def country_name(code: str) -> str:
    record = fetch_json(openalex_url(f"/countries/{code}", select="display_name"))
    return record.get("display_name") or code


def collect_snapshot(retrieved_on: str) -> dict:
    targets = resolve_targets()
    unique_citing_works: dict[str, dict] = {}
    citation_edges = 0

    for target in targets:
        works = citing_works(target["openalex_id"])
        citation_edges += len(works)
        for work in works:
            work_id = openalex_short_id(work.get("id"))
            if work_id:
                unique_citing_works[work_id] = work

    excluded_self = []
    external_works = {}
    for work_id, work in unique_citing_works.items():
        if OPENALEX_AUTHOR_ID in work_author_ids(work):
            excluded_self.append(work_id)
        else:
            external_works[work_id] = work

    full_counts: defaultdict[str, int] = defaultdict(int)
    fractional_counts: defaultdict[str, Fraction] = defaultdict(Fraction)
    unmapped = []
    multi_country_works = 0

    for work_id, work in external_works.items():
        codes = sorted(work_country_codes(work))
        if not codes:
            unmapped.append(
                {
                    "openalex_id": work_id,
                    "title": work.get("title"),
                }
            )
            continue
        if len(codes) > 1:
            multi_country_works += 1
        share = Fraction(1, len(codes))
        for code in codes:
            full_counts[code] += 1
            fractional_counts[code] += share

    countries = []
    for code in sorted(fractional_counts):
        countries.append(
            {
                "code": code,
                "name": country_name(code),
                "full_count": full_counts[code],
                "fractional_count": round(float(fractional_counts[code]), 6),
            }
        )
    countries.sort(key=lambda item: (-item["fractional_count"], item["name"]))

    geocoded_count = len(external_works) - len(unmapped)
    fractional_total = round(float(sum(fractional_counts.values(), Fraction())), 6)
    return {
        "title": "Citation geography",
        "retrieved_on": retrieved_on,
        "source": {
            "citation_metadata": "OpenAlex core corpus",
            "citation_url": "https://openalex.org/",
            "map_geometry": f"Natural Earth {NATURAL_EARTH_VERSION}",
            "map_url": "https://www.naturalearthdata.com/downloads/",
        },
        "scope": {
            "publication_count": len(targets),
            "publication_selection": "First- and last-author papers listed on the website",
            "openalex_author_id": OPENALEX_AUTHOR_ID,
        },
        "method": {
            "citing_work_deduplication": "Canonical OpenAlex work ID across all target papers",
            "direct_self_citation_rule": (
                "Exclude a citing work when its authorships include Shunyu Wu"
            ),
            "geography_field": "Distinct authorship country codes for each citing work",
            "country_assignment": (
                "A work with k country codes contributes 1/k to each country"
            ),
            "missing_country_rule": "Keep the record unmapped and do not infer a country",
        },
        "totals": {
            "citation_edges": citation_edges,
            "unique_citing_works_before_self_exclusion": len(unique_citing_works),
            "direct_self_citing_works_excluded": len(excluded_self),
            "external_citing_works": len(external_works),
            "geocoded_external_citing_works": geocoded_count,
            "unmapped_external_citing_works": len(unmapped),
            "multi_country_external_citing_works": multi_country_works,
            "country_or_region_codes": len(countries),
            "fractional_count_total": fractional_total,
        },
        "countries": countries,
        "targets": targets,
        "excluded_direct_self_citing_work_ids": sorted(excluded_self),
        "unmapped_external_citing_works": sorted(
            unmapped, key=lambda item: item["openalex_id"]
        ),
    }


def equal_earth(lon: float, lat: float) -> tuple[float, float]:
    longitude = math.radians(lon)
    latitude = math.radians(max(-89.999, min(89.999, lat)))
    a1, a2, a3, a4 = 1.340264, -0.081106, 0.000893, 0.003796
    theta = math.asin(math.sqrt(3) * math.sin(latitude) / 2)
    theta2 = theta * theta
    theta6 = theta2 * theta2 * theta2
    denominator = 3 * (
        9 * a4 * theta2 * theta6 + 7 * a3 * theta6 + 3 * a2 * theta2 + a1
    )
    x_value = 2 * math.sqrt(3) * longitude * math.cos(theta) / denominator
    y_value = theta * (a4 * theta2 * theta6 + a3 * theta6 + a2 * theta2 + a1)
    return x_value, y_value


def geometry_rings(geometry: dict) -> list[list[list[float]]]:
    if geometry.get("type") == "Polygon":
        return geometry.get("coordinates", [])
    if geometry.get("type") == "MultiPolygon":
        return [ring for polygon in geometry.get("coordinates", []) for ring in polygon]
    return []


def natural_earth_code(properties: dict) -> str:
    primary = properties.get("ISO_A2")
    if primary and primary != "-99":
        return primary
    for key in ("ISO_A2_EH", "WB_A2", "POSTAL"):
        value = properties.get(key)
        if value and value != "-99" and len(value) == 2:
            return value
    return ""


def build_svg(snapshot: dict) -> str:
    base = fetch_json(NATURAL_EARTH_BASE_URL)
    labels = fetch_json(NATURAL_EARTH_LABEL_URL)
    features = [
        feature
        for feature in base.get("features", [])
        if feature.get("properties", {}).get("ADMIN") != "Antarctica"
    ]

    projected_points = []
    for feature in features:
        for ring in geometry_rings(feature.get("geometry", {})):
            projected_points.extend(equal_earth(point[0], point[1]) for point in ring)

    min_x = min(point[0] for point in projected_points)
    max_x = max(point[0] for point in projected_points)
    min_y = min(point[1] for point in projected_points)
    max_y = max(point[1] for point in projected_points)
    width, height = 980.0, 460.0
    map_top, map_bottom = 16.0, 444.0
    margin_x = 18.0
    scale = min(
        (width - 2 * margin_x) / (max_x - min_x),
        (map_bottom - map_top) / (max_y - min_y),
    )
    content_width = (max_x - min_x) * scale
    content_height = (max_y - min_y) * scale
    offset_x = (width - content_width) / 2 - min_x * scale
    offset_y = map_top + (map_bottom - map_top - content_height) / 2 + max_y * scale

    def screen(lon: float, lat: float) -> tuple[float, float]:
        x_value, y_value = equal_earth(lon, lat)
        return offset_x + x_value * scale, offset_y - y_value * scale

    def polyline(points: list[tuple[float, float]]) -> str:
        if not points:
            return ""
        first, *rest = points
        commands = [f"M{first[0]:.1f},{first[1]:.1f}"]
        commands.extend(f"L{x_value:.1f},{y_value:.1f}" for x_value, y_value in rest)
        return "".join(commands)

    graticule_paths = []
    for latitude in (-60, -30, 0, 30, 60):
        graticule_paths.append(
            polyline([screen(longitude, latitude) for longitude in range(-180, 181, 3)])
        )
    for longitude in range(-150, 180, 30):
        graticule_paths.append(
            polyline([screen(longitude, latitude) for latitude in range(-75, 86, 3)])
        )

    land_paths = []
    for feature in features:
        ring_paths = []
        for ring in geometry_rings(feature.get("geometry", {})):
            points = [screen(point[0], point[1]) for point in ring]
            path = polyline(points)
            if path:
                ring_paths.append(f"{path}Z")
        if ring_paths:
            country = html.escape(feature.get("properties", {}).get("ADMIN", "Country"))
            land_paths.append(
                f'<path d="{"".join(ring_paths)}"><title>{country}</title></path>'
            )

    label_points = {}
    for feature in labels.get("features", []):
        properties = feature.get("properties", {})
        code = natural_earth_code(properties)
        longitude = properties.get("LABEL_X")
        latitude = properties.get("LABEL_Y")
        if code and longitude is not None and latitude is not None:
            label_points[code] = (float(longitude), float(latitude))

    citation_points = []
    for country in sorted(
        snapshot["countries"], key=lambda item: -item["fractional_count"]
    ):
        code = country["code"]
        if code not in label_points:
            raise RuntimeError(f"Natural Earth has no label point for {code}")
        longitude, latitude = label_points[code]
        x_value, y_value = screen(longitude, latitude)
        radius = 3.9 * math.sqrt(country["fractional_count"])
        label = html.escape(
            f'{country["name"]}: {country["fractional_count"]:.2f} fractional '
            f'citing works from {country["full_count"]} unique works'
        )
        citation_points.append(
            f'<circle cx="{x_value:.1f}" cy="{y_value:.1f}" r="{radius:.1f}" '
            f'data-code="{html.escape(code)}"><title>{label}</title></circle>'
        )

    graticules = "".join(f'<path d="{path}"/>' for path in graticule_paths)
    land = "".join(land_paths)
    points = "".join(citation_points)
    country_count = snapshot["totals"]["country_or_region_codes"]
    geocoded_count = snapshot["totals"]["geocoded_external_citing_works"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 460" role="img" aria-labelledby="map-title map-desc">
  <title id="map-title">Citation geography for Shunyu Wu's selected publications</title>
  <desc id="map-desc">An Equal Earth map with proportional circles for {country_count} affiliation countries or regions represented among {geocoded_count} country-coded external citing works.</desc>
  <style>
    .graticule path {{ fill: none; stroke: #e7ecef; stroke-width: 0.7; vector-effect: non-scaling-stroke; }}
    .land path {{ fill: #eef2f4; stroke: #d7e0e4; stroke-width: 0.65; vector-effect: non-scaling-stroke; }}
    .citation-points circle {{ fill: #5366a6; fill-opacity: 0.86; stroke: #ffffff; stroke-width: 1.25; vector-effect: non-scaling-stroke; }}
  </style>
  <rect width="980" height="460" fill="#fbfcfc"/>
  <g class="graticule">{graticules}</g>
  <g class="land" fill-rule="evenodd">{land}</g>
  <g class="citation-points">{points}</g>
</svg>
'''


def validate_homepage(snapshot: dict, homepage_source: Path) -> None:
    if not homepage_source.exists():
        raise RuntimeError(f"Homepage source does not exist: {homepage_source}")

    source = homepage_source.read_text(encoding="utf-8")
    section_match = re.search(
        r'<section class="home-section reach-front"(?P<attributes>[^>]*)>'
        r'(?P<body>.*?)</section>',
        source,
        flags=re.DOTALL,
    )
    if not section_match:
        raise RuntimeError("Homepage citation-geography section was not found")

    attributes = section_match.group("attributes")
    body = section_match.group("body")
    totals = snapshot["totals"]
    expected_attributes = {
        "retrieved-on": snapshot["retrieved_on"],
        "publication-count": str(snapshot["scope"]["publication_count"]),
        "external-works": str(totals["external_citing_works"]),
        "geocoded-works": str(totals["geocoded_external_citing_works"]),
        "unmapped-works": str(totals["unmapped_external_citing_works"]),
        "country-count": str(totals["country_or_region_codes"]),
    }
    issues = []
    for name, expected in expected_attributes.items():
        match = re.search(rf'data-{re.escape(name)}="([^"]+)"', attributes)
        actual = match.group(1) if match else None
        if actual != expected:
            issues.append(f'data-{name} is {actual!r}; expected {expected!r}')

    retrieved_date = date.fromisoformat(snapshot["retrieved_on"])
    display_date = f"{retrieved_date.day} {retrieved_date.strftime('%B %Y')}"
    geocoded_text = (
        f'{totals["geocoded_external_citing_works"]} of '
        f'{totals["external_citing_works"]}'
    )
    country_text = f'{totals["country_or_region_codes"]} countries or regions'
    publication_text = (
        f'the {snapshot["scope"]["publication_count"]} first- and last-author papers'
    )
    ranked_text = (
        f'{snapshot["countries"][0]["name"]} has the largest fractional count, '
        f'followed by {snapshot["countries"][1]["name"]}.'
    )
    unmapped_count = totals["unmapped_external_citing_works"]
    unmapped_text = (
        'one record without country metadata remains unmapped'
        if unmapped_count == 1
        else f'{unmapped_count} records without country metadata remain unmapped'
    )
    if body.count(display_date) < 2:
        issues.append(f'visible retrieval date must appear twice as {display_date!r}')
    if body.count(geocoded_text) < 2:
        issues.append(f'geocoded total must appear twice as {geocoded_text!r}')
    if country_text not in body:
        issues.append(f'country total is missing as {country_text!r}')
    if publication_text not in body:
        issues.append(f'publication scope is missing as {publication_text!r}')
    if ranked_text not in body:
        issues.append(f'ranked-country statement is missing as {ranked_text!r}')
    if unmapped_text not in body:
        issues.append(f'unmapped total is missing as {unmapped_text!r}')

    row_matches = re.findall(
        r'<tr data-code="([A-Z]{2})">\s*'
        r'<td>([^<]+)</td>\s*<td>(\d+)</td>\s*<td>(\d+\.\d{2})</td>\s*'
        r'</tr>',
        body,
    )
    actual_rows = {
        code: (html.unescape(name), int(full_count), float(fractional_count))
        for code, name, full_count, fractional_count in row_matches
    }
    expected_rows = {
        country["code"]: (
            country["name"],
            country["full_count"],
            round(country["fractional_count"], 2),
        )
        for country in snapshot["countries"]
    }
    if actual_rows != expected_rows:
        missing = sorted(set(expected_rows) - set(actual_rows))
        extra = sorted(set(actual_rows) - set(expected_rows))
        changed = sorted(
            code
            for code in set(actual_rows) & set(expected_rows)
            if actual_rows[code] != expected_rows[code]
        )
        issues.append(
            "country table differs from the snapshot "
            f"(missing={missing}, extra={extra}, changed={changed})"
        )

    if issues:
        details = "\n".join(f"  - {issue}" for issue in issues)
        raise RuntimeError(
            "Homepage citation-geography copy is stale. Update index.qmd and "
            f"rerun the generator:\n{details}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retrieved-on", default=date.today().isoformat())
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("assets/data/citation-geography.json"),
    )
    parser.add_argument(
        "--svg-output",
        type=Path,
        default=Path("assets/images/citation-geography.svg"),
    )
    parser.add_argument(
        "--homepage-source",
        type=Path,
        default=Path("index.qmd"),
    )
    args = parser.parse_args()

    snapshot = collect_snapshot(args.retrieved_on)
    validate_homepage(snapshot, args.homepage_source)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.svg_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.svg_output.write_text(build_svg(snapshot), encoding="utf-8")
    print(json.dumps(snapshot["totals"], indent=2))


if __name__ == "__main__":
    main()
