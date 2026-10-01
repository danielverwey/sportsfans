"""Bring the World Cup archive into the site.

  python3 tools/prepare_worldcup.py [build/harvest/worldcup]

Reads three open sources kept in that folder (fetched from GitHub when missing — `python3 tools/prepare_worldcup.py --fetch`):
  · the Fjelstul World Cup Database (CC BY-SA 4.0): matches, goals, line-ups, squads, bookings, substitutions, penalty kicks,
    referees, managers, awards, standings, stadiums and teams for every men's World Cup 1930–2022 and women's 1991–2019;
  · OpenFootball's worldcup.json (CC0) for the tournaments the database does not hold yet (2026): every match with its score after extra time, penalties
    and goalscorers, and from the full file its line-ups, substitutions, bookings, shoot-out kicks and referees;
  · Daniel's consolidated ledger (world_cup_complete_history.json) for the 2023 Women's World Cup, read from Wikipedia (CC BY-SA 4.0).
Writes data/worldcup.json: the tournaments with their hosts, standings, group tables and awards; every match as a row with its
sheet (goals, line-ups, cards, substitutions, shoot-outs) where the source holds one; the players, squads, stadiums, referees
and managers; the final of every tournament placed on the Natural Earth silhouette. Nothing in the record is altered; names
of teams are joined across the sources (tools/worldcup_common.py ALIASES) and the 2026 stadium names are the editor's.
"""
import json, re, sys, pathlib, collections, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0, str(ROOT/'tools'/'harvest'))
from worldcup_common import stage_code, STAGE_ORDER, team_name, slug, person_name, read_csv, FINALS, CAPITALS, GROUNDS_2026, CITY_COUNTRY_2023, HOSTS_KNOWN, points_rule, minute_of, openfootball_matches

HARVEST = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else ROOT/'build'/'harvest'/'worldcup'
FJELSTUL = 'https://raw.githubusercontent.com/jfjelstul/worldcup/master/data-csv/'
TABLES = ['matches', 'goals', 'players', 'squads', 'bookings', 'substitutions', 'penalty_kicks', 'referee_appearances', 'manager_appearances', 'award_winners', 'tournament_standings', 'group_standings', 'host_countries', 'tournaments', 'stadiums', 'teams', 'player_appearances']

def table(name):
    p = HARVEST/f'{name}.csv'
    if not p.exists() or '--fetch' in sys.argv:
        from common import get
        HARVEST.mkdir(parents=True, exist_ok=True); p.write_bytes(get(FJELSTUL + f'{name}.csv', pause=0.3))
    return read_csv(p.read_text(encoding='utf-8'))
def na(v): return None if v in ('', 'not applicable', 'not available', None) else v

T = {t['tournament_id']: t for t in table('tournaments')}
hosts_of = collections.defaultdict(list)
for h in table('host_countries'): hosts_of[h['tournament_id']].append(team_name(h['team_name']))
sex_of = lambda tid: 'W' if "Women" in T[tid]['tournament_name'] else 'M'
tkey = lambda tid: f'{sex_of(tid)}{T[tid]["year"]}'

# ---- teams
teams = {}
for r in table('teams'):
    teams[team_name(r['team_name'])] = {'code': r['team_code'], 'conf': na(r['confederation_code']), 'region': na(r['region_name']), 'm': r['mens_team'] == '1', 'w': r['womens_team'] == '1',
                                        'wiki': na(r['mens_team_wikipedia_link']), 'wikiW': na(r['womens_team_wikipedia_link'])}
NEW_TEAMS = {'Curaçao': ('CUW', 'CONCACAF', 'North America'), 'Cape Verde': ('CPV', 'CAF', 'Africa'), 'Jordan': ('JOR', 'AFC', 'Asia'), 'DR Congo': ('COD', 'CAF', 'Africa'), 'Uzbekistan': ('UZB', 'AFC', 'Asia'), 'Philippines': ('PHL', 'AFC', 'Asia'), 'Vietnam': ('VNM', 'AFC', 'Asia'), 'Zambia': ('ZMB', 'CAF', 'Africa'), 'Haiti': ('HTI', 'CONCACAF', 'North America'), 'Panama': ('PAN', 'CONCACAF', 'North America')}
def team(name, sex):
    n = team_name(name)
    if n not in teams:
        code, conf, region = NEW_TEAMS.get(n, (None, None, None))
        teams[n] = {'code': code, 'conf': conf, 'region': region, 'm': sex == 'M', 'w': sex == 'W', 'wiki': None, 'wikiW': None}
    teams[n]['m' if sex == 'M' else 'w'] = True
    return n

