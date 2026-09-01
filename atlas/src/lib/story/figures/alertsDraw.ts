/**
 * The canvas of the story's Figure 04 — the drawing routines and the two
 * module-level caches (the decoded satellite plate, the burn layer) behind
 * AlertsMap.svelte. DOM code, so it lives beside the component; the geometry
 * it draws with comes from the pure transforms (alertsFrame, alertsLayout,
 * alertsClock), which is where the tests are.
 */
import { geoPath } from 'd3-geo';
import type { GeoProjection } from 'd3-geo';
import type { FeatureCollection, MultiPolygon, Polygon } from 'geojson';
import { loadAlertsBurn, type BurnProps } from '$lib/maps/useGeo';
import { placed, type Alert, type AlertType } from '$lib/transforms/alerts';
import { burnDayIndex, type Clock } from '$lib/transforms/alertsClock';
import { alertsProjection } from '$lib/transforms/alertsFrame';
import { dayStrip, dotRadius, k as scaleOf, placeLabels, type Box, type Strip } from '$lib/transforms/alertsLayout';

export type Burn = FeatureCollection<Polygon | MultiPolygon, BurnProps>;

/* ── caches: one load for every mount of the figure ── */
let plate: Promise<HTMLImageElement> | null = null;
export function loadPlate(): Promise<HTMLImageElement> {
	if (!plate) {
		plate = new Promise((resolve, reject) => {
			const img = new Image();
			img.decoding = 'async';
			(img as HTMLImageElement & { fetchPriority?: string }).fetchPriority = 'low';
			img.onload = () => img.decode().then(() => resolve(img), () => resolve(img));
			img.onerror = () => reject(new Error('alerts_base.avif did not load'));
			img.src = '/geo/alerts_base.avif';
		});
	}
	return plate;
}

let burn: Promise<Burn> | null = null;
export function loadBurn(): Promise<Burn> {
	if (!burn) burn = loadAlertsBurn(fetch);
	return burn;
}

/* ── the scene: everything projected once per square size ── */
export interface XY {
	x: number;
	y: number;
	name: string;
}
export interface SceneAlert {
	i: number;
	type: AlertType;
	orders: { from: XY[]; to: XY[] }[];
}
export interface Scene {
	size: number;
	proj: GeoProjection;
	alerts: SceneAlert[];
	strip: Strip;
	/** one Path2D per burn increment, in day order */
	burnPaths: Path2D[];
	burnDays: string[];
}

export function buildScene(size: number, alerts: Alert[], burnFc: Burn | null): Scene {
	const proj = alertsProjection(size);
	const path = geoPath(proj);
	const xy = (lon: number, lat: number, name: string): XY => {
		const p = proj([lon, lat]) ?? [0, 0];
		return { x: p[0], y: p[1], name };
	};
	const scene: SceneAlert[] = alerts.map((a, i) => ({
		i,
		type: a.type,
		orders: a.orders.map((o) => ({
			from: o.from.filter(placed).map((p) => xy(p.lon, p.lat, p.nameEn)),
			to: o.to.filter(placed).map((p) => xy(p.lon, p.lat, p.nameEn))
		}))
	}));
	const burnPaths: Path2D[] = [];
	const burnDays: string[] = [];
	if (burnFc) {
		for (const f of burnFc.features) {
			const d = path(f);
			if (!d) continue;
			burnPaths.push(new Path2D(d));
			burnDays.push(f.properties.day);
		}
	}
	return { size, proj, alerts: scene, strip: dayStrip(size), burnPaths, burnDays };
}

/* ── the burn buffer: increments drawn opaque, composited translucent ── */
export interface BurnBuffer {
	canvas: HTMLCanvasElement;
	upTo: number;
	size: number;
	dpr: number;
}

export function burnBuffer(): BurnBuffer {
	return { canvas: document.createElement('canvas'), upTo: -1, size: 0, dpr: 1 };
}

function ensureBurn(b: BurnBuffer, scene: Scene, dayIdx: number, dpr: number, fire: string): void {
	const px = Math.round(scene.size * dpr);
	const ctx = b.canvas.getContext('2d');
	if (!ctx) return;
	if (b.size !== scene.size || b.dpr !== dpr || dayIdx < b.upTo) {
		b.canvas.width = px;
		b.canvas.height = px;
		b.size = scene.size;
		b.dpr = dpr;
		b.upTo = -1;
	}
	ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
	ctx.fillStyle = fire;
	for (let i = b.upTo + 1; i <= dayIdx && i < scene.burnPaths.length; i++) {
		ctx.fill(scene.burnPaths[i]);
	}
	b.upTo = Math.max(b.upTo, Math.min(dayIdx, scene.burnPaths.length - 1));
}

/* ── one frame ── */
export interface FrameInput {
	ctx: CanvasRenderingContext2D;
	scene: Scene;
	clock: Clock;
	/** the wall time inside the loop (held at endWall through the tail) */
	wall: number;
	/** the restart fade, 0 → 1 */
	tail: number;
	plate: HTMLImageElement | null;
	burn: BurnBuffer;
	dpr: number;
	fire: string;
	family: string;
	/** the HTML card's rect in CSS px — labels keep clear of it */
	card: Box | null;
}

const ease = (u: number) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
const BLACK = '#000000';
const WHITE = '#ffffff';
const GREY = '#8f8f8f';

const originColour = (t: AlertType) => (t === 'evacuation' ? BLACK : GREY);

function dot(ctx: CanvasRenderingContext2D, x: number, y: number, r: number, colour: string, alpha: number) {
	ctx.globalAlpha = alpha;
	ctx.fillStyle = colour;
	ctx.beginPath();
	ctx.arc(x, y, r, 0, Math.PI * 2);
	ctx.fill();
}

