"""Cricket: new men's and women's internationals from Cricsheet (ODC-By 1.0) — Tests, ODIs and T20Is — read ball by ball
from Cricsheet's "recently added" download and written in the archive's own shapes: the result line, the scorecard
(batting, bowling, extras, over-by-over progression, fall of wickets, target) and the players' season figures, which are
recomputed from the scorecards exactly as the archive computes them. New players take their Cricinfo key from Cricsheet's
people register; new grounds are added to the venue register. The ICC titles are not swept.
"""
import copy, datetime, hashlib, io, json, pathlib, sys, zipfile, csv
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0, str(ROOT/'tools'/'harvest'))

RECENT = 'https://cricsheet.org/downloads/recently_added_{n}_json.zip'
PEOPLE = 'https://cricsheet.org/register/people.csv'
FORMAT = {'Test': 'Test', 'ODI': 'ODI', 'T20': 'T20I'}
BOWLER_KINDS = {'bowled', 'caught', 'caught and bowled', 'lbw', 'stumped', 'hit wicket'}
NOT_OUT = {'not out', 'retired hurt', 'retired not out'}
FIELDED = {'caught', 'stumped', 'run out'}

def load_prepare():
    import prepare_cricket as P
    return P

# ---------------------------------------------------------------- one match, Cricsheet JSON → the archive's game
def margin_of(by):
    if not by: return ''
    if 'innings' in by: return f'{by["innings"]} innings & {by.get("runs", 0)} runs'
    if 'runs' in by: return f'{by["runs"]} runs'
    if 'wickets' in by: return f'{by["wickets"]} wickets'
    return ''

def innings_of(inn, pid, bpo):
    """One innings, ball by ball → [team, runs, wkts, balls, declared, forfeited, super_over, extras[w,nb,b,lb,p],
    batting rows, bowling rows, overs [over, runs, wkts, legal balls, bat runs], fall of wickets, target runs, target overs]."""
    runs = 0; wk = 0; balls = 0; X = [0, 0, 0, 0, 0]
    bat, bat_order, bowl, bowl_order, overs, fow = {}, [], {}, [], [], []
    def batter(p):
        if p not in bat: bat[p] = [p, 0, 0, 0, 0, 'not out', '', []]; bat_order.append(p)
        return bat[p]
    def bowler(p):
        if p not in bowl: bowl[p] = [p, 0, 0, 0, 0, 0, 0, 0]; bowl_order.append(p)
        return bowl[p]
    for ov in inn.get('overs', []):
        o = ov['over']; o_runs = o_wk = o_legal = o_bat = 0; o_bowlers = set(); o_conc = 0
        for d in ov.get('deliveries', []):
            batter(pid(d['batter'])); batter(pid(d['non_striker']))
            r = d.get('runs', {}); e = d.get('extras', {}) or {}
            wd, nb, b_, lb, pen = e.get('wides', 0), e.get('noballs', 0), e.get('byes', 0), e.get('legbyes', 0), e.get('penalty', 0)
            legal = not wd and not nb
            total, off_bat = r.get('total', 0), r.get('batter', 0)
            runs += total; X[0] += wd; X[1] += nb; X[2] += b_; X[3] += lb; X[4] += pen
            br = bat[pid(d['batter'])]; br[1] += off_bat
            if not wd: br[2] += 1
            if not r.get('non_boundary'):
                if off_bat == 4: br[3] += 1
                elif off_bat == 6: br[4] += 1
            bw = bowler(pid(d['bowler'])); o_bowlers.add(bw[0])
            conceded = off_bat + wd + nb
            if legal: bw[1] += 1; balls += 1; o_legal += 1
            bw[2] += conceded; bw[5] += wd; bw[6] += nb
            if legal and total == 0: bw[7] += 1   # a dot is a ball with no runs at all, as the archive counts it (byes and leg-byes are not dots)
            o_runs += total; o_bat += off_bat; o_conc += conceded
            for w in d.get('wickets', []) or []:
                kind = w.get('kind', ''); out = pid(w['player_out']); row = batter(out); row[5] = kind
                row[6] = bw[0] if kind in BOWLER_KINDS else ''
                row[7] = [pid(f['name']) for f in w.get('fielders', []) or [] if f.get('name')] if kind in FIELDED else []
                if kind in BOWLER_KINDS: bw[3] += 1
                if kind not in NOT_OUT:
                    wk += 1; o_wk += 1; fow.append([runs, wk, f'{o}.{o_legal}', out, kind])
        if len(o_bowlers) == 1 and o_legal >= bpo and o_conc == 0: bowl[next(iter(o_bowlers))][4] += 1
        overs.append([o, o_runs, o_wk, o_legal, o_bat])
    pr = inn.get('penalty_runs') or {}
    extra_pen = (pr.get('pre') or 0) + (pr.get('post') or 0); runs += extra_pen; X[4] += extra_pen
    tgt = inn.get('target') or {}
    return [inn['team'], runs, wk, balls, bool(inn.get('declared')), bool(inn.get('forfeited')), bool(inn.get('super_over')), X,
            [bat[p] for p in bat_order], [bowl[p] for p in bowl_order], overs, fow, tgt.get('runs'), tgt.get('overs')]

