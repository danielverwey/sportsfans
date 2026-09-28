#!/usr/bin/env python3
"""Formula 1 sweeper: the current season from the Jolpica F1 API (Ergast-compatible).

Only the current season is harvested; every earlier season is history and stays byte-identical.
New rounds are appended in the archive's own row shape, the season's standings are refreshed, and
new drivers, constructors and circuits are added to the registers. Track specifications and layout
ids for a new round are inherited from the latest earlier race at the same circuit (F1DB fields);
a circuit never seen before gets them left empty until F1DB's next release is applied by hand.

Jolpica's data is CC BY-NC-SA 4.0 and the API is for non-commercial use; this sweeper makes about
fifty small requests per run, at most weekly, with a descriptive User-Agent.

    python tools/harvest/f1.py            # harvest and save if anything changed
    python tools/harvest/f1.py --dry-run  # report only
"""
import sys, json, datetime, copy
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from common import get_json, load, save, today_long, report

API = 'https://api.jolpi.ca/ergast/f1'
STATUS = {'Finished': 'Finished', 'Lapped': 'Lapped', 'Disqualified': 'Disqualified', 'Did not start': 'Did not start', 'Did not qualify': 'Did not qualify', 'Not classified': 'Not classified', 'Retired': 'Retired'}

def status_of(res):
    st = res.get('status', ''); pt = res.get('positionText', '')
    if st == 'Finished': return 'Finished', pt
    if st.startswith('+') and 'Lap' in st: return 'Lapped', pt
    if pt == 'D': return 'Disqualified', 'D'
    if pt == 'W': return 'Did not start', 'W'
    if pt == 'F': return 'Did not qualify', 'W'
    if pt == 'N': return 'Not classified', 'NC'
    return 'Retired', 'R'

def row_of(res, is_sprint=False):
    d = res['Driver']['driverId']; t = res['Constructor']['constructorId']
    status, label = status_of(res); pos = int(res['position']); grid = int(res.get('grid') or 0); laps = int(res.get('laps') or 0)
    fl = res.get('FastestLap') or {}; time_ = (res.get('Time') or {}).get('time') or (res.get('status') if status == 'Lapped' else None)
    row = {'d': d, 't': t, 'num': str(res.get('number', '')), 'p': pos, 'label': label if label.isalpha() or label == 'NC' else str(pos), 'pts': float(res.get('points') or 0), 'g': grid, 'laps': laps, 'status': status, 'time': time_, 'fl': (fl.get('Time') or {}).get('time'), 'fr': int(fl['rank']) if fl.get('rank') else None}
    if is_sprint: return row
    fin = status in ('Finished', 'Lapped'); win = int(pos == 1 and fin); pod = int(pos <= 3 and fin); fast = int(row['fr'] == 1); g1 = int(grid == 1); nf = int(not fin)
    row.update({'de': 1, 'dw': win, 'dp': pod, 'df': fast, 'dg': g1, 'dn': nf, 'ce': 1, 'cw': win, 'cp': pod, 'cf': fast, 'cg': g1, 'cn': nf})
    return row

def register(D, res):
    dr = res['Driver']; d = dr['driverId']
    if d not in D['drivers']: D['drivers'][d] = {'name': f"{dr['givenName']} {dr['familyName']}", 'short': dr['familyName'], 'code': dr.get('code') or dr['familyName'][:3].upper(), 'nationality': dr.get('nationality', ''), 'dob': dr.get('dateOfBirth', '')}
    c = res['Constructor']; t = c['constructorId']
    if t not in D['teams']: D['teams'][t] = {'name': c['name'], 'color': '#b5a5ed'}   # placeholder colour: the atlas hashes it a hue of its own

def inherit(D, cid):
    """F1DB fields for a known circuit: the latest earlier race there."""
    for s in reversed(D['seasons']):
        for r in reversed(s['races']):
            if r['cid'] == cid: return {k: r.get(k) for k in ('layout', 'length', 'turns', 'scheduledLaps', 'distance', 'trackType', 'direction', 'trackSource', 'lapSource')}
    return {k: None for k in ('layout', 'length', 'turns', 'scheduledLaps', 'distance', 'trackType', 'direction', 'trackSource', 'lapSource')}

