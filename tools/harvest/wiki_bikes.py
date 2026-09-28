#!/usr/bin/env python3
"""Clean-room MotoGP (premier class) and World Superbike archives from Wikipedia.

Sources: each season article's riders' standings grid (one row per rider, one column per race, the
finishing position in every cell, points at the end) and its calendar table; and, where they exist,
the race articles with full classifications. Text and tables are CC BY-SA 4.0; the results are facts.
Nothing is taken from the championships' own sites.

    python tools/harvest/wiki_bikes.py motogp [--from 1949] [--to 2026] [--out build/harvest]
    python tools/harvest/wiki_bikes.py sbk

Runs where the network is open (GitHub Actions). Writes <out>/<sport>.json in the archive shape the
atlases read (seasons → races → rows; drivers = riders; teams = makers) plus a coverage report that
says, season by season, how many rows came from full classifications and how many from the grid.
Every request goes through the MediaWiki API with a descriptive User-Agent and a pause between calls.
"""
import sys, re, json, datetime, argparse, html, pathlib, collections, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import get_json, report, today_long, ROOT
try:
    from bs4 import BeautifulSoup
except ImportError:
    print('pip install beautifulsoup4 lxml'); sys.exit(2)

API = 'https://en.wikipedia.org/w/api.php'
def parse_page(title):
    j = get_json(API + '?' + '&'.join(['action=parse', 'prop=text', 'format=json', 'formatversion=2', 'redirects=1', 'page=' + title.replace(' ', '_')]), pause=1.0)
    if 'error' in j: return None
    return BeautifulSoup(j['parse']['text'], 'lxml')

