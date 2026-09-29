"""Bring the Dakar Rally archive into the site.

  python3 tools/prepare_dakar.py /path/to/paris_dakar_atlas_1979_2026.html

Reads the prototype page's embedded <script id="archive"> — every edition's route and era, and the podium of every
category, transcribed from Wikipedia's Dakar Rally article at a recorded revision (CC BY-SA 4.0) — and the page's
land silhouette (Natural Earth 1:110m, public domain) and gazetteer of the route towns, and writes data/dakar.json:
the editions with their podiums packed as rows, the people, the marques, the map. A route is drawn schematically
between its named towns, not stage by stage. Nothing else is altered.
"""
import json, re, sys, pathlib, collections, unicodedata
ROOT = pathlib.Path(__file__).resolve().parent.parent
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT/'build'/'harvest'/'paris_dakar_atlas_1979_2026.html')
html = src.read_text(encoding='utf-8')
D = json.loads(re.search(r'<script id="archive"[^>]*>(.*?)</script>', html, re.S).group(1))
land = re.search(r"const land='([^']+)'", html).group(1)
cities = json.loads(re.sub(r"'", '"', re.search(r"const cities=(\{.*?\});", html, re.S).group(1)))
colours = json.loads(re.sub(r"'", '"', re.search(r"const colors=(\{.*?\});", html, re.S).group(1)))
slug = lambda s: re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('ascii').lower().replace('’', '').replace("'", '')).strip('-')

# ---- routes: the named towns of each edition, in order, as the prototype reads them
FIX = [('Ḥaʼil', 'Ha’il'), ('near Yanbu', 'Yanbu'), ('al-Ula', 'AlUla'), ('Alger', 'Algiers'), ('Agades', 'Agadez'), ('Clermont-Ferrand', 'Clermont_Ferrand')]
def stops(route):
    r = route
    for a, b in FIX: r = r.replace(a, b)
    return [s.replace('_', '-').strip() for s in re.split(r'[–-]', r) if s.replace('_', '-').strip() in cities]
CATS = ['Cars', 'Bikes', 'Trucks', 'Quads', 'SSV', 'Challenger', 'Stock', 'Classic']
CAT_NOTE = {'Cars': 'The car class, from the T1 prototypes of the Peugeot and Mitsubishi years to today’s T1+ buggies and hybrids.', 'Bikes': 'The motorcycle class, the rally’s original heart.', 'Trucks': 'The truck class, from 1980; a crew of two or three in the cab.', 'Quads': 'Quad bikes, a class of their own from 2009 to 2024.', 'SSV': 'Side-by-side vehicles, a class from 2017; later the production T4 class.', 'Challenger': 'The lightweight prototype T3 class, named Challenger from 2022.', 'Stock': 'The production-based Stock class of 2026.', 'Classic': 'The Classic regularity event for pre-2000 vehicles, run alongside the rally from 2021.'}
RF = ['cat', 'rank', 'driver', 'crew', 'make']
people = {}; pid = lambda n: slug(n)
def person(n): people.setdefault(pid(n), {'id': pid(n), 'name': n}); return pid(n)
editions = []
by_year = collections.defaultdict(list)
for r in D['records']: by_year[r['year']].append(r)
for y in D['years']:
    rows = []
    for r in sorted(by_year.get(y['year'], []), key=lambda r: (CATS.index(r['category']) if r['category'] in CATS else 99, r['rank'])):
        rows.append([r['category'], r['rank'], person(r['driver']), [person(c) for c in (r.get('crew') or [r['driver']])], r['make']])
    editions.append({'y': y['year'], 'route': y['route'], 'stops': stops(y['route']), 'era': y['era'], 'cancelled': bool(y['cancelled']), 'results': rows, 'cats': [c for c in CATS if any(x[0] == c for x in rows)]})
marques = sorted({x[4] for e in editions for x in e['results']})
milestones = [{'y': int(y), 'title': t, 'text': re.sub(r'<[^>]+>', '', p)} for y, t, p in re.findall(r'<article class="milestone"><b>(\d{4})</b><h3>(.*?)</h3><p>(.*?)</p></article>', html)]
core = {'editions': editions, 'resultFields': RF, 'categories': [{'key': c, 'note': CAT_NOTE.get(c, '')} for c in CATS if any(c in e['cats'] for e in editions)], 'people': people, 'marques': marques, 'colours': colours,
        'map': {'land': land, 'cities': cities, 'boxes': {'Africa': [435, 105, 280, 280], 'South America': [288, 284, 110, 120], 'Saudi Arabia': [641, 175, 78, 78]}, 'projection': 'equirectangular: x = (lon + 180) × 3, y = (90 − lat) × 3', 'source': 'Natural Earth 1:110m land (public domain), coordinates projected and rounded by the prototype', 'sourceUrl': 'https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson'},
        'milestones': milestones, 'source': D['source'], 'revision': D['revision'], 'retrieved': D['retrieved'], 'licence': 'CC BY-SA 4.0', 'licenceUrl': 'https://creativecommons.org/licenses/by-sa/4.0/', 'snapshot': D['retrieved'], 'lastYear': max(e['y'] for e in editions),
        'coverage': {'editions': len(editions), 'held': sum(1 for e in editions if not e['cancelled']), 'cancelled': sum(1 for e in editions if e['cancelled']), 'podiums': sum(len(e['results']) for e in editions), 'wins': sum(1 for e in editions for x in e['results'] if x[1] == 1), 'people': len(people), 'marques': len(marques), 'categories': len(core['categories']) if 'core' in dir() else None},
        'method': 'Every edition in Wikipedia’s Dakar Rally article, read at the recorded revision: its route as the article names it (start, waypoint, finish), its era, and the first three of every category as the article lists them — the lead driver or rider and the crew, and the make. The map draws each route schematically between its named towns over the Natural Earth land silhouette; the stage-by-stage course is not carried. The 2008 edition, cancelled before the start, has no results and counts nothing.'}
core['coverage']['categories'] = len(core['categories'])
out = ROOT/'data'/'dakar.json'; out.write_text(json.dumps(core, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
c = core['coverage']
print(f'dakar: {c["editions"]} editions ({c["held"]} held, {c["cancelled"]} cancelled) · {c["podiums"]} podium places · {c["wins"]} category wins · {c["people"]} people · {c["marques"]} marques · {c["categories"]} categories · routes with no drawable stop: {[e["y"] for e in editions if len(e["stops"]) < 2]} · {out.stat().st_size/1e3:.0f} KB')