# ---- people
players = {}
for r in table('players'):
    pos = ''.join(c for c, k in (('G', 'goal_keeper'), ('D', 'defender'), ('M', 'midfielder'), ('F', 'forward')) if r[k] == '1')
    players[r['player_id']] = {'n': person_name(r['given_name'], r['family_name']), 'g': na(r['given_name']) or '', 'f': na(r['family_name']) or '', 'b': na(r['birth_date']), 'w': r['female'] == '1', 'pos': pos, 'wiki': na(r['player_wikipedia_link']), 't': []}
referees = {}; managers = {}
ref_of = {}; man_of = collections.defaultdict(dict)
for r in table('referee_appearances'):
    referees[r['referee_id']] = {'n': person_name(r['given_name'], r['family_name']), 'c': na(r['country_name'])}; ref_of[r['match_id']] = r['referee_id']
for r in table('manager_appearances'):
    managers[r['manager_id']] = {'n': person_name(r['given_name'], r['family_name']), 'c': na(r['country_name'])}; man_of[r['match_id']][team_name(r['team_name'])] = r['manager_id']

# ---- stadiums
stadiums = {}
for r in table('stadiums'):
    stadiums[r['stadium_id']] = {'name': r['stadium_name'], 'city': r['city_name'], 'country': team_name(r['country_name']), 'cap': int(r['stadium_capacity']) if na(r['stadium_capacity']) and r['stadium_capacity'].isdigit() else None, 'wiki': na(r['stadium_wikipedia_link'])}
by_stadium_name = {(s['name'], s['city']): sid for sid, s in stadiums.items()}
def stadium(name, city, country, prefix):
    k = (name, city)
    if k in by_stadium_name: return by_stadium_name[k]
    sid = f'{prefix}-{len([x for x in stadiums if x.startswith(prefix)]) + 1:02d}'
    stadiums[sid] = {'name': name, 'city': city, 'country': country, 'cap': None, 'wiki': None}; by_stadium_name[k] = sid; return sid

# ---- matches (Fjelstul)
MF = ['id', 't', 'y', 'sex', 'date', 'time', 'stage', 'group', 'stadium', 'home', 'away', 'hs', 'as', 'et', 'ph', 'pa', 'replay', 'winner', 'ref', 'mh', 'ma', 'src']
matches = []; details = {}
def winner_of(hs, as_, ph, pa):
    if hs != as_: return 'h' if hs > as_ else 'a'
    if ph is not None and pa is not None and ph != pa: return 'h' if ph > pa else 'a'
    return None
for r in table('matches'):
    tid = r['tournament_id']; sex = sex_of(tid); y = int(T[tid]['year'])
    hs, as_ = int(r['home_team_score']), int(r['away_team_score'])
    ph, pa = (int(r['home_team_score_penalties']), int(r['away_team_score_penalties'])) if r['penalty_shootout'] == '1' else (None, None)
    st = stage_code(r['stage_name'])
    assert st, r['stage_name']
    gname = na(r['group_name'])
    mid = r['match_id']
    matches.append([mid, tkey(tid), y, sex, r['match_date'], na(r['match_time']), st, gname, r['stadium_id'], team(r['home_team_name'], sex), team(r['away_team_name'], sex), hs, as_, r['extra_time'] == '1', ph, pa,
                    'replayed' if r['replayed'] == '1' else 'replay' if r['replay'] == '1' else '', winner_of(hs, as_, ph, pa), ref_of.get(mid), man_of[mid].get(team_name(r['home_team_name'])), man_of[mid].get(team_name(r['away_team_name'])), 'fjelstul'])
    details[mid] = {'g': [], 'l': None, 'b': [], 's': [], 'p': []}
