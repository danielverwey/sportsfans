#!/usr/bin/env python3
"""The gate every sweep must pass before a build is committed.

    python tools/gate.py f1            # compare data/f1.json against the last committed version
    python tools/gate.py ufc           # the same for any atlas: motogp, sbk, ufc, cricket, tennis, rugby, tt, dakar
    python tools/gate.py ufc --accept  # pass after you have read the report and the changes are genuine

Formula 1 (swept from an API, season by season): history is immutable (every season before the current one is
byte-identical to the committed archive); the current season only grows; registers only grow; the archive's fixed
reference facts still hold (audits/facts_f1.json).

Every other atlas (re-read in full from Wikipedia, Cricsheet or Tennis Abstract, where old articles do get corrected):
nothing may disappear — no race, bout, match, edition or standings table that the committed archive holds may be
missing from the new one, and the snapshot date may not go backwards. Changes to past records and names that left a
register are listed for review but do not fail. Exit 1 on a failure, so a broken read never reaches the site.
"""
import json, pathlib, subprocess, sys, datetime, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
def committed(path):
    try: return json.loads(subprocess.run(['git', 'show', f'HEAD:{path}'], cwd=ROOT, capture_output=True, check=True).stdout.decode('utf-8'))
    except subprocess.CalledProcessError: return None

def facts_f1(D):
    """Career totals for a set of finished careers; these can only be wrong, never new."""
    out = {}
    for d in ('senna', 'prost', 'michael_schumacher', 'fangio', 'clark', 'stewart', 'lauda', 'mansell', 'hakkinen', 'raikkonen', 'vettel', 'rosberg'):
        wins = sum(x['dw'] for s in D['seasons'] for r in s['races'] for x in r['rows'] if x['d'] == d)
        pod = sum(x['dp'] for s in D['seasons'] for r in s['races'] for x in r['rows'] if x['d'] == d)
        if wins or pod: out[d] = {'wins': wins, 'podiums': pod}
    return out

def check_f1(new, old, facts):
    errs = []; year = datetime.date.today().year
    olds = {s['year']: s for s in old['seasons']}; news = {s['year']: s for s in new['seasons']}
    for y, s in olds.items():
        if y >= year: continue
        if json.dumps(s, sort_keys=True) != json.dumps(news.get(y), sort_keys=True): errs.append(f'history changed: season {y}')
    for y, s in olds.items():
        if y not in news: errs.append(f'season {y} disappeared'); continue
        n = news[y]
        if len(n['races']) < len(s['races']): errs.append(f'{y}: rounds fell from {len(s["races"])} to {len(n["races"])}')
        nr = {r['round']: r for r in n['races']}
        for r in s['races']:
            if r['round'] not in nr: errs.append(f'{y} round {r["round"]} disappeared')
            elif r['rows'] and json.dumps(r['rows'], sort_keys=True) != json.dumps(nr[r['round']]['rows'], sort_keys=True):
                if y < year: errs.append(f'{y} round {r["round"]}: classified rows changed')
                else: print(f'note: {y} round {r["round"]}: classification corrected since the last sweep (penalties or a late reclassification)')
    for reg in ('drivers', 'teams', 'circuits'):
        missing = set(old[reg]) - set(new[reg])
        if missing: errs.append(f'{reg} lost entries: {sorted(missing)[:5]}')
    for d, f in facts.items():
        got = facts_f1(new).get(d)
        if got != f: errs.append(f'reference fact changed: {d} {f} → {got}')
    # schema
    for s in new['seasons']:
        for r in s['races']:
            for x in r['rows']:
                for k in ('d', 't', 'p', 'label', 'pts', 'status', 'dw', 'dp', 'cw'):
                    if k not in x: errs.append(f'{s["year"]} R{r["round"]}: row missing {k}'); break
    return errs

CHECKS = {'f1': check_f1}
FACTS = {'f1': facts_f1}

# ---------------------------------------------------------------- every other atlas: nothing disappears
def _keyed(pairs):
    """{key: (year, record)} from (key, year, record) triples; a key seen twice gets a counter so no record is lost."""
    out, seen = {}, {}
    for k, y, r in pairs:
        n = seen.get(k, 0); seen[k] = n + 1
        out[k if n == 0 else (k, n)] = (int(y) if y is not None else 0, r)
    return out
def recs_bikes(A, shard):
    return _keyed([(('race', r['id']), r['year'], r) for r in A['races']] + [(('standings', y), y, st) for y, st in A['standings'].items()])
