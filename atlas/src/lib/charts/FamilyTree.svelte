<script lang="ts">
	/** The contract's ΚΗΜΔΗΣ procurement family as a staged tree:
	 *  funding acts (trunk) → πρόσκληση → κατακυρώσεις (fan) → συμβάσεις,
	 *  with THIS contract's trail highlighted in the dataset colour and its
	 *  payment orders hanging below. Award↔contract pairs are drawn ONLY
	 *  when the co-op named in the award title matches the contract's
	 *  contractor (fold-contains) — never guessed from order. The timeline
	 *  table below the diagram stays as the accessible/tabular view. */
	interface Act {
		adam: string;
		kind: 'request' | 'approved_request' | 'notice' | 'auction' | 'contract' | 'completion' | 'extension';
		title: string | null;
		d: string | null;
		cancelled: number;
		in_db: boolean;
		who?: string | null;
		self?: boolean;
	}
	interface Props {
		acts: Act[];
		/** trail colour (dataset hue) */
		accent?: string;
		/** contract-page route prefix for in-db siblings */
		contractHref?: (adam: string) => string;
		/** payments summary for the trail's terminal node */
		payments?: { n: number; eur: string } | null;
		kindLabel: Record<string, string>;
		/** scale the drawing down to the box it sits in (the header slot of
		 *  the contract page) instead of drawing at its natural width */
		fit?: boolean;
	}
	let {
		acts,
		accent = 'var(--c-dase)',
		contractHref = (a) => `/dase/contract/${a}`,
		payments = null,
		kindLabel,
		fit = false
	}: Props = $props();

	// ---- text folding for the name-verified award↔contract pairing
	const fold = (s: string | null | undefined): string =>
		(s ?? '')
			.toUpperCase()
			.normalize('NFD')
			.replace(/[̀-ͯ]/g, '')
			.replace(/[^\p{L}\p{N}]/gu, '');

	// award titles read «Απευθείας ανάθεση στον ΔΑ.Σ.Ε. Χ για την …» —
	// the segment before « για » carries the co-op; display heuristic only
	function awardLabel(t: string | null): string | null {
		const m = /στ[οη]ν?\s+(.+?)\s+(για|την|του)\s/u.exec(t ?? '');
		return m ? m[1] : null;
	}

	const trunk = $derived(
		acts.filter((a) => a.kind === 'request' || a.kind === 'approved_request' || a.kind === 'notice')
	);
	const awards = $derived(acts.filter((a) => a.kind === 'auction'));
	const contracts = $derived(acts.filter((a) => a.kind === 'contract'));
	const completions = $derived(acts.filter((a) => a.kind === 'completion'));
	const selfAct = $derived(contracts.find((a) => a.self) ?? null);

	// award index -> contract index, only where the award title contains the
	// contract's contractor name after folding; the co-op's legal-form
	// prefix (ΔΑΣΕ/ΕΔΑΣΕ/…) is stripped first because award wording often
	// interleaves it («ΔΑ.Σ.Ε. ΣΥΝ.ΠΕ. Προφήτη Ηλία»). A contract pairs
	// only on a UNIQUE hit — ambiguity means no edge, never a guess.
	const whoCore = (s: string | null | undefined): string =>
		fold(s).replace(/^(ΕΔΑΣΕ|ΑΔΣΕ|ΔΑΣΕ|ΔΑΣΙΚΟΣΣΥΝΕΤΑΙΡΙΣΜΟΣ(ΕΡΓΑΣΙΑΣ)?)/u, '');
	const pairs = $derived.by(() => {
		const map = new Map<number, number>();
		const used = new Set<number>();
		contracts.forEach((c, ci) => {
			// both the full folded name and the form-stripped core may match
			const cands = [fold(c.who), whoCore(c.who)].filter(
				(s, i, arr) => s.length >= 5 && arr.indexOf(s) === i
			);
			if (!cands.length) return;
			const hits = awards
				.map((a, ai) => ({ ai, f: fold(a.title) }))
				.filter(({ ai, f }) => !used.has(ai) && cands.some((w) => f.includes(w)));
			if (hits.length === 1) {
				map.set(hits[0].ai, ci);
				used.add(hits[0].ai);
			}
		});
		return map;
	});
	const selfAwardIdx = $derived.by(() => {
		if (!selfAct) return -1;
		const ci = contracts.indexOf(selfAct);
		for (const [ai, c] of pairs) if (c === ci) return ai;
		return -1;
	});

	// ---- geometry: contracts row drives the column order; paired awards
	// sit above their contract, unpaired awards fill the leftover slots
	const NW = 108; // node width
	const NH = 44; // node height
	const GX = 10; // column gap
	const GY = 34; // row gap
	const cols = $derived(Math.max(contracts.length, awards.length, 1));
	const width = $derived(Math.max(cols * (NW + GX) - GX, 320));
	const cx = (i: number) => i * (NW + GX) + NW / 2;

	const awardCol = $derived.by(() => {
		const col = new Array<number>(awards.length).fill(-1);
		const taken = new Set<number>();
		for (const [ai, ci] of pairs) {
			col[ai] = ci;
			taken.add(ci);
		}
		let free = 0;
		for (let ai = 0; ai < awards.length; ai++) {
			if (col[ai] >= 0) continue;
			while (taken.has(free)) free++;
			col[ai] = free;
			taken.add(free);
		}
		return col;
	});

	// trunk rows stack above; then awards row, contracts row, payments row
	const trunkH = $derived(trunk.length * (NH + 18));
	const yAward = $derived(trunkH + (awards.length ? 18 : 0));
	const yContract = $derived(yAward + (awards.length ? NH + GY : 0));
	const yPay = $derived(yContract + NH + GY);
	const hasTail = $derived(!!payments || completions.length > 0);
	const height = $derived(yContract + NH + (hasTail ? NH + GY : 0) + 6);

	function pdfHref(a: Act): string | null {
		if (a.kind === 'completion') return `/pdf/diavgeia/${a.adam}`;
		if (a.kind === 'contract') return a.in_db ? `/pdf/contract/${a.adam}` : null;
		return `/pdf/${a.kind === 'approved_request' ? 'request' : a.kind}/${a.adam}`;
	}
	function short(s: string | null | undefined, n = 30): string {
		const v = (s ?? '').trim();
		return v.length > n ? v.slice(0, n - 1) + '…' : v;
	}