def convert(m, mid):
    """A Cricsheet match (dict) → the archive's game (with inn and players) and the people and venue it names,
    or None when it is not a Test, ODI or T20I."""
    info = m.get('info', {})
    f = FORMAT.get(info.get('match_type'))
    if not f or info.get('team_type') != 'international' or not info.get('match_type_number'): return None
    reg = (info.get('registry') or {}).get('people') or {}
    names = {}
    def pid(name):
        p = reg.get(name) or hashlib.sha1(name.encode('utf-8')).hexdigest()[:8]
        names.setdefault(p, name); return p
    g = 'W' if info.get('gender') == 'female' else 'M'
    dates = [str(d) for d in info.get('dates', [])]
    oc = info.get('outcome') or {}
    winner = oc.get('winner', '') or ''
    result = 'win' if winner else {'draw': 'draw', 'tie': 'tie', 'no result': 'no result'}.get(oc.get('result', ''), 'no result')
    ev = info.get('event') or {}
    stage = ev.get('stage') or (str(ev['match_number']) if ev.get('match_number') is not None else '')
    toss = info.get('toss') or {}
    bpo = info.get('balls_per_over', 6)
    inn = [innings_of(i, pid, bpo) for i in m.get('innings', [])]
    players = [[t, [pid(n) for n in ps]] for t, ps in (info.get('players') or {}).items()]
    game = {'id': str(mid), 'date': dates[0], 'end': dates[-1], 'y': int(dates[0][:4]), 'f': f, 'g': g, 'teams': list(info.get('teams', [])), 'winner': winner, 'result': result,
            'margin': margin_of(oc.get('by')), 'v': None, 'event': ev.get('name', '') or '', 'stage': stage, 'no': info['match_type_number'],
            'toss': [toss.get('winner'), toss.get('decision')] if toss else None, 'pom': [pid(n) for n in info.get('player_of_match', []) or []], 'detail': True, 'source': 'cricsheet',
            'decider': oc.get('eliminator') or oc.get('bowl_out') or '', 'method': oc.get('method', '') or '', 'rawDate': '', 'season': str(info.get('season', '')), 'inn': inn, 'players': players}
    team_of = {p: t for t, ps in players for p in ps}
    return game, names, team_of, (info.get('venue') or '', info.get('city') or '')

