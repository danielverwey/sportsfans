"""Dakar Rally: the new edition from Wikipedia's "Dakar Rally" article (CC BY-SA 4.0) — the same article the archive was
transcribed from: a table per category (Year | Route | the first three, each with the crew and the make & model), read into
the archive's podium rows. The reader first reads the last two editions the archive already holds and must reproduce them;
if it does not, nothing is written. Earlier editions are never rewritten; the newest may be completed as the article fills in.
"""
import datetime, json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0, str(ROOT/'tools'/'harvest'))
from wiki import grid, text, fold, slug

TITLE = 'Dakar Rally'
CATS = ['Cars', 'Bikes', 'Trucks', 'Quads', 'SSV', 'Challenger', 'Stock', 'Classic']
CAT_OF = [(r'\bcars?\b', 'Cars'), (r'\b(bikes?|motorcycles?|motos?)\b', 'Bikes'), (r'\btrucks?\b', 'Trucks'), (r'\bquads?\b', 'Quads'), (r'\b(ssvs?|utvs?|side.by.side)\b', 'SSV'),
          (r'(light prototypes?|challenger|\bt3\b)', 'Challenger'), (r'\bstock\b', 'Stock'), (r'\bclassics?\b', 'Classic')]
MAKE_COL = re.compile(r'make|model|truck|vehicle|machine|manufacturer|\bcar\b|\bbike\b|\bquad\b|\butv\b|\bssv\b')
FIX = [('Ḥaʼil', 'Ha’il'), ('near Yanbu', 'Yanbu'), ('al-Ula', 'AlUla'), ('Alger', 'Algiers'), ('Agades', 'Agadez'), ('Clermont-Ferrand', 'Clermont_Ferrand')]
AGREE = 0.9

def category(label):
    t = (label or '').lower()
    return next((c for pat, c in CAT_OF if re.search(pat, t)), None)

def names_in(cell):
    """The people a cell names: its links (not flags or footnotes), else its lines; a leading country code is dropped."""
    links = [a.get_text(' ', strip=True) for a in cell.find_all('a', href=True) if not a.find_parent(class_=re.compile('flagicon|reference')) and a.get_text(strip=True) and not re.fullmatch(r'[A-Z]{3}', a.get_text(strip=True))]
    if links: return links
    return [re.sub(r'^[A-Z]{3}\s+', '', p).strip() for p in re.split(r'\n|\s*/\s*', cell.get_text('\n', strip=True)) if p.strip() and not re.fullmatch(r'[A-Z]{3}', p.strip())]

def read_article(page):
    """{year: {'route': text, 'podium': {cat: [(rank, [names], make text)]}}} from the article's two table shapes: the winners
    tables (Year | Route | <category> | <category> …, two columns per category, one row per edition — the route and each
    category's winner) and the podium tables (Year | 1st | 1st | 2nd | 2nd | 3rd | 3rd under a category heading)."""
    out = {}; pod = {}   # pod[(y, cat)][rank] = (people, make)
    def groups(h0, h1):
        """Consecutive columns with the same top header, from column `start`: [(label, name cols, make col)]."""
        g = []
        for i in range(2, len(h0)):
            if g and g[-1][0] == h0[i]: (g[-1][1] if not MAKE_COL.search(h1[i]) else g[-1][2]).append(i)
            else: g.append((h0[i], [] if MAKE_COL.search(h1[i]) else [i], [i] if MAKE_COL.search(h1[i]) else []))
        return [(lab, ncols, mcols[0] if mcols else None) for lab, ncols, mcols in g]
    def year_of(row):
        m = re.match(r'(\d{4})', text(row[0])); return int(m.group(1)) if m and len(row) > 2 else None
    def edition(y, route=None):
        e = out.setdefault(y, {'route': '', 'podium': {}})
        if route and not e['route']: e['route'] = route
        return e
    for t in page.soup.find_all('table', class_=re.compile('wikitable')):
        m = grid(t)
        if len(m) < 3: continue
        h0 = [text(c) for c in m[0]]; h1 = [text(c).lower() for c in m[1]]
        if not h0 or not h0[0].lower().startswith('year') or len(h0) < 3 or len(h1) < len(h0): continue
        if h0[1].lower().startswith('route'):
            # winners: one place per category, the categories side by side
            for lab, ncols, mcol in groups(h0, h1):
                cat = category(lab)
                if not cat or not ncols: continue
                for row in m[2:]:
                    y = year_of(row)
                    if y is None: continue
                    people = [n for c in ncols if c < len(row) for n in names_in(row[c])]
                    make = text(row[mcol]) if mcol is not None and mcol < len(row) else ''
                    edition(y, text(row[1]))
                    if people and not re.search(r'cancel|not held|—', ' '.join(people).lower()): pod.setdefault((y, cat), {}).setdefault(1, (people, make))
        else:
            # a podium: 1st, 2nd, 3rd of one category, named by the heading (or caption) above the table
            cap = t.find('caption'); h = t.find_previous(['h2', 'h3', 'h4'])
            cat = category(text(cap)) if cap else None
            if not cat and h is not None: cat = category(text(h))
            if not cat: continue
            h0b = ['Year', 'Route'] + h0[1:]; h1b = ['year', 'route'] + h1[1:]   # the same column grouping, with no route column
            for lab, ncols, mcol in groups(h0b, h1b):
                rk = re.match(r'(\d)', lab)
                if not rk or not ncols: continue
                rank = int(rk.group(1)); ncols = [c - 1 for c in ncols]; mcol = mcol - 1 if mcol is not None else None
                for row in m[2:]:
                    y = year_of(row)
                    if y is None: continue
                    people = [n for c in ncols if c < len(row) for n in names_in(row[c])]
                    make = text(row[mcol]) if mcol is not None and mcol < len(row) else ''
                    edition(y)
                    if people and not re.search(r'cancel|not held|—', ' '.join(people).lower()): pod.setdefault((y, cat), {})[rank] = (people, make)
    for (y, cat), ranks in pod.items():
        out[y]['podium'][cat] = [(r, ranks[r][0], ranks[r][1]) for r in sorted(ranks)]
    return out