</script>

{#if acts.length > 1}
	<div class="treewrap">
		<svg viewBox={`0 0 ${width} ${height}`} style:width={fit ? '100%' : `${width}px`} style:max-width={`${width}px`} class="tree">
			<!-- trunk: funding acts, vertically chained, centred -->
			{#each trunk as t, i (t.adam)}
				{@const y = i * (NH + 18)}
				{#if i > 0}
					<line class="edge trail" x1={width / 2} y1={y - 18} x2={width / 2} y2={y} />
				{/if}
				<a href={pdfHref(t)} target="_blank" rel="noopener">
					<g class="node trail" transform={`translate(${width / 2 - 130}, ${y})`}>
						<rect width="260" height={NH} rx="6" />
						<text class="k" x="10" y="16">{kindLabel[t.kind] ?? t.kind} · {t.d ?? ''}</text>
						<text class="t" x="10" y="32">{short(t.title, 44)}</text>
					</g>
				</a>
			{/each}

			{#if awards.length}
				<!-- notice (or trunk bottom) fans out to every award -->
				{#each awards as a, ai (a.adam)}
					{@const x = cx(awardCol[ai])}
					<path
						class="edge"
						class:trail={ai === selfAwardIdx}
						d={`M ${width / 2} ${trunkH} C ${width / 2} ${trunkH + 14}, ${x} ${yAward - 12}, ${x} ${yAward}`}
					/>
					<a href={pdfHref(a)} target="_blank" rel="noopener">
						<g
							class="node"
							class:trail={ai === selfAwardIdx}
							transform={`translate(${x - NW / 2}, ${yAward})`}
						>
							<rect width={NW} height={NH} rx="6" />
							<text class="k" x="8" y="16">{kindLabel[a.kind] ?? 'ανάθεση'}</text>
							<text class="t" x="8" y="32">{short(awardLabel(a.title) ?? a.adam, 17)}</text>
						</g>
					</a>
				{/each}
			{/if}

			{#each contracts as c, ci (c.adam)}
				{@const x = cx(ci)}
				{@const pairedAward = [...pairs].find(([, cc]) => cc === ci)}
				{#if pairedAward !== undefined}
					<line
						class="edge"
						class:trail={c.self}
						x1={cx(awardCol[pairedAward[0]])}
						y1={yAward + NH}
						x2={x}
						y2={yContract}
					/>
				{:else if awards.length === 0 && trunk.length > 0}
					<path
						class="edge"
						class:trail={c.self}
						d={`M ${width / 2} ${trunkH} C ${width / 2} ${trunkH + 14}, ${x} ${yContract - 12}, ${x} ${yContract}`}
					/>
				{/if}
				{#if c.self}
					<g class="node self" transform={`translate(${x - NW / 2}, ${yContract})`}>
						<rect width={NW} height={NH} rx="6" />
						<text class="k" x="8" y="16">{kindLabel.contract ?? 'σύμβαση'} · {c.d ?? ''}</text>
						<text class="t strong" x="8" y="32">this contract</text>
					</g>
				{:else if c.in_db}
					<a href={contractHref(c.adam)}>
						<g class="node" transform={`translate(${x - NW / 2}, ${yContract})`}>
							<rect width={NW} height={NH} rx="6" />
							<text class="k" x="8" y="16">{kindLabel.contract ?? 'σύμβαση'} · {c.d ?? ''}</text>
							<text class="t">
								<tspan x="8" y="32">{short(c.who ?? c.adam, 17)}</tspan>
							</text>
						</g>
					</a>
				{:else}
					<a href={pdfHref(c)} target="_blank" rel="noopener">
						<g class="node faint" transform={`translate(${x - NW / 2}, ${yContract})`}>
							<rect width={NW} height={NH} rx="6" />
							<text class="k" x="8" y="16">{kindLabel.contract ?? 'σύμβαση'} · {c.d ?? ''}</text>
							<text class="t" x="8" y="32">εκτός dataset</text>
						</g>
					</a>
				{/if}
			{/each}

			{#if hasTail && selfAct}
				{@const x = cx(contracts.indexOf(selfAct))}
				<line class="edge trail" x1={x} y1={yContract + NH} x2={x} y2={yPay} />
				<a href="#payments">
					<g class="node trail" transform={`translate(${x - NW / 2}, ${yPay})`}>
						<rect width={NW} height={NH} rx="6" />
						{#if payments}
							<text class="k" x="8" y="16">{kindLabel.payment ?? 'πληρωμές'}</text>
							<text class="t" x="8" y="32">{payments.n} · {payments.eur}</text>
						{:else}
							<text class="k" x="8" y="16">{kindLabel.completion ?? 'ολοκλήρωση'}</text>
							<text class="t" x="8" y="32">{completions.length} act(s)</text>
						{/if}
					</g>
				</a>
			{/if}
		</svg>
	</div>
{/if}

<style>
	/* wide families scroll inside their own container, never the page */
	.treewrap {
		overflow-x: auto;
		margin: var(--sp-3) 0 var(--sp-4);
	}
	.tree {
		display: block;
		max-width: none;
	}
	.edge {
		fill: none;
		stroke: #c9c9c9;
		stroke-width: 1;
	}
	.edge.trail {
		stroke: var(--c-dase);
		stroke-width: 2;
	}
	.node rect {
		fill: #fff;
		stroke: #bfbfbf;
		stroke-width: 1;
	}
	.node.faint rect {
		stroke-dasharray: 3 3;
	}
	.node.trail rect,
	.node.self rect {
		stroke: var(--c-dase);
		stroke-width: 1.6;
	}
	.node.self rect {
		fill: color-mix(in srgb, var(--c-dase) 10%, #fff);
	}
	.node .k {
		font-size: 9px;
		fill: var(--ink-faint);
		letter-spacing: 0.02em;
	}
	.node .t {
		font-size: 11px;
		fill: var(--ink);
	}
	.node .t.strong {
		font-weight: 700;
	}
	a:hover .node rect {
		stroke: var(--ink);
	}
	a {
		text-decoration: none;
	}
</style>
