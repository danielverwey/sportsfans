"""Tennis: the season's tour-level singles from Jeff Sackmann's match files (Tennis Abstract, CC BY-NC-SA 4.0) —
atp_matches_<year>.csv and wta_matches_<year>.csv — with the player files for anyone new. The archive is turned back
into its source shape (prepare_tennis.unprepare), the season's matches are merged in with the archive's own conventions
(ids, tournaments, editions, champions), and the whole is prepared again. In January and February the season just
finished is read again too, for the last events and corrections. Qualifying and doubles are not swept.
"""
import copy, csv, datetime, hashlib, io, json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0, str(ROOT/'tools'/'harvest'))

RAW = {'MS': 'https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/', 'WS': 'https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/'}
FILES = {'MS': ('atp_matches_{y}.csv', 'atp_players.csv'), 'WS': ('wta_matches_{y}.csv', 'wta_players.csv')}
REPO = {'MS': 'JeffSackmann/tennis_atp', 'WS': 'JeffSackmann/tennis_wta'}
MAJORS = {'australian open': 'AO', 'roland garros': 'RG', 'french open': 'RG', 'wimbledon': 'WI', 'us open': 'US'}
TEAM_EVENTS = {'united cup', 'laver cup', 'atp cup', 'hopman cup', 'davis cup', 'billie jean king cup', 'fed cup', 'world team cup', 'nations cup'}
STATS = ['ace', 'df', 'svpt', '1stIn', '1stWon', '2ndWon', 'SvGms', 'bpSaved', 'bpFaced']
DEFAULT_COLOURS = ('#aace5a', '#4d665b')

def load_prepare():
    import importlib.util
    spec = importlib.util.spec_from_file_location('prepare_tennis', ROOT/'tools'/'prepare_tennis.py'); P = importlib.util.module_from_spec(spec)
    argv = sys.argv; sys.argv = ['prepare_tennis']
    try: spec.loader.exec_module(P)
    finally: sys.argv = argv
    return P

def num(x):
    x = (x or '').strip()
    if not x: return None
    try: return int(float(x))
    except ValueError: return None
def seed(x):
    x = (x or '').strip()
    return x[:-2] if x.endswith('.0') else x
def tid_of(name): return 'T' + hashlib.sha1(name.encode('utf-8')).hexdigest()[:8]

