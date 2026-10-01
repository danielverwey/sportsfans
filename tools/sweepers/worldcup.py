"""World Cup: the archive's sources re-read from GitHub — the Fjelstul World Cup Database (CC BY-SA 4.0) for every tournament
it holds, OpenFootball (CC0) for the tournaments it does not hold yet — and the archive rebuilt from them by
tools/prepare_worldcup.py when either has something new. The reader first proves itself: the database's matches.csv must
reproduce the archive's latest database-sourced tournament, men's and women's (ids, teams, scores); if it does not, nothing is
written. Then: a tournament the database has published that the archive holds from a lesser source (or not at all) is taken
from the database; a tournament OpenFootball has started to fill (the next men's or women's World Cup) is added or completed.
Ids never move: the database's match ids are the archive's, and an OpenFootball tournament's ids follow its match numbers.
"""
import datetime, json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0, str(ROOT/'tools'/'harvest'))
from worldcup_common import read_csv, team_name, openfootball_matches

FJELSTUL = 'https://raw.githubusercontent.com/jfjelstul/worldcup/master/data-csv/'
TABLES = ['matches', 'goals', 'players', 'squads', 'bookings', 'substitutions', 'penalty_kicks', 'referee_appearances', 'manager_appearances', 'award_winners', 'tournament_standings', 'group_standings', 'host_countries', 'tournaments', 'stadiums', 'teams', 'player_appearances']
OPENFOOTBALL = 'https://raw.githubusercontent.com/openfootball/worldcup.json/master/'
WOMEN_PATHS = ['{y}--women/worldcup.json', '{y}/womens-worldcup.json', '{y}/womensworldcup.json', '{y}/women-worldcup.json']
HARVEST = ROOT/'build'/'harvest'/'worldcup'
AGREE = 0.9

def fetch(url, get):
    try: return get(url, pause=0.3)
    except Exception as e:
        if '404' in str(e): return None
        raise