# ---------------------------------------------------------------- player-season figures, exactly as the archive computes them
def season_rows(games, PSF):
    """{(y, f, g, team, player): row} from the scorecards of the given games, in first-appearance order."""
    agg = {}
    def row(gm, t, p):
        k = (gm['y'], gm['f'], gm['g'], t, p)
        if k not in agg:
            a = {f: 0 for f in PSF[5:]}; a.update(hs=0, hsno=False, bbw=0, bbr=None); agg[k] = a
        return agg[k]
    for gm in games:
        if not gm.get('inn') and not gm.get('players'): continue
        pl = gm.get('players') or []
        for t, ps in pl:
            for p in ps: row(gm, t, p)['games'] += 1
        for p in gm.get('pom') or []:
            t = next((t for t, ps in pl if p in ps), None)
            if t: row(gm, t, p)['pom'] += 1
        for inn in gm.get('inn') or []:
            if inn[6]: continue
            bt = inn[0]; ft = next((t for t, _ in pl if t != bt), None) if len(pl) == 2 else None
            for pid_, r, balls, f4, s6, how, bw, fl in inn[8]:
                # historical scorecards leave balls, fours and sixes blank (None) where they were not recorded
                a = row(gm, bt, pid_); a['inns'] += 1; a['runs'] += r; a['balls'] += balls or 0; a['fours'] += f4 or 0; a['sixes'] += s6 or 0
                if 'sruns' in a and balls is not None: a['sruns'] += r   # runs off known balls: the strike rate's numerator
                out = how not in NOT_OUT
                a['outs' if out else 'notouts'] += 1
                if r >= 100: a['hundreds'] += 1
                elif r >= 50: a['fifties'] += 1
                if r > a['hs'] or (r == a['hs'] and not out and not a['hsno']): a['hs'] = r; a['hsno'] = not out
                for fdr in fl:
                    fa = row(gm, ft, fdr)
                    if how == 'caught': fa['catches'] += 1
                    elif how == 'stumped': fa['stumps'] += 1
                    elif how == 'run out': fa['runouts'] += 1
                if how == 'caught and bowled' and bw: row(gm, ft, bw)['catches'] += 1
            for pid_, balls, conc, wk, md, wd, nb, dots in inn[9]:
                a = row(gm, ft, pid_); a['binns'] += 1; a['bballs'] += balls; a['conceded'] += conc; a['wickets'] += wk; a['maidens'] += md
                if wk >= 5: a['five'] += 1
                if a['bbr'] is None or wk > a['bbw'] or (wk == a['bbw'] and conc < a['bbr']): a['bbw'] = wk; a['bbr'] = conc
    return {k: list(k) + [a[f] for f in PSF[5:]] for k, a in agg.items()}

# ---------------------------------------------------------------- registers
def venue_id(src, venue, city):
    V = src['venues']
    for vid, v in V.items():
        if venue in (v.get('aliases') or []): return vid
    name = venue.split(', ')[0].strip()   # Cricsheet writes 'Ground, Town' or 'Ground, Country'; the register names the ground
    for vid, v in V.items():
        if v['n'] == name and not v.get('locationOnly'):
            v.setdefault('aliases', []).append(venue); return vid
    vid = hashlib.sha1(name.encode('utf-8')).hexdigest()[:9]
    while vid in V and V[vid]['n'] != name: vid = hashlib.sha1((name + vid).encode('utf-8')).hexdigest()[:9]
    V[vid] = {'id': vid, 'n': name, 'city': city, 'locationOnly': False, 'aliases': [venue]}
    return vid

def fetch_zip(n):
    from common import get
    return zipfile.ZipFile(io.BytesIO(get(RECENT.format(n=n), timeout=300)))

def fetch_people():
    from common import get
    return {r['identifier']: r for r in csv.DictReader(io.StringIO(get(PEOPLE, timeout=120).decode('utf-8', 'replace')))}

def read_matches(z):
    for name in z.namelist():
        if not name.endswith('.json'): continue
        try: yield pathlib.Path(name).stem, json.loads(z.read(name).decode('utf-8'))
        except ValueError: continue

