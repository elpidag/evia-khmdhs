<script lang="ts">
	/**
	 * Dev-only curation widget on the sponsor project page: the reviewer
	 * pastes the project's exact location (a "lat, lon" pair or a Google
	 * Maps link), it is kept per-ΑΔΑ in localStorage, and "copy all" emits
	 * the collected batch to hand back for landing in the curated JSON.
	 * Never rendered in production builds (the page gates on `dev`).
	 */
	interface Props {
		ada: string;
		/** pre-filled Google Maps search: the act's location wording */
		query: string;
	}
	let { ada, query }: Props = $props();

	const KEY = 'anadohoi-exact-locations';
	let all = $state<Record<string, { lat: number; lon: number }>>({});
	let raw = $state('');
	let msg = $state('');
	let showOut = $state(false);
	let outEl = $state<HTMLTextAreaElement | null>(null);

	$effect(() => {
		try {
			all = JSON.parse(localStorage.getItem(KEY) ?? '{}');
		} catch {
			all = {};
		}
	});
	const mine = $derived(all[ada]);
	const nSaved = $derived(Object.keys(all).length);

	/** accepts "38.0132, 23.5201" or a Google Maps URL (@lat,lon / q=lat,lon) */
	function parse(s: string): { lat: number; lon: number } | null {
		const m =
			/@(-?\d{1,2}\.\d+),(-?\d{1,3}\.\d+)/.exec(s) ??
			/(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)/.exec(s);
		if (!m) return null;
		const lat = +m[1];
		const lon = +m[2];
		// Greece sanity window — rejects swapped/for­eign coordinates
		if (lat < 34 || lat > 42 || lon < 19 || lon > 30) return null;
		return { lat, lon };
	}

	function save() {
		const p = parse(raw);
		if (!p) {
			msg = 'could not read coordinates — paste «lat, lon» or a Google Maps link';
			return;
		}
		all = { ...all, [ada]: p };
		localStorage.setItem(KEY, JSON.stringify(all));
		raw = '';
		msg = `saved: ${p.lat}, ${p.lon}`;
	}

	function clearMine() {
		const { [ada]: _, ...rest } = all;
		all = rest;
		localStorage.setItem(KEY, JSON.stringify(all));
		msg = 'cleared';
	}

	function copyAll() {
		showOut = !showOut;
		if (!showOut) return;
		queueMicrotask(() => {
			if (!outEl) return;
			outEl.value = Object.entries(all)
				.map(([a, p]) => `${a} ${p.lat} ${p.lon}`)
				.join('\n');
			outEl.focus();
			outEl.select();
			try {
				document.execCommand('copy');
				msg = 'copied — paste it in the chat';
			} catch {
				msg = 'select & press Ctrl+C';
			}
		});
	}

	const gmaps = $derived(
		`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`
	);
</script>

<aside class="loc" aria-label="Exact location curation (dev only)">
	<h2>Exact location <small>curation · dev only</small></h2>
	{#if mine}
		<p class="cur">
			saved: <b>{mine.lat}, {mine.lon}</b>
			<a
				href={`https://www.google.com/maps/search/?api=1&query=${mine.lat},${mine.lon}`}
				target="_blank"
				rel="noopener">view</a
			>
			<button type="button" class="lnk" onclick={clearMine}>clear</button>
		</p>
	{:else}
		<p class="cur muted">no exact location saved for this project yet</p>
	{/if}
	<input
		type="text"
		bind:value={raw}
		placeholder="38.0132, 23.5201 — or paste a Google Maps link"
		onkeydown={(e) => e.key === 'Enter' && save()}
	/>
	<div class="btns">
		<button type="button" onclick={save}>save</button>
		<a href={gmaps} target="_blank" rel="noopener">search on Google Maps ↗</a>
	</div>
	{#if msg}<p class="msg">{msg}</p>{/if}
	<div class="allrow">
		<button type="button" class="lnk" onclick={copyAll}>
			copy all saved ({nSaved})
		</button>
	</div>
	{#if showOut}
		<textarea bind:this={outEl} readonly rows="4" aria-label="collected locations"></textarea>
	{/if}
</aside>

<style>
	.loc {
		width: 300px;
		max-width: 100%;
		border: 1px dashed var(--line-strong);
		border-radius: 6px;
		padding: var(--sp-2) var(--sp-3);
		background: var(--paper-2);
		font-size: var(--fs-13);
	}
	.loc h2 {
		margin: 0 0 var(--sp-1);
		font-size: var(--fs-14);
		font-weight: 700;
		font-family: 'futura-100-greek', 'futura-100-greek-book', 'Sofia Sans', system-ui, sans-serif;
		color: #000;
	}
	.loc h2 small {
		font-weight: 400;
		color: var(--ink-faint);
		font-size: var(--fs-12);
	}
	.cur {
		margin: 0 0 var(--sp-1);
	}
	.muted {
		color: var(--ink-soft);
	}
	input[type='text'] {
		width: 100%;
		font: inherit;
		font-size: var(--fs-13);
		padding: 4px 8px;
		border: 1px solid var(--line);
		border-radius: 4px;
		background: var(--paper);
		color: var(--ink);
	}
	.btns {
		display: flex;
		align-items: center;
		gap: var(--sp-3);
		margin-top: var(--sp-1);
	}
	button {
		font: inherit;
		font-size: var(--fs-13);
		padding: 2px 12px;
		border: 1px solid var(--c-anadohoi);
		border-radius: 4px;
		background: var(--c-anadohoi);
		color: #fff;
		cursor: pointer;
	}
	button.lnk {
		background: none;
		color: var(--c-anadohoi);
		border: none;
		padding: 0;
		text-decoration: underline;
	}
	.msg {
		margin: var(--sp-1) 0 0;
		color: var(--c-anadohoi);
	}
	.allrow {
		margin-top: var(--sp-2);
		border-top: 1px solid var(--line);
		padding-top: var(--sp-1);
	}
	textarea {
		width: 100%;
		margin-top: var(--sp-1);
		font: inherit;
		font-size: var(--fs-12);
		border: 1px solid var(--line);
		border-radius: 4px;
		background: var(--paper);
		color: var(--ink);
	}
	button:focus-visible,
	input:focus-visible,
	textarea:focus-visible {
		outline: 2px solid var(--c-anadohoi);
		outline-offset: 1px;
	}
</style>
