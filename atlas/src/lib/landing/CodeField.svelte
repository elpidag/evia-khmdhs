<script lang="ts">
	/**
	 * The drifting field of codes on a canvas (user mock, 2026-08-27). The
	 * layout comes from field.ts; this shell fills its wrapper, re-lays out
	 * on resize, draws one glyph per line in the site's UI face and the
	 * dataset's own colour, and runs an endless frame loop that pauses when
	 * the tab is hidden and stops when the component leaves. Under
	 * prefers-reduced-motion it draws one still frame.
	 */
	import { onMount } from 'svelte';
	import type { Landing } from '$lib/api';
	import { FIELD, FIELD_DENSE, glyphsAt, layoutColumns, poolFrom, type Ds } from './field';

	let {
		codes,
		seed = 20260827,
		playing = true,
		dense = false,
		onFirstFrame
	}: {
		codes: Landing | null;
		seed?: number;
		playing?: boolean;
		/** the cell fragment: a finer pitch, slower */
		dense?: boolean;
		onFirstFrame?: () => void;
	} = $props();

	let wrap = $state<HTMLDivElement | null>(null);
	let canvas = $state<HTMLCanvasElement | null>(null);
	let w = $state(0);
	let h = $state(0);
	const opts = $derived(dense ? FIELD_DENSE : FIELD);
	const glyphPx = 12; // Artboard 1: Obviously Regular 12 px, in the cell too

	const pool = $derived(codes ? poolFrom(codes, seed) : []);
	const columns = $derived(layoutColumns(w, h, pool, seed, opts));

	// the frame clock: elapsed advances only while playing and visible, so
	// a pause never jumps the columns
	let elapsed = 0;
	let last = 0;
	let raf = 0;
	let fontReady = false;
	let family = '';
	let colours: Record<Ds, string> = { antinero: '#000', dase: '#52b788', anadohoi: '#2d6a4f' };
	let reduced = false;
	let firstFrameSent = false;

	function draw() {
		if (!canvas || !w || !h) return;
		const ctx = canvas.getContext('2d');
		if (!ctx) return;
		const dpr = window.devicePixelRatio || 1;
		if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
			canvas.width = Math.round(w * dpr);
			canvas.height = Math.round(h * dpr);
		}
		ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
		ctx.clearRect(0, 0, w, h);
		ctx.font = `400 ${glyphPx}px ${family}`;
		ctx.textAlign = 'center';
		ctx.textBaseline = 'middle';
		const slow = dense ? 0.4 : 1;
		let current: Ds | null = null;
		for (const col of columns) {
			for (const g of glyphsAt(col, elapsed * slow, h, opts)) {
				if (g.ds !== current) {
					ctx.fillStyle = colours[g.ds];
					current = g.ds;
				}
				ctx.fillText(g.ch, g.x, g.y + opts.lineH / 2);
			}
		}
		if (!firstFrameSent && columns.length) {
			firstFrameSent = true;
			onFirstFrame?.();
		}
	}

	function tick(now: number) {
		if (playing && !document.hidden) {
			if (last) elapsed += now - last;
			last = now;
			draw();
		} else {
			last = 0;
		}
		raf = requestAnimationFrame(tick);
	}

	onMount(() => {
		reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
		if (canvas) {
			const cs = getComputedStyle(canvas);
			family = cs.fontFamily || 'sans-serif';
			colours = {
				antinero: cs.getPropertyValue('--c-antinero').trim() || colours.antinero,
				dase: cs.getPropertyValue('--c-dase').trim() || colours.dase,
				anadohoi: cs.getPropertyValue('--c-anadohoi').trim() || colours.anadohoi
			};
		}
		const ro = new ResizeObserver((entries) => {
			for (const e of entries) {
				w = e.contentRect.width;
				h = e.contentRect.height;
			}
		});
		if (wrap) ro.observe(wrap);
		const onVis = () => {
			last = 0;
		};
		document.addEventListener('visibilitychange', onVis);
		// the Typekit face may still be loading: draw once it is, or fall
		// back after a beat so the field never waits on a slow font
		const ready = Promise.race([
			document.fonts.load(`${glyphPx}px ${family}`).then(() => document.fonts.ready),
			new Promise((r) => setTimeout(r, 1200))
		]);
		ready.then(() => {
			fontReady = true;
			if (reduced) draw();
			else raf = requestAnimationFrame(tick);
		});
		return () => {
			cancelAnimationFrame(raf);
			ro.disconnect();
			document.removeEventListener('visibilitychange', onVis);
		};
	});

	// a still frame follows a resize or the payload's arrival even when the
	// loop is not running (reduced motion, paused)
	$effect(() => {
		void columns;
		if (fontReady && (reduced || !playing)) draw();
	});
</script>

<div class="wrap" bind:this={wrap}>
	<canvas bind:this={canvas} style:width="{w}px" style:height="{h}px"></canvas>
</div>

<style>
	.wrap {
		position: absolute;
		inset: 0;
		overflow: hidden;
	}
	canvas {
		display: block;
		/* the codes are set in Obviously Regular on the artboards */
		font-family: var(--font-display);
	}
</style>
