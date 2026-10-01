#!/usr/bin/env python3
"""Bring Daniel's rights-cleared Isle of Man TT harvest into the archive.

    python tools/merge_tt_harvest.py build/harvest/iom_tt_rights_cleared_harvest.json

Reads data/tt.json and writes it back in the same shape. The harvest and the archive were both transcribed from the same
licensed pages (the German list of TT winners, the English 2024–2026 race articles), so the archive's winners and
classifications are checked against it row by row before anything is added. What is genuinely new:

  no                 a ninth result field: the competition number each 2024–2026 classification table prints for the
                     finisher (0 where no licensed table gives one). Nothing else in a result row changes.
  note               on the one race whose article contradicts itself (2026 Supersport Race 1: the narrative says
                     cancelled, the article still prints a classification), the harvest's reading, kept as disputed.
  meetingsNotHeld    the years without a TT meeting as a list of their own (the wars, foot-and-mouth, the pandemic),
                     distinct from the race-level cancellations the archive already holds.
  harvest            the harvest's provenance: its sources with their roles and reuse status (including the official
                     results archive it inspected and excluded), its rights policy and methodology, and every winner it
                     reads differently from the archive — kept as discrepancies, never applied. The archive's own
                     reading of the winner stands.

Nothing is inferred: a finisher without a published number keeps 0; a race status the archive already carries is not
duplicated; a differing winner is listed, not changed.
"""
import argparse, collections, json, pathlib, re, unicodedata
ROOT = pathlib.Path(__file__).resolve().parent.parent