def sweep(log, get=None, today=None):
    today = today or datetime.date.today()
    if get is None:
        from common import get
    path = ROOT/'data'/'worldcup.json'; A = json.loads(path.read_text(encoding='utf-8')); MF = A['matchFields']
    HARVEST.mkdir(parents=True, exist_ok=True)
    # 1. prove the reader on the latest database-sourced tournaments, one of each
    raw = fetch(FJELSTUL + 'matches.csv', get)
    if raw is None: raise SystemExit('the database’s matches.csv could not be read — nothing written')
    rows = read_csv(raw.decode('utf-8')); byid = {r['match_id']: r for r in rows}
    archive = [dict(zip(MF, r)) for r in A['matches']]
    checked = have = 0; bad = []
    for sex in ('M', 'W'):
        held = [m for m in archive if m['sex'] == sex and m['src'] == 'fjelstul']
        if not held: continue
        last = max(m['y'] for m in held)
        for m in held:
            if m['y'] != last: continue
            checked += 1; r = byid.get(m['id'])
            if r and team_name(r['home_team_name']) == m['home'] and team_name(r['away_team_name']) == m['away'] and int(r['home_team_score']) == m['hs'] and int(r['away_team_score']) == m['as']: have += 1
            else: bad.append(f'{m["id"]} {m["home"]} {m["hs"]}–{m["as"]} {m["away"]}: ' + (f'read {team_name(r["home_team_name"])} {r["home_team_score"]}–{r["away_team_score"]} {team_name(r["away_team_name"])}' if r else 'not in the database'))
    log.append(f'Check: the database reproduces {have} of the archive’s {checked} matches of its latest men’s and women’s tournaments ({have / max(checked, 1):.1%}).')
    if not checked or have / checked < AGREE:
        log += [f'  - {b}' for b in bad[:12]]
        raise SystemExit('the database did not read back as the archive holds it — the layout may have changed; nothing written')
    # 2. anything new in the database?
    traw = fetch(FJELSTUL + 'tournaments.csv', get); tours = read_csv(traw.decode('utf-8')) if traw else []
    tkey = lambda t: ('W' if 'Women' in t['tournament_name'] else 'M') + t['year']
    db_keys = {tkey(t) for t in tours}; have_db = {t['id'] for t in A['tournaments'] if t['src'] == 'fjelstul'}
    new_db = sorted(k for k in db_keys if k not in have_db and any(r['tournament_id'] == next(t['tournament_id'] for t in tours if tkey(t) == k) for r in rows))
    # 3. anything new (or newer) from OpenFootball for the next tournaments?
    changed_of = []
    for sex in ('M', 'W'):
        y = A['lastYear'][sex] + 4
        paths = [f'{y}/worldcup.json'] if sex == 'M' else [p.format(y=y) for p in WOMEN_PATHS]
        doc = None; used = None
        for p in paths:
            b = fetch(OPENFOOTBALL + p, get)
            if b: doc = json.loads(b.decode('utf-8')); used = p; break
        if doc is None: log.append(f'- {sex}{y}: no OpenFootball file yet'); continue
        ms = openfootball_matches(doc, y, sex)
        if not ms: log.append(f'- {sex}{y}: OpenFootball lists the fixtures but no results yet ({len(doc.get("matches", []))} matches scheduled)'); continue
        name = f'openfootball-{"w-" if sex == "W" else ""}{y}.json'; old = (HARVEST/name).read_bytes() if (HARVEST/name).exists() else None
        (HARVEST/name).write_bytes(b)
        fb = fetch(OPENFOOTBALL + used.replace('.json', '-full.json'), get)
        fullname = name.replace('.json', '-full.json'); oldfull = (HARVEST/fullname).read_bytes() if (HARVEST/fullname).exists() else None
        if fb: (HARVEST/fullname).write_bytes(fb)
        if old != b or (fb and oldfull != fb): changed_of.append(f'{sex}{y}: {len(ms)} matches with results' + (' and the full sheets' if fb else ''))
        else: log.append(f'- {sex}{y}: OpenFootball unchanged ({len(ms)} matches with results)')
    # 4. the lesser-sourced tournaments the archive holds (OpenFootball, the ledger) are re-read every time, to complete them
    for sex in ('M', 'W'):
        for t in A['tournaments']:
            if t['sex'] != sex or t['src'] == 'fjelstul' or t['id'] in new_db: continue
            y = t['y']; paths = [f'{y}/worldcup.json'] if sex == 'M' else [p.format(y=y) for p in WOMEN_PATHS]
            for p in paths:
                b = fetch(OPENFOOTBALL + p, get)
                if not b: continue
                name = f'openfootball-{"w-" if sex == "W" else ""}{y}.json'; old = (HARVEST/name).read_bytes() if (HARVEST/name).exists() else None
                fb = fetch(OPENFOOTBALL + p.replace('.json', '-full.json'), get); fullname = name.replace('.json', '-full.json'); oldfull = (HARVEST/fullname).read_bytes() if (HARVEST/fullname).exists() else None
                if old != b or (fb and oldfull != fb):
                    (HARVEST/name).write_bytes(b)
                    if fb: (HARVEST/fullname).write_bytes(fb)
                    changed_of.append(f'{sex}{y}: OpenFootball updated')
                break
    if not new_db and not changed_of: log.append('- nothing new'); return
    # 5. rebuild from the sources: every database table refreshed, then prepare
    for name in TABLES:
        b = fetch(FJELSTUL + name + '.csv', get)
        if b is None: raise SystemExit(f'the database’s {name}.csv could not be read — nothing written')
        (HARVEST/f'{name}.csv').write_bytes(b)
    for k in new_db: log.append(f'- **{k}** published by the database' + (' (replaces the OpenFootball/ledger record)' if any(t['id'] == k for t in A['tournaments']) else ''))
    for c in changed_of: log.append(f'- {c}')
    r = subprocess.run([sys.executable, str(ROOT/'tools'/'prepare_worldcup.py'), str(HARVEST)], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0: raise SystemExit('prepare_worldcup.py failed: ' + (r.stderr or r.stdout)[-1500:])
    log += ['', '```', r.stdout.strip()[-1200:], '```']
    B = json.loads(path.read_text(encoding='utf-8')); B['snapshot'] = B['retrieved'] = today.isoformat(); path.write_text(json.dumps(B, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    log.append(f'\nArchive now {B["coverage"]["tournaments"]} tournaments, {B["coverage"]["matches"]:,} matches, through {B["lastYear"]["M"]} (men) and {B["lastYear"]["W"]} (women).')