def make_of(txt, marques):
    f = fold(txt)
    best = max((m for m in marques if f.startswith(fold(m))), key=lambda m: len(fold(m)), default=None)
    return best or (txt.split()[0] if txt.split() else txt)

def stops_of(route, cities):
    r = route
    for a, b in FIX: r = r.replace(a, b)
    return [s.replace('_', '-').strip() for s in re.split(r'\s*[–-]\s*', r) if s.replace('_', '-').strip() in cities]

def era_of(y): return 'Saudi Arabia' if y >= 2020 else 'South America' if y >= 2009 else 'Africa'

def place_coords(names, log):
    """Coordinates of towns the gazetteer lacks, from their Wikipedia articles (the coordinates the article carries)."""
    out = {}
    try:
        import urllib.parse
        from common import get_json
        j = get_json('https://en.wikipedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'prop': 'coordinates', 'titles': '|'.join(names), 'redirects': 1, 'format': 'json', 'formatversion': 2}), pause=1.0)
        q = j.get('query', {}); back = {r['to']: r['from'] for r in q.get('redirects', [])}; back.update({n['to']: n['from'] for n in q.get('normalized', [])})
        for pg in q.get('pages', []):
            c = (pg.get('coordinates') or [None])[0]
            if c: out[back.get(pg['title'], pg['title'])] = [round(c['lon'], 2), round(c['lat'], 2)]
    except Exception as e: log.append(f'  - town coordinates not read ({e})')
    return out

def diagnose(page, read, held):
    """What the reader saw, for the report when the proof fails: each table's two header rows, the category and the
    place columns it inferred, and what it read for the editions it was checked on."""
    out = ['', '<details><summary>What the reader saw</summary>', '']
    for t in page.soup.find_all('table', class_=re.compile('wikitable'))[:20]:
        m = grid(t)
        if len(m) < 2: continue
        h0 = [text(c) for c in m[0]]; h1 = [text(c).lower() for c in m[1]] if len(m) > 2 else []
        cat = category(' '.join(h0[2:])) if len(h0) > 2 else None
        places = []; names = []
        for i in range(2, len(h1)):
            if MAKE_COL.search(h1[i]): places.append((names, i)); names = []
            else: names.append(i)
        out.append(f'- table ({len(m) - 2} rows): {" | ".join(h[:16] for h in h0[:9])}')
        out.append(f'  - second header: {" | ".join(h[:16] for h in h1[:9])} → category {cat}, places {places[:3]}')
    for y in held:
        out.append(f'- {y} as read: ' + '; '.join(f'{c}: {[(r, p[0], mk[:14]) for r, p, mk in pod]}' for c, pod in read.get(y, {}).get('podium', {}).items()) if y in read else f'- {y}: not read from any table')
    return out + ['', '</details>']

def sweep(log, get_page=None, today=None):
    today = today or datetime.date.today()
    if get_page is None:
        from wiki import parse_page as get_page
    path = ROOT/'data'/'dakar.json'; A = json.loads(path.read_text(encoding='utf-8'))
    page = get_page(TITLE)
    if page is None: raise SystemExit('the Dakar Rally article could not be read — nothing written')
    read = read_article(page)
    P = A['people']; by_name = {fold(v['name']): k for k, v in P.items()}
    eds = {e['y']: e for e in A['editions']}
    # 1. prove the reader on the two latest editions the archive holds
    held = sorted(y for y, e in eds.items() if not e['cancelled'])[-2:]
    have = checked = 0; bad = []
    for y in held:
        for cat, rank, driver, crew, make in eds[y]['results']:
            checked += 1
            got = next((x for x in read.get(y, {}).get('podium', {}).get(cat, []) if x[0] == rank), None)
            if got and fold(got[1][0]) == fold(P.get(driver, {}).get('name', driver)): have += 1
            else: bad.append(f'{y} {cat} {rank}: archive {P.get(driver, {}).get("name", driver)}, read {got[1][0] if got else "nothing"}')
    log.append(f'Check on {", ".join(map(str, held))}: the reader reproduces {have} of the archive\'s {checked} podium places ({have / max(checked, 1):.1%}).')
    if not checked or have / checked < AGREE:
        log += [f'  - {b}' for b in bad[:12]]
        log += diagnose(page, read, held)
        raise SystemExit('the article did not read back as the archive holds it — the layout may have changed; nothing written')
    # 2. a new edition, or the newest completed
    latest = max(eds)
    todo = [y for y in sorted(read) if y > latest or (y == latest == today.year)]
    changed = False
    def pid(name):
        f = fold(name)
        if f in by_name: return by_name[f]
        i = slug(name); k = 2
        while i in P: i = f'{slug(name)}-{k}'; k += 1
        P[i] = {'id': i, 'name': name}; by_name[f] = i; log.append(f'  - new name: {name}'); return i
    for y in todo:
        e = read[y]; rows = []
        for cat in CATS:
            for rank, people, make in e['podium'].get(cat, []):
                rows.append([cat, rank, pid(people[0]), [pid(n) for n in people], make_of(make, A['marques'])])
        if not rows: continue
        old = eds.get(y)
        if old and len(rows) <= len(old['results']): continue
        towns = [t.strip() for t in re.split(r'\s*[–-]\s*', e['route']) if t.strip()]
        unknown = [t for t in towns if t not in A['map']['cities']]
        if unknown and get_page is not None and not getattr(get_page, 'offline', False):
            found = place_coords(unknown, log)
            for t, c in found.items(): A['map']['cities'][t] = c; log.append(f'  - {t} added to the route map ({c[1]}, {c[0]})')
        stops = stops_of(e['route'], A['map']['cities'])
        missing = [s for s in towns if s not in stops]
        ed = {'y': y, 'route': re.sub(r'\s*[–]\s*', '–', e['route']), 'stops': stops, 'era': era_of(y), 'cancelled': False, 'results': rows, 'cats': [c for c in CATS if any(r[0] == c for r in rows)]}
        if old: A['editions'] = [ed if x['y'] == y else x for x in A['editions']]; log.append(f'- **{y}** completed: {len(rows)} podium places')
        else: A['editions'].append(ed); log.append(f'- **{y} Dakar Rally** ({ed["route"]}): {len(rows)} podium places in {len(ed["cats"])} classes; Cars won by {P[rows[0][2]]["name"] if rows[0][0] == "Cars" else "—"}')
        if missing: log.append(f'  - towns not in the gazetteer (not drawn on the route map): {", ".join(missing)}')
        for r in rows:
            if r[4] not in A['marques']: A['marques'].append(r[4]); log.append(f'  - new marque: {r[4]}')
        changed = True
    if not changed: log.append('- nothing new'); return
    A['editions'].sort(key=lambda e: e['y']); A['marques'].sort()   # the archive's own order (plain sort)
    E = A['editions']
    A['coverage'].update(editions=len(E), held=sum(1 for e in E if not e['cancelled']), cancelled=sum(1 for e in E if e['cancelled']), podiums=sum(len(e['results']) for e in E),
                         wins=sum(1 for e in E for x in e['results'] if x[1] == 1), people=len(P), marques=len(A['marques']))
    A['lastYear'] = max(e['y'] for e in E); A['snapshot'] = A['retrieved'] = today.isoformat()
    if page.revid: A['revision'] = str(page.revid)
    path.write_text(json.dumps(A, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    log.append(f'\nArchive now {len(E)} editions, through {A["lastYear"]}.')