side = lambda r: 1 if r['home_team'] == '1' else 0
PERIOD = {'first half': 1, 'first half, stoppage time': 1, 'second half': 2, 'second half, stoppage time': 2, 'extra time, first half': 3, 'extra time, first half, stoppage time': 3, 'extra time, second half': 4, 'extra time, second half, stoppage time': 4}
for r in table('goals'):
    m, s = minute_of(r['minute_label'], r['minute_regulation'], r['minute_stoppage'])
    details[r['match_id']]['g'].append([side(r), r['player_id'], m, s, r['own_goal'] == '1', r['penalty'] == '1', PERIOD.get(r['match_period'], 0)])
lineups = collections.defaultdict(lambda: {'h': [], 'a': []})
for r in table('player_appearances'):
    lineups[r['match_id']]['h' if r['home_team'] == '1' else 'a'].append([r['player_id'], int(r['shirt_number']) if r['shirt_number'].isdigit() else None, na(r['position_code']) or '', r['starter'] == '1'])
for mid, l in lineups.items(): details[mid]['l'] = l
for r in table('bookings'):
    m, s = minute_of(r['minute_label'], r['minute_regulation'], r['minute_stoppage'])
    details[r['match_id']]['b'].append([side(r), r['player_id'], m, s, 'R' if r['red_card'] == '1' else 'Y2' if r['second_yellow_card'] == '1' else 'Y'])
subs = collections.defaultdict(dict)
for r in table('substitutions'):
    m, s = minute_of(r['minute_label'], r['minute_regulation'], r['minute_stoppage'])
    k = (r['match_id'], side(r), m, s); e = subs[k]
    (e.setdefault('off', []) if r['going_off'] == '1' else e.setdefault('on', [])).append(r['player_id'])
for (mid, sd, m, s), e in subs.items():
    offs, ons = e.get('off', []), e.get('on', [])
    for i in range(max(len(offs), len(ons))): details[mid]['s'].append([sd, offs[i] if i < len(offs) else None, ons[i] if i < len(ons) else None, m, s])
for r in table('penalty_kicks'):
    details[r['match_id']]['p'].append([side(r), r['player_id'], r['converted'] == '1'])
for mid in details:
    details[mid]['g'].sort(key=lambda g: (g[6], g[2], g[3])); details[mid]['b'].sort(key=lambda b: (b[2], b[3])); details[mid]['s'].sort(key=lambda x: (x[3], x[4]))

# ---- squads and the players' tournaments
squads = collections.defaultdict(lambda: collections.defaultdict(list))
for r in table('squads'):
    tid = r['tournament_id']; squads[tkey(tid)][team_name(r['team_name'])].append([r['player_id'], int(r['shirt_number']) if r['shirt_number'].isdigit() and r['shirt_number'] != '0' else None, na(r['position_code']) or ''])
    if r['player_id'] in players and tkey(tid) not in players[r['player_id']]['t']: players[r['player_id']]['t'].append(tkey(tid))

# ---- tournaments from OpenFootball (CC0): scores after extra time, penalties, goalscorers by name, and the full file's sheets
import unicodedata
fold = lambda s: re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower())
played_for = collections.defaultdict(set)   # a scorer named only by the source is joined to a register entry who played for that team before (names compared without case or accents)
for tk, sq in squads.items():
    for tn, rows in sq.items():
        for pid, _, _ in rows: played_for[(tn, fold(players[pid]['n']))].add(pid)
minted = {}
def nice(name):
    """'Ferran TORRES' → 'Ferran Torres', 'Rodrigo DE PAUL' → 'Rodrigo De Paul': the source prints surnames in capitals."""
    return ' '.join(w.capitalize() if w.isupper() and len(w) > 1 else w for w in name.replace('-', '- ').split()).replace('- ', '-').strip()
def player_by_name(name, tn, sex):
    name = nice(name.strip())
    ids = played_for.get((tn, fold(name))) or set()
    if len(ids) == 1: return next(iter(ids))
    key = (tn, fold(name))
    if key not in minted:
        pid = 'X-' + slug(f'{name}-{tn}'); minted[key] = pid
        g, _, f = name.rpartition(' ')
        players[pid] = {'n': name, 'g': g, 'f': f or name, 'b': None, 'w': sex == 'W', 'pos': '', 'wiki': None, 't': []}
    return minted[key]
