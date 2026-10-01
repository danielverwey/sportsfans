"""Summer and Winter Olympics: the next Games from Wikipedia's "List of {year} Summer|Winter Olympics medal winners" (CC BY-SA 4.0) — the
same lists the archive was transcribed from: one table per sport (Event | Gold | Silver | Bronze), each medal cell naming
the delegation and the athletes. The reader first reads the latest Games the archive already holds and must reproduce
its awards; if it does not, nothing is written. A new Games is written only when its medal table article reconciles,
delegation by delegation and colour by colour, with what was read — while the Games are on it is marked provisional and
re-read on every sweep; once the closing date has passed and the tables agree, it is final. Earlier Games are never
rewritten; ids never move.
"""
import datetime, json, pathlib, re, sys, urllib.parse, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0, str(ROOT/'tools'/'harvest'))
from wiki import grid, text, fold, flag
from olympics_common import slug, lineage, gender_of

AGREE = 0.9
SKIP_H2 = re.compile(r'medal table|leading|multiple|see also|references|notes|external links|changes|footnotes|bibliography|sources|contents|summary', re.I)
NATION_AT = re.compile(r'^(.+?) at the (\d{4}) (Summer|Winter) Olympics$')
NOT_A_PERSON = re.compile(r'Summer_Olympics|Winter_Olympics|Olympic_Games|^List_of|_at_the_|^Category:|^File:|^Wikipedia:|^Help:|^Template:', re.I)
MONTHS = 'January February March April May June July August September October November December'.split()
GAZETTEER = {'Los Angeles': [-118.24, 34.05], 'Brisbane': [153.03, -27.47], 'Paris': [2.35, 48.86], 'Tokyo': [139.69, 35.68], 'Salt Lake City': [-111.89, 40.76], 'Nice': [7.27, 43.7], 'French Alps': [6.87, 45.92], 'Milan': [9.19, 45.46]}   # used only when the coordinates API cannot be read

def heading_text(h):
    """The heading's own words, its [edit] link left out."""
    import copy
    if h is None: return ''
    c = copy.copy(h)
    for x in c.find_all(class_=re.compile('mw-editsection')): x.decompose()
    return re.sub(r'\s+', ' ', c.get_text(' ', strip=True)).strip()

def article_of(a):
    """The article title (underscored, as the archive keys athletes) a link points at; None for red links and non-articles."""
    h = a.get('href') or ''
    if 'redlink=1' in h or not h.startswith('/wiki/'): return None
    t = urllib.parse.unquote(h[6:].split('#')[0])
    return t if ':' not in t else None

def award_of(cell, y):
    """(nation, [(athlete id, name)]) named by a medal cell, or None when it names no delegation (not awarded, empty)."""
    if cell is None: return None
    nation = None; athletes = []; seen = set()
    for a in cell.find_all('a', href=True):
        if a.find_parent('sup') or a.find_parent(class_=re.compile('reference|flagicon')): continue
        txt = re.sub(r'\s+', ' ', a.get_text(' ', strip=True))
        if not txt or a.find('img'): continue
        t = article_of(a); m = NATION_AT.match((t or '').replace('_', ' '))
        if m: nation = nation or txt; continue
        if t and NOT_A_PERSON.search(t): continue
        aid = t if t else txt.replace(' ', '_')
        if 'new' in (a.get('class') or []) and t is None: aid = txt.replace(' ', '_')
        if aid not in seen: seen.add(aid); athletes.append((aid, txt))
    if nation is None:
        f = flag(cell)
        if f: nation = f
    if nation is None:
        b = cell.find('b')
        if b and not b.find('a'): nation = text(b)
    if not nation: return None
    if not athletes:   # rosters written as plain text (older lists): names between the nation and the end of the cell
        body = text(cell)
        rest = body.replace(nation, ' ', 1)
        for tok in re.split(r'\s*[,/·]\s*|\s{2,}', rest):
            tok = tok.strip(' ()')
            if len(tok.split()) >= 2 and not re.search(r'\d', tok) and len(tok) < 60: athletes.append((tok.replace(' ', '_'), tok))
    return nation.strip(), athletes

