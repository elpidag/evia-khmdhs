/**
 * What the ΓΕΜΗ (Greek business register) says about a company today.
 *
 * A κοινοπραξία is formed for one job and wound up when it ends — the joint
 * venture that signed 23SYMV013201917 is now struck off. It stays the
 * contractor, because it is who signed; the page just has to say what became
 * of it and link the register (user, 2026-08-20).
 *
 * NO DATE is printed. The publicity API returns `dateGemiRegistered`, which
 * on active companies is plainly the registration date (one reads 1992,
 * before the company's own start date) — it cannot be presented as the date
 * the status changed. The register's own «Ιστορικό Κατάστασης» table carries
 * the dates, and that is what the link goes to.
 *
 * The register's Greek term is always kept — it is the fact — with an
 * English gloss where we have a reviewed one. An unknown status is printed
 * in Greek alone rather than guessed at.
 */
const STATUS_EN: Record<string, string> = {
	Διαγραφή: 'struck off the register',
	'Λύση - Εκκαθάριση': 'dissolved and in liquidation',
	'Λύση-Εκκαθάριση': 'dissolved and in liquidation',
	Αναστολή: 'suspended',
	Αδρανής: 'dormant'
};

export interface RegistryStatus {
	status: string;
	gemi?: string | null;
}

/** The sentence shown on hover beside a contractor the register no longer
 *  lists as active. */
export function registryStatusNote(st: RegistryStatus): string {
	const en = STATUS_EN[st.status.trim()];
	const what = en ? `${en} (${st.status})` : st.status;
	return (
		`ΓΕΜΗ records this company as ${what}. It stays the contractor of this ` +
		'contract — it is the company that signed. The register page carries the ' +
		'dates of its status history.'
	);
}
