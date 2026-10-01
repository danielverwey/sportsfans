"""Bring the Summer or Winter Olympics archive into the site.

  python3 tools/prepare_olympics.py /path/to/summer_olympics_atlas_1896_2024.html     → data/olympics.json
  python3 tools/prepare_olympics.py /path/to/winter_olympics_atlas_1924_2026.html     → data/winter.json   (the page's title says which)

Reads the prototype page's embedded <script id="archive"> — every medal event of every Summer Games and the awards
(gold, silver, bronze, with the delegation and the named athletes), transcribed from Wikipedia's per-Games lists of medal
winners at recorded revisions (CC BY-SA 4.0) — and the page's land silhouette (Natural Earth 1:110m, public domain), and
writes data/olympics.json: the Games (with the three cancelled by the world wars kept as gaps), the events and awards
packed as rows, the athletes' names, the delegation colours, the map, the sources and the validation record. Nothing in
the record is altered; an event's lineage key (the same event across Games) is added so the atlas can follow it.
"""
import json, re, sys, pathlib, collections, unicodedata
ROOT = pathlib.Path(__file__).resolve().parent.parent
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT/'build'/'harvest'/'summer_olympics_atlas_1896_2024.html')
html = src.read_text(encoding='utf-8')
WINTER = 'winter' in (re.search(r'<title>(.*?)</title>', html, re.S | re.I).group(1) if re.search(r'<title>', html, re.I) else src.name).lower()
SEASON, KEY, NAME = ('Winter', 'winter', 'Winter Olympics') if WINTER else ('Summer', 'olympics', 'Summer Olympics')
D = json.loads(re.search(r'<script id="archive"[^>]*>(.*?)</script>', html, re.S).group(1))
land = re.search(r"const land='([^']+)'", html).group(1)
proto_colours = json.loads(re.sub(r"'", '"', re.search(r"const colors=(\{.*?\});", html, re.S).group(1)))

# ---- delegation colours: editorial readings of kit colours, muted for the dark page; the prototype's own first, then these; the rest take a hue from their name
COLOURS = {'United States': '#8ccef4', 'Soviet Union': '#e0708a', 'Great Britain': '#c4a8e1', 'France': '#75a2e4', 'China': '#e8756a', 'Germany': '#ecc55f', 'Italy': '#89ceb0', 'Australia': '#77c7b2', 'Japan': '#e6e9f0',
           'Hungary': '#9fd48a', 'Sweden': '#f2db80', 'Russia': '#8e9eec', 'East Germany': '#b194d5', 'Netherlands': '#f6a455', 'Canada': '#f27664', 'South Korea': '#e5cfde', 'Romania': '#f0c987', 'Poland': '#f4a3a3', 'Finland': '#b9d6e8',
           'Cuba': '#f28c6b', 'Bulgaria': '#cfe8a0', 'Denmark': '#ff9a8b', 'Switzerland': '#ef9ab0', 'West Germany': '#c9b789', 'Spain': '#f5b26b', 'Brazil': '#a4e07a', 'Norway': '#ed6676', 'Belgium': '#f6d365', 'New Zealand': '#c9ccd1',
           'Ukraine': '#9fc9ff', 'Czechoslovakia': '#a0d6e8', 'Greece': '#8fc7ff', 'Kenya': '#8fd1a4', 'United Team of Germany': '#d9cfa8', 'Unified Team': '#c9a0dc', 'Turkey': '#f0a0a0', 'Austria': '#f29686', 'South Africa': '#7fd39a',
           'Jamaica': '#c7e86a', 'Iran': '#a8e0c8', 'Belarus': '#b9d6a3', 'Yugoslavia': '#d4b2ff', 'Argentina': '#a9d8f5', 'Kazakhstan': '#9fd9e6', 'Mexico': '#a0d8a0', 'Czechia': '#bde0f0', 'ROC': '#a8b4f0', 'Ethiopia': '#a4c86a',
           'North Korea': '#e6b3c8', 'Azerbaijan': '#a5d6d6', 'Croatia': '#f0b8b8', 'Uzbekistan': '#a8e0e0', 'Georgia': '#e2a9a9', 'Ireland': '#a2dcae', 'India': '#ffb57a', 'Thailand': '#c4b5f5', 'Chinese Taipei': '#9fd1e0', 'Indonesia': '#f2a6a6',
           'Egypt': '#e8c9a0', 'Colombia': '#f5d76e', 'Estonia': '#9fbfe6', 'Slovakia': '#b9d1ee', 'Portugal': '#b7d59a', 'Mongolia': '#f5c98a', 'Slovenia': '#a9d8d0', 'Lithuania': '#d6e3a0', 'Serbia': '#c9b2d8', 'Nigeria': '#9fd8a0',
           'Morocco': '#e59a8f', 'Armenia': '#e6b8a0', 'Latvia': '#d8a8a8', 'Algeria': '#a4d9a4', 'Israel': '#a9c8ff', 'Trinidad and Tobago': '#d0a0a0', 'Venezuela': '#f0d090', 'Philippines': '#a8c8f0', 'Tunisia': '#f0a8a8', 'Bahamas': '#8fe0d6',
           'Individual Neutral Athletes': '#b8bcc4', 'Independent Olympic Participants': '#b8bcc4', 'Independent Olympic Athletes': '#b8bcc4', 'Mixed team': '#9aa4b0', 'Australasia': '#b6d9c5', 'Bohemia': '#d2b5e0', 'Russian Empire': '#d0a8b8', 'Refugee Olympic Team': '#e0d8c0'}