export function drawFrame(f: FrameInput): void {
	const { ctx, scene, clock, wall, tail } = f;
	const size = scene.size;
	const s = scaleOf(size);
	const marks = 1 - tail;
	ctx.setTransform(f.dpr, 0, 0, f.dpr, 0, 0);
	ctx.globalAlpha = 1;
	if (f.plate) ctx.drawImage(f.plate, 0, 0, size, size);
	else {
		ctx.fillStyle = '#f4f4f4';
		ctx.fillRect(0, 0, size, size);
	}

	// the burnt ground up to the clock's day
	const sim = clock.simAt(wall);
	const dayIdx = burnDayIndex(sim, scene.burnDays);
	if (dayIdx >= 0 && scene.burnPaths.length) {
		ensureBurn(f.burn, scene, dayIdx, f.dpr, f.fire);
		ctx.globalAlpha = 0.55 * marks;
		ctx.drawImage(f.burn.canvas, 0, 0, size, size);
	}

	// the alerts: past first, then fading, the active ones last and on top
	const rPast = dotRadius('past', size);
	const rActive = dotRadius('active', size);
	const live: { a: SceneAlert; alpha: number; grow: number; active: boolean }[] = [];
	for (const a of scene.alerts) {
		const ph = clock.phaseAt(wall, a.i);
		if (ph.kind === 'none') continue;
		if (ph.kind === 'past') {
			for (const o of a.orders) for (const p of o.from) dot(ctx, p.x, p.y, rPast, originColour(a.type), 0.75 * marks);
			continue;
		}
		const alpha = ph.kind === 'active' ? 1 : 1 - ph.u;
		const grow = ph.kind === 'active' && ph.u < 0.12 ? ease(ph.u / 0.12) : 1;
		live.push({ a, alpha: alpha * marks, grow, active: ph.kind === 'active' });
	}
	live.sort((p, q) => Number(p.active) - Number(q.active));
	const labels: { x: number; y: number; name: string; alpha: number }[] = [];
	for (const { a, alpha, grow, active } of live) {
		const r = rActive * grow;
		for (const o of a.orders) {
			// the lines the message states: every origin to every destination it names
			ctx.globalAlpha = 0.6 * alpha;
			ctx.strokeStyle = WHITE;
			ctx.lineWidth = 1 * s;
			for (const p of o.from) {
				for (const q of o.to) {
					ctx.beginPath();
					ctx.moveTo(p.x, p.y);
					ctx.lineTo(q.x, q.y);
					ctx.stroke();
				}
			}
			for (const q of o.to) dot(ctx, q.x, q.y, r, WHITE, alpha);
			for (const p of o.from) dot(ctx, p.x, p.y, r, originColour(a.type), alpha);
			if (active) for (const p of [...o.from, ...o.to]) labels.push({ x: p.x, y: p.y, name: p.name, alpha });
		}
	}

	// the active alerts' village names, placed clear of each other and the chrome
	if (labels.length) {
		const fontPx = 10.5 * s;
		ctx.font = `400 ${fontPx}px ${f.family}`;
		ctx.textBaseline = 'alphabetic';
		const items = labels.map((l) => ({ x: l.x, y: l.y, w: ctx.measureText(l.name).width, h: fontPx * 1.15, r: rActive }));
		const obstacles: Box[] = [{ x: 0, y: scene.strip.band.y0, w: size, h: size - scene.strip.band.y0 }];
		if (f.card) obstacles.push(f.card);
		const boxes = placeLabels(items, { w: size, h: size }, obstacles);
		ctx.fillStyle = WHITE;
		boxes.forEach((b, i) => {
			if (!b) return;
			ctx.globalAlpha = labels[i].alpha;
			ctx.fillText(labels[i].name, b.x, b.y + fontPx);
		});
	}

	drawStrip(f, sim);
	ctx.globalAlpha = 1;
}

function drawStrip(f: FrameInput, sim: number): void {
	const { ctx, scene, clock } = f;
	const st = scene.strip;
	const s = scaleOf(scene.size);
	ctx.globalAlpha = 1;
	ctx.fillStyle = 'rgba(0,0,0,0.35)';
	ctx.fillRect(0, st.band.y0, scene.size, st.band.y1 - st.band.y0);
	// the alerts' own ticks
	ctx.strokeStyle = WHITE;
	ctx.lineWidth = 1 * s;
	ctx.globalAlpha = 0.45;
	ctx.beginPath();
	for (let i = 0; i < clock.fireWall.length; i++) {
		const x = st.xOf(clock.simAt(clock.fireWall[i]));
		ctx.moveTo(x, st.y - st.tickH * 0.7);
		ctx.lineTo(x, st.y);
	}
	ctx.stroke();
	// the days
	ctx.globalAlpha = 0.9;
	ctx.beginPath();
	for (const t of st.ticks) {
		ctx.moveTo(t.x, st.y);
		ctx.lineTo(t.x, st.y + st.tickH);
	}
	ctx.moveTo(st.x0, st.y);
	ctx.lineTo(st.x1, st.y);
	ctx.stroke();
	ctx.font = `400 ${9 * s}px ${f.family}`;
	ctx.fillStyle = WHITE;
	ctx.textBaseline = 'alphabetic';
	for (const t of st.ticks) {
		if (t.label) ctx.fillText(t.label, t.x + 2 * s, st.band.y0 + 8.5 * s);
	}
	// the playhead
	ctx.globalAlpha = 1;
	ctx.lineWidth = 1.5 * s;
	const x = st.xOf(Math.min(sim, clock.end));
	ctx.beginPath();
	ctx.moveTo(x, st.band.y0);
	ctx.lineTo(x, st.y + st.tickH);
	ctx.stroke();
}
