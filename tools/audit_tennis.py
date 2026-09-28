"""Data audit for the tennis atlas: the core file and the yearly match shards against themselves and against well-known facts.
Writes audits/DATA-AUDIT-tennis.md. Nothing is changed."""
import json, collections, datetime, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
A = json.load(open(ROOT/'data'/'tennis.json', encoding='utf-8'))
SH = {int(f.stem): json.load(open(f, encoding='utf-8')) for f in sorted((ROOT/'data'/'tennis_matches').glob('*.json'))}
P = A['players']; T = {k: dict(zip(A['tFields'], r)) for k, r in A['tournaments'].items()}; E = {k: dict(zip(A['eFields'], r)) for k, r in A['editions'].items()}
C = [dict(zip(A['cFields'], r)) for r in A['champions']]; PS = [dict(zip(A['psFields'], r)) for r in A['ps']]
MF = ['id', 'w', 'l', 's', 'r', 'n', 'mins', 'bo', 'ws', 'ls', 'wr', 'lr', 'st', 'src']
iss = collections.defaultdict(list); n = lambda k, m: iss[k].append(m)
MAJ = {k for k, t in T.items() if t.get('major')}
for eid, e in E.items():
    if e['t'] not in T: n('edition with unknown tournament', eid)
    try: datetime.date.fromisoformat(e['date'])
    except Exception: n('bad edition date', eid)
    if e['y'] != int(e['date'][:4]) and not (e['y'] == int(e['date'][:4]) + 1 and e['date'][5:7] == '12'): n('edition year ≠ date (December start of the next season accepted)', eid)
    if e['c'] not in ('MS', 'WS', 'MD', 'WD'): n('unknown circuit', eid)
    if e['surface'] not in ('Hard', 'Clay', 'Grass', 'Carpet', 'Unknown'): n('unknown surface', f'{eid} {e["surface"]}')
seen = set(); by_e = collections.Counter(); nmatch = 0; badscore = 0
for y, eds in SH.items():
    for eid, rows in eds.items():
        e = E.get(eid)
        if not e: n('shard edition unknown', eid); continue
        if e['y'] != y: n('shard year ≠ edition year', eid)
        by_e[eid] += len(rows)
        for r in rows:
            m = dict(zip(MF, r)); nmatch += 1
            if m['id'] in seen: n('duplicate match id', m['id'])
            seen.add(m['id'])
            if not m['w'] or not m['l']: n('match without both sides', m['id'])
            for p in m['w'] + m['l']:
                if p not in P: n('match player unknown', f'{m["id"]} {p}')
            if set(m['w']) & set(m['l']): n('player on both sides', m['id'])
            if len(m['w']) != len(m['l']): n('unequal sides', m['id'])
            if e['c'][1] == 'S' and (len(m['w']) != 1 or len(m['l']) != 1): n('doubles pairing in a singles draw', m['id'])
            s = m['s'] or ''
            if s and not re.fullmatch(r'([0-9]+-[0-9]+(\([0-9]+\))?\s*|RET|W/O|DEF|Walkover|UNK|ABN|\[[0-9]+-[0-9]+\]\s*|In Progress|NA)+', s.strip()): badscore += 1
            if m['mins'] is not None and (m['mins'] < 10 or m['mins'] > 700): n('implausible duration', f'{m["id"]} {m["mins"]}')
            if m['wr'] is not None and m['wr'] < 1: n('bad rank', m['id'])
for eid, e in E.items():
    if e['n'] != by_e.get(eid, 0): n('edition match count ≠ shard', f'{eid} {e["n"]}≠{by_e.get(eid, 0)}')
for c in C:
    if c['t'] not in T: n('title with unknown tournament', c['id'])
    for p in c['w'] + c['l']:
        if p not in P: n('title player unknown', f'{c["id"]} {p}')
    if c['m'] and c['m'] not in seen: n('title final match missing from shards', c['id'])
    if c['id'] in E and E[c['id']]['y'] != c['y']: n('title year ≠ edition year', c['id'])
cnt = collections.Counter(c['id'] for c in C)
for k, v in cnt.items():
    if v > 1: n('duplicate title id', k)
for r in PS:
    if r['p'] not in P: n('player-season for unknown player', r['p'])
    if r['w'] != r['hw'] + r['cw'] + r['gw'] + r['iw'] or r['l'] != r['hl'] + r['cl'] + r['gl'] + r['il']: n('surface split ≠ total', f'{r["p"]} {r["y"]} {r["c"]}')
    if r['t'] > r['f']: n('titles > finals', f'{r["p"]} {r["y"]} {r["c"]}')
# well-known facts
byname = collections.defaultdict(list)
for pid, p in P.items(): byname[p['n']].append(pid)
def majors(name, circ=('MS', 'WS')):
    ids = set(byname.get(name, [])); return sum(1 for c in C if c['t'] in MAJ and c['c'] in circ and any(p in ids for p in c['w']))
def titles(name, circ=('MS', 'WS')):
    ids = set(byname.get(name, [])); return sum(1 for c in C if c['c'] in circ and any(p in ids for p in c['w']))
def h2h(a, b):
    ia, ib = set(byname.get(a, [])), set(byname.get(b, [])); wa = wb = 0
    for eds in SH.values():
        for eid, rows in eds.items():
            if E[eid]['c'] not in ('MS', 'WS'): continue
            for r in rows:
                m = dict(zip(MF, r))
                if m['w'][0] in ia and m['l'][0] in ib: wa += 1
                elif m['w'][0] in ib and m['l'][0] in ia: wb += 1
    return wa, wb
