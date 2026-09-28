"""Data audit for the UFC atlas: data/ufc.json against itself and against a few well-known facts.
Writes audits/DATA-AUDIT-ufc.md. Nothing is changed.

  python3 tools/audit_ufc.py
"""
import json, collections, datetime, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
A = json.load(open(ROOT/'data'/'ufc.json', encoding='utf-8'))
BF = A['boutFields']; B = [dict(zip(BF, r)) for r in A['bouts']]; E = {e['id']: e for e in A['events']}; F = A['fighters']; V = A['venues']; D = {d['key'] for d in A['divisions']}
iss = collections.defaultdict(list); n = lambda k, m: iss[k].append(m)
# events
ids = [e['id'] for e in A['events']]
if len(set(ids)) != len(ids): n('duplicate event id', f'{len(ids) - len(set(ids))}')
dates = [e['date'] for e in A['events']]
if dates != sorted(dates): n('events not in date order', f'{sum(1 for a, b in zip(dates, dates[1:]) if b < a)} inversions')
for e in A['events']:
    try: datetime.date.fromisoformat(e['date'])
    except Exception: n('bad event date', e['id'])
    if e['y'] != int(e['date'][:4]): n('year ≠ date', e['id'])
    if not e['bouts']: n('event without bouts', f'{e["id"]} ({e["date"]})')
    if e.get('venueId') and e['venueId'] not in V: n('venue id unknown', e['id'])
    if not e['country']: n('event without a country', e['id'])
    if e.get('att') and (e['att'] < 100 or e['att'] > 120000): n('attendance out of range', f'{e["id"]} {e["att"]}')
# bouts
bids = [b['id'] for b in B]
if len(set(bids)) != len(bids): n('duplicate bout id', f'{len(bids) - len(set(bids))}')
pairs = collections.Counter((b['date'], tuple(sorted((b['a'], b['b'])))) for b in B)
for k, c in pairs.items():
    if c > 1: n('same pair twice on one date (a no contest refought the same night is genuine)', f'{k[0]} {k[1][0]} v {k[1][1]}')
for b in B:
    if b['e'] not in E: n('bout without event', b['id']); continue
    if b['date'] != E[b['e']]['date']: n('bout date ≠ event date', b['id'])
    if b['a'] not in F or b['b'] not in F: n('fighter id unknown', b['id'])
    if b['a'] == b['b']: n('fighter against himself', b['id'])
    if b['res'] == 'W' and b['w'] not in (b['a'], b['b']): n('winner not in the bout', b['id'])
    if b['res'] != 'W' and b['w']: n('winner on a non-win', b['id'])
    if b['res'] not in ('W', 'D', 'NC'): n('unknown result', b['id'])
    if b['div'] not in D: n('unknown division', f'{b["id"]} {b["div"]}')
    if b['mk'] not in ('KO', 'SUB', 'DEC', 'DQ', 'NC', 'DRAW', 'OTHER'): n('unknown method kind', b['id'])
    if b['mk'] == 'OTHER': n('method not classified', f'{b["id"]} · {b["method"]!r}')
    if b['round'] is not None and not (1 <= b['round'] <= 5) and b['date'] >= '1999-07-16': n('round out of range', f'{b["id"]} R{b["round"]}')
    if b['time'] and not re.fullmatch(r'\d{1,2}:\d{2}', b['time']): n('time not m:ss', f'{b["id"]} {b["time"]!r}')
    if b['time'] and re.fullmatch(r'\d{1,2}:\d{2}', b['time']) and b['date'] >= '1999-07-16' and int(b['time'].split(':')[0]) * 60 + int(b['time'].split(':')[1]) > 300: n('time past five minutes', f'{b["id"]} {b["time"]}')
    if b['mk'] == 'DEC' and b['y'] >= 2001 and b['time'] and b['time'] != '5:00' and not (b['dk'] == 'technical'): n('decision not at 5:00', f'{b["id"]} {b["time"]}')
    if b['title'] and b['mk'] == 'DEC' and b['y'] >= 2001 and b['round'] not in (5, None): n('title decision not after five rounds', f'{b["id"]} R{b["round"]}')
    if not b['wc']: n('bout without a weight class', b['id'])
    if b['secs'] is None and b['round'] and b['time']: n('elapsed time not computed', b['id'])
    for who in ('a', 'b'):
        nm = F.get(b[who], {}).get('name', '')
        if re.search(r'\b(tba|tbd|vacant|unknown|opponent)\b', nm.lower()): n('placeholder fighter', f'{b["id"]} {nm}')
# fighters
for fid, f in F.items():
    r = f['rec']
    if sum(r) == 0: n('fighter without bouts', fid)
    if f.get('dob') and not (1940 <= int(f['dob'][:4]) <= 2010): n('birth date out of range', f'{fid} {f["dob"]}')
    if f.get('cm') and not (140 <= f['cm'] <= 230): n('height out of range', f'{fid} {f["cm"]}')
names = collections.Counter(f['name'].lower() for f in F.values())
for nm, c in names.items():
    if c > 1: n('two fighter ids share a name', f'{nm} ×{c}')
# well-known facts
facts = [('ufc-1', '1993-11-12', 'royce-gracie'), ('ufc-100', '2009-07-11', None), ('ufc-200', '2016-07-09', None), ('ufc-300', '2024-04-13', 'alex-pereira')]
for eid, date, main in facts:
    e = E.get(eid)
    if not e: n('well-known event missing', eid); continue
    if e['date'] != date: n('well-known event on the wrong date', f'{eid} {e["date"]} ≠ {date}')
    if main:
        bs = [b for b in B if b['e'] == eid]
        if bs and bs[0]['w'] != main: n('well-known main event winner differs', f'{eid} {bs[0]["w"]} ≠ {main}')
first_w = next((b for b in B if b['sex'] == 'W'), None)
if first_w and first_w['date'] < '2013-02-23': n('a women’s bout before UFC 157', f'{first_w["id"]} {first_w["date"]}')
# coverage
cov = A.get('coverage', {}); by_y = collections.Counter(b['y'] for b in B); ev_y = collections.Counter(e['y'] for e in A['events'])
out = [f'# Data audit · UFC atlas', '', f'Checked {datetime.date.today().isoformat()} against `data/ufc.json` (snapshot {A.get("snapshot")}). Nothing was changed.', '',
       '## Totals', '', f'- {len(A["events"])} events · {len(B):,} bouts · {len(F):,} fighters · {len(V)} venues · {cov.get("titleBouts")} title bouts · {cov.get("womensBouts")} women’s bouts', f'- fighters with an article: {cov.get("fightersWithArticle")} · with nationality: {cov.get("fightersWithNationality")} · with a birth date: {cov.get("fightersWithBirthDate")}', f'- bouts without an elapsed time: {cov.get("withoutTime")} · events whose results table could not be read: {cov.get("eventsWithoutResults")}', '',
       '## Events and bouts by year', '', '| Year | Events | Bouts |', '|---|---|---|'] + [f'| {y} | {ev_y[y]} | {by_y[y]} |' for y in sorted(ev_y)] + ['', '## Checks', '']
if not iss: out.append('All checks clean.')
for k, ms in sorted(iss.items(), key=lambda kv: -len(kv[1])):
    out.append(f'- **{k}** — {len(ms)}' + (': ' + '; '.join(ms[:12]) + (' …' if len(ms) > 12 else '') if any(ms) else ''))
(ROOT/'audits').mkdir(exist_ok=True); (ROOT/'audits'/'DATA-AUDIT-ufc.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
print('\n'.join(out[-(len(iss) + 2):]))
