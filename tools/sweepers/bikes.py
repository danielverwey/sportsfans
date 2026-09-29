"""MotoGP and WorldSBK: the current season from its Wikipedia article (CC BY-SA 4.0), read the way the archive was built —
the riders' standings grid (a finishing position in every cell; for MotoGP the Sprint position as the superscript, bold for
pole, italics for fastest lap), the calendar, the entry list for teams and numbers, and the published riders' and
manufacturers' standings.

Before anything is added the reader proves itself: it reads last season's article and the rounds of this season already in
the archive, and compares what it gets with what the archive holds. If they do not agree — the article's layout changed, or
the reader misread it — nothing is written and the sweep stops with a report. Rounds already in the archive are never
rewritten; only rounds it does not have yet are added, with this season's standings.
"""
import datetime, json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0, str(ROOT/'tools'/'harvest'))
from wiki import grid, text, sups, link_title, flag, fold, slug, title_of_url

TITLE = {'motogp': '{y} MotoGP World Championship', 'sbk': '{y} Superbike World Championship'}
PREFIX = {'motogp': 'gp', 'sbk': 'sbk'}
STATUS = {'RET': 'Ret', 'DNS': 'DNS', 'NC': 'NC', 'EX': 'EX', 'DSQ': 'EX', 'DQ': 'EX', 'WD': 'WD'}
SUB = {'R1': 'R1', 'RACE 1': 'R1', 'SPR': 'SPR', 'SP': 'SPR', 'SR': 'SPR', 'SPRINT': 'SPR', 'SUPERPOLE': 'SPR', 'R2': 'R2', 'RACE 2': 'R2', 'RAC': 'RAC', 'R': 'RAC', 'RACE': 'RAC'}
MONTHS = {m: i for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'], 1)}
AGREE = 0.9

def dates_of(txt, year):
    """'20–22 February', '22 February', 'February 20–22', '28 February – 1 March' → the days as ISO dates (first, last)."""
    t = txt.replace('–', '-').replace('—', '-')
    found = []
    for m in re.finditer(r'(\d{1,2})(?:\s*-\s*(\d{1,2}))?\s+([A-Za-z]{3,})|([A-Za-z]{3,})\s+(\d{1,2})(?:\s*-\s*(\d{1,2}))?', t):
        g = m.groups()
        d1, d2, mon = (g[0], g[1], g[2]) if g[0] else (g[4], g[5], g[3])
        mi = MONTHS.get(mon.lower()) or next((v for k, v in MONTHS.items() if k.startswith(mon.lower()[:3])), None)
        if not mi: continue
        for d in (d1, d2):
            if d:
                try: found.append(datetime.date(year, mi, int(d)))
                except ValueError: pass
    return (found[0].isoformat(), found[-1].isoformat()) if found else (None, None)

def find_grid(soup, sport):
    """The riders' standings grid: the wikitable with Pos, Rider and Pts under a riders' standings heading."""
    best = None
    for t in soup.find_all('table', class_=re.compile('wikitable')):
        m = grid(t)
        hdr = next((i for i, r in enumerate(m[:3]) if any(text(c).lower().rstrip('.') == 'pos' for c in r) and any(text(c).lower().startswith('rider') for c in r)), None)
        if hdr is None or not any(text(c).lower().startswith(('pts', 'points')) for c in m[hdr]): continue
        h = t.find_previous(['h2', 'h3', 'h4']); ht = text(h).lower() if h else ''
        score = ('rider' in ht) * 2 + ('standing' in ht) + ('championship' in ht)
        if best is None or score > best[0]: best = (score, t, m, hdr)
    return best

def read_grid(m, hdr, sport):
    """Rows of the grid → {'races': [{code, type, col, article}], 'riders': [{title, name, country, pos, bike, pts, cells: [...]}]}."""
    H = [text(c) for c in m[hdr]]; low = [h.lower().rstrip('.') for h in H]
    ipos = low.index('pos'); irider = next(i for i, h in enumerate(low) if h.startswith('rider'))
    ipts = max(i for i, h in enumerate(low) if h.startswith(('pts', 'points')))
    ibike = next((i for i, h in enumerate(low) if h in ('bike', 'manufacturer', 'motorcycle', 'constructor', 'machine')), None)
    iteam = next((i for i, h in enumerate(low) if h == 'team'), None)
    first = max(x for x in (irider, ibike or 0, iteam or 0)) + 1
    sub = m[hdr + 1] if hdr + 1 < len(m) and sum(1 for c in m[hdr + 1][first:ipts] if text(c).upper() in SUB) >= 2 else None
    races = []; seen = set()
    for i in range(first, ipts):
        c = m[hdr][i]; code = text(c)
        if not code or code.lower() in ('team', 'bike', 'no', 'no.'): continue
        mc = re.match(r'[A-Z]{3}', code); code = mc.group(0) if mc else code
        typ = SUB.get(text(sub[i]).upper()) if sub is not None else 'RAC'
        if not typ: continue
        key = (id(c), typ)
        if key in seen: continue
        seen.add(key); races.append({'code': code, 'type': typ, 'col': i, 'article': link_title(c), 'hid': id(c)})
    riders = []
    for row in m[hdr + (2 if sub is not None else 1):]:
        if len(row) <= ipts: continue
        pos_t = text(row[ipos]); name_c = row[irider]; name = text(name_c)
        if not name or name.lower().startswith(('pos', 'rider', 'source', 'key', 'colour', 'bold', 'italic')) or len({id(c) for c in row}) <= 3: continue
        cells = []
        for r in races:
            c = row[r['col']]; toks = text(c).upper().replace('†', '').split()
            up = toks[0] if toks else ''
            pos = int(up) if up.isdigit() else None; status = 'Classified' if pos else STATUS.get(up)
            marks = ' '.join(sups(c) + toks[1:]).upper()
            sp = re.findall(r'\d+', ' '.join(sups(c)))
            cells.append({'pos': pos, 'status': status, 'sprint': int(sp[0]) if sp else None,
                          'pole': bool(c.find('b')) or bool(re.search(r'(?<![A-Z])P(?![A-Z])', marks)), 'fast': bool(c.find('i')) or bool(re.search(r'(?<![A-Z])F(?![A-Z])', marks))})
        try: pts = float(re.sub(r'[^\d.]', '', text(row[ipts])) or 0)
        except ValueError: pts = 0.0
        a = next((a for a in name_c.find_all('a', href=True) if not a.find_parent(class_=re.compile('flagicon')) and a.get_text(strip=True)), None)
        nm = a.get_text(' ', strip=True) if a else re.sub(r'^[A-Z]{3}\s+', '', re.sub(r'^\W+', '', name))
        riders.append({'title': link_title(name_c), 'name': nm, 'country': flag(name_c), 'pos': int(pos_t) if pos_t.isdigit() else None,
                       'bike': text(row[ibike]) if ibike is not None else '', 'team': text(row[iteam]) if iteam is not None else '', 'pts': pts, 'cells': cells})
    # a rider on two rows (two bikes in one season) keeps one standings line
    return {'races': races, 'riders': riders}

def read_calendar(soup, year):
    """Round number → {first, last, name, circuit title, circuit text, country, races: [(pole title, fastest-lap title)] by row}.
    WorldSBK's table gives a row per race (R1, Superpole Race, R2) with its pole and fastest lap; MotoGP's a row per round."""
    for t in soup.find_all('table', class_=re.compile('wikitable')):
        m = grid(t)
        if not m: continue
        hi = next((i for i, r in enumerate(m[:3]) if any('circuit' in text(c).lower() for c in r) and any(text(c).lower().startswith(('date', 'dates')) for c in r)), None)
        if hi is None: continue
        low = [text(c).lower() for c in m[hi]]
        iround = next((i for i, h in enumerate(low) if h in ('round', 'rnd', 'no', 'no.', 'r')), 0)
        idate = next(i for i, h in enumerate(low) if h.startswith('date'))
        icirc = next(i for i, h in enumerate(low) if 'circuit' in h)
        iname = next((i for i, h in enumerate(low) if 'grand prix' in h or h in ('race', 'event', 'round name')), None)
        icountry = next((i for i, h in enumerate(low) if h in ('country', 'nation')), None)
        ipole = next((i for i, h in enumerate(low) if h.startswith('pole')), None); ifast = next((i for i, h in enumerate(low) if h.startswith('fastest')), None)
        out = {}
        for row in m[hi + 1:]:
            if len(row) <= max(idate, icirc): continue
            rt = text(row[iround]); n = int(rt) if rt.isdigit() else None
            if n is None: continue
            name = text(row[iname]) if iname is not None else next((text(c) for c in row if text(c).endswith(' Round')), '')
            cc = row[icirc]
            e = out.setdefault(n, {'days': [], 'name': name, 'circuit_title': link_title(cc), 'circuit': text(cc),
                                   'country': text(row[icountry]) if icountry is not None else (flag(cc) or next((flag(c) for c in row if flag(c)), '')), 'races': []})
            first, last = dates_of(text(row[idate]), year)
            e['days'] += [d for d in (first, last) if d]
            if ipole is not None or ifast is not None:
                e['races'].append((link_title(row[ipole]) if ipole is not None and text(row[ipole]) not in ('', '—', '–') else None,
                                   link_title(row[ifast]) if ifast is not None and text(row[ifast]) not in ('', '—', '–') else None))
        for e in out.values():
            e['first'] = min(e['days']) if e['days'] else None; e['last'] = max(e['days']) if e['days'] else None
        if out: return out
    return {}

def read_entries(soup):
    """Rider article title → [(team, number, maker, rounds text)] from the entry list."""
    out = {}
    for t in soup.find_all('table', class_=re.compile('wikitable')):
        m = grid(t)
        if not m: continue
        hi = next((i for i, r in enumerate(m[:3]) if any(text(c).lower().startswith('rider') for c in r) and any(text(c).lower() in ('no.', 'no', 'number') for c in r) and any('team' in text(c).lower() for c in r)), None)
        if hi is None: continue
        low = [text(c).lower() for c in m[hi]]
        it = next(i for i, h in enumerate(low) if 'team' in h); ino = next(i for i, h in enumerate(low) if h in ('no.', 'no', 'number')); ir = next(i for i, h in enumerate(low) if h.startswith('rider'))
        imk = next((i for i, h in enumerate(low) if h in ('constructor', 'manufacturer', 'motorcycle', 'bike')), None); ird = next((i for i, h in enumerate(low) if h.startswith('round')), None)
        for row in m[hi + 1:]:
            if len(row) <= max(it, ino, ir): continue
            title = link_title(row[ir]) or text(row[ir]); no = re.sub(r'\D', '', text(row[ino]))
            out.setdefault(title, []).append((text(row[it]), int(no) if no else None, text(row[imk]) if imk is not None else '', text(row[ird]) if ird is not None else ''))
        if out: break
    return out

def read_table_standings(soup, words):
    """A published standings table (manufacturers'): [{pos, name, points}]."""
    for t in soup.find_all('table', class_=re.compile('wikitable')):
        h = t.find_previous(['h2', 'h3', 'h4']); ht = text(h).lower() if h else ''
        if not any(w in ht for w in words): continue
        m = grid(t)
        hi = next((i for i, r in enumerate(m[:3]) if any(text(c).lower().rstrip('.') == 'pos' for c in r)), None)
        if hi is None: continue
        low = [text(c).lower().rstrip('.') for c in m[hi]]
        ipts = max(i for i, h in enumerate(low) if h.startswith(('pts', 'points'))); iname = next((i for i, h in enumerate(low) if h in ('manufacturer', 'constructor', 'bike', 'make')), 1)
        rows = []
        for row in m[hi + 1:]:
            if len(row) <= ipts: continue
            p = text(row[0]); n = text(row[iname])
            if not p.isdigit() or not n: continue
            try: rows.append({'pos': int(p), 'maker': n, 'points': float(re.sub(r'[^\d.]', '', text(row[ipts])) or 0)})
            except ValueError: continue
        if rows: return rows
    return []

def read_season(sport, year, get_page):
    page = get_page(TITLE[sport].format(y=year))
    if page is None: return None
    g = find_grid(page.soup, sport)
    if g is None: return {'page': page, 'error': 'no riders\' standings grid found'}
    _, _, m, hdr = g
    G = read_grid(m, hdr, sport)
    return {'page': page, 'grid': G, 'calendar': read_calendar(page.soup, year), 'entries': read_entries(page.soup),
            'makers': read_table_standings(page.soup, ('manufacturers', 'constructors'))}

# ---------------------------------------------------------------- the season read → the archive's races
def races_of(sport, year, S, rid_of, today):
    """Harvested season → {(round, type): race dict} in the archive's shape (circuit and names filled in by the caller)."""
    G = S['grid']; out = {}
    heads = []   # round number = order of first appearance of each round's header cell in the grid
    for r in G['races']:
        if r['hid'] not in heads: heads.append(r['hid'])
    for ri, r in enumerate(G['races']):
        rnd = heads.index(r['hid']) + 1
        types = [r['type']] + (['SPR'] if sport == 'motogp' and r['type'] == 'RAC' else [])
        for typ in types:
            rows = []; pole = fast = None
            for rider in G['riders']:
                c = rider['cells'][ri]; rid = rid_of(rider)
                if typ == 'SPR' and sport == 'motogp':
                    if c['sprint']: rows.append({'rider': rid, 'pos': c['sprint'], 'status': 'Classified', 'maker': rider['bike'], 'team': None, 'number': None, 'laps': None, 'gap': None, 'lapGap': None, 'points': None})
                    continue
                if not c['status']: continue
                rows.append({'pos': c['pos'], 'status': c['status'], 'rider': rid, 'maker': rider['bike'], 'team': None, 'number': None, 'laps': None, 'gap': None, 'lapGap': None, 'points': None, 'bestLap': None})
                if c['pole']: pole = rid
                if c['fast']: fast = rid
            if not rows: continue
            rows.sort(key=lambda x: (x['pos'] is None, x['pos'] or 0))
            out[(rnd, typ)] = {'code': r['code'], 'rows': rows, 'pole': pole, 'fast': fast}
    return out

def agreement(harvested, archive_races):
    """How many of the archive's classified (position, rider) pairs the reader reproduces, and how many it was checked on."""
    have = checked = 0; bad = []
    for key, race in archive_races.items():
        h = harvested.get(key)
        mine = {(x['pos'], x['rider']) for x in race['results'] if x['pos']}
        checked += len(mine)
        if not h: bad.append(f'{key}: not read'); continue
        got = {(x['pos'], x['rider']) for x in h['rows'] if x['pos']}
        have += len(mine & got)
        if len(mine & got) < len(mine): bad.append(f'{key}: {len(mine & got)}/{len(mine)}')
    return have, checked, bad

def sweep(log, sport, get_page=None, today=None):
    today = today or datetime.date.today()
    if get_page is None:
        from wiki import parse_page as get_page
    path = ROOT/'data'/f'{sport}.json'; A = json.loads(path.read_text(encoding='utf-8'))
    year = today.year
    have_years = {r['year'] for r in A['races']}
    if year not in have_years and today.month < 3: year -= 1   # the winter: the season just finished
    R = A['riders']; by_title = {title_of_url(v.get('url')): k for k, v in R.items() if v.get('url')}; by_name = {}
    for k, v in R.items(): by_name.setdefault(fold(v['name']), []).append(k)
    new_riders = {}
    def rid_of(rider):
        t = rider.get('title')
        if t and t in by_title: return by_title[t]
        n = by_name.get(fold(rider['name']), [])
        if len(n) == 1: return n[0]
        key = t or rider['name']
        if key in new_riders: return new_riders[key]['id']
        rid = slug(t or rider['name']); k = 2
        while rid in R or rid in [x['id'] for x in new_riders.values()]: rid = f'{slug(t or rider["name"])}-{k}'; k += 1
        new_riders[key] = {'id': rid, 'name': rider['name'], 'country': rider.get('country') or '', 'iso': '', 'number': None, 'url': 'https://en.wikipedia.org/wiki/' + t.replace(' ', '_') if t else None}
        return rid
    # 1. prove the reader on last season, which the archive holds in full
    prev = read_season(sport, year - 1, get_page)
    if not prev or prev.get('error'): raise SystemExit(f'{year - 1} season article: {(prev or {}).get("error", "not found")} — nothing written')
    prev_races = races_of(sport, year - 1, prev, rid_of, today)
    arch_prev = {(int(r['round'].split('-')[1]), r['type']): r for r in A['races'] if r['year'] == year - 1}
    have, checked, bad = agreement(prev_races, arch_prev)
    log.append(f'Check on {year - 1}: the reader reproduces {have} of the archive\'s {checked} classified places ({have / max(checked, 1):.1%}).')
    if not checked or have / checked < AGREE:
        log += [f'  - {b}' for b in bad[:12]]
        raise SystemExit(f'the {year - 1} article did not read back as the archive holds it — the layout may have changed; nothing written')
    # 2. this season
    cur = read_season(sport, year, get_page)
    if not cur or cur.get('error'): raise SystemExit(f'{year} season article: {(cur or {}).get("error", "not found")} — nothing written')
    races = races_of(sport, year, cur, rid_of, today)
    arch = {(int(r['round'].split('-')[1]), r['type']): r for r in A['races'] if r['year'] == year}
    if arch:
        have, checked, bad = agreement(races, arch)
        log.append(f'Check on {year} so far: {have} of {checked} classified places reproduced ({have / max(checked, 1):.1%}).')
        if checked and have / checked < AGREE:
            log += [f'  - {b}' for b in bad[:12]]
            raise SystemExit(f'the {year} rounds already in the archive did not read back — nothing written')
    cal = cur['calendar']; entries = cur['entries']
    TYPE_ORDER = ['R1', 'SPR', 'RAC', 'R2']
    new_keys = sorted((k for k in races if k not in arch and k[0] in cal and cal[k[0]]['last'] and cal[k[0]]['last'] <= today.isoformat()), key=lambda k: (k[0], TYPE_ORDER.index(k[1])))
    if not new_keys:
        log.append('- nothing new'); return
    # circuits, teams, numbers, names
    C = A['circuits']; c_title = {}
    for cid, c in C.items():
        for u in [c.get('url')] + [a.get('url') for a in c.get('aliases') or []]:
            t = title_of_url(u)
            if t: c_title[t] = cid
    def circuit_of(cr):
        t = cr.get('circuit_title')
        if t in c_title: return c_title[t]
        f = fold(cr['circuit'].split(',')[0])
        for cid, c in C.items():
            if fold(c['name'].split(',')[0]) == f: return cid
        cid = slug(t or cr['circuit']); C[cid] = {'name': cr['circuit'], 'place': '', 'country': cr.get('country') or '', 'length': None, 'url': 'https://en.wikipedia.org/wiki/' + t.replace(' ', '_') if t else None,
                                                  'aliases': [{'name': cr['circuit'], 'url': 'https://en.wikipedia.org/wiki/' + t.replace(' ', '_') if t else None}], 'wikidata': None, 'metadataLicence': 'CC0 1.0', 'lat': None, 'lon': None}
        c_title[t] = cid; log.append(f'  - new circuit: {cr["circuit"]}'); return cid
    label_at = {}
    for r in A['races']: label_at[r['circuit']] = r.get('venueLabel')
    def team_no(rid, title, rnd):
        for team, no, maker, rounds in entries.get(title, []) if title else []:
            if not rounds or rounds.lower() in ('all', 'all rounds') or rnd in rounds_set(rounds): return team, no
        return None, R.get(rid, {}).get('number')
    title_of_rid = {rid_of(x): x.get('title') for x in cur['grid']['riders']}
    order = max([r['order'] for r in A['races'] if r['year'] == year] or [0])
    url = cur['page'].url; added = []
    for (rnd, typ) in new_keys:
        h = races[(rnd, typ)]; cr = cal[rnd]; cid = circuit_of(cr)
        date = cr['last']   # the archive dates a race weekend by its Sunday; WorldSBK's Race 1 is the Saturday
        if sport == 'sbk' and typ == 'R1': date = (datetime.date.fromisoformat(cr['last']) - datetime.timedelta(days=1)).isoformat()
        for x in h['rows']:
            team, no = team_no(x['rider'], title_of_rid.get(x['rider']), rnd); x['team'] = team if team is not None else ''; x['number'] = no
        if sport == 'sbk' and cr.get('races'):
            k = ['R1', 'SPR', 'R2'].index(typ)
            if k < len(cr['races']):
                pt, ft = cr['races'][k]; by_t = {v: key for key, v in title_of_rid.items() if v}
                h['pole'] = by_t.get(pt) if pt else None; h['fast'] = by_t.get(ft) if ft else h['fast']
        rows = h['rows']
        if sport == 'motogp': order_ = rnd
        else: order += 1; order_ = order
        rname = cr['name'] or f'{cr.get("country", "")} Round'
        name = rname if sport == 'motogp' else f'{rname} · ' + {'R1': 'Race 1', 'SPR': 'Superpole Race', 'R2': 'Race 2'}[typ]
        race = {'id': f'{PREFIX[sport]}-{year}-{rnd}-{typ}', 'round': f'{year}-{rnd}', 'year': year, 'date': date, 'type': typ, 'name': name, 'code': h['code'], 'circuit': cid,
                'country': cr.get('country') or C[cid].get('country') or '', 'condition': ''}
        if sport == 'motogp' and typ == 'SPR':
            race.update({'url': url, 'sourceKind': 'Wikipedia season matrix', 'order': order_, 'datePrecision': 'Grand Prix weekend date; exact Sprint date not transcribed', 'results': rows,
                         'coverageNote': 'Points-scoring Sprint finishers only (positions 1–9).'})
        else:
            race.update({'results': rows, 'url': url, 'sourceKind': 'Wikipedia season matrix', 'order': order_, 'datePrecision': 'Source calendar date'})
            if h['pole']: race['pole'] = {'rider': h['pole'], 'time': None}
            if h['fast']: race['fast'] = {'rider': h['fast'], 'time': None}
        race['venueLabel'] = label_at.get(cid) or cr['circuit']
        A['races'].append(race); added.append(race)
        log.append(f'- **{year} round {rnd} {typ}** at {cr["circuit"]}: {len(rows)} results, won by {R.get(rows[0]["rider"], new_riders.get(rows[0]["rider"], {})).get("name") if rows else "—"}')
    for v in new_riders.values():
        if any(x['rider'] == v['id'] for r in added for x in r['results']):
            R[v['id']] = {k: v[k] for k in ('name', 'country', 'iso', 'number', 'url')}; log.append(f'  - new rider: {v["name"]}')
    # standings as published, coverage, provenance
    st = [{'rider': rid_of(x), 'pos': x['pos'], 'maker': x['bike'], 'points': x['pts']} for x in cur['grid']['riders'] if x['pos']]
    if st: A['standings'][str(year)] = {'rows': st, 'url': url}
    if cur['makers']: A['manufacturerStandings'][str(year)] = {'rows': cur['makers'], 'url': url}
    yr = [r for r in A['races'] if r['year'] == year]; main = [r for r in yr if r['type'] != 'SPR']
    cov = A['coverage'].setdefault(str(year), {'notes': 'Sprints: points scorers only' if sport == 'motogp' else 'Season result matrix'})
    cov.update(gp=len(main), sprint=sum(1 for r in yr if r['type'] == 'SPR'), poles=len({r['round'] for r in yr if r.get('pole')}), fast=sum(1 for r in yr if r.get('fast')),
               entries=sum(len(r['results']) for r in yr), rounds=len({r['round'] for r in yr}), podiumSlots=3 * len(yr))
    prov = next((p for p in A['provenance'] if p['year'] == year), None)
    if prov is None: prov = {'year': year, 'title': cur['page'].title, 'url': url, 'licence': 'CC BY-SA 4.0', 'credit': 'Wikipedia contributors'}; A['provenance'].append(prov)
    prov.update(retrieved=today.isoformat(), sha256=cur['page'].sha256, revision=str(cur['page'].revid) if cur['page'].revid else prov.get('revision'))
    A['snapshot'] = today.isoformat(); A['lastDate'] = max(r['date'] for r in A['races'])
    path.write_text(json.dumps(A, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    log.append(f'\nArchive now {len(A["races"]):,} races, through {A["lastDate"]}.')

def rounds_set(txt):
    out = set()
    for part in re.split(r'[,;]\s*', txt or ''):
        m = re.fullmatch(r'\s*(\d+)\s*(?:[-–]\s*(\d+))?\s*', part)
        if m: out.update(range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1))
    return out
