"""Bring the UFC harvest into the site.

  python3 tools/prepare_ufc.py [build/harvest/ufc.json]

Reads the clean-room harvest (tools/harvest/wiki_ufc.py: events, bouts, fighters from Wikipedia, CC BY-SA 4.0; fighter
facts from Wikidata, CC0) and writes data/ufc.json — the archive the atlas, the static pages and the reading edition
read. Everything derived here is derived from the transcribed rows and marked as such in the method note: the division
key from the weight-class label, the method kind from the method text, the title flag from the notes, elapsed time from
round and time, each fighter's record from the bouts. Nothing else is altered.
"""
import json, re, sys, pathlib, collections, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT/'build'/'harvest'/'ufc.json')
H = json.loads(src.read_text(encoding='utf-8'))
slug = lambda s: re.sub(r'[^a-z0-9]+', '-', str(s).lower().replace('’', '').replace("'", '')).strip('-')

# ---- divisions: the weight-class label → a key, a display label, the limit, the sex
DIVS = [('hw', 'Heavyweight', 265, 'M'), ('lhw', 'Light Heavyweight', 205, 'M'), ('mw', 'Middleweight', 185, 'M'), ('ww', 'Welterweight', 170, 'M'), ('lw', 'Lightweight', 155, 'M'), ('fw', 'Featherweight', 145, 'M'), ('bw', 'Bantamweight', 135, 'M'), ('flw', 'Flyweight', 125, 'M'),
        ('wfw', 'Women’s Featherweight', 145, 'W'), ('wbw', 'Women’s Bantamweight', 135, 'W'), ('wflw', 'Women’s Flyweight', 125, 'W'), ('wsw', 'Women’s Strawweight', 115, 'W'), ('wat', 'Women’s Atomweight', 105, 'W'),
        ('shw', 'Super Heavyweight', None, 'M'), ('open', 'Openweight', None, 'M'), ('catch', 'Catchweight', None, None)]
DIV = {d[0]: {'key': d[0], 'label': d[1], 'lb': d[2], 'sex': d[3], 'order': i} for i, d in enumerate(DIVS)}
def div_of(label):
    t = (label or '').lower().replace('’', "'")
    women = "women" in t or 'female' in t
    if 'catch' in t: return 'catch'
    if 'open' in t or 'no weight' in t or 'absolute' in t: return 'open'
    if 'super heavy' in t or 'superheavy' in t: return 'shw'
    if 'atom' in t: return 'wat'
    longest = sorted(DIVS, key=lambda d: -len(d[1]))  # 'light heavyweight' before 'heavyweight'
    for k, name, lb, sex in longest:
        n = name.lower().replace('women’s ', '')
        if n in t and (sex == 'W') == women: return k
    for k, name, lb, sex in longest:  # a plain 'Bantamweight' for a women's bout is still bantamweight
        n = name.lower().replace('women’s ', '')
        if n in t: return k if not women else {'fw': 'wfw', 'bw': 'wbw', 'flw': 'wflw'}.get(k, k)
    return 'open' if not t else 'catch'
def catch_lb(label):
    m = re.search(r'(\d{2,3})\s*(?:lb|lbs|pounds)', (label or '').lower()); return int(m.group(1)) if m else None

# ---- methods: the method text → a kind and its detail
def method_kind(method, sep):
    m = (method or '').lower()
    if 'no contest' in m or m.startswith('nc'): return 'NC'
    if m.startswith('draw'): return 'DRAW'
    if m.startswith('tko') or m.startswith('ko') or 'technical knockout' in m or 'knockout' in m: return 'KO'
    if 'submission' in m: return 'SUB'
    if m.startswith('decision') or m.startswith('technical decision'): return 'DEC'
    if 'dq' in m.split('(')[0] or 'disqualif' in m: return 'DQ'
    if sep == 'vs.': return 'NC'
    return 'OTHER'
