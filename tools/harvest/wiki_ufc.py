#!/usr/bin/env python3
"""Clean-room UFC archive from Wikipedia.

Sources: the "List of UFC events" article (every past event with its date, venue and city) and each event's own
article — its results table (weight class, the two fighters, "def." or "vs.", method, round, time, notes) and its
bonus awards. Fighter nationality, date of birth and height come from Wikidata (CC0) where the fighter has an
article. Text and tables are CC BY-SA 4.0; the results are facts. Nothing is taken from the promotion's own site
or its statistics partner.

    python tools/harvest/wiki_ufc.py [--from 1993] [--to 2026] [--out build/harvest] [--no-wikidata] [--limit N]

Runs where the network is open (GitHub Actions). Writes <out>/ufc.json — events, bouts, fighters, sources — and
<out>/ufc.md, a coverage report that says, event by event, how many bouts were read and what was skipped. Every
request goes through the MediaWiki API with a descriptive User-Agent and a pause between calls.
"""
import sys, re, json, datetime, argparse, html, pathlib, collections, time, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import get_json, report, ROOT
try:
    from bs4 import BeautifulSoup
except ImportError:
    print('pip install beautifulsoup4 lxml'); sys.exit(2)

API = 'https://en.wikipedia.org/w/api.php'
WD = 'https://www.wikidata.org/w/api.php'
LIST = 'List of UFC events'

SHA = {}   # article title → sha256 of the HTML read, for the archive's page list
def parse_page(title):
    """The rendered article as soup, with its revision id, or (None, None)."""
    j = get_json(API + '?' + urllib.parse.urlencode({'action': 'parse', 'prop': 'text|revid', 'format': 'json', 'formatversion': 2, 'redirects': 1, 'disabletoc': 1, 'page': title}), pause=1.0)
    if 'error' in j or 'parse' not in j: return None, None
    SHA[title] = __import__('hashlib').sha256(j['parse']['text'].encode('utf-8')).hexdigest()
    return BeautifulSoup(j['parse']['text'], 'lxml'), j['parse'].get('revid')

def grid_rows(table):
    """Expand rowspans/colspans of a table into a plain matrix of cells (BeautifulSoup tags)."""
    matrix = []; pending = {}
    for tr in table.find_all('tr'):
        row = []; col = 0; cells = tr.find_all(['th', 'td'], recursive=False); ci = 0
        while ci < len(cells) or col in pending:
            if col in pending:
                cell, left = pending[col]; row.append(cell)
                if left > 1: pending[col] = (cell, left - 1)
                else: del pending[col]
                col += 1; continue
            cell = cells[ci]; ci += 1
            try: rs = int(cell.get('rowspan', 1) or 1); cs = int(cell.get('colspan', 1) or 1)
            except ValueError: rs = cs = 1
            for k in range(cs):
                row.append(cell)
                if rs > 1: pending[col] = (cell, rs - 1)
                col += 1
        matrix.append(row)
    return matrix

slug = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower().replace('’', '').replace("'", '')).strip('-')
def clean(cell):
    for x in cell.find_all(['sup', 'style', 'script']): x.decompose()
    return re.sub(r'\s+', ' ', cell.get_text(' ', strip=True)).replace(' ,', ',').strip()
def link_title(cell):
    for a in cell.find_all('a', href=True):
        h = a['href']
        if h.startswith('/wiki/') and 'redlink' not in h and ':' not in h[6:]: return html.unescape(h[6:].split('#')[0].replace('_', ' '))
    return None