facts = []
facts.append(('Wimbledon’s roll of honour begins in 1877 (Spencer Gore)', min(c['y'] for c in C if c['t'] == 'WI') == 1877 and any(P.get(p, {}).get('n', '').endswith('Gore') for c in C if c['t'] == 'WI' and c['y'] == 1877 for p in c['w'])))
facts.append(('Djokovic 24 majors, Nadal 22, Federer 20 (singles)', majors('Novak Djokovic') == 24 and majors('Rafael Nadal') == 22 and majors('Roger Federer') == 20))
facts.append(('Serena Williams 23 singles majors, Steffi Graf 22; Margaret Court’s three Wimbledons (1963, 1965, 1970)', majors('Serena Williams') == 23 and majors('Steffi Graf') == 22 and sorted(c['y'] for c in C if c['t'] == 'WI' and c['c'] == 'WS' and any(P[p]['n'] == 'Margaret Court' for p in c['w'])) == [1963, 1965, 1970]))
facts.append(('Laver’s Grand Slam of 1969: all four majors', sum(1 for c in C if c['y'] == 1969 and c['t'] in MAJ and c['c'] == 'MS' and any(P[p]['n'] == 'Rod Laver' for p in c['w'])) == 4))
facts.append(('Graf’s Golden Slam of 1988: four majors and the Olympic title', sum(1 for c in C if c['y'] == 1988 and c['c'] == 'WS' and any(P[p]['n'] == 'Steffi Graf' for p in c['w']) and (c['t'] in MAJ or E.get(c['id'], {}).get('level') == 'O')) == 5))
wa, wb = h2h('Novak Djokovic', 'Rafael Nadal'); facts.append(('Djokovic–Nadal head to head 31–29', (wa, wb) == (31, 29)))
longest = max((dict(zip(MF, r))['mins'] or 0, dict(zip(MF, r))['id']) for eds in SH.values() for rows in eds.values() for r in rows if (dict(zip(MF, r))['mins'] or 0) < 700); facts.append(('Longest match Isner–Mahut, Wimbledon 2010, 665 minutes (five source durations above 700 minutes are treated as errors and kept out of the records)', longest[0] == 665 and longest[1].startswith('MS:2010-540')))
facts.append(('Nadal 14 Roland-Garros titles', sum(1 for c in C if c['t'] == 'RG' and c['c'] == 'MS' and any(P[p]['n'] == 'Rafael Nadal' for p in c['w'])) == 14))
facts.append(('Federer 103 singles titles, Connors more than a hundred', titles('Roger Federer') == 103 and titles('Jimmy Connors') >= 100))
facts.append(('First open tournament in 1968; no match records before', min(SH) == 1968))
cov = A['coverage']
lines = ['# Data audit — tennis atlas', '', f"Archive: {len(C):,} titles ({min(c['y'] for c in C)}–{max(c['y'] for c in C)}), {nmatch:,} matches in {len(SH)} yearly shards ({min(SH)}–{max(SH)}), {len(P):,} players, {len(T):,} tournaments, {len(E):,} editions, {len(PS):,} player-season rows. Source: Jeff Sackmann’s tennis_atp and tennis_wta (CC BY-NC-SA 4.0), commit {A.get('sourceCommit', '')[:10]}; Wimbledon’s own Compendium for champions before 1968 (the other majors’ rolls begin with the Open era in this archive). Nothing was changed.", '', '## Coverage', '', '| Circuit | Matches | With statistics | Match years | Titles | Title years |', '|---|---|---|---|---|---|']
for s in cov['scope']: lines.append(f"| {s['c']} | {s['matches']:,} | {s['stats']:,} | {s['start'] or '—'}–{s['end'] or '—'} | {s['titles']:,} | {s['titleStart']}–{s['titleEnd']} |")
lines += ['', f"Scores that do not parse as sets: {badscore:,} of {nmatch:,} (retirements, walkovers and unknowns are accepted as written).", '', '## Consistency checks', '', '| Check | Result |', '|---|---|']
checks = ['edition with unknown tournament', 'bad edition date', 'edition year ≠ date (December start of the next season accepted)', 'unknown circuit', 'unknown surface', 'shard edition unknown', 'shard year ≠ edition year', 'duplicate match id', 'match without both sides', 'match player unknown', 'player on both sides', 'unequal sides', 'doubles pairing in a singles draw', 'implausible duration', 'bad rank', 'edition match count ≠ shard', 'title with unknown tournament', 'title player unknown', 'title final match missing from shards', 'title year ≠ edition year', 'duplicate title id', 'player-season for unknown player', 'surface split ≠ total', 'titles > finals']
for c in checks:
    v = iss.get(c, []); lines.append(f"| {c} | {'✅ none' if not v else '⚠️ ' + str(len(v)) + ' — e.g. ' + ', '.join(str(x) for x in v[:3])} |")
lines += ['', '## Well-known facts', '', '| Fact | In the archive |', '|---|---|'] + [f"| {f} | {'✅' if ok else '❌'} |" for f, ok in facts]
lines += ['', '## Source notes', '', 'Exclusions and quirks carried from the source: ' + ', '.join(f'{k.replace("_", " ")} {v}' for k, v in cov.get('notes', {}).items()) + '.', '']
(ROOT/'audits'/'DATA-AUDIT-tennis.md').write_text('\n'.join(lines), encoding='utf-8')
print('\n'.join(lines[:4])); print('\n'.join(l for l in lines if l.startswith('| ') and ('⚠️' in l or '❌' in l)) or 'all checks clean')
