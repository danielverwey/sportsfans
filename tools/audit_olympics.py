"""Data audit for the Summer or Winter Olympics atlas: data/olympics.json (or data/winter.json) against itself and against a
few well-known facts. Writes audits/DATA-AUDIT-olympics.md (or -winter.md). Nothing is changed.

  python3 tools/audit_olympics.py            # the Summer Games
  python3 tools/audit_olympics.py winter     # the Winter Games
"""
import json, collections, datetime, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'tools')); from olympics_common import lineage, gender_of
KEY = 'winter' if 'winter' in sys.argv[1:] else 'olympics'; WINTER = KEY == 'winter'
A = json.load(open(ROOT/'data'/f'{KEY}.json', encoding='utf-8'))
EF, WF, ATH = A['eventFields'], A['awardFields'], A['athletes']
EV = [dict(zip(EF, r)) for r in A['events']]; W = [dict(zip(WF, r)) for r in A['awards']]; G = {g['y']: g for g in A['games']}
iss = collections.defaultdict(list); n = lambda k, m: iss[k].append(m)
# the Games
ys = [g['y'] for g in A['games']]
if ys != sorted(ys): n('Games not in year order', '')
if len(set(ys)) != len(ys): n('duplicate Games year', '')
for g in A['games']:
    if g['cancelled']: continue
    if not g['city'] or not g['country'] or not g['dates']: n('Games without host or dates', g['y'])
    if not g['points'] or any(not (-180 <= p[1] <= 180 and -90 <= p[2] <= 90) for p in g['points']): n('Games without a map point', g['y'])
    if g['athletes'] and g.get('men') is not None and g.get('women') is not None and g['men'] + g['women'] not in range(g['athletes'] - 60, g['athletes'] + 61): n('men + women ≠ athletes', f'{g["y"]} {g["men"]}+{g["women"]}≠{g["athletes"]}')
    ne = sum(1 for e in EV if e['y'] == g['y'])
    if not ne: n('held Games without events', g['y'])
    if g['scheduled'] and abs(ne - g['scheduled']) > max(6, g['scheduled'] // 10): n('medal events far from the scheduled programme', f'{g["y"]} {ne} events, {g["scheduled"]} scheduled')
for y in ((1940, 1944) if WINTER else (1916, 1940, 1944)):
    if y not in G or not G[y]['cancelled']: n('cancelled Games missing', y)
# events
ids = [e['id'] for e in EV]
if len(set(ids)) != len(ids): n('duplicate event id', f'{len(ids) - len(set(ids))}')
for e in EV:
    if e['y'] not in G or G[e['y']]['cancelled']: n('event in a year without Games', e['id'])
    if not e['id'].startswith(f'{e["y"]}-'): n('event id not of its year', e['id'])
    if e['gender'] not in ('Men', 'Women', 'Mixed', 'Open'): n('unknown category', f'{e["id"]} {e["gender"]}')
    if lineage(e['sport'], e['gender'], e['event']) != e['key']: n('lineage key does not match the event', e['id'])
    if e['sport'] not in A['sports']: n('sport not in the register', f'{e["id"]} {e["sport"]}')
awarded = {w['e'] for w in W}
for e in EV:
    if e['id'] not in awarded and e['status'] not in ('No medals', 'Disputed', 'Cancelled'): n('event without awards and without a status', e['id'])
# awards
byid = {e['id']: e for e in EV}; per = collections.defaultdict(list)
for w in W:
    if w['e'] not in byid: n('award of an unknown event', w['e']); continue
    if w['rank'] not in (1, 2, 3): n('rank not 1–3', f'{w["e"]} {w["rank"]}')
    if not w['nation']: n('award without a delegation', w['e'])
    if w['nation'] not in A['nations']: n('delegation not in the register', f'{w["e"]} {w["nation"]}')
    for a in w['athletes']:
        if a not in ATH: n('athlete id without a name', f'{w["e"]} {a}')
    per[w['e']].append(w)
for eid, ws in per.items():
    ranks = collections.Counter(w['rank'] for w in ws)
    if ranks[1] == 0 and ranks[2] < 2 and not byid[eid]['note']: n('event with medals but no gold, and no note saying why', eid)   # a vacated gold (1912 wrestling draw, 2000 women’s 100 m, 2016 77 kg) is genuine and explained
    if ranks[1] > 3: n('more than three golds in one event', f'{eid} {ranks[1]}')
    if ranks[3] > 4: n('more than four bronzes in one event', f'{eid} {ranks[3]}')
    seen = collections.Counter((w['rank'], w['nation'], tuple(w['athletes'])) for w in ws)
    for k, c in seen.items():
        if c > 1 and k[2]: n('the same award twice in one event', f'{eid} {k[1]} {k[0]}')
# medal tables against the validation record
for v in A['validation']:
    if v['status'] != 'matched': n('medal table not reconciled', f'{v["year"]} {v["status"]}')
    got = sum(1 for w in W if byid.get(w['e'], {}).get('y') == v['year'])
    if v.get('awards') and got != v['awards']: n('award count differs from the validation record', f'{v["year"]} {got} ≠ {v["awards"]}')
held = [g['y'] for g in A['games'] if not g['cancelled']]
for y in held:
    if not any(v['year'] == y for v in A['validation']): n('held Games without a validation record', y)
# athletes
name_of = collections.Counter(ATH.values())
count = collections.Counter(a for w in W for a in w['athletes']); gold = collections.Counter(a for w in W if w['rank'] == 1 for a in w['athletes'])
for a in ATH:
    if a not in count: n('athlete name never on a medal', a)
# well-known facts
def medals(aid): return gold[aid], count[aid]
facts = ([('Marit_Bjørgen', 8, 15), ('Bjørn_Dæhlie', 8, 12), ('Ireen_Wüst', 6, 13), ('Eric_Heiden', 5, 5), ('Sonja_Henie', 3, 3), ('Jean-Claude_Killy', 3, 3), ('Ole_Einar_Bjørndalen', 8, None)]   # Bjørndalen’s total is 13 or 14 depending on the reallocated 2014 relay
         if WINTER else [('Michael_Phelps', 23, 28), ('Larisa_Latynina', 9, 18), ('Usain_Bolt', 8, 8), ('Paavo_Nurmi', 9, 12), ('Carl_Lewis', 9, 10), ('Mark_Spitz', 9, 11), ('Nadia_Comăneci', 5, 9), ('Steve_Redgrave', 5, 6)])
for aid, g_, t_ in facts:
    if aid not in ATH: n('well-known athlete missing', aid); continue
    if medals(aid)[0] != g_ or (t_ is not None and medals(aid)[1] != t_): n('well-known athlete’s medals differ', f'{ATH[aid]} {medals(aid)} ≠ ({g_}, {t_})')
tab = collections.Counter(w['nation'] for w in W if w['rank'] == 1); LEADER = 'Norway' if WINTER else 'United States'
if tab.most_common(1)[0][0] != LEADER: n(f'the all-time leader by gold is not {LEADER}', tab.most_common(1))
for y, city, top in (((1924, 'Chamonix', 'Norway'), (1952, 'Oslo', 'Norway'), (1980, 'Lake Placid', 'Soviet Union'), (2002, 'Salt Lake City', 'Norway'), (2010, 'Vancouver', 'Canada'), (2022, 'Beijing', 'Norway')) if WINTER else ((1896, 'Athens', 'United States'), (1936, 'Berlin', 'Germany'), (1980, 'Moscow', 'Soviet Union'), (2008, 'Beijing', 'China'), (2024, 'Paris', 'United States'))):
    if G[y]['city'] != city: n('well-known host differs', f'{y} {G[y]["city"]} ≠ {city}')
    t = collections.defaultdict(lambda: [0, 0, 0])
    for w in W:
        if byid[w['e']]['y'] == y: t[w['nation']][w['rank'] - 1] += 1
    lead = sorted(t.items(), key=lambda kv: (-kv[1][0], -kv[1][1], -kv[1][2]))[:1]   # by gold, then silver, then bronze (Paris 2024: 40 golds each, the United States ahead on silver)
    if not lead or lead[0][0] != top: n('well-known leader of a Games differs', f'{y} {lead} ≠ {top}')
for y, city, cnt in (((1924, 'Chamonix', 16), (2026, 'Milano Cortina', 116)) if WINTER else ((1896, 'Athens', 43), (2024, 'Paris', 329))):
    if sum(1 for e in EV if e['y'] == y) != cnt: n(f'{city} {y} event count ≠ {cnt}', sum(1 for e in EV if e['y'] == y))
# coverage
cov = A.get('coverage', {}); ev_y = collections.Counter(e['y'] for e in EV); aw_y = collections.Counter(byid[w['e']]['y'] for w in W if w['e'] in byid); nat_y = collections.defaultdict(set)
for w in W:
    if w['e'] in byid: nat_y[byid[w['e']]['y']].add(w['nation'])
lin = collections.Counter(e['key'] for e in EV)
out = [f'# Data audit · {A.get("name", "Summer Olympics")} atlas', '', f'Checked {datetime.date.today().isoformat()} against `data/{KEY}.json` (snapshot {A.get("snapshot")}). Nothing was changed.', '',
       '## Totals', '', f'- {cov.get("held")} Games held · {cov.get("cancelled")} cancelled · {cov.get("events"):,} medal events · {cov.get("awards"):,} awards ({cov.get("gold"):,} gold) · {cov.get("medallists"):,} named medallists · {cov.get("nations")} delegations · {cov.get("sports")} sports', f'- medal tables reconciled against the cited comparison table: {cov.get("validated")} of {cov.get("held")} · event lineages (the same event across Games): {len(lin):,}, of which {sum(1 for c in lin.values() if c >= 3):,} held at three Games or more', f'- corrections recorded: {len(A.get("corrections", []))} · name aliases: {len(A.get("aliases", {}))} · sources cited: {len(A.get("sources", []))}', '',
       '## Games', '', '| Games | Host | Medal events | Awards | Delegations on the podium | Athletes |', '|---|---|---|---|---|---|'] + [f'| {g["y"]} | {"cancelled" if g["cancelled"] else g["city"] + ", " + g["country"]} | {ev_y[g["y"]] or "—"} | {aw_y[g["y"]] or "—"} | {len(nat_y[g["y"]]) or "—"} | {g["athletes"] or "—"} |' for g in A['games']] + ['', '## Checks', '']
if not iss: out.append('All checks clean.')
for k, ms in sorted(iss.items(), key=lambda kv: -len(kv[1])):
    out.append(f'- **{k}** — {len(ms)}' + (': ' + '; '.join(str(m) for m in ms[:12]) + (' …' if len(ms) > 12 else '') if any(str(m) for m in ms) else ''))
(ROOT/'audits').mkdir(exist_ok=True); (ROOT/'audits'/f'DATA-AUDIT-{KEY}.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
print('\n'.join(out[-(len(iss) + 2):]))