MONTHS = {m: i for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'], 1)}
def iso_date(txt):
    """'November 12, 1993', '12 November 1993', 'Nov 12, 1993', '1993-11-12' → ISO, else None."""
    t = (txt or '').replace(' ', ' ')
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', t)
    if m: return m.group(0)
    m = re.search(r'([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})', t) or re.search(r'(\d{1,2})\s+([A-Za-z]+)\.?,?\s+(\d{4})', t)
    if not m: return None
    g = m.groups(); mon, day, yr = (g[0], g[1], g[2]) if not g[0].isdigit() else (g[1], g[0], g[2])
    mi = MONTHS.get(mon.lower()) or next((v for k, v in MONTHS.items() if k.startswith(mon.lower()[:3])), None)
    if not mi: return None
    try: return datetime.date(int(yr), mi, int(day)).isoformat()
    except ValueError: return None
def number(txt):
    m = re.search(r'\d[\d,]*', (txt or '').replace(' ', ' '))
    return int(m.group(0).replace(',', '')) if m else None
def money(txt):
    m = re.search(r'\$\s?([\d,]+)', txt or '')
    return int(m.group(1).replace(',', '')) if m else None

def canonical_titles(titles, log=None):
    """Article titles through Wikipedia's redirects: an event card often links a fighter by a redirect ('Dooho Choi'),
    the fighter's article has one canonical title. {asked: canonical}."""
    out = {}; titles = sorted({t for t in titles if t})
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        try: j = get_json(API + '?' + urllib.parse.urlencode({'action': 'query', 'titles': '|'.join(chunk), 'redirects': 1, 'format': 'json', 'formatversion': 2}), pause=0.8)
        except Exception as e:
            if log is not None: log.append(f'- redirects batch {i // 50}: {e}')
            continue
        q = j.get('query', {}); norm_ = {n['from']: n['to'] for n in q.get('normalized', [])}; red = {r['from']: r['to'] for r in q.get('redirects', [])}
        for t in chunk: t2 = norm_.get(t, t); out[t] = red.get(t2, t2)
    return out

# ---------- the list of events
def event_list(log):
    soup, rev = parse_page(LIST)
    if soup is None: raise SystemExit('the list of events could not be read')
    rows = []
    for t in soup.find_all('table', class_=re.compile('wikitable')):
        heads = [clean(th).lower() for th in t.find_all('th')[:12]]
        if not (any('event' in h for h in heads) and any('date' in h for h in heads) and any('venue' in h for h in heads)): continue
        h = t.find_previous(['h2', 'h3']); section = clean(h).lower() if h else ''
        if any(w in section for w in ('scheduled', 'upcoming', 'future', 'cancel')): continue
        col = {}; matrix = grid_rows(t)
        if not matrix: continue
        for i, th in enumerate(matrix[0]):
            k = clean(th).lower()
            for key, words in (('n', ('#', 'no.')), ('event', ('event',)), ('date', ('date',)), ('venue', ('venue',)), ('location', ('location', 'city')), ('attendance', ('attendance',))):
                if key not in col and any(w == k or (w != '#' and w in k) for w in words): col[key] = i
        if 'event' not in col or 'date' not in col: continue
        for cells in matrix[1:]:
            if len(cells) <= max(col.values()) or cells[col['event']].name == 'th': continue
            ev = cells[col['event']]; title = link_title(ev); name = clean(ev); date = iso_date(clean(cells[col['date']]))
            if not name or not date: continue
            rows.append({'n': number(clean(cells[col['n']])) if 'n' in col else None, 'title': title or name, 'name': name, 'date': date,
                         'venue': clean(cells[col['venue']]) if 'venue' in col else '', 'location': clean(cells[col['location']]) if 'location' in col else '',
                         'attendance': number(clean(cells[col['attendance']])) if 'attendance' in col else None, 'linked': bool(title)})
    seen = set(); out = []
    for r in rows:
        k = (r['title'], r['date'])
        if k in seen: continue
        seen.add(k); out.append(r)
    out.sort(key=lambda r: (r['date'], r['n'] or 0))
    log.append(f'- list of events: {len(out)} past events, {sum(1 for r in out if not r["linked"])} without an article link, revision {rev}')
    return out, rev

# ---------- one event article
SEP = {'def.': 'def.', 'def': 'def.', 'vs.': 'vs.', 'vs': 'vs.', 'drew': 'vs.', 'draw': 'vs.'}
CARD_WORDS = ('card', 'final', 'semifinal', 'quarterfinal', 'superfight', 'super fight', 'alternate', 'preliminary', 'prelim', 'bout', 'tournament', 'round', 'opening', 'main', 'undercard', 'reserve', 'championship')
def infobox(soup):
    box = soup.find('table', class_=re.compile('infobox')); out = {}
    if not box: return out
    for tr in box.find_all('tr'):
        th, td = tr.find('th'), tr.find('td')
        if th and td: out[clean(th).lower().rstrip(':')] = clean(td)
    return out

def bouts_of(soup, log, ename):
    """Every bout row of the article's results tables, in page order (the main event first), with its card heading."""
    bouts = []; cards = []; card = None; ncards = 0
    for t in soup.find_all('table'):
        cls = ' '.join(t.get('class', []))
        if 'infobox' in cls or 'navbox' in cls or 'sidebar' in cls: continue
        h = t.find_previous(['h2', 'h3', 'h4']); ht = clean(h) if h else ''
        if ht and len(ht) < 60 and any(w in ht.lower() for w in CARD_WORDS) and 'result' not in ht.lower(): card = ht
        for tr in t.find_all('tr'):
            cells = tr.find_all(['th', 'td'], recursive=False)
            if not cells: continue
            texts = [clean(c) for c in cells]
            if len(cells) == 1 or (len([x for x in texts if x]) == 1 and cells[0].get('colspan')):
                head = next((x for x in texts if x), '')
                if head and len(head) < 60 and any(w in head.lower() for w in CARD_WORDS) and 'weight class' not in head.lower():
                    card = head; cards.append(card); ncards += 1
                continue
            sep_i = next((i for i, x in enumerate(texts) if x.lower().rstrip('.') + '.' in SEP or x.lower() in SEP), None)
            if sep_i is None or sep_i < 1 or len(texts) < sep_i + 4: continue
            a_cell, b_cell = cells[sep_i - 1], cells[sep_i + 1]
            a, b = clean(a_cell), clean(b_cell)
            if not a or not b: continue
            wc = texts[sep_i - 2] if sep_i >= 2 else ''
            method = texts[sep_i + 2] if len(texts) > sep_i + 2 else ''
            rnd = texts[sep_i + 3] if len(texts) > sep_i + 3 else ''
            tm = texts[sep_i + 4] if len(texts) > sep_i + 4 else ''
            notes = ' '.join(x for x in texts[sep_i + 5:] if x) if len(texts) > sep_i + 5 else ''
            def fighter(cell, txt):
                champ = bool(re.search(r'\((?:c|ic)\)', txt))
                name = re.sub(r'\s*\((?:c|ic)\)', '', txt).strip()
                return {'name': name, 'title': link_title(cell), 'champ': champ}
            bouts.append({'card': card or 'Card', 'wc': wc, 'a': fighter(a_cell, a), 'b': fighter(b_cell, b), 'sep': SEP.get(texts[sep_i].lower(), SEP.get(texts[sep_i].lower().rstrip('.') + '.', 'vs.')),
                          'method': method, 'round': int(rnd) if rnd.isdigit() else None, 'time': tm if re.fullmatch(r'\d{1,2}:\d{2}', tm) else (tm or None), 'notes': notes})
    if not bouts: log.append(f'- {ename}: no results table read')
    return bouts

BONUS = ('Fight of the Night', 'Performance of the Night', 'Knockout of the Night', 'Submission of the Night')
def bonuses_of(soup):
    """The bonus-award list under the 'Bonus awards' heading: kind, the names as written, the linked article titles."""
    out = []
    for h in soup.find_all(['h2', 'h3', 'h4']):
        if 'bonus' not in clean(h).lower(): continue
        start = h.parent if h.parent and h.parent.name == 'div' and 'mw-heading' in ' '.join(h.parent.get('class', [])) else h
        ul = None
        for sib in start.next_siblings:
            if getattr(sib, 'name', None) is None: continue
            if sib.name in ('h2', 'h3', 'h4') or (sib.name == 'div' and 'mw-heading' in ' '.join(sib.get('class', []))): break
            if sib.name == 'ul': ul = sib; break
            found = sib.find('ul') if hasattr(sib, 'find') else None
            if found: ul = found; break
        for li in (ul.find_all('li') if ul else []):
            txt = clean(li)
            for kind in BONUS:
                if txt.lower().startswith(kind.lower()):
                    who = re.sub(r'^' + re.escape(kind) + r'\s*:\s*', '', txt, flags=re.I)
                    names = [n.strip() for n in re.split(r'\s+vs\.?\s+|\s+and\s+|,\s+|\s+&\s+', who) if n.strip()]
                    titles = [html.unescape(a['href'][6:].split('#')[0].replace('_', ' ')) for a in li.find_all('a', href=True) if a['href'].startswith('/wiki/') and 'redlink' not in a['href']]
                    out.append({'type': kind, 'who': names, 'titles': titles})
        break
    return out

def harvest_event(row, log):
    soup, rev = parse_page(row['title'])
    if soup is None:
        log.append(f'- {row["name"]} ({row["date"]}): article not found'); return None
    box = infobox(soup)
    date = iso_date(box.get('date', '')) or row['date']
    venue = box.get('venue') or row['venue']; city = box.get('city') or row['location']
    ev = {'id': slug(row['title']), 'n': row['n'], 'name': row['name'], 'title': row['title'], 'date': date, 'y': int(date[:4]), 'venue': venue, 'city': city,
          'attendance': number(box.get('attendance', '')) or row['attendance'], 'gate': money(box.get('total gate', '') or box.get('gate', '')), 'buyrate': number(box.get('buyrate', '')),
          'url': 'https://en.wikipedia.org/wiki/' + row['title'].replace(' ', '_'), 'revid': rev, 'bouts': bouts_of(soup, log, row['name']), 'bonuses': bonuses_of(soup)}
    return ev

# ---------- Wikidata: nationality, date of birth, height for fighters with an article
def wikidata(titles, log):
    out = {}; countries = {}
    titles = sorted(set(titles))
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        q = WD + '?' + urllib.parse.urlencode({'action': 'wbgetentities', 'sites': 'enwiki', 'props': 'claims|sitelinks', 'format': 'json', 'titles': '|'.join(chunk)})
        try: j = get_json(q, pause=0.8)
        except Exception as e: log.append(f'- wikidata batch {i // 50}: {e}'); continue
        for qid, ent in (j.get('entities') or {}).items():
            title = ((ent.get('sitelinks') or {}).get('enwiki') or {}).get('title')
            if not title or 'claims' not in ent: continue
            c = ent['claims']; rec = {'qid': qid}
            nat = [s['mainsnak']['datavalue']['value']['id'] for s in c.get('P27', []) if s.get('mainsnak', {}).get('datavalue')]
            if nat: rec['natq'] = nat; countries.update({n: None for n in nat})
            dob = [s['mainsnak']['datavalue']['value']['time'] for s in c.get('P569', []) if s.get('mainsnak', {}).get('datavalue')]
            if dob: rec['dob'] = dob[0][1:11]
            h = [s['mainsnak']['datavalue']['value'] for s in c.get('P2048', []) if s.get('mainsnak', {}).get('datavalue')]
            if h:
                v = h[0]; amt = float(v['amount']); unit = v.get('unit', '')
                rec['height_cm'] = round(amt * 100) if unit.endswith('Q11573') else round(amt * 2.54) if unit.endswith('Q218593') else round(amt) if unit.endswith('Q174728') else None
            out[title] = rec
    ids = sorted(countries)
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        try: j = get_json(WD + '?' + urllib.parse.urlencode({'action': 'wbgetentities', 'props': 'labels', 'languages': 'en', 'format': 'json', 'ids': '|'.join(chunk)}), pause=0.8)
        except Exception as e: log.append(f'- wikidata labels {i // 50}: {e}'); continue
        for qid, ent in (j.get('entities') or {}).items(): countries[qid] = ((ent.get('labels') or {}).get('en') or {}).get('value')
    for rec in out.values():
        if 'natq' in rec: rec['nat'] = [countries.get(q) for q in rec.pop('natq') if countries.get(q)]
    log.append(f'- wikidata: {len(out)} fighters matched of {len(titles)} with an article; {sum(1 for r in out.values() if r.get("nat"))} with nationality, {sum(1 for r in out.values() if r.get("dob"))} with a date of birth')
    return out

# ---------- the harvest (the whole archive, or a window for the sweeper)
def harvest(y0=1993, y1=None, since=None, before_today=False, no_wikidata=False, limit=0, log=None):
    """Every past event from y0 to y1 (or from the ISO date `since`) in the harvest shape. before_today leaves out
    today's card, which may still be in progress."""
    log = log if log is not None else []; today = datetime.date.today().isoformat(); y1 = y1 or datetime.date.today().year
    rows, list_rev = event_list(log)
    rows = [r for r in rows if y0 <= int(r['date'][:4]) <= y1 and (r['date'] < today if before_today else r['date'] <= today) and (since is None or r['date'] >= since)]
    if limit: rows = rows[-limit:]
    class A: pass
    a = A(); a.no_wikidata = no_wikidata
    events = []; issues = []
    for i, r in enumerate(rows):
        ev = harvest_event(r, log)
        if ev is None: continue
        if not ev['bouts']: issues.append({'event': ev['name'], 'date': ev['date'], 'issue': 'no results table read'})
        events.append(ev)
        if i % 25 == 0: print(f'{i + 1}/{len(rows)} {ev["name"]} · {len(ev["bouts"])} bouts', flush=True)
    # fighters: by article title when linked, else by name; a name that is also a linked fighter's name joins that record
    by_title = {}; by_name = {}
    def fid_of(f):
        if f['title']:
            fid = slug(f['title']); by_title.setdefault(fid, {'id': fid, 'name': f['name'], 'title': f['title'], 'url': 'https://en.wikipedia.org/wiki/' + f['title'].replace(' ', '_')}); by_name.setdefault(f['name'].lower(), fid); return fid
        return None
    for ev in events:
        for b in ev['bouts']: fid_of(b['a']); fid_of(b['b'])
    unlinked = {}
    for ev in events:
        for b in ev['bouts']:
            for side in ('a', 'b'):
                f = b[side]; fid = fid_of(f) or by_name.get(f['name'].lower())
                if not fid:
                    fid = slug(f['name']) or 'unknown'
                    if fid in by_title: fid = fid + '-2'
                    unlinked.setdefault(fid, {'id': fid, 'name': f['name'], 'title': None, 'url': None})
                b[side] = {'id': fid, 'champ': f['champ']}
    fighters = {**by_title, **unlinked}
    if not a.no_wikidata:
        wd = wikidata([f['title'] for f in by_title.values()], log)
        for f in by_title.values():
            rec = wd.get(f['title'])
            if rec: f.update({k: v for k, v in rec.items() if k in ('qid', 'nat', 'dob', 'height_cm')})
    bouts = []
    for ev in events:
        ids = []
        for k, b in enumerate(ev['bouts']):
            bid = f'{ev["id"]}#{k + 1}'; ids.append(bid)
            bouts.append({'id': bid, 'e': ev['id'], 'date': ev['date'], 'y': ev['y'], 'n': k + 1, 'card': b['card'], 'wc': b['wc'], 'a': b['a']['id'], 'b': b['b']['id'], 'champ': [s for s in ('a', 'b') if b[s]['champ']],
                          'sep': b['sep'], 'method': b['method'], 'round': b['round'], 'time': b['time'], 'notes': b['notes']})
        ev['bouts'] = ids
    out = {'events': events, 'bouts': bouts, 'fighters': fighters, 'issues': issues,
           'sources': [{'name': 'Wikipedia — List of UFC events and each event article', 'url': 'https://en.wikipedia.org/wiki/List_of_UFC_events', 'licence': 'CC BY-SA 4.0', 'licenceUrl': 'https://creativecommons.org/licenses/by-sa/4.0/', 'revid': list_rev},
                       {'name': 'Wikidata — fighter nationality, date of birth, height', 'url': 'https://www.wikidata.org/', 'licence': 'CC0 1.0', 'licenceUrl': 'https://creativecommons.org/publicdomain/zero/1.0/'}],
           'licence': 'CC BY-SA 4.0', 'licenceUrl': 'https://creativecommons.org/licenses/by-sa/4.0/', 'snapshot': datetime.date.today().isoformat(),
           'coverage': {'events': len(events), 'bouts': len(bouts), 'fighters': len(fighters), 'fightersWithArticle': len(by_title), 'eventsWithoutResults': len(issues), 'boutsWithoutRound': sum(1 for b in bouts if b['round'] is None), 'boutsWithoutTime': sum(1 for b in bouts if not b['time'])},
           'method': 'Each past event in the list of UFC events is read from its own article: the results table gives the weight class, the two fighters, the result, the method, the round, the time and the notes; the infobox gives the date, venue, city and attendance; the bonus-award list is read where present. Fighters are identified by their article where they have one and by name otherwise. Nationality, date of birth and height are taken from Wikidata.'}
    for ev in events: ev['sha256'] = SHA.get(ev['title'])
    return out, events, bouts, fighters, issues, by_title

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--from', dest='y0', type=int, default=1993); ap.add_argument('--to', dest='y1', type=int, default=datetime.date.today().year)
    ap.add_argument('--out', default='build/harvest'); ap.add_argument('--no-wikidata', action='store_true'); ap.add_argument('--limit', type=int, default=0); ap.add_argument('--since', default=None, help='only events on or after this ISO date')
    a = ap.parse_args(); log = [f'# UFC harvest · {datetime.date.today().isoformat()}', '']
    out, events, bouts, fighters, issues, by_title = harvest(a.y0, a.y1, since=a.since, no_wikidata=a.no_wikidata, limit=a.limit, log=log)
    outdir = ROOT/a.out; outdir.mkdir(parents=True, exist_ok=True)
    (outdir/'ufc.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    log += ['', f'## Coverage', '', f'- {len(events)} events · {len(bouts)} bouts · {len(fighters)} fighters ({len(by_title)} with an article)', f'- events without a readable results table: {len(issues)}'] + [f'  - {i["event"]} ({i["date"]})' for i in issues[:60]]
    log += [f'- bouts without a round: {out["coverage"]["boutsWithoutRound"]}; without a time: {out["coverage"]["boutsWithoutTime"]}', '', '## Cards seen', ''] + [f'- {c}: {n}' for c, n in collections.Counter(b['card'] for b in bouts).most_common(40)]
    log += ['', '## Weight classes seen', ''] + [f'- {c or "(blank)"}: {n}' for c, n in collections.Counter(b['wc'] for b in bouts).most_common(60)]
    log += ['', '## Methods seen (top 40)', ''] + [f'- {c}: {n}' for c, n in collections.Counter(b['method'] for b in bouts).most_common(40)]
    report(log, 'ufc.md')

if __name__ == '__main__': main()
