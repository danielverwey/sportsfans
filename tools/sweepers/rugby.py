"""Rugby union: new Tests of the ten nations from Nuck's Rugby Archive (https://rugbyarchive.github.io/) — the archive
this atlas was built from — read from the data file its own pages load (data/archive-data.js), in one request.

The file is `window.RUGBY_DATA = {meta, fields, lookups, <rows>}`: each match a row of the listed fields, with teams,
grounds, cities, countries and competitions given as positions in the lookup lists. The reader does not assume more
than that: it finds the rows, decodes them, and then learns the archive's own conventions from the Tests both hold —
which classes of match the atlas counts as Tests, how a World Cup stage is named, how a competition is filed.

Before anything is written, the reader must reproduce the Tests of the last two years that the atlas already holds from
this source (same date, same sides, same score) in at least 90% of cases; if it does not, the layout has changed and
nothing is written. New Tests are only ever appended after the atlas's last Test, so the ids that players and coaches
link to never move. Earlier rows that differ or are missing are listed for review, never changed. Player and coach
snapshots stay as dated; they are not extended from results.
"""
import collections, datetime, json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0, str(ROOT/'tools'/'harvest'))
from wiki import slug

URL = 'https://rugbyarchive.github.io/data/archive-data.js'
SOURCE = 'https://rugbyarchive.github.io/'
LOOKUP = {'home': 'teams', 'away': 'teams', 'stadium': 'stadium', 'city': 'city', 'country': 'country', 'competition': 'competition'}
AGREE = 0.9
PROVE_DAYS = 730
# three-letter codes for sides the atlas has not met yet (the atlas's own codes are read from its sourceIds first)
ISO = {'Austria': 'AUT', 'Belgium': 'BEL', 'Botswana': 'BWA', 'Bulgaria': 'BGR', 'Cameroon': 'CMR', 'China': 'CHN', 'Colombia': 'COL', 'Cook Islands': 'COK',
       'Cyprus': 'CYP', 'Finland': 'FIN', 'Ghana': 'GHA', 'Guyana': 'GUY', 'Hong Kong': 'HKG', 'Hong Kong China': 'HKG', 'Hungary': 'HUN', 'India': 'IND',
       'Israel': 'ISR', 'Jamaica': 'JAM', 'Kazakhstan': 'KAZ', 'Kenya': 'KEN', 'Latvia': 'LVA', 'Lithuania': 'LTU', 'Luxembourg': 'LUX', 'Malaysia': 'MYS',
       'Malta': 'MLT', 'Mexico': 'MEX', 'Moldova': 'MDA', 'Nigeria': 'NGA', 'Niue': 'NIU', 'Norway': 'NOR', 'Pakistan': 'PAK', 'Papua New Guinea': 'PNG',
       'Philippines': 'PHL', 'Senegal': 'SEN', 'Serbia': 'SRB', 'Singapore': 'SGP', 'Slovenia': 'SVN', 'Sri Lanka': 'LKA', 'Sweden': 'SWE', 'Switzerland': 'CHE',
       'Chinese Taipei': 'TPE', 'Taiwan': 'TPE', 'Thailand': 'THA', 'Trinidad and Tobago': 'TTO', 'Uganda': 'UGA', 'Ukraine': 'UKR', 'United Arab Emirates': 'ARE',
       'Venezuela': 'VEN', 'Zambia': 'ZMB', 'Algeria': 'DZA', 'Andorra': 'AND', 'Bosnia and Herzegovina': 'BIH', 'Tahiti': 'PYF', 'Barbarians': 'BAR'}

# ---------------------------------------------------------------- reading the file
def parse(raw):
    """The object assigned to RUGBY_DATA (the first JSON value after the '=')."""
    t = raw.decode('utf-8-sig') if isinstance(raw, bytes) else raw
    m = re.search(r'RUGBY_DATA\s*=\s*', t)
    start = m.end() if m else t.index('{')
    obj, _ = json.JSONDecoder().raw_decode(t[start:].lstrip())
    return obj