colours = {**COLOURS, **{k: v for k, v in proto_colours.items() if k in COLOURS or k != 'Other delegations'}}
colours = {k: v for k, v in colours.items() if k != 'Other delegations'}

sys.path.insert(0, str(ROOT/'tools')); from olympics_common import slug, lineage   # shared with the sweeper and the audit

# ---- the Games, with the three cancelled editions kept as gaps
games = []
for y in sorted(D['editions'], key=lambda e: e['year']):
    games.append({'y': y['year'], 'city': y['city'], 'country': y['country'], 'dates': y['dates'], 'athletes': y['athletes'], 'men': y['men'], 'women': y['women'], 'scheduled': y['scheduledEvents'],
                  'delegations': int(re.match(r'\d+', str(y['delegations']).replace(',', '')).group(0)) if re.match(r'\d+', str(y['delegations']).replace(',', '')) else None, 'points': [[p['city'], p['lon'], p['lat']] for p in y['points']], 'cancelled': False})
CANCELLED = {'Summer': ((1916, 'Berlin was to host; the Games were cancelled because of the First World War.'), (1940, 'Tokyo, then Helsinki, were to host; the Games were cancelled because of the Second World War.'), (1944, 'London was to host; the Games were cancelled because of the Second World War.')),
             'Winter': ((1940, 'Sapporo, then St. Moritz, then Garmisch-Partenkirchen were to host; the Games were cancelled because of the Second World War.'), (1944, 'Cortina d’Ampezzo was to host; the Games were cancelled because of the Second World War.'))}
for y, why in CANCELLED[SEASON]:
    games.append({'y': y, 'city': 'Cancelled', 'country': '', 'dates': '', 'athletes': None, 'men': None, 'women': None, 'scheduled': None, 'delegations': None, 'points': [], 'cancelled': True, 'note': why})
games.sort(key=lambda g: g['y'])
NOTES = {'Summer': {1956: 'The equestrian events were held in Stockholm in June because of Australian quarantine rules; everything else in Melbourne in November and December.', 2020: 'Held in 2021 after a one-year postponement, and kept the name Tokyo 2020.'},
         'Winter': {1994: 'Two years after Albertville: from Lillehammer the Winter Games moved to the even years between the Summer Games.', 2026: 'Two host cities, Milan and Cortina d’Ampezzo, with the snow events spread across the Dolomites and the Valtellina.'}}
for g in games:
    if g['y'] in NOTES[SEASON]: g['note'] = NOTES[SEASON][g['y']]

# ---- events and awards as rows
EF = ['id', 'y', 'sport', 'event', 'gender', 'url', 'section', 'status', 'note', 'key']
events = []; fixed = []
for e in D['events']:
    if re.search(r'\bwoman\b', e['event'], re.I) and e['gender'] == 'Men': e['gender'] = 'Women'; fixed.append(f"{e['year']} {e['sport']} {e['event']}")   # the prototype read 'Two-woman' bobsleigh as men's
    events.append([e['id'], e['year'], e['sport'], e['event'], e['gender'], e['url'], e.get('section') or '', e.get('status') or '', e.get('note') or '', lineage(e['sport'], e['gender'], e['event'])])