def add_openfootball(y, sex, of, FM):
    """One tournament from OpenFootball: the basic file for results and scorers, the full file (if any) for line-ups, cards, kicks and referees."""
    tk = f'{sex}{y}'; prefix = 'S-' + str(y)[2:] + ('W' if sex == 'W' else ''); n = 0
    for m in openfootball_matches(of, y, sex):
        mid = f'M-{y}-{m["num"]:02d}'; st = stage_code(m['round']); assert st, m['round']
        ground = GROUNDS_2026.get(m['ground'] or '', (m['ground'] or 'Unknown', (m['ground'] or '').split(' (')[0], None)) if y == 2026 else ((m['ground'] or 'Unknown').split(', ')[0], (m['ground'] or '').split(', ')[-1], None)
        sid = stadium(ground[0], ground[1], ground[2], prefix)
        home, away = team(m['home'], sex), team(m['away'], sex)
        ph, pa = (m['pens'][0], m['pens'][1]) if m['pens'] else (None, None)
        matches.append([mid, tk, y, sex, m['date'], m['time'], st, (m['group'] or None), sid, home, away, m['hs'], m['as'], m['et'], ph, pa, '', winner_of(m['hs'], m['as'], ph, pa), None, None, None, 'openfootball'])
        d = details[mid] = {'g': [], 'l': None, 'b': [], 's': [], 'p': []}
        squads[tk][home]; squads[tk][away]
        for sd, g in m['goals']:
            tn = home if sd == 1 else away; mm, ss = minute_of(g.get('minute'))
            own = bool(g.get('owngoal')); scorer_team = (away if sd == 1 else home) if own else tn
            pid = player_by_name(g.get('name', '').strip(), scorer_team, sex)
            if tk not in players[pid]['t']: players[pid]['t'].append(tk)
            period = 1 if mm <= 45 else 2 if mm <= 90 else 3 if mm <= 105 else 4
            d['g'].append([sd, pid, mm, ss, own, bool(g.get('penalty')), period])
        d['g'].sort(key=lambda g: (g[6], g[2], g[3])); n += 1
    # the full file: line-ups, substitutions, bookings, shoot-out kicks and referees; names printed with surnames in capitals
    if FM:
        by26 = {(r[4], r[9], r[10]): r for r in matches if r[1] == tk}; n_full = 0
        for fm in FM:
            home, away = team_name(fm.get('team1')), team_name(fm.get('team2')); r = by26.get((fm.get('date'), home, away))
            if r is None: continue
            mid = r[0]; d = details[mid]; n_full += 1
            lu = fm.get('lineup') or []
            if len(lu) == 2:
                d['l'] = {'h': [], 'a': []}
                for sd, side_, tn in ((1, 'h', home), (0, 'a', away)):
                    L = lu[0 if sd == 1 else 1]; ons = {nice(x['on']): x for x in L.get('subs', []) if x.get('on')}
                    for pz in L.get('starter', []): d['l'][side_].append([player_by_name(pz['name'], tn, sex), None, '', True])
                    for pz in L.get('bench', []):
                        if nice(pz['name']) in ons: d['l'][side_].append([player_by_name(pz['name'], tn, sex), None, '', False])
                    for x in L.get('subs', []):
                        mm, ss = minute_of(x.get('minute')); d['s'].append([sd, player_by_name(x['off'], tn, sex) if x.get('off') else None, player_by_name(x['on'], tn, sex) if x.get('on') else None, mm, ss])
                    for pid, *_ in d['l'][side_]:
                        if tk not in players[pid]['t']: players[pid]['t'].append(tk)
                        if not any(q[0] == pid for q in squads[tk][tn]): squads[tk][tn].append([pid, None, ''])
                d['s'].sort(key=lambda x: (x[3], x[4]))
            bk = fm.get('bookings') or []
            if len(bk) == 2:
                for sd, tn, rows in ((1, home, bk[0]), (0, away, bk[1])):
                    for b in rows:
                        mm, ss = minute_of(b.get('minute')); d['b'].append([sd, player_by_name(b['name'], tn, sex), mm, ss, {'Y': 'Y', 'Y/R': 'Y2', 'R': 'R'}.get(b.get('type'), 'Y')])
                d['b'].sort(key=lambda b: (b[2], b[3]))
            if fm.get('referees'):
                rf = fm['referees'][0]; rid = 'R-OF-' + slug(nice(rf['name']))
                referees.setdefault(rid, {'n': nice(rf['name']), 'c': rf.get('country')}); r[18] = rid
            if fm.get('penalties') and r[14] is not None:
                names_h = {fold(nice(pz['name'])) for L in lu[:1] for pz in L.get('starter', []) + L.get('bench', [])}
                for k in fm['penalties']:
                    tn = home if fold(nice(k['name'])) in names_h else away
                    d['p'].append([1 if tn == home else 0, player_by_name(k['name'], tn, sex), k.get('note') != 'missed'])
            if fm.get('attendance'): r[21] = 'openfootball'
        print(f'{tk}: line-ups, cards and referees from the full OpenFootball file for {n_full} matches')
    for tn in list(squads.get(tk, {})):
        if not squads[tk][tn]: del squads[tk][tn]
    return n