def rows_of(D):
    """The match rows as dicts keyed by the file's field names, wherever the file keeps them."""
    F = D.get('fields') or []
    def cols(v):
        if isinstance(v, dict) and all(f in v for f in ('date', 'home', 'away')) and isinstance(v['date'], list):
            n = len(v['date']); return [{f: v[f][i] for f in v if isinstance(v[f], list) and len(v[f]) == n} for i in range(n)]
    for k, v in D.items():
        if k in ('meta', 'fields', 'lookups'): continue
        if isinstance(v, list) and v:
            if F and all(isinstance(r, list) and len(r) == len(F) for r in v[:50]): return [dict(zip(F, r)) for r in v]
            if all(isinstance(r, dict) and 'date' in r for r in v[:50]): return v
        c = cols(v)
        if c: return c
    c = cols(D)
    if c: return c
    raise SystemExit(f'the data file holds no match rows the reader recognises (top-level keys: {", ".join(D)}) — nothing written')

def truthy(v): return v not in (None, False, 0, 0.0, '', 'N', 'n', 'No', 'no', 'FALSE', 'False', 'false', '0', 'n/a', '-')

def dates_decoder(values, today):
    """ISO strings, yyyymmdd numbers, days since 1970 or Excel serials — whichever makes sense of the whole column."""
    nums = [int(v) for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    def iso(v):
        if isinstance(v, str):
            m = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', v) or None
            if m: return datetime.date(int(m[1]), int(m[2]), int(m[3]))
            m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', v)
            if m: return datetime.date(int(m[3]), int(m[2]), int(m[1]))
        return None
    ways = {'yyyymmdd': lambda n: datetime.date(n // 10000, n // 100 % 100, n % 100),
            'epoch': lambda n: datetime.date(1970, 1, 1) + datetime.timedelta(days=n),
            'excel': lambda n: datetime.date(1899, 12, 30) + datetime.timedelta(days=n)}
    best = None
    if nums:
        for name, f in ways.items():
            try: top = max(f(n) for n in nums); low = min(f(n) for n in nums)
            except (ValueError, OverflowError): continue
            if top <= today + datetime.timedelta(days=60) and low.year >= 1860 and (best is None or top > best[1]): best = (name, top)
    num = ways[best[0]] if best else None
    def dec(v):
        d = iso(v)
        if d is None and num and isinstance(v, (int, float)) and not isinstance(v, bool):
            try: d = num(int(v))
            except (ValueError, OverflowError): d = None
        return d.isoformat() if d else None
    return dec

def decoded(D, today):
    L = D.get('lookups') or {}
    R = rows_of(D)
    dec = dates_decoder([r.get('date') for r in R], today)
    def look(f, v):
        lk = L.get(LOOKUP.get(f, ''))
        if lk is None or isinstance(v, bool): return v
        if isinstance(v, int) and isinstance(lk, list): return lk[v] if 0 <= v < len(lk) else None
        if isinstance(lk, dict) and v is not None and str(v) in lk: return lk[str(v)]
        return v
    def score(v):
        try: return int(v)
        except (TypeError, ValueError): return None
    out = []
    for r in R:
        x = {f: look(f, v) for f, v in r.items()}
        x['date'] = dec(r.get('date')); x['home_score'] = score(r.get('home_score')); x['away_score'] = score(r.get('away_score'))
        for f in ('stadium', 'city', 'country', 'competition'):
            if isinstance(x.get(f), str): x[f] = x[f].strip() or None
        out.append(x)
    return out

# ---------------------------------------------------------------- the archive's conventions
def category(raw, learned):
    if raw:
        k = re.sub(r'\d{4}', 'Y', raw)
        if k in learned: return learned[k]
    t = (raw or '').lower()
    if re.search(r'world cup', t) and not re.search(r'sevens|women|qualif|u2\d|under', t): return 'World Cup'
    if re.search(r'\b(six|five|four|home) nations\b', t): return 'Six / Five / Home Nations'
    if re.search(r'rugby championship|tri.?nations', t): return 'Rugby Championship / Tri Nations'
    if re.search(r'\blions\b', t): return 'Lions series'
    if re.search(r'nations championship', t): return 'Nations Championship'
    if re.search(r'olympic', t): return 'Historical / Olympic'
    return 'Test / international'

def stage_of(r, learned):
    k = (str(r.get('match_type') or ''), str(r.get('trophy') or ''))
    if k in learned: return learned[k]
    t = ' '.join(k).lower()
    if re.search(r'bronze|third', t): return 'Bronze final'
    if re.search(r'quarter.?final.?play.?off', t): return 'Quarter-final playoff'
    if 'quarter' in t: return 'Quarter-final'
    if 'semi' in t: return 'Semi-final'
    if re.search(r'\bfinal\b', t): return 'Final'
    return 'Pool match'

def codes_of(M):
    out = {}
    for m in M:   # in date order: the latest code a side played under wins
        s = m.get('sourceId')
        if s:
            h, a = s.split('-')[:2]; out[m['home']] = h; out[m['away']] = a
    return out

def code(team, codes):
    if team in codes: return codes[team]
    if team in ISO: return ISO[team]
    return (re.sub(r'[^A-Z]', '', slug(team).upper()) + 'XXX')[:3]

# ---------------------------------------------------------------- the sweep
def fetch():
    from common import get
    return get(URL, pause=1.0, headers={'Accept': 'application/javascript, text/javascript, */*'})

def sweep(log, fetch_raw=None, today=None):
    today = today or datetime.date.today()
    path = ROOT/'data'/'rugby.json'; A = json.loads(path.read_text(encoding='utf-8'))
    M = A['matches']; TEN = [t['name'] for t in A['teams']]; tenset = set(TEN)
    D = parse((fetch_raw or fetch)())
    meta = D.get('meta') or {}
    rows = [r for r in decoded(D, today) if r['date'] and r.get('home') and r.get('away')]
    log.append(f'Read {len(rows):,} matches from Nuck\'s Rugby Archive (built {meta.get("built", "?")}, last match {meta.get("last_match") or max(r["date"] for r in rows)}).')
    missing = [t for t in TEN if not any(t in (r['home'], r['away']) for r in rows)]
    if missing: raise SystemExit(f'the file does not name {", ".join(missing)} as it did — team names may have changed; nothing written')

    by_key = {}; by_pair = collections.defaultdict(list)
    for r in rows:
        by_key[(r['date'], r['home'], r['away'])] = r; by_pair[frozenset((r['home'], r['away']))].append(r)
    def find(m):
        r = by_key.get((m['date'], m['home'], m['away'])) or by_key.get((m['date'], m['away'], m['home']))
        if r: return r
        d0 = datetime.date.fromisoformat(m['date'])
        near = [r for r in by_pair.get(frozenset((m['home'], m['away'])), []) if abs((datetime.date.fromisoformat(r['date']) - d0).days) <= 3]
        return near[0] if len(near) == 1 else None
    def same(m, r):
        return (r['home'], r['home_score'], r['away_score']) == (m['home'], m['hs'], m['as_']) or (r['away'], r['away_score'], r['home_score']) == (m['home'], m['hs'], m['as_'])

    # 1. prove the reader on the Tests of the last two years the atlas already holds from this source
    last = max(m['date'] for m in M)
    since = (datetime.date.fromisoformat(last) - datetime.timedelta(days=PROVE_DAYS)).isoformat()
    recent = [m for m in M if m['date'] >= since and SOURCE in m['sources']]
    good = []; bad = []
    for m in recent:
        r = find(m)
        (good if r and same(m, r) else bad).append((m, r))
    log.append(f'Check on {since} to {last}: the file reproduces {len(good)} of the atlas\'s {len(recent)} Tests from this source ({len(good) / max(len(recent), 1):.1%}).')
    if not recent or len(good) / len(recent) < AGREE:
        reads = lambda r: f'{r["home"]} {r["home_score"]}–{r["away_score"]} {r["away"]}' if r else 'nothing'
        log += [f'  - {m["date"]} {m["home"]} {m["hs"]}–{m["as_"]} {m["away"]}: file reads {reads(r)}' for m, r in bad[:12]]
        raise SystemExit('the file did not read back as the atlas holds it — the layout may have changed; nothing written')

    # 2. learn the atlas's conventions from every Test both hold
    held = {(m['date'], frozenset((m['home'], m['away']))) for m in M}
    pairs = [(m, find(m)) for m in M if SOURCE in m['sources']]
    pairs = [(m, r) for m, r in pairs if r]
    cat = collections.defaultdict(collections.Counter)
    for m in M:
        if m['competitionRaw']: cat[re.sub(r'\d{4}', 'Y', m['competitionRaw'])][m['competition']] += 1
    cats = {k: c.most_common(1)[0][0] for k, c in cat.items()}
    stg = collections.defaultdict(collections.Counter)
    for m, r in pairs:
        if m['worldcup']: stg[(str(r.get('match_type') or ''), str(r.get('trophy') or ''))][m['stage']] += 1
    stages = {k: c.most_common(1)[0][0] for k, c in stg.items() if c.most_common(1)[0][1] >= 0.8 * sum(c.values())}
    wc_field = [truthy(r.get('world_cup')) == bool(m['worldcup']) for m, r in pairs if 'world_cup' in r]
    by_flag = bool(wc_field) and sum(wc_field) >= 0.98 * len(wc_field)
    def is_wc(r): return truthy(r.get('world_cup')) if by_flag else category(r.get('competition'), {}) == 'World Cup'
    klass = lambda r: (str(r.get('match_class')), str(r.get('full_intl')), str(r.get('eligible')))
    inc, exc = collections.Counter(), collections.Counter()
    for r in rows:
        if r['date'] < '1990-01-01' or r['date'] > last or not ({r['home'], r['away']} & tenset): continue
        (inc if (r['date'], frozenset((r['home'], r['away']))) in held else exc)[klass(r)] += 1
    counts = lambda r: inc[klass(r)] > 0 and inc[klass(r)] >= exc[klass(r)]

    # 3. differences on Tests already held (reported, never changed)
    for m, r in pairs:
        if m['date'] >= since and not same(m, r):
            log.append(f'  - review: {m["date"]} {m["home"]} {m["hs"]}–{m["as_"]} {m["away"]} — the file now reads {r["home"]} {r["home_score"]}–{r["away_score"]} {r["away"]} (the atlas is unchanged)')

    # 4. new Tests after the atlas's last one
    cand = sorted((r for r in rows if ({r['home'], r['away']} & tenset) and r['date'] <= today.isoformat() and (r['date'], frozenset((r['home'], r['away']))) not in held),
                  key=lambda r: (r['date'], r.get('seq') if isinstance(r.get('seq'), (int, float)) else 0))
    late = [r for r in cand if r['date'] <= last and r['date'] >= since and counts(r)]
    for r in late:
        log.append(f'  - review: {r["date"]} {r["home"]} {r["home_score"]}–{r["away_score"]} {r["away"]} is in the file but not in the atlas; it predates the atlas\'s last Test, so it is not inserted (ids never move)')
    new = []
    for r in (r for r in cand if r['date'] > last):
        if r['home_score'] is None or r['away_score'] is None: continue
        if not counts(r):
            log.append(f'  - left out: {r["date"]} {r["home"]} v {r["away"]} (a class of match the atlas does not count as a Test: {klass(r)})'); continue
        new.append(r)
    if not new:
        log.append('- nothing new'); return

    codes = codes_of(M); seen = collections.Counter()
    for r in new:
        y = int(r['date'][:4]); wc = is_wc(r)
        venue = r.get('stadium') or 'Ground not recorded'; city = r.get('city'); country = r.get('country')
        raw = r.get('competition')
        comp = 'World Cup' if wc else category(raw, cats)
        if comp == 'World Cup' and not wc: comp = 'Test / international'
        sid = f'{code(r["home"], codes)}-{code(r["away"], codes)}-{r["date"]}'; seen[sid] += 1
        m = {'date': r['date'], 'home': r['home'], 'away': r['away'], 'hs': r['home_score'], 'as_': r['away_score'], 'venue': venue, 'city': city, 'country': country,
             'competitionRaw': raw, 'stage': stage_of(r, stages) if wc else None, 'worldcup': y if wc else None, 'historical': False,
             'eligible': [t for t in TEN if t in (r['home'], r['away'])], 'sources': [SOURCE], 'sourceId': f'{sid}-{seen[sid]:03d}',
             'dateUncertain': truthy(r.get('date_guessed')), 'notes': [], 'scoreUnit': 'points', 'competition': comp,
             'stadium': slug(f'{venue} {city or ""}'), 'id': len(M), 'year': y}
        M.append(m)
        log.append(f'- **{m["date"]}** {m["home"]} {m["hs"]}–{m["as_"]} {m["away"]} · {venue}{", " + city if city else ""} · {raw or comp}' + (f' · {m["stage"]}' if wc else ''))
    # 5. the registers the atlas keeps beside the results
    for t in A['teams']:
        mine = [m for m in M if t['name'] in m['eligible']]
        t['count'] = len(mine); t['through'] = max(m['date'] for m in mine)
    A['through'] = M[-1]['date']; A['asof'] = today.isoformat()
    am = A.get('archiveMeta') or {}
    for k in am:
        if k in meta: am[k] = meta[k]
    log.append(f'\nAtlas now {len(M):,} Tests, through {A["through"]}. Player and coach snapshots stay dated {A.get("coachAsOf")}.')
    path.write_text(json.dumps(A, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
