// The frame contract of the story's Figure 04 (the «112» alerts of August
// 2021): emit atlas/static/geo/alerts_frame.json from the SAME module the
// client projects with (src/lib/transforms/alertsFrame.ts — imported here
// directly, node strips the types), the way build-topo.mjs emits frame.json
// for the relief. scripts/build_alerts_base.py bakes the satellite plate for
// the corners written here; alertsFrame.test.ts pins the file against a
// fresh fit. Run: `npm run geo:alerts`.
import { writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
	ALERTS_BOX,
	BAKE_PX,
	alertsProjection,
	frameCorners
} from '../src/lib/transforms/alertsFrame.ts';

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, '..', 'static', 'geo', 'alerts_frame.json');

const p = alertsProjection(BAKE_PX);
const { nw, se } = frameCorners(BAKE_PX);
const frame = {
	w: BAKE_PX,
	h: BAKE_PX,
	box: ALERTS_BOX,
	scale: p.scale(),
	translate: p.translate(),
	nw,
	se
};
writeFileSync(out, JSON.stringify(frame));
console.log(
	`alerts_frame.json: ${BAKE_PX}px, nw=[${nw.map((v) => v.toFixed(5))}] se=[${se.map((v) => v.toFixed(5))}]`
);
