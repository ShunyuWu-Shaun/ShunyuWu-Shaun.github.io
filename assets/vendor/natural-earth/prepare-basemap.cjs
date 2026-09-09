/* Rebuild from the two official Natural Earth v5.1.2 GeoJSON downloads.
 * Usage: node prepare-basemap.cjs /path/to/downloads /path/to/assets/data
 * The small-scale map is a visual reference, not a geocoding boundary source.
 */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const input = process.argv[2];
const output = process.argv[3];
if (!input || !output) throw new Error('Supply input and output directories.');
function distance2(p, a, b) {
  let x = a[0], y = a[1], dx = b[0] - x, dy = b[1] - y;
  if (dx || dy) {
    const t = ((p[0] - x) * dx + (p[1] - y) * dy) / (dx * dx + dy * dy);
    if (t > 1) { x = b[0]; y = b[1]; }
    else if (t > 0) { x += dx * t; y += dy * t; }
  }
  return (p[0] - x) ** 2 + (p[1] - y) ** 2;
}
function simplify(points, tolerance) {
  if (points.length <= 3) return points;
  const keep = new Set([0, points.length - 1]);
  const stack = [[0, points.length - 1]];
  while (stack.length) {
    const [first, last] = stack.pop();
    let greatest = tolerance ** 2, at = -1;
    for (let i = first + 1; i < last; i++) {
      const d = distance2(points[i], points[first], points[last]);
      if (d > greatest) { greatest = d; at = i; }
    }
    if (at >= 0) { keep.add(at); stack.push([first, at], [at, last]); }
  }
  return [...keep].sort((a, b) => a - b).map(i => points[i]);
}
function round(points) { return points.map(p => p.map(n => Number(n.toFixed(4)))); }
function line(points, tolerance) { return round(simplify(points, tolerance)); }
function ring(points) {
  const simple = line(points, 0.015);
  return simple.length >= 4 ? simple : round(points);
}
function geometry(g) {
  if (g.type === 'LineString') return {type:g.type, coordinates:line(g.coordinates, 0.01)};
  if (g.type === 'MultiLineString') return {type:g.type, coordinates:g.coordinates.map(p => line(p, 0.01))};
  if (g.type === 'Polygon') return {type:g.type, coordinates:g.coordinates.map(ring)};
  if (g.type === 'MultiPolygon') return {type:g.type, coordinates:g.coordinates.map(p => p.map(ring))};
  throw new Error('Unexpected geometry ' + g.type);
}
const metadata = [];
for (const [sourceName, targetName, keys] of [
  ['countries.geojson', 'citation-world.geojson', ['ADMIN', 'ISO_A2', 'ISO_A3']],
  ['admin1.geojson', 'citation-admin1.geojson', ['NAME', 'name', 'adm0_a3']]
]) {
  const source = fs.readFileSync(path.join(input, sourceName));
  const collection = JSON.parse(source);
  const sourceFeatures = collection.features.filter(f => f.geometry);
  let features = sourceFeatures.map(f => ({type:'Feature', properties:Object.fromEntries(keys.filter(k => k in f.properties).map(k => [k, f.properties[k]])), geometry:geometry(f.geometry)}));
  // Boundary lines need no per-segment interaction. One SVG path avoids 10,000
  // separate DOM elements while preserving every nonempty source segment.
  if (sourceName === 'admin1.geojson') features = [{type:'Feature', properties:{source:'Natural Earth 10m admin 1 lines'}, geometry:{type:'MultiLineString', coordinates:features.flatMap(f => f.geometry.type === 'LineString' ? [f.geometry.coordinates] : f.geometry.coordinates)}}];
  const data = JSON.stringify({type:'FeatureCollection', features});
  fs.writeFileSync(path.join(output, targetName), data + '\n');
  metadata.push({source:sourceName, source_sha256:crypto.createHash('sha256').update(source).digest('hex'), output:targetName, source_features:sourceFeatures.length, output_features:features.length, omitted_null_geometries:collection.features.length - sourceFeatures.length, bytes:Buffer.byteLength(data), output_sha256:crypto.createHash('sha256').update(data + '\n').digest('hex')});
}
console.log(JSON.stringify(metadata, null, 2));
