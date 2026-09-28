"""Bring the Isle of Man TT archive into the site.

  python3 tools/prepare_tt.py /path/to/isle_of_man_tt_atlas_1907_2026.html

Reads the prototype page's embedded <script id="data"> (races and results transcribed from Wikipedia, CC BY-SA 4.0) and
<script id="mapdata"> (the Snaefell Mountain Course from OpenStreetMap relation 188240, ODbL), and writes data/tt.json:
the races with their results packed as rows, the riders, the lap records, the cancellations and reconciliation notes, and
the course as a 500×500 outline with its named places. A sidecar result whose marque the source leaves blank is given the
marque named in its machine description, marked as derived. Nothing else is altered.
"""
import json, re, sys, pathlib, math
ROOT = pathlib.Path(__file__).resolve().parent.parent
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/root/.claude/uploads/2262494c-9f9b-56f3-9e1e-9ea59da7ec22/84f371c5-isle_of_man_tt_atlas_1907_2026.html')
html = src.read_text(encoding='utf-8')
def block(sid):
    m = re.search(r'<script id="%s" type="[^"]*">(.*?)</script>' % sid, html, flags=re.S); return json.loads(m.group(1)) if m else None
D = block('data'); M = block('mapdata')
assert D and D.get('licence', '').startswith('CC BY-SA')
sys.path.insert(0, str(ROOT/'tools')); import osm_outlines
# ---- the course: stitch relation ways into the lap, project the named places into the same box
feats = [f for f in (M.get('geojson') or {}).get('features', []) if f.get('geometry', {}).get('type') == 'LineString']
ways = [{'geometry': [{'lon': c[0], 'lat': c[1]} for c in f['geometry']['coordinates']], 'tags': {}} for f in feats]  # every member way of the route relation belongs to the lap, service-tagged dips included
loop = osm_outlines.stitch(ways)
lat0 = sum(p[1] for p in loop) / len(loop); k = math.cos(math.radians(lat0))
xs = [p[0] * k for p in loop]; ys = [-p[1] for p in loop]; minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys); span = max(maxx - minx, maxy - miny) or 1; pad = 40; scale = (500 - 2 * pad) / span
ox = pad + (500 - 2 * pad - (maxx - minx) * scale) / 2; oy = pad + (500 - 2 * pad - (maxy - miny) * scale) / 2
proj = lambda lon, lat: (round(ox + (lon * k - minx) * scale, 1), round(oy + (-lat - miny) * scale, 1))
course_d = osm_outlines.to_path(loop)
landmarks = []
for l in M.get('landmarks', []):
    lon, lat = l['coordinates']; x, y = proj(lon, lat)
    # position along the lap: nearest vertex of the loop, as a fraction of its length (the replay and the list use it)
    best, bi = 1e9, 0; acc = 0; cum = [0]
    for i in range(1, len(loop)): cum.append(cum[-1] + math.hypot((loop[i][0] - loop[i-1][0]) * k, loop[i][1] - loop[i-1][1]))
    for i, p in enumerate(loop):
        d = math.hypot((p[0] - lon) * k, p[1] - lat)
        if d < best: best, bi = d, i
    landmarks.append({'n': l['name'], 'x': x, 'y': y, 't': round(cum[bi] / cum[-1], 4), 'wp': (l.get('tags') or {}).get('wikipedia', '')})
landmarks.sort(key=lambda l: l['t'])
# the lap starts at the Grandstand on Glencrutchery Road if it is among the places: rotate the fractions so it is 0
start = next((l for l in landmarks if 'grandstand' in l['n'].lower() or 'glencrutchery' in l['n'].lower() or 'start line' in l['n'].lower()), None)
if start:
    t0 = start['t']
    for l in landmarks: l['t'] = round((l['t'] - t0) % 1, 4)
    for l in landmarks:  # the lap ends at Governor's Bridge, a few metres before the line where the open chain begins
        if l['t'] < 0.002 and 'governor' in l['n'].lower(): l['t'] = 0.9995
    landmarks.sort(key=lambda l: l['t'])
