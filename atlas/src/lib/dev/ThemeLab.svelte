<script lang="ts">
	/**
	 * THEME LAB — the author's try-out panel for colours and fonts
	 * (2026-09-03). DEV-ONLY: lazy-imported by the layout when the URL
	 * carries `?lab` and never part of a production render.
	 *
	 * It reads the design tokens straight from `tokens.css` (the ?raw
	 * import, so the list can never go stale), overrides them live on
	 * `:root` while the author browses the real site, keeps named presets
	 * in localStorage, and copies the CHANGED tokens as a ready `:root`
	 * block to hand back for baking in.
	 *
	 * Since the same day's follow-up the chart palettes (category colours,
	 * year ramps, map ramps, gantt statuses) are CSS strings over these
	 * tokens, so they follow a change live; every apply/clear announces
	 * itself as a `themelab:change` window event and the canvas charts
	 * redraw through $lib/theme.svelte's tick.
	 */
	import tokensRaw from '$lib/styles/tokens.css?raw';

	interface Tok {
		name: string;
		base: string;
		kind: 'color' | 'font' | 'derived';
	}
	const TOKENS: Tok[] = [];
	for (const m of tokensRaw.matchAll(/--([a-z0-9-]+):\s*([^;]+);/g)) {
		const name = m[1];
		const value = m[2].replace(/\s+/g, ' ').trim();
		if (name.startsWith('font-')) {
			TOKENS.push({ name, base: value, kind: 'font' });
		} else if (value.includes('var(')) {
			// tokens.css derives these from the primaries (the author's
			// optimisation, 2026-09-03) — shown, never edited here
			TOKENS.push({ name, base: value, kind: 'derived' });
		} else if (/^(#|rgb|oklch|hsl)/.test(value)) {
			TOKENS.push({ name, base: value, kind: 'color' });
		}
	}

	/** current overrides, token name → value */
	let over = $state<Record<string, string>>({});
	/** ancillary loads that must come back after a reload */
	let liveGoogle = $state<string[]>([]);
	let liveKits = $state<string[]>([]);
	/** the google-font trial name typed per font token */
	let fontPick = $state<Record<string, string>>({});
	let presets = $state<Record<string, Record<string, string>>>(loadPresets());
	let copied = $state(false);

	function loadPresets(): Record<string, Record<string, string>> {
		try {
			return JSON.parse(localStorage.getItem('themelab.presets') ?? '{}');
		} catch {
			return {};
		}
	}
	function persist() {
		try {
			localStorage.setItem('themelab.presets', JSON.stringify(presets));
		} catch {
			/* storage may be unavailable; presets just don't survive */
		}
	}

	/** the LIVE state survives a reload: overrides + the fonts they need
	 *  (google families and adobe kits re-inject; a font loaded from a FILE
	 *  cannot come back by itself — its row says session-only) */
	function persistLive() {
		try {
			localStorage.setItem(
				'themelab.live',
				JSON.stringify({ over, google: liveGoogle, kits: liveKits })
			);
		} catch {
			/* fine */
		}
	}
	function injectGoogle(fam: string) {
		const id = `themelab-font-${fam.replace(/\s+/g, '-').toLowerCase()}`;
		if (document.getElementById(id)) return;
		const link = document.createElement('link');
		link.id = id;
		link.rel = 'stylesheet';
		link.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(fam).replace(/%20/g, '+')}:wght@300;400;700;900&display=swap`;
		document.head.appendChild(link);
	}
	function injectKit(id: string) {
		const dom = `themelab-kit-${id}`;
		if (document.getElementById(dom)) return;
		const link = document.createElement('link');
		link.id = dom;
		link.rel = 'stylesheet';
		link.href = `https://use.typekit.net/${id}.css`;
		document.head.appendChild(link);
	}
	// restore the live state once, when the panel mounts after a reload
	$effect(() => {
		try {
			const raw = localStorage.getItem('themelab.live');
			if (!raw) return;
			const live = JSON.parse(raw) as {
				over?: Record<string, string>;
				google?: string[];
				kits?: string[];
			};
			for (const fam of live.google ?? []) injectGoogle(fam);
			for (const id of live.kits ?? []) injectKit(id);
			liveGoogle = live.google ?? [];
			liveKits = live.kits ?? [];
			for (const [k, v] of Object.entries(live.over ?? {})) {
				if (!(k in over)) apply(k, v);
			}
		} catch {
			/* fine */
		}
	});

	function announce() {
		window.dispatchEvent(new CustomEvent('themelab:change'));
	}
	function apply(name: string, value: string) {
		over = { ...over, [name]: value };
		document.documentElement.style.setProperty(`--${name}`, value);
		persistLive();
		announce();
	}
	function clear(name: string) {
		const { [name]: _, ...rest } = over;
		over = rest;
		document.documentElement.style.removeProperty(`--${name}`);
		persistLive();
		announce();
	}
	function resetAll() {
		for (const name of Object.keys(over)) {
			document.documentElement.style.removeProperty(`--${name}`);
		}
		over = {};
		liveGoogle = [];
		liveKits = [];
		try {
			localStorage.removeItem('themelab.live');
		} catch {
			/* fine */
		}
		announce();
	}

	/** per-font status line: loaded, not found, file loaded … */
	let fontMsg = $state<Record<string, string>>({});

	/** a Google Fonts trial: verify the family EXISTS there, then load it in
	 *  front of the stack — an unknown name (the author's commercial faces)
	 *  used to fail silently; now it says so and still tries the name as a
	 *  LOCALLY INSTALLED font */
	async function tryFont(tok: Tok) {
		const fam = (fontPick[tok.name] ?? '').trim();
		if (!fam) return;
		const href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(fam).replace(/%20/g, '+')}:wght@300;400;700;900&display=swap`;
		let ok = false;
		try {
			ok = (await fetch(href)).ok;
		} catch {
			ok = false;
		}
		if (ok) {
			injectGoogle(fam);
			if (!liveGoogle.includes(fam)) liveGoogle = [...liveGoogle, fam];
			fontMsg = { ...fontMsg, [tok.name]: 'Google font loaded ✓' };
		} else {
			fontMsg = {
				...fontMsg,
				[tok.name]:
					'not on Google Fonts — applied as a locally installed name (shows only if that exact name is installed); otherwise load its file with 📁'
			};
		}
		apply(tok.name, `'${fam}', ${tok.base}`);
	}

	/** the author's own font files: .woff2/.otf/.ttf straight into the page
	 *  (FontFace API; weight range covers variable fonts) — session-only,
	 *  so the export names the family for the later proper wiring */
	async function loadFontFile(tok: Tok, ev: Event) {
		const input = ev.currentTarget as HTMLInputElement;
		const f = input.files?.[0];
		if (!f) return;
		try {
			const fam = f.name.replace(/\.[^.]+$/, '');
			const face = new FontFace(fam, await f.arrayBuffer(), { weight: '100 900' });
			await face.load();
			document.fonts.add(face);
			apply(tok.name, `'${fam}', ${tok.base}`);
			fontMsg = { ...fontMsg, [tok.name]: `file loaded ✓ — ${f.name} (this browser session only)` };
		} catch (e) {
			fontMsg = { ...fontMsg, [tok.name]: `could not read ${f.name}` };
		}
		input.value = '';
	}

	/** an Adobe Fonts WEB PROJECT by id or URL: loads its stylesheet, so
	 *  the kit's families resolve by their CSS names (the lowercase slugs
	 *  the web-project page shows, e.g. novel-sans-pro) */
	let kitId = $state('');
	let kitMsg = $state('');
	function loadKit() {
		const raw = kitId.trim();
		if (!raw) return;
		const m = raw.match(/([a-z0-9]{6,8})(?:\.css)?$/i);
		if (!m) {
			kitMsg = 'that does not look like a kit id or use.typekit.net URL';
			return;
		}
		const id = m[1].toLowerCase();
		if (!document.getElementById(`themelab-kit-${id}`)) {
			injectKit(id);
			kitMsg = `kit ${id} loading … then type its CSS family names below and press try`;
		} else {
			kitMsg = `kit ${id} already loaded`;
		}
		if (!liveKits.includes(id)) liveKits = [...liveKits, id];
		persistLive();
	}

	function savePreset() {
		const name = prompt('Preset name?');
		if (!name) return;
		presets = { ...presets, [name]: { ...over } };
		persist();
	}
	function applyPreset(name: string) {
		resetAll();
		for (const [k, v] of Object.entries(presets[name] ?? {})) apply(k, v);
	}
	function dropPreset(name: string) {
		const { [name]: _, ...rest } = presets;
		presets = rest;
		persist();
	}

	async function copyCss() {
		const lines = Object.entries(over).map(([k, v]) => `\t--${k}: ${v};`);
		const css = lines.length ? `:root {\n${lines.join('\n')}\n}` : '/* no changes */';
		await navigator.clipboard.writeText(css);
		copied = true;
		setTimeout(() => (copied = false), 1500);
	}

	/** an <input type=color> speaks only #rrggbb */
	const hexish = (v: string) => /^#[0-9a-fA-F]{6}$/.test(v.trim());
	const colors = TOKENS.filter((t) => t.kind === 'color');
	const derived = TOKENS.filter((t) => t.kind === 'derived');
	const fonts = TOKENS.filter((t) => t.kind === 'font');
	let open = $state(true);

	/** the derived tones RESOLVED for their swatches — recomputed whenever a
	 *  primary changes, through a probe element (a color-mix string cannot
	 *  paint a swatch by itself) */
	let resolved = $state<Record<string, string>>({});
	$effect(() => {
		void over;
		const probe = document.createElement('div');
		document.body.appendChild(probe);
		const out: Record<string, string> = {};
		for (const t of derived) {
			probe.style.color = `var(--${t.name})`;
			out[t.name] = getComputedStyle(probe).color;
		}
		probe.remove();
		resolved = out;
	});
</script>

<aside class="lab" class:min={!open}>
	<header>
		<button class="tt" onclick={() => (open = !open)}>THEME LAB {open ? '▾' : '▸'}</button>
		{#if open}
			<div class="acts">
				<button onclick={copyCss}>{copied ? 'copied ✓' : 'copy CSS'}</button>
				<button onclick={savePreset}>save preset</button>
				<button onclick={resetAll}>reset</button>
			</div>
		{/if}
	</header>
	{#if open}
		{#if Object.keys(presets).length}
			<div class="presets">
				{#each Object.keys(presets) as p (p)}
					<span>
						<button class="pname" onclick={() => applyPreset(p)}>{p}</button>
						<button class="px" onclick={() => dropPreset(p)} aria-label={`delete ${p}`}>✕</button>
					</span>
				{/each}
			</div>
		{/if}

		<h3>COLOURS</h3>
		{#each colors as t (t.name)}
			{@const cur = over[t.name] ?? t.base}
			<div class="row" class:changed={t.name in over}>
				<label for={`tl-${t.name}`}>--{t.name}</label>
				{#if hexish(cur)}
					<input
						id={`tl-${t.name}`}
						type="color"
						value={cur}
						oninput={(e) => apply(t.name, e.currentTarget.value)}
					/>
				{:else}
					<span class="swatch" style:background={cur}></span>
				{/if}
				<input
					class="hex"
					type="text"
					value={cur}
					onchange={(e) => apply(t.name, e.currentTarget.value)}
				/>
				{#if t.name in over}
					<button class="px" onclick={() => clear(t.name)} aria-label="reset token">↺</button>
				{/if}
			</div>
		{/each}

		<h3>DERIVED — FOLLOW INK &amp; PAPER</h3>
		<p class="hint">
			These tones are mixed automatically from the primaries above (tokens.css `color-mix`):
			change --ink or --paper and every grey refills itself.
		</p>
		{#each derived as t (t.name)}
			<div class="row drow">
				<label for={`tld-${t.name}`}>--{t.name}</label>
				<span id={`tld-${t.name}`} class="swatch" style:background={resolved[t.name] ?? 'transparent'}
				></span>
				<span class="dval">{t.base}</span>
			</div>
		{/each}

		<h3>FONTS</h3>
		<p class="hint">
			Type a Google Fonts family name and press try — it loads and jumps to the front of that
			token's stack. ↺ restores the kit font. For ADOBE FONTS: put the fonts in a web project on
			fonts.adobe.com, paste the project's kit id or use.typekit.net URL here, then use the CSS
			family names the project page shows (lowercase, e.g. novel-sans-pro).
		</p>
		<div class="kit">
			<input
				type="text"
				placeholder="Adobe kit id or use.typekit.net URL"
				bind:value={kitId}
				onkeydown={(e) => e.key === 'Enter' && loadKit()}
			/>
			<button onclick={loadKit}>load kit</button>
		</div>
		{#if kitMsg}<p class="msg kitmsg">{kitMsg}</p>{/if}
		{#each fonts as t (t.name)}
			<div class="frow" class:changed={t.name in over}>
				<label for={`tl-${t.name}`}>--{t.name}</label>
				<span class="cur">{(over[t.name] ?? t.base).split(',')[0].replace(/'/g, '')}</span>
				<span class="try">
					<input
						id={`tl-${t.name}`}
						type="text"
						placeholder="e.g. Archivo"
						bind:value={fontPick[t.name]}
						onkeydown={(e) => e.key === 'Enter' && tryFont(t)}
					/>
					<button onclick={() => tryFont(t)}>try</button>
					<label class="file" title="load a font file (.woff2 / .otf / .ttf)">
						📁<input
							type="file"
							accept=".woff2,.woff,.otf,.ttf"
							onchange={(e) => loadFontFile(t, e)}
						/>
					</label>
					{#if t.name in over}
						<button class="px" onclick={() => clear(t.name)} aria-label="reset font">↺</button>
					{/if}
				</span>
				{#if fontMsg[t.name]}
					<span class="msg">{fontMsg[t.name]}</span>
				{/if}
			</div>
		{/each}

		<p class="foot">
			Chart-internal colours (the category palette, year greys, map ramps) live in code and
			follow these tokens live, charts included; a preset is your palette, applied whole.
		</p>
	{/if}
</aside>

<style>
	.lab {
		position: fixed;
		top: 100px;
		right: 12px;
		z-index: 1000;
		width: 330px;
		max-height: calc(100vh - 130px);
		overflow-y: auto;
		background: #fff;
		border: 1px solid #bbb;
		box-shadow: 0 12px 34px rgba(0, 0, 0, 0.18);
		padding: 10px 12px 12px;
		font-family: system-ui, sans-serif;
		font-size: 12px;
		color: #222;
	}
	.lab.min {
		width: auto;
		max-height: none;
		padding: 6px 10px;
	}
	header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
	}
	.tt {
		font-weight: 700;
		letter-spacing: 0.06em;
		background: none;
		border: 0;
		cursor: pointer;
		padding: 0;
		font-size: 12px;
	}
	.acts {
		display: flex;
		gap: 4px;
	}
	button {
		font-size: 11px;
		border: 1px solid #ccc;
		background: #f6f6f6;
		border-radius: 3px;
		padding: 2px 7px;
		cursor: pointer;
	}
	button:hover {
		background: #ececec;
	}
	.presets {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		margin-top: 8px;
	}
	.presets span {
		display: inline-flex;
		gap: 2px;
	}
	h3 {
		margin: 12px 0 6px;
		font-size: 11px;
		letter-spacing: 0.08em;
		color: #666;
	}
	.row,
	.frow {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 2px 0;
	}
	.frow {
		flex-wrap: wrap;
	}
	.row.changed label,
	.frow.changed label {
		font-weight: 700;
	}
	label {
		flex: 0 0 128px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-family: ui-monospace, monospace;
		font-size: 11px;
	}
	input[type='color'] {
		width: 26px;
		height: 20px;
		padding: 0;
		border: 1px solid #ccc;
		background: none;
	}
	.swatch {
		width: 26px;
		height: 20px;
		border: 1px solid #ccc;
		display: inline-block;
	}
	.hex {
		flex: 1;
		min-width: 0;
		font-family: ui-monospace, monospace;
		font-size: 11px;
		border: 1px solid #ddd;
		padding: 2px 4px;
	}
	.px {
		border: 0;
		background: none;
		padding: 0 2px;
		cursor: pointer;
	}
	.cur {
		flex: 1;
		font-style: italic;
		color: #555;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.try {
		display: flex;
		gap: 4px;
		flex: 1 0 100%;
		padding-left: 128px;
		box-sizing: border-box;
	}
	.try input[type='text'] {
		flex: 1;
		min-width: 0;
		border: 1px solid #ddd;
		padding: 2px 4px;
		font-size: 11px;
	}
	.kit {
		display: flex;
		gap: 4px;
		margin: 4px 0 8px;
	}
	.kit input {
		flex: 1;
		min-width: 0;
		border: 1px solid #ddd;
		padding: 2px 4px;
		font-size: 11px;
	}
	.kitmsg {
		padding-left: 0;
	}
	.file {
		border: 1px solid #ccc;
		background: #f6f6f6;
		border-radius: 3px;
		padding: 1px 6px;
		cursor: pointer;
		font-size: 12px;
	}
	.file input {
		display: none;
	}
	.msg {
		flex: 1 0 100%;
		padding-left: 128px;
		box-sizing: border-box;
		font-size: 10px;
		line-height: 1.3;
		color: #946200;
	}
	.drow label {
		color: #888;
	}
	.dval {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-family: ui-monospace, monospace;
		font-size: 10px;
		color: #999;
	}
	.hint,
	.foot {
		margin: 4px 0;
		font-size: 10.5px;
		line-height: 1.35;
		color: #777;
	}
	.foot {
		margin-top: 10px;
		border-top: 1px solid #eee;
		padding-top: 6px;
	}
</style>
