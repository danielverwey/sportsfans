"""Isle of Man TT: the year's races from its English Wikipedia article ("<year> Isle of Man TT", CC BY-SA 4.0) — a results
table per race (Position | Number | Rider(s) | Machine | Time | Speed) — written as the archive writes its modern races:
the top ten, the machine, the marque (a sidecar's from its machine description, by the archive's own rules), the race
average and the time. The reader first reads last year's article and must reproduce the archive's races for that year;
if it does not, nothing is written. Races already in the archive are never rewritten.
"""
import datetime, json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0, str(ROOT/'tools'/'harvest'))
from wiki import grid, text, link_title, flag, fold, slug
from tt_rules import MARQUES, MARQUE_ALIAS, derive

TITLE = '{y} Isle of Man TT'
GENERIC = ('result', 'classification', 'race', 'standings')
CLASS = re.compile(r'\b(Superbike|Supersport|Superstock|Supertwin|Sidecar|Senior|Junior|Lightweight|Ultra-?Lightweight|Formula \w+|Production \w*|Classic \w*|TT Zero|Zero)\b', re.I)
AGREE = 0.9

def race_name(heading):
    """'Superbike TT Race' → 'Superbike'; 'Sidecar TT Race 1' → 'Sidecar Race 1'; 'TT Zero' stays."""
    t = re.sub(r'\bIsle of Man\b', '', heading or '').strip()
    t = re.sub(r'\[.*?\]|\(.*?\)', '', t)
    if not re.fullmatch(r'\s*TT Zero\s*', t, re.I): t = re.sub(r'\bTT\b', '', t)
    t = re.sub(r'\bRace\s*$', '', t.strip()); t = re.sub(r'\bRace\s+(one|two)\b', lambda m: 'Race ' + {'one': '1', 'two': '2'}[m.group(1).lower()], t, flags=re.I)
    m = CLASS.search(t)   # a sponsor's name before the class ("RST x D3O Superbike", "3wheeling.media Sidecar Race 1") is not part of the race's name
    if m: t = t[m.start():]
    return re.sub(r'\s+', ' ', t).strip()

def names_of(cell):
    """The rider (or the sidecar crew) in a cell: the linked names, else the text split at '/', '&' or a line break."""
    links = [a.get_text(' ', strip=True) for a in cell.find_all('a', href=True) if not a.find_parent(class_=re.compile('flagicon|reference')) and a.get_text(strip=True)]
    parts = re.split(r'\s*/\s*|\s*&\s*|\n', text(cell))
    parts = [re.sub(r'^[A-Z]{3}\s+', '', p).strip() for p in parts if p.strip()]
    if links and len(links) >= len(parts): return links   # every name linked: the linked spelling is the canonical one
    return parts or links   # a crew with one member unlinked ("Ben Birchall / Patrick Rosney") keeps both names

def read_year(y, get_page):
    page = get_page(TITLE.format(y=y))
    if page is None: return None, []
    races = []
    for t in page.soup.find_all('table', class_=re.compile('wikitable')):
        m = grid(t)
        if not m: continue
        low = [text(c).lower() for c in m[0]]
        irider = next((i for i, h in enumerate(low) if h.startswith('rider')), None)
        ipos = next((i for i, h in enumerate(low) if h.startswith(('pos', 'rank', 'place'))), None)
        itime = next((i for i, h in enumerate(low) if h.startswith('time')), None); ispd = next((i for i, h in enumerate(low) if h.startswith(('speed', 'average', 'avg'))), None)
        imach = next((i for i, h in enumerate(low) if h.startswith(('machine', 'bike', 'motorcycle', 'team'))), None)
        if irider is None or ipos is None or (itime is None and ispd is None): continue
        h = t.find_previous(['h2', 'h3', 'h4'])
        while h is not None and any(w in text(h).lower() for w in GENERIC) and not re.search(r'(superbike|supersport|superstock|supertwin|senior|sidecar|lightweight|zero|sportbike|junior|lightweight)', text(h).lower()):
            h = h.find_previous(['h2', 'h3', 'h4'])
        name = race_name(text(h)) if h is not None else ''
        if not name: continue
        rows = []
        for row in m[1:]:
            if len(row) <= max(irider, ipos): continue
            p = re.sub(r'\D', '', text(row[ipos]))
            if not p: continue
            spd = re.search(r'\d+(?:\.\d+)?', text(row[ispd])) if ispd is not None else None
            rows.append({'pos': int(p), 'names': names_of(row[irider]), 'machine': text(row[imach]) if imach is not None else '',
                         'mph': float(spd.group(0)) if spd else None, 'time': text(row[itime]) if itime is not None else None})
        if rows: races.append({'name': name, 'rows': rows})
    return page, races

