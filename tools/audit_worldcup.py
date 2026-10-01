"""Data audit for the World Cup atlas: data/worldcup.json against itself (every match in its tournament, every goal to a
player, every table to its matches, the winner the final's winner) and against a few well-known facts. Writes
audits/DATA-AUDIT-worldcup.md. Nothing is changed.

  python3 tools/audit_worldcup.py
"""
import json, collections, datetime, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'tools')); from worldcup_common import STAGE_ORDER, points_rule
A = json.load(open(ROOT/'data'/'worldcup.json', encoding='utf-8'))
MF = A['matchFields']; M = [dict(zip(MF, r)) for r in A['matches']]; D = A['details']; P = A['players']; T = {t['id']: t for t in A['tournaments']}
iss = collections.defaultdict(list); n = lambda k, m: iss[k].append(m)
# tournaments
ids = [t['id'] for t in A['tournaments']]
if len(set(ids)) != len(ids): n('duplicate tournament id', '')
for sex in ('M', 'W'):
    ys = [t['y'] for t in A['tournaments'] if t['sex'] == sex]
    if ys != sorted(ys): n('tournaments not in year order', sex)
by_t = collections.defaultdict(list)
for m in M: by_t[m['t']].append(m)
for t in A['tournaments']:
    rows = by_t[t['id']]
    if not rows: n('tournament without matches', t['id']); continue
    if t['matches'] != len(rows): n('match count differs from the tournament', f'{t["id"]} {t["matches"]} ≠ {len(rows)}')
    if not t['hosts']: n('tournament without a host', t['id'])
    if not t['point'] or not (-180 <= t['point'][1] <= 180 and -90 <= t['point'][2] <= 90): n('tournament without a map point', t['id'])
    if t['points'] != points_rule(t['sex'], t['y']): n('points rule differs from the convention', t['id'])
    teams = {m['home'] for m in rows} | {m['away'] for m in rows}
    if set(t['teams']) != teams: n('tournament teams differ from its matches', t['id'])
    if t['count'] != len(teams): n('team count differs', f'{t["id"]} {t["count"]} ≠ {len(teams)}')
    for tm in teams:
        if tm not in A['teams']: n('team not in the register', f'{t["id"]} {tm}')
    if 'final' in t['stages']:
        f = next((m for m in rows if m['id'] == t['final']), None)
        if not f or f['stage'] != 'final': n('final not found or not a final', t['id'])
        elif t['winner']:
            w = f['home'] if f['winner'] == 'h' else f['away'] if f['winner'] == 'a' else None
            if f['replay'] == 'replayed': w = None   # a drawn final that was replayed decides nothing by itself
            if w and w != t['winner']: n('the winner is not the final’s winner', f'{t["id"]} {t["winner"]} vs {w}')
    elif t['id'] == 'M1950' and t['winner'] != 'Uruguay': n('1950 winner', t['winner'])
    if t['standings'][0] != t['winner']: n('first in the standings is not the winner', t['id'])
    if t['y'] < max(x['y'] for x in A['tournaments'] if x['sex'] == t['sex']) and not t['winner']: n('completed tournament without a winner', t['id'])
    # group tables against the matches
    for g in t['groups']:
        gm = [m for m in rows if m['stage'] == g['stage'] and (m['group'] == g['name'] or (g['stage'] == 'final-round'))]
        for row in g['table']:
            team, Pl, W, Dr, L, GF, GA, Pts = row[:8]
            mine = [m for m in gm if team in (m['home'], m['away'])]
            if len(mine) != Pl: n('group table played ≠ matches', f'{t["id"]} {g["name"]} {team} {Pl} vs {len(mine)}'); continue
            w = d = l = gf = ga = 0
            for m in mine:
                hs, as_ = (m['hs'], m['as']) if m['home'] == team else (m['as'], m['hs'])
                gf += hs; ga += as_; w += hs > as_; d += hs == as_; l += hs < as_
            if (w, d, l, gf, ga) != (W, Dr, L, GF, GA): n('group table figures ≠ matches', f'{t["id"]} {g["name"]} {team}')
            if Pts != w * t['points'] + d: n('group points ≠ wins and draws', f'{t["id"]} {g["name"]} {team} {Pts}')