# ---------- points tables (only used for rows that come from a standings grid; published totals are kept as they are)
def points_motogp(year, sprint=False):
    if sprint: return [12, 9, 7, 6, 5, 4, 3, 2, 1]
    if year == 1949: return [10, 8, 7, 6, 5]
    if year <= 1968: return [8, 6, 4, 3, 2, 1]
    if year <= 1987: return [15, 12, 10, 8, 6, 5, 4, 3, 2, 1]
    if year <= 1991: return [20, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    if year == 1992: return [20, 15, 12, 10, 8, 6, 4, 3, 2, 1]
    return [25, 20, 16, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
def points_sbk(year, sprint=False):
    if sprint: return [12, 9, 7, 6, 5, 4, 3, 2, 1]
    if year <= 1992: return [20, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    return [25, 20, 16, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

slug = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
MONTHS = {m: i for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'], 1)}
def iso_date(txt, year):
    """'4 June', '4–6 June', 'June 4', '4 June 1962' → '1962-06-04' (the last day of a range is the race day); otherwise the text as given."""
    t = txt.replace('\u2013', '-').replace('\u2014', '-')
    m = re.search(r'(\d{1,2})(?:\s*-\s*(\d{1,2}))?\s+([A-Za-z]+)(?:\s+(\d{4}))?', t) or re.search(r'([A-Za-z]+)\s+(\d{1,2})(?:\s*-\s*(\d{1,2}))?(?:,?\s+(\d{4}))?', t)
    if not m: return txt
    g = m.groups()
    if g[0].isdigit(): d1, d2, mon, yr = g
    else: mon, d1, d2, yr = g
    mi = MONTHS.get(mon.lower()) or next((v for k, v in MONTHS.items() if k.startswith(mon.lower()[:3])), None)
    if not mi: return txt
    day = int(d2 or d1); y = int(yr) if yr else year
    try: return datetime.date(y, mi, day).isoformat()
    except ValueError: return txt
def clean(cell):
    for sup in cell.find_all(['sup', 'style']): sup.decompose()
    return re.sub(r'\s+', ' ', cell.get_text(' ', strip=True)).strip()
def link_title(cell):
    a = cell.find('a', href=True)
    if a and a['href'].startswith('/wiki/') and 'redlink' not in a['href']: return html.unescape(a['href'][6:].split('#')[0].replace('_', ' '))
    return None

NON = {'RET': 'Retired', 'DNS': 'Did not start', 'DNQ': 'Did not qualify', 'DNPQ': 'Did not qualify', 'DSQ': 'Disqualified', 'DQ': 'Disqualified', 'WD': 'Did not start', 'NC': 'Not classified', 'EX': 'Disqualified', 'DNA': None, 'C': None, '': None, '–': None, '—': None}
def cell_result(txt):
    """A standings-grid cell → (position or None, status, label)."""
    t = txt.replace('†', '').strip().upper()
    if re.fullmatch(r'\d+', t): p = int(t); return p, 'Finished', str(p)
    if t in NON: st = NON[t]; return (None, None, None) if st is None else (None, st, {'Retired': 'R', 'Did not start': 'W', 'Did not qualify': 'W', 'Disqualified': 'D', 'Not classified': 'NC'}[st])
    return None, None, None

def find_table(soup, must_have, prefer_headings=()):
    """The first wikitable whose header cells include every string in must_have (case-insensitive), preferring the one under a heading in prefer_headings."""
    cands = []
    for t in soup.find_all('table', class_=re.compile('wikitable')):
        head = ' '.join(clean(th).lower() for th in t.find_all('th')[:40])
        if all(m.lower() in head for m in must_have):
            h = t.find_previous(['h2', 'h3', 'h4']); ht = clean(h).lower() if h else ''
            score = max((i for i, p in enumerate(prefer_headings) if p.lower() in ht), default=-1)
            cands.append((score, t))
    if not cands: return None
    cands.sort(key=lambda c: -c[0]); return cands[0][1]

def grid_rows(table):
    """Expand rowspans/colspans of a wikitable into a plain matrix of cells (BeautifulSoup tags)."""
    matrix = []; pending = {}
    for tr in table.find_all('tr'):
        row = []; col = 0
        cells = tr.find_all(['th', 'td'], recursive=False)
        ci = 0
        while ci < len(cells) or col in pending:
            if col in pending:
                cell, left = pending[col]; row.append(cell)
                if left > 1: pending[col] = (cell, left - 1)
                else: del pending[col]
                col += 1; continue
            cell = cells[ci]; ci += 1; rs = int(cell.get('rowspan', 1) or 1); cs = int(cell.get('colspan', 1) or 1)
            for k in range(cs):
                row.append(cell)
                if rs > 1: pending[col] = (cell, rs - 1)
                col += 1
        matrix.append(row)
    return matrix

# ---------- season page
def season_titles(sport, year):
    if sport == 'motogp': return [f'{year} Grand Prix motorcycle racing season', f'{year} Grand Prix motorcycle racing world championship']
    return [f'{year} Superbike World Championship', f'{year} Superbike World Championship season']

def harvest_season(sport, year, log):
    soup = None
    for t in season_titles(sport, year):
        soup = parse_page(t)
        if soup: break
    if soup is None: log.append(f'- {year}: season article not found'); return None
    cls = 'motogp' if (sport == 'motogp' and year >= 2002) else ('500cc' if sport == 'motogp' else 'riders')
    st = find_table(soup, ['pos', 'pts'], prefer_headings=([f'{cls} riders', 'motogp riders', 'riders'] if sport == 'motogp' else ["riders' standings", 'riders standings']))
    if st is None: log.append(f'- {year}: no standings grid'); return None
    m = grid_rows(st)
    # header: find the row with Pos … Pts and the round columns between
    hdr = None
    for row in m:
        txt = [clean(c).lower() for c in row]
        if 'pos' in txt and any(t.startswith('pts') or t == 'points' for t in txt): hdr = row; break
    if hdr is None: log.append(f'- {year}: standings header not recognised'); return None
    htxt = [clean(c).lower() for c in hdr]; ipos = htxt.index('pos'); ipts = next(i for i, t in enumerate(htxt) if t.startswith('pts') or t == 'points')
    irider = next((i for i, t in enumerate(htxt) if t.startswith('rider')), ipos + 1); ibike = next((i for i, t in enumerate(htxt) if t in ('bike', 'machine', 'motorcycle', 'manufacturer', 'make')), None)
    round_cols = [i for i in range(max(irider, ibike or 0) + 1, ipts) if clean(hdr[i]) and clean(hdr[i]).lower() not in ('team', 'no', 'no.', 'bike', 'machine', 'rider', 'pos', 'points', 'pts', 'motorcycle', 'manufacturer')]
    # WorldSBK: two header rows (round, then R1/R2); detect by the row after the header being R1/R2 labels
    sub = None
    hi = m.index(hdr)
    if hi + 1 < len(m) and all(clean(c).upper() in ('R1', 'R2', 'SP', 'SPR', 'R', 'S') or clean(c) == '' for c in m[hi + 1][len(m[hi + 1]) - len(round_cols):]): sub = m[hi + 1]
    races = []  # one per column
    for i in round_cols:
        c = hdr[i]; title = link_title(c); code = clean(c)
        rtype = 'RAC'
        if sub is not None:
            lab = clean(sub[i]).upper() if i < len(sub) else ''
            rtype = {'R1': 'R1', 'R2': 'R2', 'SP': 'SPR', 'SPR': 'SPR', 'S': 'SPR'}.get(lab, 'R1')
        races.append({'col': i, 'code': code, 'article': title, 'type': rtype})
    riders = []
    for row in m[(hi + 2 if sub is not None else hi + 1):]:
        if len(row) <= ipts or len({id(c) for c in row}) <= 2: continue   # a spanning 'Sources' or note row
        name_cell = row[irider]; name = clean(name_cell); title = link_title(name_cell)
        if not name or clean(row[ipos]).lower().startswith(('pos', 'source', 'note')) or name.lower().startswith(('source', 'note')): continue
        name = re.sub(r'^\W+', '', name)
        pos_t = clean(row[ipos]); pts_t = clean(row[ipts]).replace(',', '')
        try: pts = float(re.sub(r'[^\d.]', '', pts_t) or 0)
        except ValueError: pts = 0.0
        bike = clean(row[ibike]) if ibike is not None else ''
        cells = []
        for rc in races:
            c = row[rc['col']] if rc['col'] < len(row) else None
            txt = clean(c) if c is not None else ''
            p, status, label = cell_result(txt)
            pole = bool(c is not None and c.find('b')); fast = bool(c is not None and c.find('i'))
            cells.append((p, status, label, pole, fast))
        riders.append({'name': name, 'title': title, 'pos': pos_t, 'pts': pts, 'maker': bike, 'cells': cells})
    # calendar: dates and circuits
    cal = find_table(soup, ['date', 'circuit'], prefer_headings=('calendar', 'schedule', 'grands prix', 'race calendar'))
    cal_rows = []
    if cal is not None:
        cm = grid_rows(cal); ch = None
        for row in cm:
            txt = [clean(c).lower() for c in row]
            if 'date' in txt and 'circuit' in txt: ch = row; break
        if ch is not None:
            ctxt = [clean(c).lower() for c in ch]; idate = ctxt.index('date'); icirc = ctxt.index('circuit'); iname = next((i for i, t in enumerate(ctxt) if 'grand prix' in t or t in ('race', 'round', 'event', 'name')), None)
            for row in cm[cm.index(ch) + 1:]:
                if len(row) <= max(idate, icirc) or len({id(c) for c in row}) <= 2: continue
                cal_rows.append({'date': iso_date(clean(row[idate]), year), 'circuit': clean(row[icirc]), 'circuit_title': link_title(row[icirc]), 'name': clean(row[iname]) if iname is not None else '', 'name_title': link_title(row[iname]) if iname is not None else None, 'country': ''})
    log.append(f'- {year}: {len(races)} race columns, {len(riders)} riders in the grid, {len(cal_rows)} calendar rows')
    return {'year': year, 'races': races, 'riders': riders, 'calendar': cal_rows}

# ---------- race article: full classification
def harvest_race(title, sport, year, log):
    soup = parse_page(title)
    if soup is None: return None
    tables = []
    for heading in (['motogp classification', '500cc classification', 'classification', 'race classification', 'race result', 'results'] if sport == 'motogp' else ['race 1', 'race 2', 'superpole race', 'classification', 'results']):
        pass
    out = {}
    for t in soup.find_all('table', class_=re.compile('wikitable')):
        head = [clean(th).lower() for th in t.find_all('th')[:12]]
        if not any(h.startswith('pos') for h in head) or not any(h.startswith('rider') for h in head): continue
        h = t.find_previous(['h2', 'h3', 'h4']); ht = clean(h).lower() if h else ''
        if sport == 'motogp' and year >= 2002 and ('moto2' in ht or 'moto3' in ht or '250' in ht or '125' in ht): continue
        if sport == 'motogp' and year < 2002 and re.search(r'\b(350|250|125|50|80|sidecar)\b', ht): continue
        key = 'SPR' if 'sprint' in ht else ('R1' if 'race 1' in ht else 'R2' if 'race 2' in ht else 'SPR' if 'superpole' in ht else 'RAC')
        if key in out: continue
        m = grid_rows(t); hdr = next((r for r in m if any(clean(c).lower().startswith('pos') for c in r)), None)
        if hdr is None: continue
        htxt = [clean(c).lower() for c in hdr]
        col = lambda *names: next((i for i, x in enumerate(htxt) for n in names if x.startswith(n)), None)
        ipos, irid, imk, ilap, itime, igrid, ipts, ino = col('pos'), col('rider'), col('manufacturer', 'bike', 'machine', 'motorcycle', 'make'), col('laps'), col('time'), col('grid'), col('points', 'pts'), col('no')
        rows = []
        for row in m[m.index(hdr) + 1:]:
            if irid is None or len(row) <= irid: continue
            pos_t = clean(row[ipos]) if ipos is not None else ''; name = re.sub(r'^\W+', '', clean(row[irid]))
            if not name or pos_t.lower().startswith(('source', 'fastest', 'pole')): continue
            p, status, label = cell_result(pos_t)
            if p is None and status is None: continue
            rows.append({'name': name, 'title': link_title(row[irid]), 'pos': p, 'status': status, 'label': label, 'maker': clean(row[imk]) if imk is not None else '', 'laps': clean(row[ilap]) if ilap is not None else '', 'time': clean(row[itime]) if itime is not None else '', 'grid': clean(row[igrid]) if igrid is not None else '', 'pts': clean(row[ipts]) if ipts is not None else '', 'num': clean(row[ino]) if ino is not None else ''})
        if rows: out[key] = rows
    return out or None

# ---------- assemble the archive
def build_archive(sport, seasons_raw, races_raw, log):
    D = {'circuits': {}, 'layouts': {}, 'cutoff': today_long(), 'seasons': [], 'drivers': {}, 'teams': {}, 'source': 'Wikipedia (CC BY-SA 4.0), season standings grids and race articles', 'built': datetime.date.today().isoformat()}
    pts_of = points_motogp if sport == 'motogp' else points_sbk
    rider_id = {}
    def rid(name, title):
        key = title or name
        if key not in rider_id:
            base = slug(title or name); i = base; n = 2
            while i in D['drivers'] and D['drivers'][i]['name'] != name: i = f'{base}-{n}'; n += 1
            rider_id[key] = i
            if i not in D['drivers']: D['drivers'][i] = {'name': name, 'short': name.split(' ')[-1], 'code': re.sub(r'[^A-Z]', '', name.split(' ')[-1].upper())[:3] or 'RID', 'nationality': ''}
        return rider_id[key]
    def mid(maker):
        m = maker or 'Unknown'; i = slug(m) or 'unknown'
        if i not in D['teams']: D['teams'][i] = {'name': m, 'color': '#b5a5ed'}
        return i
    for sr in seasons_raw:
        y = sr['year']; season = {'year': y, 'races': [], 'round': 0, 'drivers': [], 'teams': []}
        rider_pos_cells = sr['riders']
        for k, rc in enumerate(sr['races']):
            cal = sr['calendar'][k] if k < len(sr['calendar']) else {}
            cname = cal.get('circuit') or rc['code']; cid = slug(cal.get('circuit_title') or cname) or f'c-{k}'
            if cid not in D['circuits']: D['circuits'][cid] = {'id': cid, 'name': cname, 'country': '', 'place': '', 'url': f'https://en.wikipedia.org/wiki/{cal["circuit_title"].replace(" ", "_")}' if cal.get('circuit_title') else '', 'layouts': []}
            full = races_raw.get((y, rc['article'], rc['type'])) if rc['article'] else None
            rows = []
            if full:
                for x in full:
                    d = rid(x['name'], x['title']); t = mid(x['maker'])
                    p = x['pos']; status = x['status']; label = x['label']
                    try: pts = float(x['pts']) if x['pts'] else 0.0
                    except ValueError: pts = 0.0
                    grid = int(x['grid']) if x['grid'].isdigit() else 0; laps = int(x['laps']) if x['laps'].isdigit() else 0
                    rows.append({'d': d, 't': t, 'num': x['num'], 'p': p if p else 900 + len(rows), 'label': label, 'pts': pts, 'g': grid, 'laps': laps, 'status': status, 'time': x['time'] or None, 'fl': None, 'fr': None})
                src = 'article'
            else:
                pt = pts_of(y, rc['type'] == 'SPR')
                for r in rider_pos_cells:
                    p, status, label, pole, fast = r['cells'][k] if k < len(r['cells']) else (None, None, None, False, False)
                    if p is None and status is None: continue
                    d = rid(r['name'], r['title']); t = mid(r['maker'])
                    rows.append({'d': d, 't': t, 'num': '', 'p': p if p else 900 + len(rows), 'label': label, 'pts': float(pt[p - 1]) if p and p <= len(pt) else 0.0, 'g': 1 if pole else 0, 'laps': 0, 'status': status, 'time': None, 'fl': None, 'fr': 1 if fast else None})
                src = 'grid'
            rows.sort(key=lambda x: x['p'])
            for x in rows:
                fin = x['status'] in ('Finished',); win = int(x['p'] == 1 and fin); pod = int(x['p'] <= 3 and fin); fast = int(x['fr'] == 1); g1 = int(x['g'] == 1); nf = int(not fin)
                x.update({'de': 1, 'dw': win, 'dp': pod, 'df': fast, 'dg': g1, 'dn': nf, 'ce': 1, 'cw': win, 'cp': pod, 'cf': fast, 'cg': g1, 'cn': nf})
            race = {'round': k + 1, 'name': (cal.get('name') or rc['code']) + ('' if rc['type'] == 'RAC' else ' · ' + {'SPR': 'Sprint', 'R1': 'Race 1', 'R2': 'Race 2'}[rc['type']]), 'date': cal.get('date', ''), 'circuit': cname, 'cid': cid, 'country': '', 'place': '', 'url': f'https://en.wikipedia.org/wiki/{rc["article"].replace(" ", "_")}' if rc['article'] else '', 'layout': None, 'rows': rows if rc['type'] != 'SPR' else [], 'sprint': rows if rc['type'] == 'SPR' else [], 'type': rc['type'], 'rowsFrom': src}
            season['races'].append(race)
        # published standings from the grid
        for r in sorted(rider_pos_cells, key=lambda r: (int(re.sub(r'\D', '', r['pos']) or 999), -r['pts'])):
            season['drivers'].append({'id': rid(r['name'], r['title']), 'p': re.sub(r'\D', '', r['pos']) or '-', 'pts': r['pts'], 'wins': sum(1 for c in r['cells'] if c[0] == 1), 'teams': [mid(r['maker'])]})
        season['round'] = len(season['races']); D['seasons'].append(season)
        n_art = sum(1 for r in season['races'] if r['rowsFrom'] == 'article'); n_rows = sum(len(r['rows']) + len(r['sprint']) for r in season['races'])
        log.append(f'  {y}: {len(season["races"])} races ({n_art} from race articles, {len(season["races"]) - n_art} from the grid), {n_rows} rows, {len(season["drivers"])} riders')
    return D

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('sport', choices=['motogp', 'sbk']); ap.add_argument('--from', dest='y0', type=int); ap.add_argument('--to', dest='y1', type=int); ap.add_argument('--out', default='build/harvest'); ap.add_argument('--no-articles', action='store_true', help='grids only (faster)')
    a = ap.parse_args(); y0 = a.y0 or (1949 if a.sport == 'motogp' else 1988); y1 = a.y1 or datetime.date.today().year
    log = [f'# {a.sport} clean-room harvest · {today_long()} · {y0}–{y1}']
    seasons_raw = []; races_raw = {}
    for y in range(y0, y1 + 1):
        sr = harvest_season(a.sport, y, log)
        if not sr: continue
        seasons_raw.append(sr)
        if not a.no_articles:
            for rc in sr['races']:
                if not rc['article'] or (y, rc['article'], rc['type']) in races_raw: continue
                full = harvest_race(rc['article'], a.sport, y, log)
                if full:
                    for key, rows in full.items(): races_raw[(y, rc['article'], key)] = rows
    D = build_archive(a.sport, seasons_raw, races_raw, log)
    out = ROOT/a.out; out.mkdir(parents=True, exist_ok=True)
    (out/f'{a.sport}.json').write_text(json.dumps(D, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    log.append(f'\nseasons {len(D["seasons"])} · races {sum(len(s["races"]) for s in D["seasons"])} · rows {sum(len(r["rows"]) + len(r["sprint"]) for s in D["seasons"] for r in s["races"])} · riders {len(D["drivers"])} · makers {len(D["teams"])} · circuits {len(D["circuits"])}')
    report(log, f'{a.sport}-report.md')

if __name__ == '__main__': main()