def build(y, races, R, url, new_riders):
    """Harvested races → the archive's race dicts (packed rows)."""
    by_name = {}
    for k, v in R.items(): by_name.setdefault(fold(v['name']), k)
    def rid_of(n):
        f = fold(n)
        if f in by_name: return by_name[f]
        if f in new_riders: return new_riders[f]['id']
        rid = slug(n); k = 2
        while rid in R or rid in {x['id'] for x in new_riders.values()}: rid = f'{slug(n)}-{k}'; k += 1
        new_riders[f] = {'id': rid, 'name': n}; return rid
    out = []
    for r in races:
        kind = 'sidecar' if 'sidecar' in r['name'].lower() else 'solo'
        rows = []
        for x in sorted(r['rows'], key=lambda x: x['pos']):
            mach = x['machine']
            if kind == 'solo':
                marque = MARQUE_ALIAS.get(mach, mach) if mach in MARQUES or mach in MARQUE_ALIAS else (derive(mach) or mach); mq = 'src' if mach else ''
            else:
                marque = derive(mach); mq = 'machine' if marque else ''
            rows.append([[rid_of(n) for n in x['names']], x['pos'], 'Classified', mach or None, marque or None, x['mph'], x['time'], mq])
        fam = re.sub(r'\s+Race\s+\d+$', '', r['name'])
        out.append({'id': f'tt-{y}-{slug(r["name"])}', 'y': y, 'name': r['name'], 'family': fam, 'course': 'Mountain Course', 'kind': kind, 'scope': 'tt', 'date': None, 'laps': None, 'results': rows, 'url': url})
    return out

def diagnose(page, races, mine, archive):
    """What the reader saw, for the report when the proof fails: every results-like table's headers and first row, the
    reader's first placings per race next to the archive's, and the riders it could not match."""
    out = ['', '<details><summary>What the reader saw</summary>', '']
    for t in page.soup.find_all('table', class_=re.compile('wikitable'))[:16]:
        m = grid(t)
        if len(m) < 2: continue
        out.append(f'- table: {" | ".join(text(c)[:18] for c in m[0][:8])}')
        out.append(f'  - first row: {" | ".join(text(c)[:22] for c in m[1][:8])}')
    for r in archive[:12]:
        got = mine.get(r['id'], {}).get('results', [])
        out.append(f'- {r["id"]}: archive {[(x[1], x[0]) for x in r["results"][:3]]} · read {[(x[1], x[0]) for x in got[:3]] if got else "nothing"}')
    for r in races[:3]:
        out.append(f'- raw {r["name"]}: {[(x["pos"], x["names"], x["machine"]) for x in r["rows"][:3]]}')
    return out + ['', '</details>']

def sweep(log, get_page=None, today=None):
    today = today or datetime.date.today()
    if get_page is None:
        from wiki import parse_page as get_page
    path = ROOT/'data'/'tt.json'; A = json.loads(path.read_text(encoding='utf-8'))
    y = today.year; new_riders = {}
    # 1. prove the reader on last year's article
    page, races = read_year(y - 1, get_page)
    if page is None: raise SystemExit(f'{y - 1} Isle of Man TT article not found — nothing written')
    mine = {r['id']: r for r in build(y - 1, races, A['riders'], page.url, new_riders)}
    have = checked = 0; bad = []
    for r in A['races']:
        if r['y'] != y - 1 or len(r['results']) < 2: continue
        want = {(x[1], tuple(x[0])) for x in r['results'] if x[1]}; got = {(x[1], tuple(x[0])) for x in mine.get(r['id'], {}).get('results', [])}
        checked += len(want); have += len(want & got)
        if len(want & got) < len(want): bad.append(f'{r["id"]}: {len(want & got)}/{len(want)}')
    log.append(f'Check on {y - 1}: the reader reproduces {have} of the archive\'s {checked} placings ({have / max(checked, 1):.1%}).')
    if checked and have / checked < AGREE:
        log += [f'  - {b}' for b in bad[:10]]
        log += diagnose(page, races, mine, [r for r in A['races'] if r['y'] == y - 1])
        raise SystemExit(f'the {y - 1} article did not read back as the archive holds it — nothing written')
    # 2. this year's article
    new_riders = {}
    page, races = read_year(y, get_page)
    if page is None: log.append(f'- the {y} article does not exist yet'); return
    have_ids = {r['id'] for r in A['races']}
    add = [r for r in build(y, races, A['riders'], page.url, new_riders) if r['id'] not in have_ids and r['results']]
    if not add: log.append('- nothing new'); return
    for r in add:
        A['races'].append(r)
        w = r['results'][0]
        log.append(f'- **{y} {r["name"]}**: {len(r["results"])} places, won by {" / ".join(A["riders"].get(i, next((v for v in new_riders.values() if v["id"] == i), {})).get("name", i) for i in w[0])} ({w[3]})')
    used = {i for r in add for x in r['results'] for i in x[0]}
    for v in new_riders.values():
        if v['id'] in used: A['riders'][v['id']] = {'name': v['name'], 'url': ''}; log.append(f'  - new rider: {v["name"]}')
    A['sources'].append({'title': page.title, 'url': page.url, 'retrieved': today.isoformat(), 'sha256': page.sha256, 'credit': 'English Wikipedia contributors', 'licence': 'CC BY-SA 4.0'})
    cov = A['coverage']; races_all = A['races']
    cov.update(races=len(races_all), raceYears=len({r['y'] for r in races_all}), results=sum(len(r['results']) for r in races_all), expandedRaces=sum(1 for r in races_all if len(r['results']) > 1),
               winnerOnly=sum(1 for r in races_all if len(r['results']) == 1), marquesDerived=sum(1 for r in races_all for x in r['results'] if x[7] == 'machine'))
    A['lastYear'] = max(r['y'] for r in races_all); A['snapshot'] = today.isoformat()
    path.write_text(json.dumps(A, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    log.append(f'\nArchive now {len(races_all)} races, through {A["lastYear"]}.')