# matches
mids = [m['id'] for m in M]
if len(set(mids)) != len(mids): n('duplicate match id', len(mids) - len(set(mids)))
for m in M:
    if m['t'] not in T: n('match of an unknown tournament', m['id']); continue
    if m['y'] != T[m['t']]['y'] or m['sex'] != T[m['t']]['sex']: n('match year or sex differs from its tournament', m['id'])
    if m['stage'] not in STAGE_ORDER: n('unknown stage', f'{m["id"]} {m["stage"]}')
    if m['home'] == m['away']: n('a team against itself', m['id'])
    if m['hs'] is None or m['as'] is None: n('match without a score', m['id']); continue
    exp = 'h' if m['hs'] > m['as'] else 'a' if m['as'] > m['hs'] else ('h' if (m['ph'] or 0) > (m['pa'] or 0) else 'a' if (m['pa'] or 0) > (m['ph'] or 0) else None)
    if m['winner'] != exp and m['replay'] != 'replayed': n('winner does not follow the score', f'{m["id"]} {m["hs"]}–{m["as"]} ({m["ph"]}–{m["pa"]}) {m["winner"]}')
    if m['ph'] is not None and m['hs'] != m['as']: n('shoot-out after an unlevel score', m['id'])
    if m['stage'] in ('group', 'group2', 'final-round') and not m['group'] and m['stage'] != 'final-round': n('group match without a group', m['id'])
    if m['stadium'] and m['stadium'] not in A['stadiums']: n('stadium not in the register', f'{m["id"]} {m["stadium"]}')
    if m['ref'] and m['ref'] not in A['referees']: n('referee not in the register', m['id'])
    d = D.get(m['id'])
    if d is None: n('match without a detail record', m['id']); continue
    goals = [g for g in d['g'] if True]
    if goals and m['src'] == 'fjelstul':
        hg = sum(1 for g in goals if g[0] == 1); ag = sum(1 for g in goals if g[0] == 0)
        if (hg, ag) != (m['hs'], m['as']): n('goals listed ≠ score', f'{m["id"]} {hg}–{ag} vs {m["hs"]}–{m["as"]}')
    for g in goals:
        if g[1] not in P: n('scorer not in the register', f'{m["id"]} {g[1]}')
        if not (0 <= g[2] <= 120): n('goal minute out of range', f'{m["id"]} {g[2]}')
    if d['l']:
        for side in ('h', 'a'):
            st = sum(1 for p in d['l'][side] if p[3])
            if st != 11: n('line-up without eleven starters', f'{m["id"]} {side} {st}')
            for p in d['l'][side]:
                if p[0] not in P: n('line-up player not in the register', f'{m["id"]} {p[0]}')
    for b in d['b']:
        if b[4] not in ('Y', 'Y2', 'R'): n('unknown card', f'{m["id"]} {b[4]}')
    if m['ph'] is not None and d['p'] and m['src'] == 'fjelstul':
        hc = sum(1 for k in d['p'] if k[0] == 1 and k[2]); ac = sum(1 for k in d['p'] if k[0] == 0 and k[2])
        if (hc, ac) != (m['ph'], m['pa']): n('kicks converted ≠ shoot-out score', f'{m["id"]} {hc}–{ac} vs {m["ph"]}–{m["pa"]}')
# squads and players
for tk, sq in A['squads'].items():
    if tk not in T: n('squad of an unknown tournament', tk); continue
    for team, rows in sq.items():
        if team not in T[tk]['teams']: n('squad of a team not in the tournament', f'{tk} {team}')
        for p in rows:
            if p[0] not in P: n('squad player not in the register', f'{tk} {p[0]}')
used = {g[1] for d in D.values() for g in d['g']} | {p[0] for d in D.values() if d['l'] for s in ('h', 'a') for p in d['l'][s]} | {p[0] for sq in A['squads'].values() for rows in sq.values() for p in rows}
for pid, p in P.items():
    if not p['n']: n('player without a name', pid)
    if pid not in used: n('player never in a squad, line-up or goal', pid)
# well-known facts
scored = collections.Counter(); scored_t = collections.Counter()
for m in M:
    for g in D[m['id']]['g']:
        if not g[4]: scored[g[1]] += 1; scored_t[(g[1], m['t'])] += 1
def by_name(name): return [pid for pid, p in P.items() if p['n'] == name]
def goals_of(name, t=None):
    ids_ = by_name(name)
    return sum((scored_t[(i, t)] if t else scored[i]) for i in ids_)
for name, t, want in (('Just Fontaine', 'M1958', 13), ('Miroslav Klose', None, 16), ('Ronaldo', None, 15), ('Gerd Müller', None, 14), ('Marta', None, 17), ('Birgit Prinz', None, 14), ('Harry Kane', 'M2018', 6), ('Kylian Mbappé', 'M2022', 8), ('Pelé', None, 12)):
    g = goals_of(name, t)
    if g != want: n('well-known scorer’s goals differ', f'{name}{" " + t if t else ""} {g} ≠ {want}')
