/**
 * The story's sections — the author's own (2026-09-02): each id is a content
 * file the author named (`src/content/story/<id>.md`, their text distributed
 * from Website_Text_Storyboard.docx), each title the document's own heading.
 * The heading row above the narrative prints the title of the section the
 * reader is in; the ids are also the anchors.
 */
export interface Chapter {
	id: string;
	title: string;
}

export const CHAPTERS: Chapter[] = [
	{ id: 'introduction', title: 'INTRODUCTION' },
	{ id: 'chronology', title: 'CHRONOLOGY OF FIRES AND EVENTS' },
	// the timeline disclaimer is NOT a narrative section: it prints under
	// the timeline itself, left of the collapsed line (its .md stays the source)
	{ id: 'methodology', title: 'METHODOLOGY' },
	{ id: 'keyfindingandopenquestions', title: 'KEY FINDINGS AND OPEN QUESTIONS' },
	{ id: 'financedbyprivatecompanies', title: 'FINANCED BY PRIVATE COMPANIES' },
	{ id: 'antineroprogramme', title: 'ANTINERO PROGRAMME' },
	{ id: 'coops', title: 'WORKS EXECUTED BY FOREST WORKERS’ COOPERATIVES' },
	// the document spells it «Bibiography» — corrected here, flagged to the author
	{ id: 'bibliography', title: 'BIBLIOGRAPHY' }
];