def sweep(log, fetch=None, people=None, today=None):
    today = today or datetime.date.today()
    P = load_prepare()
    core = json.loads((ROOT/'data'/'cricket.json').read_text(encoding='utf-8')); det = P.read_details()
    src = P.unprepare(core, det); PSF = src['psFields']
    # the archive must come back through the converter unchanged, or a merge could not be trusted
    if P.prepare(copy.deepcopy(src)) != (core, det):
        raise SystemExit('data/cricket.json does not come back unchanged through tools/prepare_cricket.py — the converter and the archive disagree; nothing written')
    log.append('Round trip: the archive comes back unchanged through prepare_cricket.py.')
    have = {g['id']: i for i, g in enumerate(src['games'])}
    days = 7 if (today - datetime.date.fromisoformat(src['lastDate'])).days <= 5 else 30
    log.append(f'Archive through {src["lastDate"]}; reading the matches Cricsheet added in the last {days} days.'); log.append('')
    matches = list((fetch or (lambda n: read_matches(fetch_zip(n))))(days))
    new, refreshed, affected = [], 0, set(); names_all, teams_all = {}, {}
    for mid, m in matches:
        c = convert(m, mid)
        if not c: continue
        game, names, team_of, (venue, city) = c
        game['v'] = venue_id(src, venue, city)
        names_all.update(names); teams_all.update({p: (t, game['g']) for p, t in team_of.items()})
        if game['id'] in have:
            old = src['games'][have[game['id']]]
            if json.dumps(old, sort_keys=True) == json.dumps(game, sort_keys=True): continue
            src['games'][have[game['id']]] = game; refreshed += 1
        else: new.append(game)
        affected.add((game['y'], game['f'], game['g']))
        log.append(f'- {"re-read" if game["id"] in have else "**added**"}: {game["date"]} {game["g"]} {game["f"]} {" v ".join(game["teams"])} — {game["winner"] + " by " + game["margin"] if game["winner"] else game["result"]}')
    if not new and not refreshed: log.append('- nothing new'); return
    games = src['games'] + new
    order = {id(g): i for i, g in enumerate(games)}
    src['games'] = sorted(games, key=lambda g: (g['date'], order[id(g)]))
    # a side the archive has never met (an associate's first international) gets a register entry of its own
    import colorsys
    for g in new:
        for t in g['teams']:
            if t not in src['teams']:
                h = int(hashlib.sha1(t.encode('utf-8')).hexdigest()[:6], 16) / 0xffffff
                col = lambda l, s_: '#%02x%02x%02x' % tuple(int(v * 255) for v in colorsys.hls_to_rgb(h, l, s_))
                src['teams'][t] = {'n': t, 'abbr': ''.join(w[0] for w in t.split()[:3]).upper() if ' ' in t else t[:3].upper(), 'c': col(.55, .6), 'c2': col(.7, .35), 'flag': '', 'major': False}
                log.append(f'- new side in the register: {t}')
    # players: new ones into the register, new teams onto known ones
    P_ = src['players']; missing = [p for p in names_all if p not in P_]
    reg = (people or fetch_people)() if missing else {}
    for p in missing:
        n = names_all[p]; P_[p] = {'n': n, 'short': n, 'espn': (reg.get(p) or {}).get('key_cricinfo', '') or '', 'teams': [], 'gender': []}
    for p, (t, gd) in teams_all.items():
        if p in P_:
            if t not in P_[p]['teams']: P_[p]['teams'].append(t)
            if gd not in P_[p]['gender']: P_[p]['gender'].append(gd)
    if missing: log.append(f'- {len(missing)} new players ({", ".join(names_all[p] for p in missing[:6])}{" …" if len(missing) > 6 else ""})')
    # player-season figures for every season a new game touches, recomputed from all its scorecards
    rows = season_rows([g for g in src['games'] if (g['y'], g['f'], g['g']) in affected], PSF)
    kept = []; seen = set()
    for r in src['ps']:
        k = tuple(r[:5])
        if (k[0], k[1], k[2]) in affected:
            if k in rows: kept.append(rows[k]); seen.add(k)
        else: kept.append(r)
    kept += [r for k, r in rows.items() if k not in seen]
    src['ps'] = kept
    # coverage
    G = src['games']; cov = src['coverage']
    cov.update(matches=len(G), detailed=sum(1 for g in G if g.get('detail')), historicOnly=sum(1 for g in G if not g.get('detail')), players=len(P_), venues=len(src['venues']), added=cov.get('added', 0) + len(new))
    for sc in cov.get('scope', []):
        mine = [g for g in G if g['g'] == sc['g'] and g['f'] == sc['f']]
        if mine: sc.update(n=len(mine), detail=sum(1 for g in mine if g.get('detail')), end=max(g['date'] for g in mine))
    src['lastDate'] = max(g['date'] for g in G); src['snapshot'] = today.isoformat()
    core2, det2 = P.prepare(src)
    P.write(core2, det2)
    log += ['', f'Archive now {len(G):,} internationals ({len(new)} added, {refreshed} re-read), through {src["lastDate"]}.']