GENERIC_SECTION = re.compile(r"^(medal(l)?ists?|events?|men'?s? events?|women'?s? events?|mixed events?|open events?|results?)$", re.I)
MEDAL_HEAD = (('gold', 1), ('silver', 2), ('bronze', 3))

def read_list(page, y, diag=None):
    """The Games' medal events as the list page holds them: [{'sport','section','event','url','gender','awards': [(rank, nation, [(id, name)])]}]
    in page order. A table counts when a row among its first six holds Gold, Silver and Bronze headers; a row that spans the whole
    table ("Men's events", "Freestyle") names the section of the rows below it. `diag`, a list, collects what was skipped and why."""
    out = []
    for t in page.soup.find_all('table', class_=re.compile('wikitable')):
        if t.find_parent('table'): continue   # the inner table of a layout wrapper is read on its own
        m = grid(t)
        if len(m) < 2: continue
        h2 = t.find_previous('h2'); sport = heading_text(h2)
        if not sport or SKIP_H2.search(sport): continue
        hi = cols = None
        for i, row in enumerate(m[:6]):
            head = [text(c).lower() for c in row]
            if any(h.startswith(('rank', 'noc', 'total')) or h in ('nation', 'nations', 'country', 'team') for h in head): break   # a medal-count table, not an event table
            c = {}
            for j, h in enumerate(head):
                for k, r in MEDAL_HEAD:
                    if h.startswith(k) and r not in c and (j == 0 or row[j] is not row[j - 1]): c[r] = j
            if len(c) == 3: hi, cols = i, c; break
        if hi is None:
            if diag is not None and len(m) >= 3: diag.append(f'{sport}: table of {len(m)} rows not read — first row: ' + ' | '.join(text(c)[:24] for c in m[0][:5]))
            continue
        head = [text(c).lower() for c in m[hi]]
        evc = next((j for j in range(cols[1]) if not head[j].startswith(('gold', 'silver', 'bronze', 'time', 'score', 'result', 'mark', 'note'))), 0)
        sub = t.find_previous(['h2', 'h3', 'h4']); section = heading_text(sub) if sub is not None and sub.name != 'h2' else 'Medalists'
        group = None
        for row in m[:hi]:
            if len(row) >= 3 and all(c is row[0] for c in row): group = text(row[0])
        rows = {}; n_before = len(out); last = None
        for ri, row in enumerate(m[hi + 1:]):
            if not row or len(row) <= evc: continue
            if len(row) >= 3 and all(c is row[0] for c in row): group = text(row[0]); last = None; continue   # a group row: the section of what follows
            ec = row[evc]; ename = text(ec); ename = re.sub(r'\s*\bdetails\b\s*$', '', ename, flags=re.I).strip()
            if ename.lower().startswith(('event', 'total')): continue
            if not ename:   # a tie written as a second row with an empty event cell belongs to the event above
                if last is None: continue
                e = last
            else:
                link = next((a for a in ec.find_all('a', href=True) if a.get_text(strip=True).lower() != 'details' and (a.get('href') or '').startswith('/wiki/')), None) or next((a for a in ec.find_all('a', href=True) if (a.get('href') or '').startswith('/wiki/')), None)
                url = 'https://en.wikipedia.org' + link['href'].split('#')[0] if link else page.url
                url = urllib.parse.unquote(url); gender = gender_of(ename, (group or '') + ' ' + section, url)
                key = (group, ename, gender)   # the same name twice in one table for one category (a tie written as a repeated row, or a rowspan the grid expanded) is one event
                e = rows.get(key)
            if e is None:
                sec = group if group and not GENERIC_SECTION.match(group) else (section if not GENERIC_SECTION.match(section) or not group else group)
                e = {'sport': sport, 'section': sec, 'event': ename, 'url': url, 'gender': gender, 'awards': []}; rows[key] = e; out.append(e)
            last = e
            for r, ci in sorted(cols.items()):
                if ci >= len(row): continue
                aw = award_of(row[ci], y)
                if not aw: continue
                sig = (r, fold(aw[0]), tuple(i for i, _ in aw[1]))
                if sig in {(a[0], fold(a[1]), tuple(i for i, _ in a[2])) for a in e['awards']}: continue
                e['awards'].append((r, aw[0], aw[1]))
        if diag is not None and len(out) == n_before: diag.append(f'{sport}: table of {len(m)} rows gave no events — header: ' + ' | '.join(head[:5]))
    return [e for e in out if e['awards']]