def detail_of(method):
    m = re.search(r'\((.*?)\)', method or ''); return m.group(1).strip() if m else ''
def dec_kind(method):
    m = (method or '').lower()
    for k in ('unanimous', 'split', 'majority', 'technical'):
        if k in m: return k
    return ''

# ---- titles from the notes and the card
def title_of(notes, card, wc):
    n = (notes or '').lower(); c = (card or '').lower()
    t = {}
    m = re.search(r'for the (vacant )?(interim )?(?:ufc )?(?:women\'s |women’s )?(.+?) (?:title|championship)', n)
    if m: t['title'] = 'interim' if m.group(2) else 'vacant' if m.group(1) else 'title'
    elif 'championship' in n and 'for the' in n: t['title'] = 'title'
    if 'superfight' in n or 'superfight' in c: t['title'] = t.get('title', 'title')
    if 'tournament' in n or 'tournament' in c or any(w in c for w in ('quarterfinal', 'semifinal', 'final', 'alternate', 'reserve')):
        t['tour'] = 'final' if ('final' in c and 'semi' not in c and 'quarter' not in c) or 'tournament final' in n else 'semi' if 'semi' in c else 'quarter' if 'quarter' in c else 'alternate' if 'alternate' in c or 'reserve' in c else 'round'
    return t
def card_kind(card):
    c = (card or '').lower()
    if 'early' in c: return 'early'
    if 'prelim' in c: return 'prelim'
    if 'main' in c: return 'main'
    if any(w in c for w in ('final', 'semi', 'quarter', 'alternate', 'reserve', 'tournament', 'round')): return 'tournament'
    return 'other'

# ---- places
COUNTRY = {'u.s.': 'United States', 'us': 'United States', 'usa': 'United States', 'u.s.a.': 'United States', 'united states of america': 'United States', 'u.k.': 'United Kingdom', 'uk': 'United Kingdom', 'england': 'United Kingdom', 'scotland': 'United Kingdom', 'wales': 'United Kingdom', 'northern ireland': 'United Kingdom', 'uae': 'United Arab Emirates', 'south korea': 'South Korea', 'republic of korea': 'South Korea', 'russian federation': 'Russia', 'people\'s republic of china': 'China', 'prc': 'China'}
UK = {'england', 'scotland', 'wales', 'northern ireland'}
def place_of(city):
    parts = [p.strip() for p in (city or '').split(',') if p.strip()]
    if not parts: return '', ''
    last = parts[-1]; country = COUNTRY.get(last.lower(), last)
    town = ', '.join(parts[:-1]) if len(parts) > 1 else ''
    if last.lower() in UK: town = ', '.join(parts[:-1] + [last]) if parts[:-1] else last
    if not town: town = last if country != last else ''
    return town, country

# ---- events
events = []; bouts_by_event = {}
for ev in H['events']:
    name = ev['name'] or ev['title']; m = re.match(r'^(UFC \d+[A-Za-z]?|UFC Fight Night|UFC on [A-Za-z0-9+ ]+?|UFC Live|UFC Fight for the Troops|The Ultimate Fighter[^:]*|UFC [A-Za-z ]+?)\s*(?::|-|–)\s*(.+)$', name)
    short, sub = (m.group(1).strip(), m.group(2).strip()) if m else (name, '')
    kind = 'ppv' if re.match(r'^UFC \d+[A-Za-z]?$', short) else 'tuf' if 'ultimate fighter' in short.lower() else 'fight night'
    town, country = place_of(ev.get('city') or '')
    venue = (ev.get('venue') or '').strip()
    events.append({'id': ev['id'], 'n': ev.get('n'), 'name': name, 'short': short, 'sub': sub, 'kind': kind, 'date': ev['date'], 'y': ev['y'], 'venue': venue, 'city': town, 'country': country, 'att': ev.get('attendance'), 'gate': ev.get('gate'), 'buys': ev.get('buyrate'), 'url': ev.get('url'), 'bouts': list(ev['bouts']), 'bonuses': [{'t': b['type'], 'who': b.get('titles') or b.get('who') or []} for b in ev.get('bonuses', [])]})