# every OpenFootball file in the harvest folder: openfootball-<year>.json (men) or openfootball-w-<year>.json (women), with -full beside it when published;
# a year the Fjelstul database already holds is left to the database
held_years = {(sex_of(tid), int(T[tid]['year'])) for tid in T}
for f in sorted(HARVEST.glob('openfootball-*.json')):
    mm = re.match(r'openfootball-(w-)?(\d{4})\.json$', f.name)
    if not mm: continue
    sex_, y_ = ('W' if mm.group(1) else 'M'), int(mm.group(2))
    if (sex_, y_) in held_years: continue
    doc = json.loads(f.read_text(encoding='utf-8')); fullp = f.with_name(f.name.replace('.json', '-full.json'))
    FM_ = json.loads(fullp.read_text(encoding='utf-8'))['matches'] if fullp.exists() else None
    n_ = add_openfootball(y_, sex_, doc, FM_); print(f'{sex_}{y_}: {n_} matches from OpenFootball')

# ---- 2023 Women's World Cup from the ledger (Wikipedia): results, stages, grounds; no scorers
ledger = json.loads((HARVEST/'world_cup_complete_history.json').read_text(encoding='utf-8'))
w23 = sorted([m for m in ledger['matches'] if m['gender'] == 'women' and m['year'] == 2023], key=lambda m: (m['date'], m.get('timeLocal') or ''))
for i, m in enumerate(w23, 1):
    mid = f'M-2023-{i:02d}'; st = stage_code(m['stage']); assert st, m['stage']
    city = m.get('city') or ''; sid = stadium(m.get('venue') or 'Unknown', city, CITY_COUNTRY_2023.get(city), 'S-W23') if m.get('venue') else None
    home, away = team(m['homeTeam']['name'], 'W'), team(m['awayTeam']['name'], 'W')
    ps = m.get('penaltyShootout'); ph, pa = (ps['home'], ps['away']) if ps else (None, None)
    hs, as_ = m['score']['home'], m['score']['away']
    matches.append([mid, 'W2023', 2023, 'W', m['date'], m.get('timeLocal'), st, m.get('group'), sid, home, away, hs, as_, bool(m.get('extraTime')), ph, pa, '', winner_of(hs, as_, ph, pa), None, None, None, 'ledger'])
    details[mid] = {'g': [], 'l': None, 'b': [], 's': [], 'p': []}

# ---- tournaments: hosts, standings, group tables, awards, the final on the map
rows_of = collections.defaultdict(list)
for r in matches: rows_of[r[1]].append(r)
standings = collections.defaultdict(dict)
for r in table('tournament_standings'): standings[tkey(r['tournament_id'])][int(r['position'])] = team_name(r['team_name'])
fj_groups = collections.defaultdict(lambda: collections.defaultdict(dict))
for r in table('group_standings'):
    st = stage_code(r['stage_name'])
    if st in ('group', 'group2', 'final-round'): fj_groups[tkey(r['tournament_id'])][(st, na(r['group_name']) or 'Final round')][team_name(r['team_name'])] = (int(r['position']), r['advanced'] == '1')