course = {'name': 'Snaefell Mountain Course', 'd': course_d, 'closed': loop[0] == loop[-1], 'startT': start['t'] if start else 0, 'landmarks': landmarks, 'km': 60.72, 'miles': 37.73, 'source': M.get('source'), 'sourceVersion': M.get('sourceVersion'), 'sourceTimestamp': M.get('sourceTimestamp'), 'retrieved': M.get('retrieved'), 'licence': M.get('licence'), 'attribution': M.get('attribution'), 'changes': M.get('changes')}
COURSES = {'Mountain Course': {'from': 1911, 'km': 60.72, 'note': 'The Snaefell Mountain Course, 37.73 miles from the Grandstand over the mountain and back, used from 1911 for every TT race that was not run on a short course.'}, 'St. John’s Short Course': {'from': 1907, 'to': 1910, 'km': 25.44, 'note': 'The first course, 15.8 miles through St John’s, Ballacraine, Kirk Michael and Peel, used for the four TTs of 1907–1910.'}, 'Clypse Course': {'from': 1954, 'to': 1959, 'km': 17.36, 'note': 'A 10.79-mile course from the Grandstand through Onchan and Creg-ny-Baa, used for the Lightweight, Ultra-Lightweight and Sidecar races of 1954–1959.'}, 'Billown Circuit': {'km': 6.85, 'note': 'The 4.25-mile Castletown course of the Southern 100 and the Pre-TT Classic, used for support races.'}}
# ---- races: results packed, sidecar marques derived from the machine where blank
MARQUES = ['Honda', 'Yamaha', 'Suzuki', 'Kawasaki', 'BMW', 'Triumph', 'Norton', 'Ducati', 'MV Agusta', 'Moto Guzzi', 'BSA', 'Velocette', 'Paton', 'AJS', 'Mugen', 'Rudge', 'New Imperial', 'Excelsior', 'Sunbeam', 'Vincent', 'MotoCzysz', 'Matchless', 'Rex-Acme', 'Benelli', 'Mondial', 'Gilera', 'EMC', 'Douglas', 'Scott', 'Indian', 'Aprilia', 'LCR', 'Windle', 'Ireson', 'Baker', 'Shelbourne', 'DMR', 'Derbyshire', 'Bimota', 'Rotax', 'Konig', 'König', 'Weslake', 'Imp', 'Fath', 'URS', 'Cotton', 'Levis', 'HRD', 'Royal Enfield', 'Ariel', 'Guzzi', 'NSU', 'DKW', 'Jawa', 'CZ', 'MZ', 'Bultaco', 'Ossa', 'Montesa', 'Morini', 'Chevallier', 'Ryan', 'Harley-Davidson', 'Kreidler', 'Cagiva', 'Petronas', 'Sarolea', 'Motosacoche', 'Husqvarna', 'Puch', 'Zundapp', 'Zündapp', 'Terrot', 'Peugeot', 'Alcyon', 'Humber', 'Rover', 'Rex', 'Ivy', 'OK-Supreme', 'OK Supreme', 'Cotton', 'AJW', 'Dunelt', 'James', 'Francis-Barnett', 'Coventry-Eagle', 'Grindlay-Peerless', 'Zenith', 'Chater-Lea', 'Ner-a-Car', 'ABC', 'Sun', 'Diamond', 'Blackburne', 'Calthorpe', 'P&M', 'Panther', 'Brough Superior', 'Vincent-HRD', 'Greeves', 'Cotton', 'Villiers', 'Seeley', 'Yamsel', 'Rickman', 'Metisse', 'Padgett', 'Spondon', 'Maxton', 'Harris', 'Bakker', 'Britten', 'Buell', 'Aermacchi', 'Bianchi', 'Parilla', 'Ducson', 'Itom', 'Motobi', 'Derbi', 'Tomos', 'Garelli', 'Minarelli', 'Malanca', 'Piovaticci', 'Van Veen', 'Morbidelli', 'Sanvenero', 'Cimatti', 'Motom', 'Laverda', 'Bimota', 'Yamaha', 'Kawasaki']
# the sources spell a few marques two ways; the archive keeps one. 'Unknown' in a source is a blank, not a marque.
MARQUE_ALIAS = {'A.J.S.': 'AJS', 'M.Z.': 'MZ', 'Rex Acme': 'Rex-Acme', 'OK Supreme': 'OK-Supreme', 'B.S.A.': 'BSA', 'N.S.U.': 'NSU', 'H.R.D.': 'HRD', 'M.V. Agusta': 'MV Agusta', 'MV': 'MV Agusta', 'Unknown': '', 'unknown': '', '?': '', '—': '', '-': ''}
def derive(machine):
    m = machine or ''
    for q in sorted(set(MARQUES), key=len, reverse=True):
        if re.search(r'(?<![A-Za-z])' + re.escape(q) + r'(?![A-Za-z])', m, flags=re.I): return q
    return None
