"""Import the story timeline's events from the author's own Timeline.xlsx.

Writes `atlas/src/lib/story/events.ts` — the 31 events the story's left column
draws — so nothing is ever retyped and a re-import reproduces the file exactly.
Run it after the author edits the workbook:

    .venv/Scripts/python.exe scripts/import_story_timeline.py

Two mechanical folds happen on the way in, both documented in the emitted
module's header: the CATEGORY column is written four ways across the rows and is
folded onto the three lanes Sheet2 names (an unknown spelling STOPS the import
rather than inventing a lane), and `id` is a short stable slug of the title —
the anchor a timeline bullet and its narrative passage are bound by.

What the sheet does NOT carry is that binding: which passage mentions each
event. `StoryEvent.beat` is therefore left unset here and filled in by hand as
the narrative is placed.
"""
import sys, io, os, pathlib, zipfile, re, datetime as dt, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from xml.etree import ElementTree as ET

M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
ROOT = pathlib.Path(__file__).resolve().parent.parent
BOOK = pathlib.Path(
    os.environ.get("STORY_TIMELINE_XLSX", ROOT.parent.parent / "INVESTIGATIVE-REPORT" / "Timeline.xlsx")
)
OUT = ROOT / "atlas" / "src" / "lib" / "story" / "events.ts"
if not BOOK.exists():
    sys.exit("workbook not found: %s (set STORY_TIMELINE_XLSX to point at it)" % BOOK)
z = zipfile.ZipFile(BOOK)
shared = [''.join(t.text or '' for t in si.iter(f'{{{M}}}t'))
          for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(f'{{{M}}}si')]

sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
rows = []
for row in sheet.iter(f'{{{M}}}row'):
    cells = {}
    for c in row.findall(f'{{{M}}}c'):
        col = re.match(r'([A-Z]+)', c.get('r')).group(1)
        v = c.find(f'{{{M}}}v')
        if v is None:
            continue
        cells[col] = shared[int(v.text)] if c.get('t') == 's' else v.text
    if cells.get('B') and cells.get('D') and re.fullmatch(r'[0-9.]+', cells['B']):
        rows.append(cells)

EPOCH = dt.date(1899, 12, 30)
def iso(serial):
    return (EPOCH + dt.timedelta(days=int(float(serial)))).isoformat()

# the author writes the category four ways; Sheet2 lists the three canonical ones
LANE = {
    'fires in greece': 'fire',
    'events & legislation changes in greece': 'greece',
    'events & legislative changes in greece': 'greece',
    'global events& eu legislation changes': 'world',
    'global events & eu legislation changes': 'world',
    'global events & eu legislative changes': 'world',
}

def slug(t):
    t = unicodedata.normalize('NFD', t)
    t = ''.join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r'\(.*?\)', ' ', t)
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')
    STOP = {'the','of','a','an','and','in','for','to','with','on','its','by'}
    words = [w for w in t.split('-') if w][:5]
    while words and words[-1] in STOP:
        words.pop()
    return '-'.join(words)

def q(s):
    """a TS single-quoted literal"""
    s = s.replace('\\', '\\\\').replace("'", "\\'")
    return "'" + re.sub(r'\s+', ' ', s).strip() + "'"

out, seen = [], {}
for c in rows:
    lane = LANE.get((c['A'] or '').strip().lower())
    if not lane:
        sys.exit('unknown category: %r' % c['A'])
    start, end = iso(c['B']), iso(c.get('C', c['B']))
    title = re.sub(r'\s+', ' ', c['D']).strip().rstrip('.')
    body = re.sub(r'\s+', ' ', c.get('E', '') or '').strip()
    base = slug(title)
    n = seen.get(base, 0)
    seen[base] = n + 1
    out.append({
        'id': base if not n else '%s-%d' % (base, n + 1),
        'lane': lane,
        'date': start,
        'end': end if end != start else None,
        'title': title,
        'body': body,
    })
out.sort(key=lambda e: (e['date'], ['world', 'greece', 'fire'].index(e['lane'])))

lines = []
for e in out:
    lines.append('	{')
    lines.append('		id: %s,' % q(e['id']))
    lines.append("		lane: '%s'," % e['lane'])
    lines.append("		date: '%s'," % e['date'])
    if e['end']:
        lines.append("		end: '%s'," % e['end'])
    lines.append('		title: %s%s' % (q(e['title']), ',' if e['body'] else ''))
    if e['body']:
        lines.append('		body: %s' % q(e['body']))
    lines.append('	},')
rows = chr(10).join(lines)

# the prose around the data is the module's OWN — kept, never regenerated, so a
# re-import cannot silently drop the notes that explain the folds above
MARK_A = 'export const EVENTS: StoryEvent[] = [' + chr(10)
MARK_B = chr(10) + '];'
prev = OUT.read_text(encoding='utf-8')
a = prev.index(MARK_A) + len(MARK_A)
b = prev.index(MARK_B, a)
# newline='' so the module keeps LF endings on Windows too
with open(OUT, 'w', encoding='utf-8', newline='') as fh:
    fh.write(prev[:a] + rows + prev[b:])
print('%d events -> %s' % (len(out), OUT.relative_to(ROOT)))
