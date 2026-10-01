#!/usr/bin/env python3
"""Bring Daniel's rights-cleared Dakar harvest into the archive: the final classification beyond the podium wherever a
licensed rally-year article carries it, and the entry lists the recent articles print.

    python tools/merge_dakar_harvest.py build/harvest/dakar_rights_cleared_final_harvest.json

Reads data/dakar.json and writes it back in the same shape. Every podium row stays as it is (the harvest's 534 podium
records agree with the archive to the row). Each edition gains:

  places     the classified finishers after third place, as rows of `placeFields` (class, place, lead name, crew, make,
             vehicle as printed, time, gap, competition number, team, sub-class) — positions 4–10 for 1985, 1990, 1995,
             2000, 2010 and 2015, and whatever the articles print for 2022–2026 (up to the whole classification). Rows of
             a sub-classification the article lists separately (Rally2, Original by Motul) keep their sub-class label;
             the 2024 Mission 1000 rows keep their own class label.
  entrants   the entry list rows the 2022, 2023 and 2025 articles print, as rows of `entrantFields` (class, competition
             number, the row as printed).

People named only beyond the podium join the register with new ids. Nothing is inferred: a missing time, gap or crew
stays missing; no non-finisher is carried, because no licensed source lists them.
"""
import argparse, collections, json, pathlib, re, sys, unicodedata
ROOT = pathlib.Path(__file__).resolve().parent.parent

def slug(s): return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('ascii').lower().replace('’', '').replace("'", '')).strip('-')
def fold(s): return re.sub(r'[^a-z0-9]+', ' ', unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode('ascii').lower()).strip()
JUNK = [re.compile(r'cite\d*†'), re.compile(r'[-]'), re.compile(r'Image†thumb\.wikimedia\.org\s*'), re.compile(r'\^\{\s*\[[a-z0-9]+\]\s*\}'), re.compile(r'\[[a-z0-9]+\]')]
def clean(s):
    s = str(s or '')
    for j in JUNK: s = j.sub('', s)
    return re.sub(r'\s+', ' ', s).strip(' †')
CAT_MAP = {'Classics': 'Classic', 'Classic': 'Classic', 'SSVs': 'SSV', 'SSV': 'SSV', 'SSV (T4)': 'SSV', 'Light Prototypes': 'Challenger', 'Challenger (T3)': 'Challenger', 'Challenger': 'Challenger', 'Cars': 'Cars', 'Bikes': 'Bikes', 'Trucks': 'Trucks', 'Quads': 'Quads', 'Stock': 'Stock',
           'Rally2 Bikes': ('Bikes', 'Rally2'), 'Original by Motul': ('Bikes', 'Original by Motul'), 'Mission 1000': ('Mission 1000', '')}
def cat_of(label):
    v = CAT_MAP.get(label, label)
    return v if isinstance(v, tuple) else (v, '')
MAKE_ALIAS = {'mercedes': 'Mercedes-Benz', 'mercedes benz': 'Mercedes-Benz', 'land rover': 'Land Rover', 'gas gas': 'GasGas', 'gasgas': 'GasGas', 'brp': 'Can-Am', 'brp can am': 'Can-Am', 'can am': 'Can-Am', 'range rover': 'Land Rover', 'range': 'Land Rover', 'md': 'MD Rallye', 'md rallye': 'MD Rallye', 'md optimus': 'MD Rallye', 'mm technology': 'MM Technology', 'mm': 'MM Technology', 'century': 'Century', 'kove': 'Kove', 'smg': 'SMG', 'red bull': 'Red Bull', 'bmw': 'BMW', 'ktm': 'KTM', 'man': 'MAN', 'liaz': 'LIAZ', 'maz': 'MAZ', 'daf': 'DAF', 'brx': 'BRX', 'ot3': 'OT3', 'ginaf': 'GINAF', 'acmat': 'ACMAT'}
def make_of(vehicle, marques):
    v = fold(vehicle)
    if not v: return ''
    for m in sorted(marques, key=lambda m: -len(m)):   # the archive's own marque names first, longest match
        if v == fold(m) or v.startswith(fold(m) + ' '): return m
    for k in sorted(MAKE_ALIAS, key=len, reverse=True):
        if v == k or v.startswith(k + ' '): return MAKE_ALIAS[k]
    return clean(vehicle).split(' ')[0]

ap = argparse.ArgumentParser(); ap.add_argument('harvest', nargs='?', default=str(ROOT/'build'/'harvest'/'dakar_rights_cleared_final_harvest.json')); args = ap.parse_args()
A = json.loads((ROOT/'data'/'dakar.json').read_text(encoding='utf-8')); H = json.loads(pathlib.Path(args.harvest).read_text(encoding='utf-8'))
RF = A['resultFields']; P = A['people']; by_name = {fold(v['name']): k for k, v in P.items()}; eds = {e['y']: e for e in A['editions']}
report = collections.Counter()
# the podium rows must agree before anything is added
atl = {(e['y'], x[0], x[1]): (fold(P[x[2]]['name']), x[4]) for e in A['editions'] for x in e['results']}
hp = {(p['year'], p['category'], p['rank']): (fold(p['driver']), p['make']) for p in H['podiumRecords']}
assert set(atl) == set(hp) and all(atl[k][0] == hp[k][0] for k in atl), 'the harvest’s podium records differ from the archive'
def pid(name):
    f = fold(name)
    if f in by_name: return by_name[f]
    i = slug(name) or 'x'; k = 2
    while i in P: i = f'{slug(name)}-{k}'; k += 1
    P[i] = {'id': i, 'name': name}; by_name[f] = i; report['people added'] += 1; return i