RF = ['crew', 'pos', 'status', 'machine', 'marque', 'mph', 'time', 'mq']  # mq: 'src' = marque as transcribed, 'machine' = derived here, '' = none
# plausible ceilings for a race average, by year: a table that exceeds them was transcribed in km/h (1951's Clubman's races), a value under 20 is unreadable
def ceiling(y): return 55 if y < 1914 else 72 if y < 1931 else 95 if y < 1950 else 105 if y < 1960 else 112 if y < 1976 else 122 if y < 1991 else 130 if y < 2006 else 137
speed_fixes = []
races = []; derived = 0
for r in D['races']:
    rows = []
    speeds = [x.get('mph') for x in r['results'] if x.get('mph')]
    kmh = bool(speeds) and all(v > ceiling(r['year']) for v in speeds) and all(v / 1.609344 <= ceiling(r['year']) for v in speeds)
    if kmh: speed_fixes.append({'race': r['id'], 'fix': 'km/h read as mph: divided by 1.609344', 'values': len(speeds)})
    for x in r['results']:
        mph = x.get('mph') or None  # a 0.0 is a blank cell (a non-finisher), not a speed
        if mph is not None:
            if kmh: mph = round(mph / 1.609344, 2)
            elif mph < 20 or mph > ceiling(r['year']) * 1.15: speed_fixes.append({'race': r['id'], 'fix': f'unreadable average {mph} discarded', 'rider': x['crew'][0] if x.get('crew') else None}); mph = None
        x = dict(x, mph=mph)
        marque = MARQUE_ALIAS.get((x.get('marque') or '').strip(), (x.get('marque') or '').strip()) or None  # one spelling per marque; 'Unknown' is a blank
        mq = 'src' if marque else ''
        if not marque:
            d = derive(x.get('machine'))
            if d: marque, mq = d, 'machine'; derived += 1
        rows.append([x['crew'], x.get('pos'), x.get('status'), x.get('machine'), marque, x.get('mph'), x.get('time'), mq])
    races.append({'id': r['id'], 'y': r['year'], 'name': r['name'], 'family': r['family'], 'course': r['course'], 'kind': r['kind'], 'scope': r['scope'], 'date': r.get('date'), 'laps': r.get('laps'), 'results': rows, 'url': r['results'][0].get('url') if r['results'] else None})
races.sort(key=lambda r: (r['y'], r['date'] or '9999', r['name']))
core = {'races': races, 'resultFields': RF, 'riders': D['riders'], 'records': D['records'], 'cancelled': D['cancelled'], 'issues': D['issues'], 'corrections': D['corrections'], 'speedFixes': speed_fixes, 'sources': D['sources'], 'coverage': dict(D['coverage'], marquesDerived=derived, marquesAliased=len(MARQUE_ALIAS), speedsConverted=sum(1 for f in speed_fixes if f['fix'].startswith('km/h')), speedsDiscarded=sum(1 for f in speed_fixes if f['fix'].startswith('unreadable'))), 'method': D['method'], 'licence': D['licence'], 'licenceUrl': D['licenceUrl'], 'snapshot': D['snapshot'], 'lastYear': max(r['y'] for r in races), 'course': course, 'courses': COURSES}
out = ROOT/'data'/'tt.json'; out.write_text(json.dumps(core, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'tt: speed fixes {len(speed_fixes)} ({sum(1 for f in speed_fixes if f["fix"].startswith("km/h"))} tables in km/h, {sum(1 for f in speed_fixes if f["fix"].startswith("unreadable"))} values discarded)'); print(f'tt: {len(races)} races · {sum(len(r["results"]) for r in races):,} results · {len(D["riders"]):,} riders · {derived} sidecar marques derived from the machine · course {len(loop)} points, closed={loop[0] == loop[-1]}, {len(landmarks)} named places, start at {start["n"] if start else "—"} · {out.stat().st_size/1e6:.1f} MB')
