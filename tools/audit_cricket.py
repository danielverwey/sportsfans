"""Data audit for the cricket atlas: the core file and the detail shards against themselves and against a few well-known facts.
Writes audits/DATA-AUDIT-cricket.md. Nothing is changed."""
import json, collections, datetime, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
A = json.load(open(ROOT/'data'/'cricket.json', encoding='utf-8'))
DET = {int(f.stem): json.load(open(f, encoding='utf-8')) for f in sorted((ROOT/'data'/'cricket_details').glob('*.json'))}
G = A['games']; T = A['teams']; V = A['venues']; P = A['players']; C = A['champions']; PSF = A['psFields']; PS = [dict(zip(PSF, r)) for r in A['ps']]
iss = collections.defaultdict(list); n = lambda k, m: iss[k].append(m)
ids = [g['id'] for g in G]
if len(set(ids)) != len(ids): n('duplicate game id', '')
dates = [g['date'] for g in G]
if dates != sorted(dates): n('games not in date order', f'{sum(1 for a, b in zip(dates, dates[1:]) if b < a)} inversions')
for g in G:
    try: datetime.date.fromisoformat(g['date'])
    except Exception: n('bad date', g['id'])
    if g['y'] != int(g['date'][:4]): n('year ≠ date', g['id'])
    if g['f'] not in ('Test', 'ODI', 'T20I'): n('unknown format', g['id'])
    if g['g'] not in ('M', 'W'): n('unknown game', g['id'])
    if len(g['teams']) != 2 or g['teams'][0] == g['teams'][1]: n('sides malformed', g['id'])
    for t in g['teams']:
        if t not in T: n('side not in teams', f'{g["id"]} {t}')
    if g['result'] == 'win' and g['winner'] not in g['teams']: n('winner not playing', g['id'])
    if g['result'] != 'win' and g['winner']: n('winner on a non-win', g['id'])
    if g['result'] not in ('win', 'draw', 'tie', 'no result'): n('unknown result', g['id'])
    if g['f'] != 'Test' and g['result'] == 'draw': n('drawn limited-overs match', g['id'])
    if g.get('v') and g['v'] not in V: n('venue id unknown', g['id'])
    for i in g.get('sc', []):
        if i[0] not in g['teams']: n('innings side not playing', g['id'])
        if i[1] < 0 or i[2] < 0 or i[2] > 10: n('innings total out of range', g['id'])
    if g.get('detail'):
        d = DET.get(g['y'], {}).get(g['id'])
        if not d: n('detail flag without shard entry', g['id'])
        else:
            for inn in d['inn']:
                bat = sum(b[1] for b in inn[8]); ex = sum(inn[7]);
                if bat + ex != inn[1]: n('batting + extras ≠ total', f'{g["id"]} {inn[0]} {bat}+{ex}≠{inn[1]}')
                outs = sum(1 for b in inn[8] if b[5] not in ('not out', 'retired hurt', 'retired not out', 'did not bat', ''));
                if outs != inn[2] and not inn[6]: n('dismissals ≠ wickets', f'{g["id"]} {inn[0]} {outs}≠{inn[2]}')
                bw = sum(b[3] for b in inn[9]); fielded = sum(1 for b in inn[8] if b[5] in ('run out', 'retired hurt', 'retired not out', 'retired out', 'obstructing the field', 'handled the ball', 'timed out', 'hit the ball twice', 'not out', 'did not bat', ''))
                if bw > inn[2]: n('bowler wickets > innings wickets', f'{g["id"]} {inn[0]}')
for k, d in DET.items():
    for gid in d:
        g = next((x for x in G if x['id'] == gid), None) if len(d) < 50 else None
    if any(int(k) != k for k in [k]): pass
for c in C:
    if c['g'] not in ('M', 'W'): n('champion game unknown', c['id'])
    for w in c['w']:
        if w not in T: n('champion side unknown', f'{c["id"]} {w}')
seen = set()
for r in PS:
    if r['p'] not in P: n('player-season for unknown player', r['p'])
    if r['t'] not in T: n('player-season for unknown team', r['t'])
    if r['outs'] > r['inns']: n('outs > innings', f'{r["p"]} {r["y"]} {r["f"]}')
    if r['hs'] > r['runs']: n('highest score > runs', f'{r["p"]} {r["y"]} {r["f"]}')
    key = (r['y'], r['f'], r['g'], r['t'], r['p'])
    if key in seen: n('duplicate player-season', str(key))
    seen.add(key)