def adopt_categories(rd, A):
    """An event whose list gives no category cue ('Pair skating', 'Team relay', nordic combined's 'Individual large hill/10 km') takes the
    category the archive already files that event under in its sport — mixed, men's, open — so lineages continue as the archive drew them."""
    EF = A['eventFields']; isp, ig, ie, iy = EF.index('sport'), EF.index('gender'), EF.index('event'), EF.index('y')
    seen = {}
    for r in A['events']:
        k = (r[isp], lineage(r[isp], 'x', r[ie].split(' · ')[-1]).split('|', 2)[2])
        if r[iy] >= seen.get(k, (0, None))[0]: seen[k] = (r[iy], r[ig])
    n = 0
    for e in rd:
        if e['gender'] != 'Open': continue
        k = (e['sport'], lineage(e['sport'], 'x', e['event']).split('|', 2)[2])
        if k in seen and seen[k][1] != 'Open': e['gender'] = seen[k][1]; n += 1
    return n

def read_medal_table(page):
    """{nation: (gold, silver, bronze)} from the Games' medal table article."""
    out = {}
    for t in page.soup.find_all('table', class_=re.compile('wikitable')):
        m = grid(t)
        if len(m) < 2: continue
        head = [text(c).lower() for c in m[0]]
        if not any(h.startswith('rank') for h in head) or not any(h.startswith(('noc', 'nation', 'team', 'country')) for h in head): continue
        ci = {k: next((i for i, h in enumerate(head) if h.startswith(k)), None) for k in ('noc', 'nation', 'team', 'country', 'gold', 'silver', 'bronze')}
        ni = next((ci[k] for k in ('noc', 'nation', 'team', 'country') if ci[k] is not None), None)
        if ni is None or None in (ci['gold'], ci['silver'], ci['bronze']): continue
        for row in m[1:]:
            if len(row) <= max(ci['gold'], ci['silver'], ci['bronze'], ni): continue
            n = re.sub(r'\s*\(.*?\)\s*|\*|‡|†', '', text(row[ni])).strip()
            if not n or n.lower().startswith('total'): continue
            try: out[n] = tuple(int(re.sub(r'[^\d]', '', text(row[i])) or 0) for i in (ci['gold'], ci['silver'], ci['bronze']))
            except ValueError: continue
        if out: return out
    return out

def read_infobox(page):
    """Host city, country, dates, athletes, delegations and scheduled events from the Games' own article."""
    box = page.soup.find('table', class_=re.compile('infobox'))
    info = {}
    if box is None: return info
    for tr in box.find_all('tr'):
        th, td = tr.find('th'), tr.find('td')
        if th is None or td is None: continue
        info[text(th).lower()] = text(td)
    num = lambda s: int(re.search(r'\d[\d,]*', s or '').group(0).replace(',', '')) if re.search(r'\d', s or '') else None
    host = info.get('host city') or info.get('host') or ''
    city, _, country = host.rpartition(',')
    if not city: city, country = host, ''
    def day(s):
        m = re.search(r'(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})', s or '')
        return (int(m.group(1)), m.group(2), int(m.group(3))) if m else None
    o, c = day(info.get('opening') or info.get('opened')), day(info.get('closing') or info.get('closed'))
    dates = ''
    if o and c: dates = f'{o[0]}–{c[0]} {c[1]} {c[2]}' if o[1] == c[1] and o[2] == c[2] else f'{o[0]} {o[1]}{"" if o[2] == c[2] else " " + str(o[2])} – {c[0]} {c[1]} {c[2]}'
    closing = datetime.date(c[2], MONTHS.index(c[1]) + 1, c[0]) if c and c[1] in MONTHS else None
    return {'city': city.strip(), 'country': country.strip(), 'dates': dates, 'athletes': num(info.get('athletes')), 'delegations': num(info.get('nations')), 'scheduled': num(info.get('events')), 'closing': closing}