def recs_ufc(A, shard):
    F = A['boutFields']; i, iy = F.index('id'), F.index('y')
    return _keyed([(('event', e['id']), e['y'], e) for e in A['events']] + [(('bout', b[i]), b[iy], b) for b in A['bouts']])
def recs_cricket(A, shard):
    return _keyed([(('match', g['id']), g['y'], g) for g in A['games']])
def recs_tennis(A, shard):
    ey = A['eFields'].index('y'); C = A['cFields']; ci, cc, cy = C.index('id'), C.index('c'), C.index('y')
    out = [(('edition', k), r[ey], r) for k, r in A['editions'].items()] + [(('title', r[ci], r[cc]), r[cy], r) for r in A['champions']]
    for y in A.get('matchYears', []):
        for ed, rows in (shard(f'data/tennis_matches/{y}.json') or {}).items():
            out += [(('match', r[0]), y, r) for r in rows]
    return _keyed(out)
def recs_rugby(A, shard):
    return _keyed([(('test', m['date'], m['home'], m['away']), m['date'][:4], m) for m in A['matches']])
def recs_tt(A, shard):
    return _keyed([(('race', r['id']), r['y'], r) for r in A['races']])
def recs_dakar(A, shard):
    return _keyed([(('edition', e['y']), e['y'], e) for e in A['editions']])
RECORDS = {'motogp': recs_bikes, 'sbk': recs_bikes, 'ufc': recs_ufc, 'cricket': recs_cricket, 'tennis': recs_tennis, 'rugby': recs_rugby, 'tt': recs_tt, 'dakar': recs_dakar}
REGISTERS = {'motogp': ['riders', 'circuits'], 'sbk': ['riders', 'circuits'], 'ufc': ['fighters'], 'cricket': ['players', 'teams', 'venues'], 'tennis': ['players', 'tournaments'], 'rugby': [], 'tt': ['riders'], 'dakar': ['people']}
def label(k):
    k = k[0] if isinstance(k, tuple) and isinstance(k[0], tuple) else k
    return ' '.join(str(x) for x in (k if isinstance(k, tuple) else (k,)))
def snap(A): return next((A[k] for k in ('snapshot', 'asof', 'retrieved') if isinstance(A.get(k), str)), '')

def _t(v): return 'num' if isinstance(v, (int, float)) and not isinstance(v, bool) else type(v).__name__
def profile(records):
    """What records of one kind look like in the committed archive: the keys (or row length) and the types each field has taken,
    one level into lists of rows or objects."""
    P = {'keys': collections.Counter(), 'n': 0, 'types': collections.defaultdict(set), 'lens': set(), 'inner': collections.defaultdict(list)}
    for r in records:
        P['n'] += 1
        items = r.items() if isinstance(r, dict) else enumerate(r) if isinstance(r, list) else []
        if isinstance(r, dict): P['keys'].update(r.keys())
        elif isinstance(r, list): P['lens'].add(len(r))
        for k, v in items:
            P['types'][k].add(_t(v))
            if isinstance(v, list) and v and isinstance(v[0], (dict, list)): P['inner'][k].extend(v[:40])
    P['inner'] = {k: profile(v) for k, v in P['inner'].items()}
    return P
def misfits(r, P, where='', names=None):
    """How a new record differs from the archive's own records of that kind; empty when it looks like them."""
    out = []; nm = lambda k: names[k] if names and isinstance(k, int) and k < len(names) else k
    if isinstance(r, dict):
        must = {k for k, n in P['keys'].items() if n >= 0.98 * P['n']}
        out += [f'{where}missing field {k}' for k in sorted(must - set(r))] + [f'{where}unknown field {k}' for k in sorted(set(r) - set(P['keys']))]
        items = r.items()
    elif isinstance(r, list):
        if P['lens'] and len(r) not in P['lens']: out.append(f'{where}row of {len(r)} fields (archive rows have {sorted(P["lens"])})')
        items = enumerate(r)
    else: return out
    for k, v in items:
        seen = P['types'].get(k)
        if seen and _t(v) not in seen and not (v is None and 'NoneType' in seen): out.append(f'{where}{nm(k)} is {_t(v)} (archive: {"/".join(sorted(seen))})')
        if k in P['inner'] and isinstance(v, list):
            for x in v[:60]: out += misfits(x, P['inner'][k], f'{where}{k}[]·')
    return out[:6]

