<script lang="ts">
	/**
	 * Promise-vs-delivery Gantt: one row per sponsor project — bar from
	 * appointment to the initial deadline, a lighter segment for amendment
	 * extensions, ✓ where a completion act exists, ✕ where revoked, and a
	 * "today" rule. Grouped by outcome so the finding is visible at a glance.
	 */
	import { grInt } from '$lib/transforms/format';

	export interface GanttProject {
		ada: string;
		company: string;
		fire: string | null;
		start: string | null;
		deadline0: string | null;
		deadline: string | null;
		completed: string | null;
		revoked: string | null;
		status: string;
	}

	interface Props {
		projects: GanttProject[];
		/** status_as_of from the DB — the "today" rule */
		today: string;
		/** ada → short annotation printed beside the row */
		annotations?: Record<string, string>;
	}
	let { projects, today, annotations = {} }: Props = $props();

	const GROUPS: [string, string][] = [
		['completed', 'Completion act on record'],
		['active', 'Still inside their deadline'],
		['no_completion_recorded', 'Deadline passed — no completion act found'],
		['revoked', 'Revoked'],
		['superseded', 'Restated (not counted)']
	];
	const COLOR: Record<string, string> = {
		completed: 'var(--c-anadohoi)',
		active: '#9a8c74',
		no_completion_recorded: 'var(--c-antinero)',
		revoked: '#7a1f1f',
		superseded: '#b8b0a2'
	};

	const T0 = new Date('2021-07-01').getTime();
	const T1 = new Date('2029-03-01').getTime();
	const W = 920;
	const LABEL_W = 190;
	const ROW_H = 13;
	const HEAD_H = 22;

	function x(d: string | null): number | null {
		if (!d) return null;
		const t = new Date(d).getTime();
		if (Number.isNaN(t)) return null;
		return LABEL_W + ((W - LABEL_W - 8) * (t - T0)) / (T1 - T0);
	}

	interface Row {
		p: GanttProject;
		y: number;
	}
	const layout = $derived.by(() => {
		const rows: Row[] = [];
		const heads: { y: number; label: string; n: number }[] = [];
		let y = 0;
		for (const [status, label] of GROUPS) {
			const members = projects
				.filter((p) => p.status === status)
				.sort((a, b) => (a.start ?? '').localeCompare(b.start ?? ''));
			if (!members.length) continue;
			heads.push({ y, label, n: members.length });
			y += HEAD_H;
			for (const p of members) {
				rows.push({ p, y });
				y += ROW_H;
			}
			y += 10;
		}
		return { rows, heads, height: y + 24 };
	});

	const years = ['2022', '2023', '2024', '2025', '2026', '2027', '2028'];
	const todayX = $derived(x(today) ?? LABEL_W);

	function tip(p: GanttProject): string {
		const bits = [
			p.company,
			p.fire ?? '',
			`appointed ${p.start ?? '—'}`,
			`deadline ${p.deadline ?? '—'}${p.deadline0 && p.deadline0 !== p.deadline ? ` (initially ${p.deadline0})` : ''}`,
			p.completed ? `completed ${p.completed}` : '',
			p.revoked ? `revoked ${p.revoked}` : ''
		];
		return bits.filter(Boolean).join(' · ');
	}
</script>

<svg viewBox="0 0 {W} {layout.height}" role="img" aria-label="Timeline of every sponsor project">
	<!-- year grid -->
	{#each years as yr (yr)}
		{@const gx = x(`${yr}-01-01`)}
		{#if gx}
			<line x1={gx} y1="0" x2={gx} y2={layout.height - 16} class="grid" />
			<text x={gx} y={layout.height - 4} class="axis">{yr}</text>
		{/if}
	{/each}

	<!-- today rule -->
	<line x1={todayX} y1="0" x2={todayX} y2={layout.height - 16} class="today" />
	<text x={todayX + 4} y="10" class="today-label">today ({today})</text>

	{#each layout.heads as h (h.label)}
		<text x="0" y={h.y + 14} class="ghead">{h.label} — {grInt(h.n)}</text>
	{/each}

	{#each layout.rows as { p, y } (p.ada)}
		{@const xs = x(p.start)}
		{@const xd0 = x(p.deadline0 ?? p.deadline)}
		{@const xd = x(p.deadline)}
		{@const xc = x(p.completed)}
		{@const xr = x(p.revoked)}
		{@const c = COLOR[p.status]}
		<g class="row">
			<title>{tip(p)}</title>
			<a href={`/anadohoi/project/${p.ada}`}>
				<text x={LABEL_W - 6} y={y + 9} class="label">{p.company.slice(0, 26)}</text>
			</a>
			{#if xs !== null && xd0 !== null && xd0 > xs}
				<rect x={xs} y={y + 2} width={xd0 - xs} height="7" fill={c} opacity="0.85" rx="1" />
			{:else if xs !== null}
				<rect x={xs} y={y + 2} width="3" height="7" fill={c} opacity="0.85" />
			{/if}
			{#if xd0 !== null && xd !== null && xd > xd0}
				<rect x={xd0} y={y + 2} width={xd - xd0} height="7" fill={c} opacity="0.35" rx="1" />
			{/if}
			{#if xc !== null}
				<text x={xc + 2} y={y + 10} class="mark ok">✓</text>
			{/if}
			{#if xr !== null}
				<text x={xr + 2} y={y + 10} class="mark bad">✕</text>
			{/if}
			{#if annotations[p.ada]}
				{@const ax = Math.max(xd ?? 0, xc ?? 0, xr ?? 0, xs ?? 0) + 14}
				<text x={ax} y={y + 10} class="anno">← {annotations[p.ada]}</text>
			{/if}
		</g>
	{/each}
</svg>

<style>
	svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.grid {
		stroke: var(--line);
		stroke-width: 0.5;
	}
	.axis {
		font-size: 10px;
		fill: var(--ink-faint);
		text-anchor: middle;
	}
	.today {
		stroke: var(--ink);
		stroke-width: 1;
		stroke-dasharray: 3 3;
	}
	.today-label {
		font-size: 10px;
		fill: var(--ink);
		font-weight: 600;
	}
	.ghead {
		font-size: 12px;
		font-weight: 700;
		fill: var(--ink);
	}
	.label {
		font-size: 9.5px;
		fill: var(--ink-soft);
		text-anchor: end;
	}
	.row a:hover .label {
		fill: var(--ink);
		text-decoration: underline;
	}
	.mark {
		font-size: 10px;
		font-weight: 700;
	}
	.mark.ok {
		fill: var(--c-anadohoi);
	}
	.mark.bad {
		fill: #7a1f1f;
	}
	.anno {
		font-size: 10px;
		fill: var(--ink);
		font-style: italic;
	}
</style>