def city_coords(city, log):
    """[lon, lat] of the host city from its article's coordinates; the small gazetteer when the API cannot be read."""
    try:
        from common import get_json
        j = get_json('https://en.wikipedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'prop': 'coordinates', 'titles': city, 'redirects': 1, 'format': 'json', 'formatversion': 2}), pause=1.0)
        for pg in j.get('query', {}).get('pages', []):
            c = (pg.get('coordinates') or [None])[0]
            if c: return [round(c['lon'], 2), round(c['lat'], 2)]
    except Exception as e: log.append(f'  - coordinates of {city} not read ({e})')
    return GAZETTEER.get(city)

def tally(awards):
    t = collections.defaultdict(lambda: [0, 0, 0])
    for w in awards: t[w[2]][w[1] - 1] += 1
    return t

def reconcile(awards, table):
    """The awards' tally against the medal table article, by folded delegation name: {} when they agree."""
    mine = {fold(n): (n, tuple(v)) for n, v in tally(awards).items()}; theirs = {fold(n): (n, v) for n, v in table.items()}
    diff = {}
    for k in set(mine) | set(theirs):
        a = mine.get(k, (theirs.get(k, ('',))[0], (0, 0, 0))); b = theirs.get(k, (a[0], (0, 0, 0)))
        if tuple(a[1]) != tuple(b[1]): diff[a[0] or b[0]] = {'archive': list(a[1]), 'table': list(b[1])}
    return diff

def sweep(log, sport='olympics', get_page=None, today=None, coords=None):
    """sport is 'olympics' (the Summer Games, data/olympics.json) or 'winter' (the Winter Games, data/winter.json)."""
    today = today or datetime.date.today()
    if get_page is None:
        from wiki import parse_page as get_page
    coords = coords or city_coords
    SEASON = 'Winter' if sport == 'winter' else 'Summer'
    path = ROOT/'data'/f'{sport}.json'; A = json.loads(path.read_text(encoding='utf-8'))
    EF, WF = A['eventFields'], A['awardFields']; ATH = A['athletes']
    games = {g['y']: g for g in A['games']}; last = A['lastYear']
    # 1. prove the reader on the latest Games the archive holds
    page = get_page(f'List of {last} {SEASON} Olympics medal winners')
    if page is None: raise SystemExit(f'the {last} {SEASON} list of medal winners could not be read — nothing written')
    diag = []; read = read_list(page, last, diag); adopt_categories(read, A)
    held = [dict(zip(EF, r)) for r in A['events'] if r[EF.index('y')] == last]; byid = {e['id']: e for e in held}
    hw = [dict(zip(WF, r)) for r in A['awards'] if r[0] in byid]
    plain = lambda sport, gender, name: lineage(sport, gender, name.split(' · ')[-1])   # the archive prefixes some names with their section ("Men's freestyle · 57 kg"); compare without it
    got = {}
    for e in read:
        for r, n, ath in e['awards']: got.setdefault((plain(e['sport'], e['gender'], e['event']), r, fold(n)), []).append({i for i, _ in ath})
    have = rosters = 0; bad = []
    for w in hw:
        e = byid[w['e']]; k = (plain(e['sport'], e['gender'], e['event']), w['rank'], fold(w['nation']))
        if k in got:
            have += 1
            if any(set(w['athletes']) == s for s in got[k]): rosters += 1
        else: bad.append(f'{e["sport"]} · {e["event"]} · {["gold", "silver", "bronze"][w["rank"] - 1]} {w["nation"]}')
    log.append(f'Check on {last}: the reader reproduces {have} of the archive\'s {len(hw)} awards ({have / max(len(hw), 1):.1%}); {rosters} with the same named athletes.')
    if not hw or have / len(hw) < AGREE:
        log += [f'  - not read back: {b}' for b in bad[:15]]
        held_by = collections.Counter(e['sport'] for e in held); read_by = collections.Counter(e['sport'] for e in read)
        log.append(f'  - read {len(read)} events with awards from {page.url}; archive holds {len(held)}')
        log.append('  - by sport (archive → read): ' + ', '.join(f'{sp} {held_by[sp]}→{read_by.get(sp, 0)}' for sp in sorted(held_by) if read_by.get(sp, 0) != held_by[sp]) + (f'; read but not in the archive: {", ".join(sorted(set(read_by) - set(held_by)))}' if set(read_by) - set(held_by) else ''))
        log += [f'  - {d}' for d in diag[:25]]
        raise SystemExit('the list did not read back as the archive holds it — the layout may have changed; nothing written')
    # 2. the newest Games if provisional, then the next one
    todo = ([last] if games[last].get('provisional') else []) + [last + 4]
    changed = False
    for y in todo:
        lp = page if y == last else get_page(f'List of {y} {SEASON} Olympics medal winners')
        if lp is None: log.append(f'- {y}: no list of medal winners yet'); continue
        rd = read if y == last else read_list(lp, y)
        if y != last: adopt_categories(rd, A)
        awards_read = [(e, r, n, ath) for e in rd for r, n, ath in e['awards']]
        if not awards_read: log.append(f'- {y}: the list holds no medal awards yet'); continue
        mt = get_page(f'{y} {SEASON} Olympics medal table')
        table = read_medal_table(mt) if mt else {}
        diff = reconcile([(None, r, n) for _, r, n, _ in awards_read], table) if table else None
        if diff is None: log.append(f'- {y}: {len(awards_read)} awards read, but the medal table article could not be read; nothing written until it reconciles'); continue
        if diff:
            log.append(f'- {y}: {len(awards_read)} awards read; the medal table does not reconcile for {len(diff)} delegation(s) — ' + '; '.join(f'{n}: read {v["archive"]}, table {v["table"]}' for n, v in list(diff.items())[:6]) + ('; …' if len(diff) > 6 else '') + '. Nothing written until they agree.'); continue
        old_n = sum(1 for r in A['awards'] if r[0] in {e[EF.index('id')] for e in A['events'] if e[EF.index('y')] == y})
        if y == last and len(awards_read) <= old_n and not games[y].get('provisional'): continue
        if y == last and len(awards_read) < old_n: log.append(f'- {y}: the list now holds fewer awards ({len(awards_read)}) than the archive ({old_n}); left as it is'); continue
        gp = get_page(f'{y} {SEASON} Olympics'); info = read_infobox(gp) if gp else {}
        g = games.get(y) or {'y': y, 'city': '', 'country': '', 'dates': '', 'athletes': None, 'men': None, 'women': None, 'scheduled': None, 'delegations': None, 'points': [], 'cancelled': False}
        for k in ('city', 'country', 'dates', 'athletes', 'delegations', 'scheduled'):
            if info.get(k): g[k] = info[k]
        if g['city'] and not g['points']:
            c = coords(g['city'], log)
            if c: g['points'] = [[g['city'], c[0], c[1]]]
            else: log.append(f'  - {g["city"]} could not be placed on the map (no coordinates read)')
        closing = info.get('closing'); provisional = closing is None or closing >= today
        # events and awards: ids by lineage where the Games is already held, new ids after the last
        old_ev = [dict(zip(EF, r)) for r in A['events'] if r[EF.index('y')] == y]; by_key = {}
        for e in old_ev: by_key.setdefault(e['key'], []).append(e['id'])
        n = max([int(e['id'].split('-')[1]) for e in old_ev if e['id'].split('-')[1].isdigit()] or [0])
        new_events, new_awards, new_names = [], [], 0
        prefixed = collections.defaultdict(lambda: [0, 0])   # (sport, section) → [names carrying "section · ", names]: the archive's own habit, learned from what it holds
        for r in A['events']:
            sec = r[EF.index('section')]
            if sec and not GENERIC_SECTION.match(sec): c = prefixed[(r[EF.index('sport')], fold(sec))]; c[1] += 1; c[0] += r[EF.index('event')].startswith(sec + ' · ')
        plain_names = collections.Counter((e['sport'], e['gender'], fold(e['event'])) for e in rd)
        for e in rd:
            sec = e['section']; c = prefixed.get((e['sport'], fold(sec)))
            if sec and not GENERIC_SECTION.match(sec) and ((c and c[0] * 2 > c[1]) or (not c and plain_names[(e['sport'], e['gender'], fold(e['event']))] > 1)) and not e['event'].startswith(sec + ' · '): e['event'] = f'{sec} · {e["event"]}'
            key = lineage(e['sport'], e['gender'], e['event'])
            if by_key.get(key): eid = by_key[key].pop(0)
            else: n += 1; eid = f'{y}-{n}'
            new_events.append([eid, y, e['sport'], e['event'], e['gender'], e['url'], e['section'], '', '', key])
            for r, nation, ath in e['awards']:
                for i, name in ath:
                    if i not in ATH: ATH[i] = name; new_names += 1
                new_awards.append([eid, r, nation, [i for i, _ in ath], ''])
        keep_e = [r for r in A['events'] if r[EF.index('y')] != y]; gone = {r[0] for r in A['events'] if r[EF.index('y')] == y}
        A['events'] = keep_e + new_events; A['awards'] = [r for r in A['awards'] if r[0] not in gone] + new_awards
        g['provisional'] = provisional
        if provisional: g['note'] = f'Games in progress: the medal record as the lists stood on {today:%d %B %Y}; it is re-read on every sweep and completed once the Games close.'
        elif str(g.get('note', '')).startswith('Games in progress'): g.pop('note', None)
        if not provisional: g.pop('provisional', None)
        if y not in games: A['games'].append(g); games[y] = g
        A['sources'] = [s for s in A['sources'] if s.get('year') != y] + [{'year': y, 'title': lp.title, 'url': lp.url, 'revision': str(lp.revid or '')}, {'year': y, 'title': mt.title, 'url': mt.url, 'revision': str(mt.revid or '')}]
        A['validation'] = [v for v in A['validation'] if v.get('year') != y] + [{'year': y, 'status': 'matched', 'awards': len(new_awards), 'difference': {}, 'reference': mt.url}]
        golds = sum(1 for w in new_awards if w[1] == 1); top = sorted(tally([(None, w[1], w[2]) for w in new_awards]).items(), key=lambda kv: (-kv[1][0], -kv[1][1], -kv[1][2]))[:1]
        log.append(f'- **{g["city"] or y} {y}**{" (provisional, Games in progress)" if provisional else ""}: {len(new_events)} medal events in {len({e[2] for e in new_events})} sports, {len(new_awards)} awards ({golds} gold), medal table reconciled' + (f'; on top: {top[0][0]} with {top[0][1][0]} gold' if top else '') + (f'; {new_names} new names' if new_names else ''))
        changed = True
    if not changed: log.append('- nothing new'); return
    A['games'].sort(key=lambda g: g['y']); A['events'].sort(key=lambda r: (r[1], int(r[0].split('-')[1]) if r[0].split('-')[1].isdigit() else 10**6, r[0]))
    order = {r[0]: i for i, r in enumerate(A['events'])}; A['awards'].sort(key=lambda r: (order.get(r[0], 10**9), r[1]))
    A['sports'] = sorted({r[2] for r in A['events']}); A['nations'] = sorted({r[2] for r in A['awards']})
    held_g = [g for g in A['games'] if not g['cancelled']]
    A['coverage'].update(games=len(A['games']), held=len(held_g), cancelled=len(A['games']) - len(held_g), events=len(A['events']), medalEvents=len({r[0] for r in A['awards']}), awards=len(A['awards']), gold=sum(1 for r in A['awards'] if r[1] == 1),
                         athletes=len(ATH), medallists=len({a for r in A['awards'] for a in r[3]}), nations=len(A['nations']), sports=len(A['sports']), validated=sum(1 for v in A['validation'] if v.get('status') == 'matched'))
    A['lastYear'] = max(g['y'] for g in held_g); A['snapshot'] = A['retrieved'] = today.isoformat()
    path.write_text(json.dumps(A, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    log.append(f'\nArchive now {len(held_g)} Games held, {len(A["events"]):,} medal events, {len(A["awards"]):,} awards, through {A["lastYear"]}.')