awards = collections.defaultdict(list)
for r in table('award_winners'): awards[tkey(r['tournament_id'])].append([r['award_name'], r['player_id'], team_name(r['team_name']), r['shared'] == '1'])
def group_tables(tk, rows, sex, y):
    pts = points_rule(sex, y); tables = []
    knock = {r[9] for r in rows if r[6] in ('r32', 'r16', 'qf', 'sf', '3rd', 'final')} | {r[10] for r in rows if r[6] in ('r32', 'r16', 'qf', 'sf', '3rd', 'final')}
    later = {'group': {r[9] for r in rows if r[6] in ('group2', 'final-round')} | {r[10] for r in rows if r[6] in ('group2', 'final-round')} | knock, 'group2': knock, 'final-round': set()}
    for st in ('group', 'group2', 'final-round'):
        grp = collections.defaultdict(list)
        for r in rows:
            if r[6] == st and r[16] != 'replayed': grp[r[7] or ('Final round' if st == 'final-round' else 'Group')].append(r)
        for gname, ms in grp.items():
            t = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0, 0])   # P W D L GF GA Pts
            for r in ms:
                for tn, gf, ga in ((r[9], r[11], r[12]), (r[10], r[12], r[11])):
                    x = t[tn]; x[0] += 1; x[4] += gf; x[5] += ga
                    if gf > ga: x[1] += 1; x[6] += pts
                    elif gf == ga: x[2] += 1; x[6] += 1
                    else: x[3] += 1
            fj = fj_groups.get(tk, {}).get((st, gname))
            order = sorted(t, key=lambda tn: (fj[tn][0] if fj and tn in fj else 99, -t[tn][6], -(t[tn][4] - t[tn][5]), -t[tn][4], tn))
            adv = {tn: (fj[tn][1] if fj and tn in fj else tn in later[st]) for tn in order}
            tables.append({'stage': st, 'name': gname, 'table': [[tn] + t[tn] + [adv[tn]] for tn in order]})
    tables.sort(key=lambda g: (STAGE_ORDER.index(g['stage']), g['name']))
    return tables
tournaments = []
for tk in sorted(rows_of, key=lambda k: (int(k[1:]), k[0])):
    rows = sorted(rows_of[tk], key=lambda r: (r[4], r[5] or '', r[0])); sex, y = tk[0], int(tk[1:])
    fj = next((t for t in T.values() if tkey(t['tournament_id']) == tk), None)
    final = next((r for r in reversed(rows) if r[6] == 'final'), None); third = next((r for r in reversed(rows) if r[6] == '3rd'), None)
    st = dict(standings.get(tk, {}))
    if not st and final:
        st[1] = final[9] if final[17] == 'h' else final[10]; st[2] = final[10] if final[17] == 'h' else final[9]
        if third and third[17]: st[3] = third[9] if third[17] == 'h' else third[10]; st[4] = third[10] if third[17] == 'h' else third[9]
    if not st and tk == 'M1950':   # the 1950 final round: Uruguay, Brazil, Sweden, Spain
        fr = group_tables(tk, rows, sex, y); st = {i + 1: row[0] for i, row in enumerate(fr[-1]['table'])} if fr else {}
    hosts = hosts_of.get(fj['tournament_id']) if fj else HOSTS_KNOWN.get(tk, [])
    tn_all = sorted({r[9] for r in rows} | {r[10] for r in rows})
    name = f'{y} Women’s World Cup' if sex == 'W' else f'{y} World Cup'
    stages = [s for s in STAGE_ORDER if any(r[6] == s for r in rows)]
    point = FINALS.get(tk) or next((CAPITALS[h] for h in hosts if h in CAPITALS), None)
    note = {'M1950': 'No final: a final round of four decided the title, and Uruguay beat Brazil in its last match at the Maracanã.', 'M1934': 'A straight knockout of sixteen; Italy beat Spain in a replay a day after a draw.', 'M1938': 'A straight knockout of fifteen after Austria withdrew; three first-round ties went to replays.',
            'M2002': 'The first World Cup with two hosts, South Korea and Japan.', 'M2026': 'Forty-eight teams, twelve groups and a round of 32 across the United States, Canada and Mexico.', 'W2023': 'Thirty-two teams across Australia and New Zealand.'}.get(tk, '')
    n_l = sum(1 for r in rows if details[r[0]]['l']); n_g = sum(len(details[r[0]]['g']) for r in rows)
    if rows[0][21] == 'openfootball': note = (note + ' ' if note else '') + ('The record as OpenFootball holds it' + (' — results, scorers, line-ups and cards.' if n_l else ' — results and scorers named, no line-ups.') if n_g else 'The record as OpenFootball holds it — results only.')
    elif rows[0][21] == 'ledger': note = (note + ' ' if note else '') + 'The record as Wikipedia’s group and knockout pages hold it — results, no scorers.'
    tournaments.append({'id': tk, 'sex': sex, 'y': y, 'name': name, 'source': fj['tournament_name'] if fj else (f'{y} FIFA World Cup' if sex == 'M' else f'{y} FIFA Women’s World Cup'), 'hosts': hosts, 'start': rows[0][4], 'end': rows[-1][4],
                        'teams': tn_all, 'count': len(tn_all), 'winner': st.get(1), 'standings': [st.get(i) for i in (1, 2, 3, 4)], 'final': final[0] if final else None, 'points': points_rule(sex, y), 'stages': stages,
                        'groups': group_tables(tk, rows, sex, y), 'awards': awards.get(tk, []), 'point': point, 'note': note, 'src': rows[0][21], 'lineups': sum(1 for r in rows if details[r[0]]['l']), 'goals': sum(len(details[r[0]]['g']) for r in rows), 'matches': len(rows)})