events.sort(key=lambda e: (e['date'], e['n'] or 0))
E = {e['id']: e for e in events}

# ---- bouts
F = {fid: dict(f) for fid, f in H['fighters'].items()}
BF = ['id', 'e', 'y', 'date', 'n', 'card', 'ck', 'wc', 'div', 'lb', 'a', 'b', 'w', 'res', 'method', 'mk', 'det', 'dk', 'round', 'time', 'secs', 'title', 'tour', 'champ', 'notes']
rows = []; div_seen = collections.Counter(); women = set()
FIVE_MINUTE_ROUNDS = '1999-07-16'  # UFC 21: five-minute rounds; before that a long first round and short overtimes
def secs_of(rnd, tm, date):
    if not tm or not re.fullmatch(r'\d{1,2}:\d{2}', tm): return None
    mm, ss = tm.split(':'); s = int(mm) * 60 + int(ss)
    if rnd is None: return None
    if date >= FIVE_MINUTE_ROUNDS: return (rnd - 1) * 300 + s
    return s if rnd == 1 else None
for b in H['bouts']:
    if b['e'] not in E: continue
    dk = div_of(b['wc']); t = title_of(b['notes'], b['card'], b['wc']); mk = method_kind(b['method'], b['sep'])
    res = 'W' if b['sep'] == 'def.' and mk not in ('NC', 'DRAW') else 'D' if mk == 'DRAW' else 'NC'
    w = b['a'] if res == 'W' else None
    rows.append({'id': b['id'], 'e': b['e'], 'y': b['y'], 'date': b['date'], 'n': b['n'], 'card': b['card'], 'ck': card_kind(b['card']), 'wc': b['wc'], 'div': dk, 'lb': catch_lb(b['wc']) if dk == 'catch' else DIV[dk]['lb'], 'a': b['a'], 'b': b['b'], 'w': w, 'res': res, 'method': b['method'], 'mk': mk, 'det': detail_of(b['method']), 'dk': dec_kind(b['method']) if mk == 'DEC' else '', 'round': b['round'], 'time': b['time'], 'secs': secs_of(b['round'], b['time'], b['date']), 'title': t.get('title'), 'tour': t.get('tour'), 'champ': b.get('champ') or [], 'notes': b['notes']})
    div_seen[dk] += 1
    if DIV[dk]['sex'] == 'W': women.update((b['a'], b['b']))
for r in rows:  # a catchweight between two women is a women's bout
    if r['div'] == 'catch' and r['a'] in women and r['b'] in women: r['sex'] = 'W'
    else: r['sex'] = DIV[r['div']]['sex'] or 'M'
BF.append('sex')
rows.sort(key=lambda r: (r['date'], E[r['e']]['n'] or 0, r['n']))
for e in events: e['bouts'] = [r['id'] for r in rows if r['e'] == e['id']]

# ---- fighters: record and span from the bouts
rec = collections.defaultdict(lambda: {'w': 0, 'l': 0, 'd': 0, 'nc': 0, 'first': None, 'last': None, 'divs': collections.Counter(), 'ko': 0, 'sub': 0, 'title': 0, 'titleW': 0})
for r in rows:
    for side in ('a', 'b'):
        fid = r[side]; x = rec[fid]
        if r['res'] == 'W': x['w' if fid == r['w'] else 'l'] += 1
        elif r['res'] == 'D': x['d'] += 1
        else: x['nc'] += 1
        x['first'] = min(x['first'] or r['y'], r['y']); x['last'] = max(x['last'] or r['y'], r['y']); x['divs'][r['div']] += 1
        if fid == r['w'] and r['mk'] == 'KO': x['ko'] += 1
        if fid == r['w'] and r['mk'] == 'SUB': x['sub'] += 1
        if r['title']: x['title'] += 1; x['titleW'] += 1 if fid == r['w'] else 0