def names_of(r):
    if r.get('personNames'): return [clean(n) for n in r['personNames'] if clean(n)]
    lead = clean(r.get('participant') or r.get('driver') or r.get('rider') or r.get('entrant') or '')
    out = [lead] if lead else []
    for k in ('coDriver', 'technician'):
        n = clean(r.get(k) or '')
        if n and n not in out: out.append(n)
    return out
PF = ['cat', 'rank', 'driver', 'crew', 'make', 'vehicle', 'time', 'gap', 'no', 'team', 'sub']
places = collections.defaultdict(list); seen = set()
for r in H['records']:
    e = eds.get(r['year'])
    if not e or e['cancelled']: report['rows for an edition the archive lacks (skipped)'] += 1; continue
    names = names_of(r)
    if not names: report['rows with no name (skipped)'] += 1; continue
    cat, sub = cat_of(r['category'])
    key = (r['year'], cat, sub, r['rank'])
    if key in seen: report['duplicate rows (skipped)'] += 1; continue
    seen.add(key)
    if r['rank'] <= 3: report['podium-rank rows in the classification file (skipped)'] += 1; continue
    ids = [pid(n) for n in names]
    places[r['year']].append([cat, r['rank'], ids[0], ids, make_of(r.get('vehicle'), A['marques']), clean(r.get('vehicle') or ''), r.get('time') or r.get('result') or '', r.get('difference') or r.get('gap') or '', r.get('entryCompetitionNumber') or r.get('competitionNumber') or 0, clean(r.get('team') or r.get('entrant') or ''), sub])
    report['classified places added'] += 1
    if sub: report['sub-class rows'] += 1
    if cat not in [c['key'] for c in A['categories']]: report[f'rows in the extra class {cat}'] += 1
EF = ['cat', 'no', 'text']
entrants = collections.defaultdict(list)
for r in H['entrantRosters']:
    if r['year'] not in eds: continue
    cat, sub = cat_of(r['category'])
    entrants[r['year']].append([cat if not sub else f'{cat} · {sub}', r['competitionNumber'], clean(r['sourceRowText'])]); report['entry list rows added'] += 1
order = [c['key'] for c in A['categories']]
for e in A['editions']:
    e['places'] = sorted(places.get(e['y'], []), key=lambda x: (order.index(x[0]) if x[0] in order else 99, x[10], x[1]))
    e['entrants'] = sorted(entrants.get(e['y'], []), key=lambda x: (x[0], x[1]))
A['placeFields'] = PF; A['entrantFields'] = EF
A['classification'] = {'generated': H['generatedAt'], 'licence': H['license'], 'licenceUrl': H['licenseUrl'], 'attribution': H['attribution'], 'rightsPolicy': H['rightsPolicy'], 'scope': H['scope'], 'limitations': H['limitations'],
                       'sources': [{'url': s['url'], 'title': s['title'], 'used': s['used']} for s in H['sources'] if 'odium' not in s['used'][:12]], 'excluded': [{'source': a['source'], 'status': a['status'], 'finding': a.get('finding', '')} for a in H['resourceAudit'] if a['status'].lower().startswith('excluded')],
                       'years': sorted(places), 'rows': sum(len(v) for v in places.values()), 'entrantYears': sorted(entrants), 'entrants': sum(len(v) for v in entrants.values())}
c = A['coverage']; c['places'] = A['classification']['rows']; c['classified'] = c['podiums'] + c['places']; c['entrants'] = A['classification']['entrants']; c['people'] = len(P); c['classifiedYears'] = len(places)
A['method'] = A['method'].rstrip('.') + '. Beyond the podium, the final classification is carried wherever a rally-year article under the same licence prints it — positions 4–10 for 1985, 1990, 1995, 2000, 2010 and 2015, and what the 2022–2026 articles give, up to the whole classification — with the entry lists the 2022, 2023 and 2025 articles print. No non-finisher is carried: no licensed source lists them.'
out = ROOT/'data'/'dakar.json'; out.write_text(json.dumps(A, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
for k, v in sorted(report.items()): print(f'{v:>7,}  {k}')
print(f'editions with places {len(places)} · places {c["places"]:,} · podiums {c["podiums"]} · classified {c["classified"]:,} · entry rows {c["entrants"]:,} · people {c["people"]:,} · {out.stat().st_size/1e3:.0f} KB')
