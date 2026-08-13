/**
 * Build quantized TopoJSON from the committed webui GeoJSON layers.
 * Reads webui/static/ READ-ONLY; writes atlas/static/geo/ (committed).
 *
 * No re-simplification: the upstream layers were built with GEOS
 * coverage_simplify (shared borders identical on both sides) — quantization
 * preserves that; simplifying here independently would reintroduce slivers.
 *
 * Run: npm run geo
 */
import { readFileSync, writeFileSync, mkdirSync, copyFileSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { geoArea, geoMercator } from 'd3-geo';
import { topology } from 'topojson-server';
import { feature } from 'topojson-client';

/**
 * d3-geo treats polygons as SPHERICAL: a ring wound the "wrong" way encloses
 * everything except the region (fitSize then frames the whole world — the
 * upstream layers use the planar RFC-7946 convention that Leaflet ignores
 * but d3 does not). Rewind exteriors clockwise / holes counter-clockwise
 * (planar shoelace), which is d3's small-region convention.
 */
function rewindRing(ring, clockwise) {
	let area = 0;
	for (let i = 0, len = ring.length, j = len - 1; i < len; j = i++) {
		area += (ring[i][0] - ring[j][0]) * (ring[j][1] + ring[i][1]);
	}
	if (area >= 0 !== clockwise) ring.reverse();
}

function rewind(geo) {
	for (const f of geo.features) {
		const polys =
			f.geometry.type === 'MultiPolygon' ? f.geometry.coordinates : [f.geometry.coordinates];
		if (f.geometry.type === 'MultiPolygon' || f.geometry.type === 'Polygon') {
			for (const poly of polys) poly.forEach((ring, i) => rewindRing(ring, i === 0));
		}
		const a = geoArea(f);
		if (a > 0.1) {
			throw new Error(`${f.properties?.pe ?? '?'}: spherical area ${a} — winding still wrong`);
		}
	}
	return geo;
}

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, '..', '..');
const src = join(repo, 'webui', 'static');
const out = join(here, '..', 'static', 'geo');
mkdirSync(out, { recursive: true });

/** @param {string} file @param {string} name @param {number} q */
function build(file, name, q, outFile) {
	const geo = JSON.parse(readFileSync(join(src, file), 'utf8'));
	if (geo.features[0]?.geometry?.type?.includes('Polygon')) rewind(geo);
	const topo = topology({ [name]: geo }, q);
	const path = join(out, outFile);
	writeFileSync(path, JSON.stringify(topo));
	const inKB = (statSync(join(src, file)).size / 1024).toFixed(0);
	const outKB = (statSync(path).size / 1024).toFixed(0);
	console.log(`${file} (${inKB} KB) -> ${outFile} (${outKB} KB, q=${q})`);
}

build('greek_pe.geojson', 'pe', 1e4, 'pe.topo.json');
build('greek_pe_hires.geojson', 'pe', 1e5, 'pe_hires.topo.json');
build('greek_muni_borders.geojson', 'muni', 1e5, 'muni_borders.topo.json');
copyFileSync(join(src, 'pe_centroids.json'), join(out, 'pe_centroids.json'));
console.log('pe_centroids.json copied');

// The map frame contract for the baked relief underlay: replicate
// PaperMap's EXACT projection fit (geoMercator().fitSize on the
// quantized coarse layer — the same FeatureCollection the client
// derives from pe.topo.json) and export it so the Python relief bake
// (scripts/build_relief.py) aligns by arithmetic, never by reimplementing
// fitSize. Frame = the 640×620 country view every PaperMap uses.
{
	const W = 640;
	const H = 620;
	const topo = JSON.parse(readFileSync(join(out, 'pe.topo.json'), 'utf8'));
	const coarse = feature(topo, topo.objects.pe);
	const p = geoMercator().fitSize([W, H], coarse);
	const frame = {
		w: W,
		h: H,
		scale: p.scale(),
		translate: p.translate(),
		nw: p.invert([0, 0]),
		se: p.invert([W, H])
	};
	writeFileSync(join(out, 'frame.json'), JSON.stringify(frame));
	console.log(
		`frame.json: nw=[${frame.nw.map((v) => v.toFixed(5))}] se=[${frame.se.map((v) => v.toFixed(5))}]`
	);
}