def convert(c, rows, D, log):
    """Sackmann match rows of one circuit and season → (games, editions, tournaments) in the archive's shape."""
    T, E = D['tournaments'], D['editions']
    team_tids = {e['t'] for e in E.values() if e['team']}; plain_tids = {e['t'] for e in E.values() if not e['team']}
    # a tournament keeps its id across name changes ('Monte Carlo' → 'Monte Carlo Masters'): the source's own event number
    # for the circuit first, then the name as the archive knows it, then a new id from the name
    by_code = {}; by_name = {}
    for eid, e in sorted(E.items(), key=lambda t: t[1]['date']):
        by_code[(e['c'], eid.split(':', 1)[1].split('-', 1)[-1].lstrip('0'))] = e['t']
        by_name.setdefault(e['name'].lower(), e['t'])
    for tid, t in T.items(): by_name[t['n'].lower()] = tid
    games, eds, tours = [], {}, {}; seen = {}; skipped = 0
    for r in rows:
        rnd = (r.get('round') or '').strip()
        if re.fullmatch(r'Q\d', rnd.upper()) or not r.get('winner_id') or not r.get('loser_id') or not r.get('tourney_id'):
            skipped += 1; continue
        name = (r.get('tourney_name') or '').strip(); level = (r.get('tourney_level') or '').strip()
        code = r['tourney_id'].strip().split('-', 1)[-1].lstrip('0')
        tid = (MAJORS.get(name.lower()) if level == 'G' else None) or by_code.get((c, code)) or by_name.get(name.lower()) or by_name.get(re.sub(r'\s+masters$', '', name, flags=re.I).lower()) or tid_of(name)
        by_code[(c, code)] = tid; by_name.setdefault(name.lower(), tid)
        if tid not in T and tid not in tours:
            tours[tid] = {'n': name, 'c': DEFAULT_COLOURS[0], 'c2': DEFAULT_COLOURS[1], 's': '', 'city': '', 'url': '', 'major': False}
        eid = f'{c}:{r["tourney_id"].strip()}'
        if eid not in E and eid not in eds:
            d = (r.get('tourney_date') or '').strip()
            team = level == 'D' or name.lower() in TEAM_EVENTS or (tid in team_tids and tid not in plain_tids)
            eds[eid] = {'t': tid, 'c': c, 'y': int(d[:4]), 'date': f'{d[:4]}-{d[4:6]}-{d[6:8]}', 'surface': (r.get('surface') or '').strip(), 'level': level, 'name': name, 'draw': num(r.get('draw_size')), 'team': bool(team)}
        mn = num(r.get('match_num'))
        gid = f'{eid}:{mn}'
        if gid in seen: gid = f'{eid}:{mn}:{rnd}:' + hashlib.sha1((r['winner_id'] + r['loser_id'] + rnd).encode()).hexdigest()[:6]
        seen[gid] = 1
        ws = [num(r.get(f'w_{k}')) for k in STATS]; ls = [num(r.get(f'l_{k}')) for k in STATS]
        st = None if all(v is None for v in ws + ls) else [ws, ls]
        p = 'M' if c == 'MS' else 'W'
        games.append([gid, eid, [p + r['winner_id'].strip()], [p + r['loser_id'].strip()], (r.get('score') or '').strip(), rnd, mn, num(r.get('minutes')), num(r.get('best_of')),
                      seed(r.get('winner_seed')), seed(r.get('loser_seed')), num(r.get('winner_rank')), num(r.get('loser_rank')), st, 0])
    if skipped: log.append(f'  - {c}: {skipped} qualifying or incomplete rows left out')
    return games, eds, tours

def player_of(c, row):
    return {'n': f'{(row.get("name_first") or "").strip()} {(row.get("name_last") or "").strip()}'.strip(), 'g': 'M' if c == 'MS' else 'W', 'ioc': (row.get('ioc') or '').strip(),
            'dob': (row.get('dob') or '').strip().split('.')[0], 'hand': (row.get('hand') or '').strip(), 'height': num(row.get('height'))}

def merge(D, c, games, eds, tours, players_csv, log):
    """Games in, by id: a new id is added, a known one refreshed. Returns (added, refreshed)."""
    GF = D['gameFields']; ix = {g[0]: i for i, g in enumerate(D['games'])}
    added = refreshed = 0
    D['tournaments'].update(tours); D['editions'].update(eds)
    for g in games:
        if g[0] in ix:
            if D['games'][ix[g[0]]] != g: D['games'][ix[g[0]]] = g; refreshed += 1
        else: D['games'].append(g); ix[g[0]] = len(D['games']) - 1; added += 1
    need = {pid for g in games for pid in g[2] + g[3] if pid not in D['players']}
    if need:
        prefix = 'M' if c == 'MS' else 'W'
        byid = {prefix + row['player_id'].strip(): row for row in players_csv() if row.get('player_id')}
        for pid in sorted(need):
            D['players'][pid] = player_of(c, byid[pid]) if pid in byid else {'n': pid, 'g': prefix, 'ioc': '', 'dob': '', 'hand': '', 'height': None}
        log.append(f'  - {c}: {len(need)} new players ({", ".join(D["players"][p]["n"] for p in sorted(need)[:6])}{" …" if len(need) > 6 else ""})')
    # champions: the one final of an individual event (team events and Davis Cup ties have none)
    have = {ch['id'] for ch in D['champions']}
    by_ed = {}
    for g in games: by_ed.setdefault(g[1], []).append(g)
    for eid, gs in by_ed.items():
        e = D['editions'][eid]; finals = [g for g in gs if g[5] == 'F']
        if eid in have or e['team'] or len(finals) != 1: continue
        f = finals[0]
        D['champions'].append({'id': eid, 't': e['t'], 'c': e['c'], 'y': e['y'], 'w': f[2], 'l': f[3], 's': f[4], 'm': f[0], 'src': 0, 'url': ''})
        log.append(f'  - champion: {D["tournaments"][e["t"]]["n"]} {e["y"]} — {D["players"].get(f[2][0], {}).get("n", f[2][0])}')
    return added, refreshed