fighters = {}
for fid, f in F.items():
    x = rec.get(fid)
    if not x: continue
    nat = f.get('nat') or []
    fighters[fid] = {'id': fid, 'name': f['name'], 'url': f.get('url'), 'nat': nat[0] if nat else None, 'dob': f.get('dob') if f.get('dob') and not f['dob'].endswith('-00-00') else None, 'cm': f.get('height_cm'), 'rec': [x['w'], x['l'], x['d'], x['nc']], 'ko': x['ko'], 'sub': x['sub'], 'first': x['first'], 'last': x['last'], 'div': x['divs'].most_common(1)[0][0], 'divs': [d for d, _ in x['divs'].most_common()], 'title': x['title'], 'titleW': x['titleW']}
for r in rows:
    for side in ('a', 'b'):
        if r[side] not in fighters: fighters[r[side]] = {'id': r[side], 'name': r[side].replace('-', ' ').title(), 'url': None, 'nat': None, 'dob': None, 'cm': None, 'rec': [0, 0, 0, 0], 'ko': 0, 'sub': 0, 'first': r['y'], 'last': r['y'], 'div': r['div'], 'divs': [r['div']], 'title': 0, 'titleW': 0}

# ---- venues, listed (never drawn): the venue where the archive names one, the town otherwise
venues = {}
for e in events:
    key = slug(e['venue'] or e['city'] or e['country'] or 'unknown')
    v = venues.get(key) or venues.setdefault(key, {'id': key, 'name': e['venue'] or e['city'] or e['country'] or 'Unrecorded', 'city': e['city'], 'country': e['country'], 'n': 0, 'first': e['y'], 'last': e['y'], 'events': []})
    v['n'] += 1; v['first'] = min(v['first'], e['y']); v['last'] = max(v['last'], e['y']); v['events'].append(e['id']); e['venueId'] = key

core = {'events': events, 'boutFields': BF, 'bouts': [[r.get(k) for k in BF] for r in rows], 'fighters': fighters, 'divisions': [DIV[k] for k, *_ in DIVS if div_seen[k]], 'venues': venues, 'issues': H.get('issues', []),
        'sources': H.get('sources', []), 'licence': H.get('licence'), 'licenceUrl': H.get('licenceUrl'), 'snapshot': H.get('snapshot'), 'lastDate': max(e['date'] for e in events), 'lastYear': max(e['y'] for e in events),
        'coverage': dict(H.get('coverage', {}), events=len(events), bouts=len(rows), fighters=len(fighters), venues=len(venues), titleBouts=sum(1 for r in rows if r['title']), tournamentBouts=sum(1 for r in rows if r['tour']), withoutTime=sum(1 for r in rows if r['secs'] is None), womensBouts=sum(1 for r in rows if r['sex'] == 'W'), fightersWithNationality=sum(1 for f in fighters.values() if f['nat']), fightersWithBirthDate=sum(1 for f in fighters.values() if f['dob'])),
        'method': (H.get('method', '') + ' Derived here, from those rows alone: the division from the weight-class label (a catchweight between two women counts as a women’s bout), the method kind from the method text, the title flag from the notes, the elapsed time from round and time (five-minute rounds from UFC 21 in July 1999; before that only a first-round time is taken as elapsed), each fighter’s record from the bouts in the archive. Venues are listed as the sources name them and never drawn.').strip()}
out = ROOT/'data'/'ufc.json'; out.write_text(json.dumps(core, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
c = core['coverage']
print(f'ufc: {c["events"]} events · {c["bouts"]:,} bouts · {c["fighters"]:,} fighters · {c["venues"]} venues · {c["titleBouts"]} title bouts · {c["womensBouts"]} women’s bouts · {c["withoutTime"]} bouts without an elapsed time · divisions {dict(div_seen)} · {out.stat().st_size/1e6:.1f} MB')