titles = collections.Counter(t['winner'] for t in A['tournaments'] if t['sex'] == 'M' and t['winner'])   # the database keeps West Germany for 1954, 1974 and 1990
for team, want in (('Brazil', 5), ('Germany', 1), ('West Germany', 3), ('Italy', 4), ('Argentina', 3), ('France', 2), ('Uruguay', 2), ('England', 1), ('Spain', 2)):
    if titles[team] != want: n('well-known titles differ', f'{team} {titles[team]} ≠ {want}')
wt = collections.Counter(t['winner'] for t in A['tournaments'] if t['sex'] == 'W' and t['winner'])
for team, want in (('United States', 4), ('Germany', 2), ('Norway', 1), ('Japan', 1), ('Spain', 1)):
    if wt[team] != want: n('well-known women’s titles differ', f'{team} {wt[team]} ≠ {want}')
for tid, home, hs, as_, away, ph, pa in (('M-1982-05', 'Hungary', 10, 1, 'El Salvador', None, None), ('M-2022-64', 'Argentina', 3, 3, 'France', 4, 2), ('M-2014-61', 'Brazil', 1, 7, 'Germany', None, None), ('M-1950-22', 'Uruguay', 2, 1, 'Brazil', None, None)):
    m = next((m for m in M if m['id'] == tid), None)
    if not m: n('well-known match missing', tid); continue
    if (m['home'], m['hs'], m['as'], m['away'], m['ph'], m['pa']) != (home, hs, as_, away, ph, pa): n('well-known match differs', f'{tid} {m["home"]} {m["hs"]}–{m["as"]} {m["away"]} ({m["ph"]}–{m["pa"]})')
for tk, winner in (('M1930', 'Uruguay'), ('M1966', 'England'), ('M2010', 'Spain'), ('M2022', 'Argentina'), ('M2026', 'Spain'), ('W1991', 'United States'), ('W2011', 'Japan'), ('W2023', 'Spain')):
    if tk not in T: n('well-known tournament missing', tk)
    elif T[tk]['winner'] != winner: n('well-known winner differs', f'{tk} {T[tk]["winner"]} ≠ {winner}')
pele = [pid for pid in by_name('Pelé')]
if pele:
    y58 = [m for m in M if m['t'] == 'M1958' and any(g[1] in pele for g in D[m['id']]['g'])]
    if not y58: n('Pelé’s 1958 goals missing', '')
for tk, cnt in (('M1930', 13), ('M1998', 32), ('M2026', 48), ('W1991', 12), ('W2023', 32)):
    if tk in T and T[tk]['count'] != cnt: n('well-known team count differs', f'{tk} {T[tk]["count"]} ≠ {cnt}')
for tk, cnt in (('M1930', 18), ('M2022', 64), ('M2026', 104), ('W2023', 64)):
    if tk in T and T[tk]['matches'] != cnt: n('well-known match count differs', f'{tk} {T[tk]["matches"]} ≠ {cnt}')
# report
cov = A.get('coverage', {})
out = [f'# Data audit · World Cup atlas', '', f'Checked {datetime.date.today().isoformat()} against `data/worldcup.json` (snapshot {A.get("snapshot")}). Nothing was changed.', '',
       '## Totals', '', f'- {cov.get("tournaments")} tournaments ({cov.get("men")} men’s, {cov.get("women")} women’s) · {cov.get("matches"):,} matches · {cov.get("goals"):,} goals · {cov.get("shootouts")} shoot-outs · {cov.get("lineups"):,} line-ups · {cov.get("players"):,} players ({cov.get("playersWithArticle"):,} with an article) · {cov.get("teams")} teams · {cov.get("stadiums")} grounds · {cov.get("referees")} referees · {cov.get("managers")} managers · {cov.get("awards")} awards',
       f'- players named only by a fixture source (OpenFootball, the ledger), not yet joined to the database’s register: {cov.get("minted")} · sources cited: {len(A.get("sources", []))}', '',
       '## Tournaments', '', '| Tournament | Hosts | Teams | Matches | Goals | Line-ups | Winner | Source |', '|---|---|---|---|---|---|---|---|'] + \
      [f'| {t["name"]} | {", ".join(t["hosts"]) or "—"} | {t["count"]} | {t["matches"]} | {t["goals"] or "—"} | {t["lineups"] or "—"} | {t["winner"] or "—"} | {t["src"]} |' for t in A['tournaments']] + ['', '## Checks', '']
if not iss: out.append('All checks clean.')
for k, ms in sorted(iss.items(), key=lambda kv: -len(kv[1])):
    out.append(f'- **{k}** — {len(ms)}' + (': ' + '; '.join(str(m) for m in ms[:12]) + (' …' if len(ms) > 12 else '') if any(str(m) for m in ms) else ''))
(ROOT/'audits').mkdir(exist_ok=True); (ROOT/'audits'/'DATA-AUDIT-worldcup.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
print('\n'.join(out[-(len(iss) + 2):]))