def fetch_csv(url):
    from common import get
    return list(csv.DictReader(io.StringIO(get(url, timeout=120).decode('utf-8', 'replace'))))

def latest_commit(repo):
    try:
        from common import get_json
        return get_json(f'https://api.github.com/repos/{repo}/commits/master')['sha']
    except Exception: return None

def sweep(log, fetch=None, today=None, commit=None):
    today = today or datetime.date.today(); fetch = fetch or fetch_csv; commit = commit or latest_commit
    P = load_prepare()
    core = json.loads((ROOT/'data'/'tennis.json').read_text(encoding='utf-8')); shards = P.read_shards()
    D = P.unprepare(core, shards); before = len(D['games'])
    # the archive must come back through the converter unchanged (rivalries aside: ties there have no fixed order)
    k2, s2 = P.prepare(copy.deepcopy(D)); norm = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True)
    if any(norm(core[k]) != norm(k2.get(k)) for k in core if k != 'rivals') or norm(s2) != norm(shards):
        raise SystemExit('data/tennis.json does not come back unchanged through tools/prepare_tennis.py — the converter and the archive disagree; nothing written')
    log.append('Round trip: the archive comes back unchanged through prepare_tennis.py.')
    years = [today.year - 1, today.year] if today.month <= 2 else [today.year]
    log.append(f'Archive through {core["lastDate"]}; reading {", ".join(map(str, years))} from Tennis Abstract.'); log.append('')
    added = refreshed = 0
    for c in ('MS', 'WS'):
        cache = {}
        def players_csv(c=c):
            if 'p' not in cache: cache['p'] = fetch(RAW[c] + FILES[c][1])
            return cache['p']
        for y in years:
            try: rows = fetch(RAW[c] + FILES[c][0].format(y=y))
            except Exception as e: log.append(f'- {c} {y}: not available ({e})'); continue
            games, eds, tours = convert(c, rows, D, log)
            a, r = merge(D, c, games, eds, tours, players_csv, log)
            log.append(f'- {c} {y}: {len(rows)} rows read · {a} new matches · {r} refreshed · {len(eds)} new editions'); added += a; refreshed += r
    if not added and not refreshed: log.append('- nothing new'); return
    D['snapshot'] = today.isoformat()
    sha = commit(REPO['MS'])
    if sha: D['sourceCommit'] = sha
    cov = D['coverage']; cov.update(matches=len(D['games']), players=len(D['players']), tournaments=len(D['tournaments']), editions=len(D['editions']), titles=len(D['champions']),
                                     statistics=sum(1 for g in D['games'] if g[13]))
    for sc in cov.get('scope', []):
        if sc['c'] in ('MS', 'WS'):
            mine = [g for g in D['games'] if g[1].startswith(sc['c'] + ':')]
            sc.update(matches=len(mine), stats=sum(1 for g in mine if g[13]), end=max(D['editions'][g[1]]['y'] for g in mine), titles=sum(1 for ch in D['champions'] if ch['c'] == sc['c']),
                      titleEnd=max(ch['y'] for ch in D['champions'] if ch['c'] == sc['c']))
    core2, shards2 = P.prepare(D)
    P.write(core2, shards2)
    log += ['', f'Archive now {len(D["games"]):,} matches (+{len(D["games"]) - before:,}), through {core2["lastDate"]}.']