# ---- colours: kit readings for the dark page; the rest take the Olympics palette or a hue in the atlas
oly = json.loads((ROOT/'data'/'olympics.json').read_text(encoding='utf-8'))
WC = {'Brazil': '#f2db50', 'Argentina': '#8ccef4', 'Germany': '#e6e9f0', 'West Germany': '#e6e9f0', 'Italy': '#6fa8e8', 'France': '#5c7fd6', 'England': '#f0f0f0', 'Spain': '#e8505b', 'Uruguay': '#9fd1ff', 'Netherlands': '#f6a455',
      'Portugal': '#c93d4a', 'Belgium': '#e9b457', 'Croatia': '#ef9ab0', 'Mexico': '#5dbf7a', 'United States': '#8e9eec', 'Sweden': '#f2db80', 'Hungary': '#9fd48a', 'Soviet Union': '#e0708a', 'Czechoslovakia': '#a0d6e8', 'Yugoslavia': '#d4b2ff',
      'Poland': '#f4a3a3', 'Austria': '#f29686', 'Japan': '#6d8fe0', 'South Korea': '#e5cfde', 'Norway': '#ed6676', 'China': '#e8756a', 'Colombia': '#f5d76e', 'Chile': '#d85a5a', 'Denmark': '#ff9a8b', 'Switzerland': '#ef9ab0', 'Russia': '#c9a0dc',
      'Cameroon': '#8fd1a4', 'Nigeria': '#9fd8a0', 'Senegal': '#a4e07a', 'Ghana': '#c7e86a', 'Morocco': '#e59a8f', 'Australia': '#77c7b2', 'Canada': '#f27664', 'Turkey': '#f0a0a0', 'Paraguay': '#d0a8b8', 'Peru': '#f0b8b8', 'Scotland': '#9fc9ff',
      'Wales': '#f28c6b', 'Northern Ireland': '#a2dcae', 'Republic of Ireland': '#8fd39a', 'East Germany': '#b194d5', 'Serbia': '#c9b2d8', 'Ukraine': '#9fc9ff', 'Ecuador': '#f5c98a', 'Costa Rica': '#d6e3a0', 'Saudi Arabia': '#a8e0c8', 'Iran': '#b9d6a3', 'Qatar': '#d0a0a0', 'South Africa': '#7fd39a', 'New Zealand': '#c9ccd1'}
colours = {**{k: v for k, v in oly.get('colours', {}).items() if k in teams}, **WC}

