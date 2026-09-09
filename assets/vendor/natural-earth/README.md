# Citation-map boundary sources

The map uses Natural Earth country outlines and first-order administrative boundary lines. Natural Earth map data are public domain. The publisher's [terms of use](https://www.naturalearthdata.com/about/terms-of-use/) were verified on 9 September 2026 and are archived in `terms-of-use.html`.

The [admin-1 documentation](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/) describes states, provinces, and equivalent first-order divisions, with exceptions for some small territories. The simplified files here provide visual reference boundaries. The citation pipeline retains affiliation region names where available; any spatial completion of missing regions uses the original, unsimplified admin-1 polygons and is recorded separately in the ledger.

Source files from the official Natural Earth repository, pinned to the `v5.1.2` release:

- [10m country polygons](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_10m_admin_0_countries.geojson), downloaded as `countries.geojson`.
- [10m state and province lines](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_10m_admin_1_states_provinces_lines.geojson), downloaded as `admin1.geojson`.

`prepare-basemap.cjs` reduces coordinate precision to four decimals and simplifies lines with the Douglas–Peucker method: 0.015 degrees for country rings and 0.01 degrees for state/province lines. Small rings that would otherwise collapse retain their original vertices. One source boundary feature has no geometry and is omitted. The remaining 10,178 segments are combined into one `MultiLineString` to avoid thousands of separate browser elements. Geographic labels and political classifications have not been manually changed.

Rebuild with Node.js:

```text
node assets/vendor/natural-earth/prepare-basemap.cjs /path/to/downloads assets/data
```

The output files are `assets/data/citation-world.geojson` and `assets/data/citation-admin1.geojson`. Source and output hashes, feature counts, and byte sizes are in `basemap-manifest.json`.

The homepage loads all basemap data from these local files. It uses no external map tiles or geolocation service.
