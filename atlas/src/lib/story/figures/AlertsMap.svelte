<script lang="ts">
	import { resolveCssColor } from '$lib/theme.svelte';
	/**
	 * Figure 04 of the story: the «112» alerts of August 2021, looping on one
	 * national satellite frame (DATA_DECISIONS 2026-09-02). A canvas the size
	 * of the figure square — the baked Sentinel-2 plate, the burnt ground
	 * growing day by day, a black dot for every village told to leave and a
	 * white one for every village it was sent to — under a black card with the
	 * clock and the current order, a day strip along the bottom, a key.
	 *
	 * The component mounts only while the reader is on Figure 04 (StoryFigure
	 * keys the slot on the figure number), so mounting is the loop's start;
	 * inside, the frame loop runs only while the square is on screen and the
	 * tab visible, and prefers-reduced-motion gets the final state once.
	 */
	import { onMount } from 'svelte';
	import { ALERTS, END_MS, START_MS, alertsIdleLine } from '$lib/transforms/alerts';
	import { CLOCK, buildClock, loopPhase } from '$lib/transforms/alertsClock';
	import { cardLine, formatClock } from '$lib/transforms/alertsText';
	import { burnBuffer, buildScene, drawFrame, loadBurn, loadPlate, type Burn, type Scene } from './alertsDraw';

	let wrap = $state<HTMLDivElement | null>(null);
	let canvas = $state<HTMLCanvasElement | null>(null);
	let card = $state<HTMLDivElement | null>(null);
	let size = $state(0);
	let clockText = $state('');
	let lineText = $state(alertsIdleLine());

	const clock = buildClock(ALERTS, CLOCK, START_MS, END_MS);
	// plain lets: the scene and the layers are big and must never be proxied
	let scene: Scene | null = null;
	let plate: HTMLImageElement | null = null;
	let burnFc: Burn | null = null;
	const burn = burnBuffer();
	let elapsed = 0;
	let last = 0;
	let raf = 0;
	let running = false;
	let reduced = false;
	let inView = false;
	let hidden = false;
	let loaded = false;
	let family = 'sans-serif';
	let fire = '#6b2d35';

	function draw(wallOverride?: number) {
		if (!canvas || !size) return;
		const ctx = canvas.getContext('2d');
		if (!ctx) return;
		const dpr = window.devicePixelRatio || 1;
		if (canvas.width !== Math.round(size * dpr) || canvas.height !== Math.round(size * dpr)) {
			canvas.width = Math.round(size * dpr);
			canvas.height = Math.round(size * dpr);
		}
		if (!scene || scene.size !== size) scene = buildScene(size, ALERTS, burnFc);
		const { wall, tail } =
			wallOverride === undefined ? loopPhase(elapsed, clock) : { wall: wallOverride, tail: 0 };
		const cardBox = card
			? { x: card.offsetLeft, y: card.offsetTop, w: card.offsetWidth, h: card.offsetHeight }
			: null;
		drawFrame({ ctx, scene, clock, wall, tail, plate, burn, dpr, fire, family, card: cardBox });
		// the card's two lines, written only when they change
		const sim = clock.simAt(wall);
		const t = formatClock(sim);
		if (t !== clockText) clockText = t;
		let latest = -1;
		for (let i = 0; i < clock.fireWall.length; i++) if (clock.fireWall[i] <= wall) latest = i;
		const line = latest >= 0 ? cardLine(ALERTS[latest]) : alertsIdleLine();
		if (line !== lineText) lineText = line;
	}

	function tick(now: number) {
		if (last) elapsed += now - last;
		last = now;
		draw();
		raf = requestAnimationFrame(tick);
	}

	function update() {
		const should = !reduced && loaded && !hidden && inView && size > 0;
		if (should && !running) {
			running = true;
			last = 0;
			raf = requestAnimationFrame(tick);
		} else if (!should && running) {
			running = false;
			cancelAnimationFrame(raf);
			last = 0;
		}
	}

	onMount(() => {
		reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
		if (canvas) {
			const cs = getComputedStyle(canvas);
			family = cs.fontFamily || family;
			fire = resolveCssColor('var(--c-fire)');
		}
		const ro = new ResizeObserver((entries) => {
			for (const e of entries) size = Math.floor(Math.min(e.contentRect.width, e.contentRect.height));
			if (reduced && loaded) draw(clock.endWall);
			update();
		});
		if (wrap) ro.observe(wrap);
		const io = new IntersectionObserver(
			(entries) => {
				inView = entries.some((e) => e.isIntersecting);
				update();
			},
			{ threshold: 0.25 }
		);
		if (wrap) io.observe(wrap);
		const onVis = () => {
			hidden = document.hidden;
			last = 0;
			update();
		};
		document.addEventListener('visibilitychange', onVis);
		// the Typekit face may still be loading: wait for it, but never long
		const fonts = Promise.race([
			document.fonts.load(`12px ${family}`).then(() => document.fonts.ready),
			new Promise((r) => setTimeout(r, 1200))
		]);
		Promise.all([loadPlate().catch(() => null), loadBurn().catch(() => null), fonts]).then(([img, fc]) => {
			plate = img;
			burnFc = fc;
			scene = null;
			loaded = true;
			if (reduced) draw(clock.endWall);
			else update();
		});
		return () => {
			cancelAnimationFrame(raf);
			running = false;
			ro.disconnect();
			io.disconnect();
			document.removeEventListener('visibilitychange', onVis);
		};
	});
</script>

<div class="wrap" bind:this={wrap}>
	<canvas bind:this={canvas} style:width="{size}px" style:height="{size}px"></canvas>
	<div class="tip" bind:this={card} aria-live="off">
		<div class="clock">{clockText}</div>
		<div class="line">{lineText}</div>
	</div>
	<div class="key">
		<span class="sw black"></span>evacuate
		<span class="sw white"></span>go to
		<span class="sw grey"></span>stay indoors
	</div>
</div>

<style>
	.wrap {
		position: relative;
		width: 100%;
		height: 100%;
		overflow: hidden;
		background: var(--paper-2);
	}
	canvas {
		display: block;
		font-family: var(--font-ui);
	}
	/* the site's black hover card (PaperMap .tip), at the map's top-left */
	.tip {
		position: absolute;
		top: var(--sp-2);
		left: var(--sp-2);
		max-width: 64%;
		background: #000;
		color: #fff;
		border-radius: 4px;
		padding: var(--sp-1) var(--sp-2);
		font-size: var(--fs-13);
		line-height: 1.35;
		font-variant-numeric: tabular-nums;
		pointer-events: none;
	}
	.tip .clock {
		white-space: nowrap;
	}
	.tip .line {
		color: #d9d9d9;
		min-height: 1.35em;
	}
	.key {
		position: absolute;
		right: var(--sp-2);
		bottom: calc(22px + var(--sp-2));
		display: flex;
		align-items: center;
		gap: 0 4px;
		padding: 2px 6px;
		border-radius: 3px;
		background: rgba(0, 0, 0, 0.55);
		color: #fff;
		font-size: 10.5px;
		line-height: 14px;
		white-space: nowrap;
		pointer-events: none;
	}
	.sw {
		display: inline-block;
		width: 7px;
		height: 7px;
		border-radius: 50%;
		margin: 0 3px 0 6px;
	}
	.sw:first-child {
		margin-left: 0;
	}
	.sw.black {
		background: #000;
	}
	.sw.white {
		background: #fff;
	}
	.sw.grey {
		background: #8f8f8f;
	}
</style>