held = tournaments
core = {'tournaments': tournaments, 'teams': teams, 'matchFields': MF, 'matches': matches, 'details': details, 'players': players, 'squads': {tk: dict(v) for tk, v in squads.items()}, 'stadiums': stadiums, 'referees': referees, 'managers': managers,
        'colours': colours, 'map': oly['map'], 'stageLabel': {k: v for k, v in __import__('worldcup_common').STAGE_LABEL.items()},
        'sources': [{'name': 'The Fjelstul World Cup Database', 'url': 'https://github.com/jfjelstul/worldcup', 'licence': 'CC BY-SA 4.0', 'attribution': 'Joshua C. Fjelstul, Ph.D., The Fjelstul World Cup Database, © 2023 Joshua C. Fjelstul, Ph.D.', 'covers': 'men 1930–2022, women 1991–2019: matches, goals, line-ups, squads, bookings, substitutions, penalty kicks, referees, managers, awards, standings, stadiums'},
                    {'name': 'OpenFootball worldcup.json', 'url': 'https://github.com/openfootball/worldcup.json', 'licence': 'CC0 1.0', 'attribution': 'OpenFootball contributors', 'covers': '2026: every match with its score, extra time, penalties and goalscorers'},
                    {'name': 'Wikipedia', 'url': 'https://en.wikipedia.org/wiki/2023_FIFA_Women%27s_World_Cup', 'licence': 'CC BY-SA 4.0', 'attribution': 'Wikipedia contributors', 'covers': '2023 Women’s World Cup: results, stages and grounds, consolidated by Daniel’s ledger'},
                    {'name': 'Natural Earth', 'url': 'https://www.naturalearthdata.com/', 'licence': 'public domain', 'attribution': 'Natural Earth', 'covers': 'the land silhouette behind the map of finals'}],
        'licence': 'CC BY-SA 4.0', 'licenceUrl': 'https://creativecommons.org/licenses/by-sa/4.0/', 'retrieved': datetime.date.today().isoformat(), 'snapshot': datetime.date.today().isoformat(),
        'lastYear': {'M': max(t['y'] for t in tournaments if t['sex'] == 'M'), 'W': max(t['y'] for t in tournaments if t['sex'] == 'W')},
        'method': 'Every match of every World Cup as the sources record it: the Fjelstul World Cup Database for 1930–2022 (men) and 1991–2019 (women), with each match’s goals, line-ups, bookings, substitutions and shoot-out kicks where the database holds them (line-ups from 1970); OpenFootball for 2026, with scores after extra time, penalties and goalscorers; Wikipedia’s pages for the 2023 Women’s World Cup, with results only. Scores are after extra time; shoot-outs are kept apart. Group tables are computed from the results with the points rule of the year and ordered as the database ranks them; a team advanced if it played in the next stage. Replayed matches are kept with their replays. The final of every tournament is placed on the Natural Earth land silhouette at approximate coordinates; stadiums are listed, not drawn. Team names stay as the sources give them, joined across sources only where they are the same team under another spelling.'}
cov = {'tournaments': len(tournaments), 'men': sum(1 for t in tournaments if t['sex'] == 'M'), 'women': sum(1 for t in tournaments if t['sex'] == 'W'), 'matches': len(matches), 'goals': sum(len(d['g']) for d in details.values()),
       'withScorers': sum(1 for r in matches if details[r[0]]['g'] or (r[11] + r[12] == 0 and r[21] != 'ledger')), 'lineups': sum(1 for d in details.values() if d['l']), 'bookings': sum(len(d['b']) for d in details.values()), 'substitutions': sum(len(d['s']) for d in details.values()),
       'shootouts': sum(1 for r in matches if r[14] is not None), 'players': len(players), 'playersWithArticle': sum(1 for p in players.values() if p['wiki']), 'teams': len(teams), 'stadiums': len(stadiums), 'referees': len(referees), 'managers': len(managers), 'awards': sum(len(t['awards']) for t in tournaments), 'minted': len(minted)}
core['coverage'] = cov
out = ROOT/'data'/'worldcup.json'; out.write_text(json.dumps(core, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'worldcup: {cov["tournaments"]} tournaments ({cov["men"]} men’s, {cov["women"]} women’s) · {cov["matches"]:,} matches · {cov["goals"]:,} goals · {cov["lineups"]:,} line-ups · {cov["players"]:,} players · {cov["teams"]} teams · {cov["stadiums"]} stadiums · {cov["awards"]} awards · {cov["minted"]} players named only by a fixture source · {out.stat().st_size/1e6:.1f} MB')