WF = ['e', 'rank', 'nation', 'athletes', 'correction']
awards = [[w['eventId'], w['rank'], w['nation'], list(w['athletes']), w.get('correction') or ''] for w in D['awards']]
athletes = dict(D['athletes'])
for w in awards:
    for a in w[3]:
        if a not in athletes: athletes[a] = a.replace('_', ' ')
sports = sorted({e[2] for e in events})
nations = sorted({w[2] for w in awards})
milestones = [{'y': y.strip(), 'title': t, 'text': re.sub(r'<[^>]+>', '', p)} for y, t, p in re.findall(r'<article class="milestone"><b>(.*?)</b><h3>(.*?)</h3><p>(.*?)</p></article>', html)]
notes = [re.sub(r'<[^>]+>', '', p) for p in re.findall(r'<details open><summary>What the atlas counts</summary>(.*?)</details>', html, re.S)[0].split('</p>') if p.strip()] if '<details open><summary>What the atlas counts' in html else []

held = [g for g in games if not g['cancelled']]
core = {'games': games, 'eventFields': EF, 'events': events, 'awardFields': WF, 'awards': awards, 'athletes': athletes, 'sports': sports, 'nations': nations, 'colours': colours,
        'map': {'land': land, 'projection': 'equirectangular: x = (lon + 180) × 3, y = (90 − lat) × 3', 'source': 'Natural Earth 1:110m land (public domain), coordinates projected and rounded by the prototype', 'sourceUrl': 'https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson'},
        'season': KEY if WINTER else 'summer', 'name': NAME, 'milestones': milestones, 'notes': notes, 'sources': D['sources'], 'validation': D['validation'], 'corrections': D.get('corrections', []), 'aliases': D.get('aliases', {}),
        'licence': 'CC BY-SA 4.0', 'licenceUrl': 'https://creativecommons.org/licenses/by-sa/4.0/', 'retrieved': D['retrieved'], 'snapshot': D['retrieved'], 'lastYear': max(g['y'] for g in held),
        'coverage': {'games': len(games), 'held': len(held), 'cancelled': len(games) - len(held), 'events': len(events), 'medalEvents': len({w[0] for w in awards}), 'awards': len(awards), 'gold': sum(1 for w in awards if w[1] == 1),
                     'athletes': len(athletes), 'medallists': len({a for w in awards for a in w[3]}), 'nations': len(nations), 'sports': len(sports), 'validated': sum(1 for v in D['validation'] if v['status'] == 'matched')},
        'method': f'Every medal event of every {SEASON} Games, read from Wikipedia’s list of medal winners for that Games at the recorded revision: the event and its sport, the men’s, women’s, mixed or open category, and the gold, silver and bronze awards with the delegation and the athletes the list names. A team, pair or relay counts once in a delegation’s table; ties are separate awards; the medal table of every Games reconciles by delegation and colour against the cited comparison table. ' + ('Demonstration events are outside the archive. ' if WINTER else 'Art competitions, demonstration events and the 1906 Intercalated Games are outside the archive. ') + 'Host cities are placed on the Natural Earth land silhouette at approximate coordinates.'}
out = ROOT/'data'/f'{KEY}.json'; out.write_text(json.dumps(core, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
c = core['coverage']
if fixed: print(f'{KEY}: category corrected to women for {len(fixed)} events named "…woman": {", ".join(fixed[:3])}{" …" if len(fixed) > 3 else ""}')
print(f'{KEY}: {c["held"]} Games held ({c["cancelled"]} cancelled) · {c["events"]:,} events · {c["awards"]:,} awards ({c["gold"]:,} gold) · {c["medallists"]:,} medallists of {c["athletes"]:,} names · {c["nations"]} delegations · {c["sports"]} sports · {c["validated"]}/{c["held"]} medal tables reconciled · lineages {len({e[9] for e in events}):,} · {out.stat().st_size/1e6:.1f} MB')
