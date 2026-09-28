#!/usr/bin/env python3
"""The gate every sweep must pass before a build is committed.

    python tools/gate.py f1            # compare data/f1.json against the last committed version

Rules: history is immutable (every season before the current one is byte-identical to the committed
archive); the current season only grows (rounds and rows never disappear); registers only grow; the
archive's fixed reference facts still hold (audits/facts_<sport>.json, frozen figures for finished careers).
Exit 1 on any violation, so a broken source can never reach the site.
"""
import json, pathlib, subprocess, sys, datetime
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
            elif r['rows'] and json.dumps(r['rows'], sort_keys=True) != json.dumps(nr[r['round']]['rows'], sort_keys=True): errs.append(f'{y} round {r["round"]}: classified rows changed')
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

if __name__ == '__main__':
    sport = sys.argv[1]; path = f'data/{sport}.json'
    new = json.loads((ROOT/path).read_text(encoding='utf-8')); old = committed(path)
    fp = ROOT/'audits'/f'facts_{sport}.json'
    if not fp.exists(): fp.write_text(json.dumps(FACTS[sport](new), indent=1), encoding='utf-8'); print('reference facts frozen →', fp)
    facts = json.loads(fp.read_text(encoding='utf-8'))
    if old is None: print('no committed archive to compare against; facts checked only'); errs = [f'reference fact changed: {d}' for d, f in facts.items() if FACTS[sport](new).get(d) != f]
    else: errs = CHECKS[sport](new, old, facts)
    if errs:
        print('GATE FAILED'); [print(' -', e) for e in errs]; sys.exit(1)
    print(f'gate passed: {sport} archive is a superset of the committed one; history unchanged; {len(facts)} reference facts hold')
