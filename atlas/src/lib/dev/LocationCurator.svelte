<script lang="ts">
	/**
	 * Dev-only curation widget on the sponsor project page: the reviewer
	 * pastes an exact location (a "lat, lon" pair or a Google Maps link),
	 * chooses WHICH work site of the project it belongs to (projects may
	 * have several), it is kept per-ΑΔΑ/per-site in localStorage, and
	 * "copy all" emits the collected batch to hand back for landing in the
	 * curated JSON. Never rendered in production builds (`dev`-gated).
	 * Storage upgrades v1 entries ({lat,lon} per ΑΔΑ) to the per-site map
	 * under the '' (whole-project) slot.
	 */
	interface Props {
		ada: string;
		/** pre-filled Google Maps search: the act's location wording */
		query: string;
		/** curated work-site names of this project (may be empty) */
		sites?: string[];
	}
	let { ada, query, sites = [] }: Props = $props();

	const KEY = 'anadohoi-exact-locations';
	type Pt = { lat: number; lon: number };
	type Store = Record<string, Record<string, Pt>>;
	let all = $state<Store>({});
	let raw = $state('');
	let site = $state('');
	let msg = $state('');
	let showOut = $state(false);
	let outEl = $state<HTMLTextAreaElement | null>(null);

	$effect(() => {
		try {
			const v = JSON.parse(localStorage.getItem(KEY) ?? '{}');
			const up: Store = {};
			for (const [a, e] of Object.entries(v as Record<string, unknown>)) {
				const o = e as Record<string, unknown>;
				// v1 shape: {lat, lon} directly under the ΑΔΑ
				if (typeof o.lat === 'number' && typeof o.lon === 'number')
					up[a] = { '': { lat: o.lat as number, lon: o.lon as number } };
				else up[a] = o as Record<string, Pt>;
			}
			all = up;
		} catch {
			all = {};
		}
	});
	const mine = $derived(all[ada] ?? {});
	const nSaved = $derived(
		Object.values(all).reduce((s, m) => s + Object.keys(m).length, 0)
	);

	/** accepts "38.0132, 23.5201" or a Google Maps URL (@lat,lon / q=lat,lon) */
	function parse(s: string): Pt | null {
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

	function persist() {
		localStorage.setItem(KEY, JSON.stringify(all));
	}
	function save() {
		const p = parse(raw);
		if (!p) {
			msg = 'could not read coordinates — paste «lat, lon» or a Google Maps link';
			return;
		}
		all = { ...all, [ada]: { ...(all[ada] ?? {}), [site]: p } };
		persist();
		raw = '';
		msg = `saved ${site || 'όλο το έργο'}: ${p.lat}, ${p.lon}`;
	}

	function clearOne(s: string) {
		const m = { ...(all[ada] ?? {}) };
		delete m[s];
		if (Object.keys(m).length) all = { ...all, [ada]: m };
		else {
			const { [ada]: _, ...rest } = all;
			all = rest;
		}
		persist();
		msg = 'cleared';
	}

	function copyAll() {
		showOut = !showOut;
		if (!showOut) return;
		queueMicrotask(() => {
			if (!outEl) return;
			outEl.value = Object.entries(all)
				.flatMap(([a, m]) =>
					Object.entries(m).map(([s, p]) =>
						s ? `${a}\t${s}\t${p.lat} ${p.lon}` : `${a} ${p.lat} ${p.lon}`
					)
				)
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
		`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
			site ? `${site} ${query}` : query
		)}`
	);
</script>

<aside class="loc" aria-label="Exact location curation (dev only)">
	<h2>Exact location <small>curation · dev only</small></h2>
	{#if Object.keys(mine).length}
		{#each Object.entries(mine) as [s, p] (s)}
			<p class="cur">
				<b>{s || 'όλο το έργο'}</b>: {p.lat}, {p.lon}
				<a
					href={`https://www.google.com/maps/search/?api=1&query=${p.lat},${p.lon}`}
					target="_blank"
					rel="noopener">view</a
				>
				<button type="button" class="lnk" onclick={() => clearOne(s)}>clear</button>
			</p>
		{/each}
	{:else}
		<p class="cur muted">no exact location saved for this project yet</p>
	{/if}
	{#if sites.length}
		<select bind:value={site} aria-label="which work site">
			<option value="">όλο το έργο (μία θέση)</option>
			{#each sites as s (s)}
				<option value={s}>{s}</option>
			{/each}
		</select>
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
	select,
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
	select {
		margin-bottom: var(--sp-1);
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
	select:focus-visible,
	input:focus-visible,
	textarea:focus-visible {
		outline: 2px solid var(--c-anadohoi);
		outline-offset: 1px;
	}
</style>