# well-known facts
def find(**kw): return [g for g in G if all(g.get(k) == v for k, v in kw.items())]
facts = []
first = min(G, key=lambda g: g['date']); facts.append(('First Test at Melbourne, 15 March 1877, Australia v England', first['date'] == '1877-03-15' and set(first['teams']) == {'Australia', 'England'}))
ties = [g for g in G if g['result'] == 'tie' and g['f'] == 'Test']; facts.append(('Exactly two tied Tests (Brisbane 1960, Madras 1986)', len(ties) == 2 and {g['y'] for g in ties} == {1960, 1986}))
odi1 = min((g for g in G if g['f'] == 'ODI'), key=lambda g: g['date']); facts.append(('First ODI 5 January 1971 at Melbourne', odi1['date'] == '1971-01-05'))
t201 = min((g for g in G if g['f'] == 'T20I' and g['g'] == 'M'), key=lambda g: g['date']); facts.append(('First men’s T20I 17 February 2005', t201['date'] == '2005-02-17'))
wc = {c['y']: c['w'] for c in C if c['kind'] == 'MWC'}; facts.append(('Men’s World Cup winners 1975–2023', wc.get(1975) == ['West Indies'] and wc.get(1983) == ['India'] and wc.get(1999) == ['Australia'] and wc.get(2011) == ['India'] and wc.get(2019) == ['England'] and wc.get(2023) == ['Australia']))
hi = max((i[1], g['y'], i[0]) for g in G for i in g.get('sc', []) if g['f'] == 'Test' and not i[6]); facts.append(('Highest recorded Test total 823/7d England at Multan, 2024 (innings totals exist only where a scorecard does, from 2001)', hi[0] == 823 and hi[1] == 2024 and hi[2] == 'England'))
lara = max((r['hs'] for r in PS if r['f'] == 'Test'), default=0); facts.append(('Highest recorded Test score 400* (Lara, 2004)', lara == 400))
sa_iso = [g for g in G if 'South Africa' in g['teams'] and 1971 <= g['y'] <= 1990]; facts.append(('South Africa played no internationals 1971–1990', len(sa_iso) == 0))
top = max(PS, key=lambda r: r['runs']); facts.append(('Best recorded single season-format batting is plausible (< 2,000 runs)', top['runs'] < 2000))
# report
cov = A['coverage']; scope = cov['scope']
lines = [f"# Data audit — cricket atlas", "", f"Archive results through {A['lastDate']}. Core file {len(G):,} internationals, {len(P):,} players, {len(V)} venues ({sum(1 for v in V.values() if v.get('locationOnly'))} recorded as a city only), {len(T)} sides, {len(C)} ICC titles, {len(PS):,} player-season rows; {sum(len(d) for d in DET.values()):,} scorecards in {len(DET)} yearly shards. Nothing was changed.", "", "## Coverage", "", "| Game | Format | Matches | With scorecard | From | To | Scorecards from |", "|---|---|---|---|---|---|---|"]
for s in scope: lines.append(f"| {'Men' if s['g'] == 'M' else 'Women'} | {s['f']} | {s['n']:,} | {s['detail']:,} | {s['start']} | {s['end']} | {s['detailStart']} |")
lines += ["", "## Consistency checks", "", "| Check | Result |", "|---|---|"]
checks = ['duplicate game id', 'games not in date order', 'bad date', 'year ≠ date', 'unknown format', 'unknown game', 'sides malformed', 'side not in teams', 'winner not playing', 'winner on a non-win', 'unknown result', 'drawn limited-overs match', 'venue id unknown', 'innings side not playing', 'innings total out of range', 'detail flag without shard entry', 'batting + extras ≠ total', 'dismissals ≠ wickets', 'bowler wickets > innings wickets', 'champion game unknown', 'champion side unknown', 'player-season for unknown player', 'player-season for unknown team', 'outs > innings', 'highest score > runs', 'duplicate player-season']
for c in checks:
    v = iss.get(c, []); lines.append(f"| {c} | {'✅ none' if not v else '⚠️ ' + str(len(v)) + ' — e.g. ' + ', '.join(str(x) for x in v[:3])} |")
lines += ["", "## Well-known facts", "", "| Fact | In the archive |", "|---|---|"] + [f"| {f} | {'✅' if ok else '❌'} |" for f, ok in facts]
lines += ["", "## Source reconciliation", "", f"{cov['joined']:,} matches matched between the historical results list and Cricsheet; {cov['added']:,} added from Cricsheet alone; {cov['historicOnly']:,} historical only. {len(cov['conflicts'])} match-number conflicts, resolved to the Cricsheet number: " + '; '.join(f"{c['key'][0]} {c['key'][1]} {c['date']} (historic #{c['historic']}, Cricsheet #{c['cricsheet']})" for c in cov['conflicts']) + ".", "", "Dismissal kinds across all scorecards: " + ', '.join(f"{k} {v:,}" for k, v in sorted(cov['dismissals'].items(), key=lambda x: -x[1])) + ".", ""]
(ROOT/'audits'/'DATA-AUDIT-cricket.md').write_text('\n'.join(lines), encoding='utf-8')
print('\n'.join(lines[:8])); print(); print('\n'.join(l for l in lines if l.startswith('| ') and ('⚠️' in l or '❌' in l)) or 'all checks clean')