def check_generic(sport, new, old):
    """Returns (failures, report lines)."""
    disk = lambda path: json.loads((ROOT/path).read_text(encoding='utf-8')) if (ROOT/path).exists() else None
    N, O = RECORDS[sport](new, disk), RECORDS[sport](old, committed)
    gone = [k for k in O if k not in N]; added = [k for k in N if k not in O]
    changed = [k for k in O if k in N and json.dumps(O[k][1], sort_keys=True) != json.dumps(N[k][1], sort_keys=True)]
    kind = lambda k: (k[0] if isinstance(k[0], tuple) else k)[0] if isinstance(k, tuple) else 'record'
    shapes = {}; odd = []
    for k in added:
        kd = kind(k)
        if kd not in shapes: shapes[kd] = profile([v[1] for kk, v in O.items() if kind(kk) == kd])
        if shapes[kd]['n']:
            bad = misfits(N[k][1], shapes[kd], names={('ufc', 'bout'): new.get('boutFields'), ('tennis', 'edition'): new.get('eFields'), ('tennis', 'title'): new.get('cFields')}.get((sport, kd)))
            if bad: odd.append(f'{label(k)}: {"; ".join(bad)}')
    errs, rep = [], [f'gate · {sport} · committed snapshot {snap(old) or "—"} → new {snap(new) or "—"}',
                     f'  records {len(O):,} → {len(N):,}: {len(added):,} added · {len(gone):,} missing · {len(changed):,} changed']
    by = lambda ks, idx: {y: [k for k in ks if idx[k][0] == y] for y in sorted({idx[k][0] for k in ks}, reverse=True)}
    for y, ks in by(added, N).items(): rep.append(f'  {y}: +{len(ks)} added — {", ".join(label(k) for k in ks[:4])}{" …" if len(ks) > 4 else ""}')
    for y, ks in by(changed, N).items(): rep.append(f'  {y}: {len(ks)} changed (review) — {", ".join(label(k) for k in ks[:4])}{" …" if len(ks) > 4 else ""}')
    for y, ks in by(gone, O).items():
        errs.append(f'{y}: {len(ks)} missing — {", ".join(label(k) for k in ks[:6])}{" …" if len(ks) > 6 else ""}')
    if snap(old) and snap(new) and snap(new) < snap(old): errs.append(f'snapshot went backwards: {snap(old)} → {snap(new)}')
    if odd: errs.append(f'{len(odd)} new record(s) do not look like the archive\'s own — the reader may have misread its source: ' + ' | '.join(odd[:5]))
    for reg in REGISTERS[sport]:
        if isinstance(old.get(reg), dict) and isinstance(new.get(reg), dict):
            left = sorted(set(old[reg]) - set(new[reg])); rep.append(f'  {reg}: {len(old[reg]):,} → {len(new[reg]):,}' + (f' · {len(left)} left the register (review): {", ".join(left[:5])}{" …" if len(left) > 5 else ""}' if left else ''))
    return errs, rep

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; accept = '--accept' in sys.argv
    if not args or (args[0] not in CHECKS and args[0] not in RECORDS): sys.exit('usage: python tools/gate.py <' + '|'.join(list(CHECKS) + list(RECORDS)) + '> [--accept]')
    sport = args[0]; path = f'data/{sport}.json'
    new = json.loads((ROOT/path).read_text(encoding='utf-8')); old = committed(path)
    if sport not in CHECKS:
        if old is None: print(f'gate · {sport}: no committed archive to compare against; passed'); sys.exit(0)
        errs, rep = check_generic(sport, new, old); print('\n'.join(rep))
        if errs:
            print('GATE FAILED' + (' — accepted by hand (--accept)' if accept else '')); [print(' -', e) for e in errs]
            sys.exit(0 if accept else 1)
        print(f'gate passed: nothing the committed {sport} archive holds is missing'); sys.exit(0)
    fp = ROOT/'audits'/f'facts_{sport}.json'
    if not fp.exists(): fp.write_text(json.dumps(FACTS[sport](new), indent=1), encoding='utf-8'); print('reference facts frozen →', fp)
    facts = json.loads(fp.read_text(encoding='utf-8'))
    if old is None: print('no committed archive to compare against; facts checked only'); errs = [f'reference fact changed: {d}' for d, f in facts.items() if FACTS[sport](new).get(d) != f]
    else: errs = CHECKS[sport](new, old, facts)
    if errs:
        print('GATE FAILED'); [print(' -', e) for e in errs]; sys.exit(1)
    print(f'gate passed: {sport} archive is a superset of the committed one; history unchanged; {len(facts)} reference facts hold')