def harvest(year, dry=False):
    D = load('f1'); before = json.dumps(D, sort_keys=True); lines = [f'# F1 sweep · {today_long()} · season {year}']
    season = next((s for s in D['seasons'] if s['year'] == year), None)
    if season is None:
        season = {'year': year, 'races': [], 'round': 0, 'drivers': [], 'teams': []}; D['seasons'].append(season); lines.append(f'- new season {year} opened')
    have = {r['round'] for r in season['races'] if r['rows']}
    sched = get_json(f'{API}/{year}.json?limit=100')['MRData']['RaceTable']['Races']
    lines.append(f'- {len(sched)} rounds scheduled, {len(have)} already held')
    for rc in sched:
        rnd = int(rc['round'])
        if rnd in have: continue
        res = get_json(f'{API}/{year}/{rnd}/results.json?limit=100')['MRData']['RaceTable']['Races']
        if not res or not res[0].get('Results'): continue   # not yet run
        results = res[0]['Results']; circ = rc['Circuit']; cid = circ['circuitId']
        for x in results: register(D, x)
        if cid not in D['circuits']: D['circuits'][cid] = {'id': cid, 'name': circ['circuitName'], 'country': circ['Location']['country'], 'place': circ['Location']['locality'], 'lat': circ['Location']['lat'], 'lon': circ['Location']['long'], 'url': circ.get('url', ''), 'layouts': []}
        sprint = []
        try:
            sp = get_json(f'{API}/{year}/{rnd}/sprint.json?limit=100')['MRData']['RaceTable']['Races']
            if sp and sp[0].get('SprintResults'):
                for x in sp[0]['SprintResults']: register(D, x)
                sprint = [row_of(x, True) for x in sp[0]['SprintResults']]
        except Exception: pass
        race = {'round': rnd, 'name': rc['raceName'], 'date': rc['date'], 'circuit': circ['circuitName'], 'cid': cid, 'lat': circ['Location']['lat'], 'lon': circ['Location']['long'], 'circuitUrl': circ.get('url', ''), 'country': circ['Location']['country'], 'place': circ['Location']['locality'], 'rows': [row_of(x) for x in results], 'sprint': sprint, 'url': rc.get('url', '')}
        race.update(inherit(D, cid)); season['races'].append(race); season['races'].sort(key=lambda r: r['round']); season['round'] = len(season['races'])
        lines.append(f'- added round {rnd} {rc["raceName"]} ({rc["date"]}): {len(results)} rows{", sprint " + str(len(sprint)) if sprint else ""}')
    # standings
    ds = get_json(f'{API}/{year}/driverStandings.json?limit=100')['MRData']['StandingsTable']['StandingsLists']
    if ds:
        season['drivers'] = [{'id': x['Driver']['driverId'], 'p': x.get('positionText') or x.get('position') or '-', 'pts': float(x['points']), 'wins': int(x['wins']), 'teams': [c['constructorId'] for c in x.get('Constructors', [])]} for x in ds[0]['DriverStandings']]
    cs = get_json(f'{API}/{year}/constructorStandings.json?limit=100')['MRData']['StandingsTable']['StandingsLists']
    if cs:
        season['teams'] = [{'id': x['Constructor']['constructorId'], 'p': x.get('positionText') or x.get('position') or '-', 'pts': float(x['points']), 'wins': int(x['wins'])} for x in cs[0]['ConstructorStandings']]
    changed = json.dumps(D, sort_keys=True) != before
    if changed: D['cutoff'] = today_long()   # the dated line moves only when the archive does, so an idle week commits nothing
    lines.append(f'- standings refreshed: {len(season["drivers"])} drivers, {len(season["teams"])} constructors · {"changes" if changed else "no change"}')
    report(lines, 'f1.md')
    if changed and not dry: save('f1', D); print('saved data/f1.json')
    return changed

if __name__ == '__main__':
    year = datetime.date.today().year
    changed = harvest(year, dry='--dry-run' in sys.argv)
    sys.exit(0)