def fold(s):
    s = str(s or '').replace('ß', 'ss')
    return re.sub(r'[^a-z0-9]+', ' ', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii').lower()).strip()
COUNTRY = re.compile(r'^(?:(?:Vereinigtes K[oö]nigreich(?: 1801)?|Deutschland(?: Bundesrepublik)?|Deutsches Reich|Irland|Nordirland|Schweiz|[OÖ]sterreich|Italien|Neuseeland|Australien|Kanada|Vereinigte Staaten|Frankreich|Niederlande|Belgien|Schweden|Finnland|Spanien|Isle of Man|Japan|Rhodesien|S[uü]dafrika|Tschechoslowakei|Jersey|Guernsey|Schottland|England|Wales|Ungarn|Norwegen|D[aä]nemark)\s+)+')
# the harvest's spelling → the archive's, where the surname alone would not meet (typos, umlaut transcriptions, suffixes)
SURNAME_ALIAS = {'houseley': 'housley', 'horner': 'hoerner', 'wohlegemuth': 'wohlgemuth', 'ito': 'itoh'}
NICK = {'percy': 'tim', 'josef': 'sepp'}   # Percy “Tim” Hunt, Josef “Sepp” Huber: the archive carries the name the TT knew them by
def person(n):
    """(surname, set of given-name initials) — enough to tell Joey Dunlop from Robert Dunlop and M.Grünwald from Manfred Grünwald."""
    toks = [t for t in fold(n).split(' ') if t and t not in ('sr', 'jr', 'snr', 'jnr')]
    if not toks: return ('', set())
    sur = SURNAME_ALIAS.get(toks[-1], toks[-1]); given = [NICK.get(t, t) for t in toks[:-1]]
    return (sur, {g[0] for g in given})
def same(a, b):
    (sa, ia), (sb, ib) = person(a), person(b)
    return bool(sa) and sa == sb and (not ia or not ib or ia & ib)
GERMAN = [('Gespanne Rennen', 'Sidecar Race'), ('Gespanne', 'Sidecar'), ('Rennen', 'Race'), ('Formel I', 'Formula I'), ('cm³', 'cc')]
def english(cat):
    for g, e in GERMAN: cat = cat.replace(g, e)
    return cat

ap = argparse.ArgumentParser(); ap.add_argument('harvest', nargs='?', default=str(ROOT/'build'/'harvest'/'iom_tt_rights_cleared_harvest.json')); args = ap.parse_args()
A = json.loads((ROOT/'data'/'tt.json').read_text(encoding='utf-8')); H = json.loads(pathlib.Path(args.harvest).read_text(encoding='utf-8'))
RF = A['resultFields']; R = A['riders']; name = lambda i: R.get(i, {}).get('name', i)
report = collections.Counter()
by_year = collections.defaultdict(list)
for r in A['races']: by_year[r['y']].append(r)
POS, CREW = RF.index('pos'), RF.index('crew')

# 1. winners: every annual winner the harvest reads must be a winner of that year in the archive (surname and a given-name initial)
winners_of = {y: [name(i) for r in rs for x in r['results'] if x[POS] == 1 for i in x[CREW]] for y, rs in by_year.items()}
discrepancies = []
for w in H['annualWinners']:
    names = [COUNTRY.sub('', n).strip() for n in re.split(r'\s*/\s*', w['riderOrCrew']) if n.strip()]
    have = winners_of.get(w['year'], [])
    missing = [n for n in names if fold(n) and not any(same(n, h) for h in have)]
    report['annual winners checked'] += 1
    if not missing: continue
    cat = fold(english(w['category']))
    race = next((r for r in by_year.get(w['year'], []) if fold(r['name']) == cat), None) or next((r for r in by_year.get(w['year'], []) if cat in fold(r['name']) or fold(r['name']) in cat), None)
    discrepancies.append({'year': w['year'], 'category': w['category'], 'harvest': names, 'machine': w['machine'], 'race': race['id'] if race else None,
                          'archive': [name(i) for x in race['results'] if x[POS] == 1 for i in x[CREW]] if race else [], 'source': 'dewiki-winners', 'line': w['sourceLine']})
    report['winners read differently (kept as discrepancies)'] += 1
corr = {c['race']: c['note'] for c in A.get('corrections', [])}
for d in discrepancies:
    if d['race'] in corr: d['reconciled'] = corr[d['race']]; report['of them already reconciled in the archive’s corrections'] += 1
assert len(discrepancies) <= 12, f'{len(discrepancies)} winner discrepancies — the harvest is not the archive’s list'

# 2. race statuses: every cancellation the harvest records must already be in the archive's list
canc = {(c['year'], fold(c['class'])) for c in A['cancelled']}
for s in H['raceStatusRecords']:
    assert (s['year'], fold(english(s['category']))) in canc, f'race status not in the archive: {s}'
    report['race statuses confirmed'] += 1

# 3. the 2024–2026 classifications: every harvest row must sit at the same position in the archive; the number is new
def race_for(year, label):
    toks = set(fold(label).split(' '))
    cands = [r for r in by_year.get(year, []) if set(fold(r['name']).split(' ')) <= toks]
    if len(cands) > 1: cands = [r for r in cands if len(fold(r['name'])) == max(len(fold(c['name'])) for c in cands)]
    assert len(cands) == 1, f'no single race for {year} {label!r}: {[c["name"] for c in cands]}'
    return cands[0]
if 'no' not in RF:
    RF.append('no')
    for r in A['races']:
        for x in r['results']: x.append(0)
NO = RF.index('no')
numbered = set(); notes = {}
for d in H['detailedResults']:
    r = race_for(d['year'], d['race'])
    row = next((x for x in r['results'] if x[POS] == d['position']), None)
    assert row is not None, f'position {d["position"]} of {r["id"]} is not in the archive'
    hs = [n for n in re.split(r'\s*/\s*', d['riders']) if n.strip()]
    assert any(same(h, name(i)) for h in hs for i in row[CREW]), f'{r["id"]} P{d["position"]}: harvest {d["riders"]!r} vs archive {[name(i) for i in row[CREW]]}'
    if d.get('number'):
        if row[NO] and row[NO] != d['number']: report['numbers that changed'] += 1
        row[NO] = int(d['number']); numbered.add(r['id']); report['competition numbers set'] += 1
    report['classified rows confirmed'] += 1
    if d.get('classificationNote'): notes[r['id']] = d['classificationNote']
for r in A['races']:
    if r['id'] in notes: r['note'] = notes[r['id']]; report['races carrying a disputed-classification note'] += 1

# 4. the years without a meeting, as a list of their own (the archive's cancellation list keeps 2001 at race level)
mnh = [{'years': e['years'], 'reason': e['reason'], 'source': 'enwiki-history'} for e in H['eventCancellations']]
fmd = next((c for c in A['cancelled'] if c['year'] == 2001), None)
if fmd and not any(2001 in m['years'] for m in mnh): mnh.append({'years': [2001], 'reason': 'Foot-and-mouth disease', 'source': 'dewiki-winners'})
A['meetingsNotHeld'] = sorted(mnh, key=lambda m: m['years'][0])

# 5. provenance
A['harvest'] = {'title': H['title'], 'harvestedAt': H['harvestedAt'], 'rightsPolicy': H['rightsPolicy'], 'attribution': H['attributionAndShareAlike'], 'methodology': H['methodology'],
                'sources': [{'id': s['id'], 'title': s['title'], 'url': s['url'], 'licence': s['license'], 'role': s['role'], 'coverage': s.get('coverage', ''), 'status': s['reuseStatus']} for s in H['sources']],
                'excluded': [s['id'] for s in H['sources'] if not s['reuseStatus'].startswith('Reusable')],
                'gaps': H['coverage']['remainingGaps'], 'discrepancies': discrepancies,
                'numbers': {'rows': report['competition numbers set'], 'races': len(numbered), 'years': sorted({int(y) for y in H['coverage']['detailedResultsByYear']})}}
c = A['coverage']; c['numbers'] = report['competition numbers set']; c['numberedRaces'] = len(numbered); c['harvestDiscrepancies'] = len(discrepancies); c['meetingsNotHeld'] = sum(len(m['years']) for m in A['meetingsNotHeld'])
tail = ' Competition numbers are carried where a licensed 2024–2026 classification table prints them; a second, independent transcription of the same pages was checked against every winner and every recent classification, and the handful of winners it reads differently are listed in the data file, not applied.'
if 'Competition numbers are carried' not in A['method']: A['method'] = A['method'].rstrip('.') + '.' + tail
out = ROOT/'data'/'tt.json'; out.write_text(json.dumps(A, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
for k, v in sorted(report.items()): print(f'{v:>7,}  {k}')
for d in discrepancies: print(f'   {d["year"]} {d["category"]}: harvest {" / ".join(d["harvest"])} ({d["machine"]}) · archive {" / ".join(d["archive"]) or "no such race"}')
print(f'races {len(A["races"])} · results {sum(len(r["results"]) for r in A["races"]):,} · numbered rows {c["numbers"]} in {c["numberedRaces"]} races · meetings not held {c["meetingsNotHeld"]} years · {out.stat().st_size/1e3:.0f} KB')
