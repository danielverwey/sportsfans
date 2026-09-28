#!/usr/bin/env python3
"""Circuit outlines from OpenStreetMap (© OpenStreetMap contributors, ODbL).

For each circuit in a bikes archive that has no outline yet, query Overpass for the mapped track near the
circuit's coordinates, stitch the lap, and write a 500×500 SVG path into src/bikes/assets_<sport>.json
under "osm". Run where the network is open (GitHub Actions or a desktop):

    python tools/osm_outlines.py motogp sbk

Three passes per circuit, each only if the previous found nothing: highway=raceway ways within 2.5 km,
the same within 5 km, then the roads of a named route relation or motor-sport track within 8 km (the
public-road courses: Dundrod, Clady, Opatija, Solitude…). The Snaefell Mountain Course is copied from the
TT archive (data/tt.json), which already carries it from OSM relation 188240. Circuits with an F1DB survey
keep it. Overpass is shared public infrastructure: one query at a time, a descriptive User-Agent, a pause
between calls, three tries per query across mirrors with a short backoff, a mirror rested after repeated refusals, and a
run that stops itself after OUTLINES_MINUTES (100) keeping every outline found so far. Everything found and
everything skipped (with the reason) is written to the GitHub job summary when there is one.
"""
import json, math, os, pathlib, re, sys, time, urllib.error, urllib.request, urllib.parse
ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = 'sportsfans.co.za atlas build (https://sportsfans.co.za; sportsfans.co.za@gmail.com) python-urllib'
ENDPOINTS = ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter', 'https://overpass.private.coffee/api/interpreter']
BACKOFF = [6, 18]            # seconds after a refusal, per retry (three tries per query in all)
MIRROR_REST = 600            # a mirror that fails twice running is left alone for ten minutes
DEADLINE_MIN = float(os.environ.get('OUTLINES_MINUTES', '100'))  # the run stops itself before the job's timeout and keeps what it has
T0 = time.time()
sys.setrecursionlimit(20000)
_bad = {}  # mirror → (consecutive failures, time of the last one)

class OverpassError(Exception): pass

def _mirrors():
    now = time.time(); live = [m for m in ENDPOINTS if not (_bad.get(m, (0, 0))[0] >= 2 and now - _bad[m][1] < MIRROR_REST)]
    return live or ENDPOINTS

def overpass(query, tries=3):
    """POST a query, rotating mirrors: a 429 (slot busy), 5xx (overloaded) or a dropped connection waits and tries the next.
    A mirror that keeps failing is rested so the run does not spend its time on it."""
    errors = []; ms = _mirrors()
    for i in range(tries):
        url = ms[i % len(ms)]
        req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': query}).encode(), headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=120) as r: body = r.read().decode('utf-8')
            try: out = json.loads(body); _bad[url] = (0, 0); return out
            except ValueError: errors.append(f'{url}: not JSON ({body[:80]!r})')
        except urllib.error.HTTPError as e:
            errors.append(f'{url}: HTTP {e.code}')
            if e.code == 400: raise OverpassError(f'query rejected by {url}: ' + e.read().decode("utf-8", "replace")[:300])
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            errors.append(f'{url}: {getattr(e, "reason", e)}')
        n, _ = _bad.get(url, (0, 0)); _bad[url] = (n + 1, time.time())
        if i < tries - 1: time.sleep(BACKOFF[min(i, len(BACKOFF) - 1)])
    raise OverpassError('; '.join(errors))

def out_of_time(): return (time.time() - T0) / 60 > DEADLINE_MIN

def geocode(name, country):
    """Nominatim search for a circuit by name (one request per second, descriptive User-Agent, as their policy asks)."""
    for q in (f'{name}, {country}', f'{name} circuit, {country}', name):
        url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({'q': q, 'format': 'json', 'limit': 1})
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=60) as r: hits = json.loads(r.read().decode('utf-8'))
        time.sleep(1.2)
        if hits: return float(hits[0]['lat']), float(hits[0]['lon'])
    return None, None

def raceway_ways(lat, lon, radius=2500):
    q = f'[out:json][timeout:90];(way["highway"="raceway"](around:{radius},{lat},{lon}););out geom;'
    return overpass(q).get('elements', [])

# a route relation is a circuit when its name says so as a word (circuit, course, autodrom, Rennstrecke, the Finnish and
# Swedish track nouns) or ends in -ring/-strecke/-bana/-rata; bus, cycle, hiking and rail routes are never candidates
ROUTE_NAME = '(^|[^a-z])(circuit|circuito|circuits|course|racecourse|rennstrecke|racing|autodrom|autodromo|autódromo|motodrom|moottorirata|motorbana|racerbana|rennen|grand prix|tourist trophy)([^a-z]|$)|ring$|strecke$|bana$|rata$'
NOT_ROUTE = 'bus|bicycle|hiking|foot|walking|train|tram|ferry|railway|subway|light_rail|mtb|ski|horse|running|detour|trolleybus|canoe|inline_skates|piste|power|pipeline'
def route_ways(lat, lon, radius=8000):
    """The public-road courses: the member ways of a route relation named like a circuit, or of a relation or track
    tagged for motor sport, within the radius. The stitcher then takes the largest closed cycle or the longest chain."""
    q = (f'[out:json][timeout:120];'
         f'(relation(around:{radius},{lat},{lon})["type"="route"]["name"~"{ROUTE_NAME}",i]["route"!~"{NOT_ROUTE}"];'
         f'relation(around:{radius},{lat},{lon})["sport"~"motor"];'
         f'relation(around:{radius},{lat},{lon})["type"="route"]["route"~"^(racing|motor|motorsport|road_racing)$"];)->.r;'
         f'(way(r.r);way(around:{radius},{lat},{lon})["leisure"="track"]["sport"~"motor"];);'
         f'out geom;')
    return overpass(q).get('elements', [])

MIN_LAP_KM, MAX_LAP_KM = 1.5, 30.0  # a racing lap; shorter is a kart track or a fragment, longer is a ring road
def loop_km(loop):
    """Length of a lon/lat polyline in km (equirectangular, fine at circuit scale)."""
    lat0 = sum(p[1] for p in loop) / len(loop); k = math.cos(math.radians(lat0))
    return sum(math.hypot((b[0] - a[0]) * k, b[1] - a[1]) for a, b in zip(loop, loop[1:])) * 111.32

SIDE = ('pit', 'paddock', 'service', 'access', 'escape', 'run-off', 'runoff', 'kart', 'oval link', 'link road', 'bypass')
def is_side(tags):
    """Ways that are part of the venue but not the racing line: pit lanes, service roads, kart tracks."""
    t = {k.lower(): str(v).lower() for k, v in (tags or {}).items()}
    name = t.get('name', '') + ' ' + t.get('description', '')
    return any(w in name for w in SIDE) or t.get('service') in ('pit_lane', 'paddock') or t.get('sport') in ('karting',) or t.get('highway') == 'service'
def chain_length(seg):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(seg, seg[1:]))
def stitch(ways):
    """The racing line from a venue's raceway ways: pit lanes and service ways are left out, then the ways form a small
    graph whose longest-area simple cycle is searched by depth-first traversal (bounded), so an alternative chicane or a
    link road cannot short-circuit the lap. If nothing closes, the longest open chain is returned."""
    segs = [[(p['lon'], p['lat']) for p in w.get('geometry', [])] for w in ways if w.get('geometry') and not is_side(w.get('tags'))]
    segs = [s for s in segs if len(s) > 1]
    if not segs: return None
    def area(loop):
        lat0 = sum(p[1] for p in loop) / len(loop); k = math.cos(math.radians(lat0))
        return abs(sum((a[0] * k) * b[1] - (b[0] * k) * a[1] for a, b in zip(loop, loop[1:] + loop[:1]))) / 2
    closed = [s for s in segs if s[0] == s[-1]]
    best = max(closed, key=area) if closed else None; best_a = area(best) if best else 0
    longcyc = max(closed, key=chain_length) if closed else None  # the longest simple cycle, kept beside the largest-area one
    # adjacency: endpoint → [(segment index, oriented points)]
    adj = {}
    for i, s in enumerate(segs):
        adj.setdefault(s[0], []).append((i, s)); adj.setdefault(s[-1], []).append((i, s[::-1]))
    budget = [60000]
    def dfs(start, node, used, path):
        if budget[0] <= 0: return
        for i, pts in adj.get(node, []):
            if i in used: continue
            budget[0] -= 1
            nxt = pts[-1]; new_path = path + pts[1:]
            if nxt == start:
                a = area(new_path)
                nonlocal best, best_a, longcyc
                if a > best_a: best, best_a = new_path, a
                if longcyc is None or chain_length(new_path) > chain_length(longcyc): longcyc = new_path
                continue
            if nxt in seen_nodes: continue
            seen_nodes.add(nxt); used.add(i); dfs(start, nxt, used, new_path); used.discard(i); seen_nodes.discard(nxt)
    for i, s in enumerate(segs):
        seen_nodes = {s[0]}; dfs(s[0], s[0], set(), [s[0]])
        if budget[0] <= 0: break
    longest = None
    for start in range(len(segs)):
        pool = segs[:start] + segs[start + 1:]; loop = list(segs[start]); changed = True
        while pool and changed:
            changed = False
            for i, s in enumerate(pool):
                if s[0] == loop[-1]: loop += s[1:]; pool.pop(i); changed = True; break
                if s[-1] == loop[-1]: loop += s[-2::-1]; pool.pop(i); changed = True; break
                if s[-1] == loop[0]: loop = s[:-1] + loop; pool.pop(i); changed = True; break
                if s[0] == loop[0]: loop = s[::-1][:-1] + loop; pool.pop(i); changed = True; break
        if longest is None or chain_length(loop) > chain_length(longest): longest = loop
    # an oval inside a road course encloses more area than the lap that uses part of it: when a much longer simple
    # cycle exists, the longer one is the lap
    if best is not None and longcyc is not None and chain_length(longcyc) >= 1.4 * chain_length(best): best = longcyc; best_a = area(best)
    # a closed cycle wins unless it is a fragment (a roundabout, a link) beside a much longer open chain
    if best is not None and best_a > 0 and (longest is None or chain_length(best) >= 0.5 * chain_length(longest)): return best
    # an open chain whose ends nearly meet (a missing node at the line) is closed
    if longest is not None and len(longest) > 2:
        lat0 = longest[0][1]; k = math.cos(math.radians(lat0)); gap = math.hypot((longest[0][0] - longest[-1][0]) * k, longest[0][1] - longest[-1][1]) * 111.32
        if gap <= 0.3 and gap <= 0.03 * chain_length(longest) * 111.32: longest = longest + [longest[0]]
    return longest

def to_path(loop):
    lat0 = sum(p[1] for p in loop) / len(loop)
    xs = [p[0] * math.cos(math.radians(lat0)) for p in loop]; ys = [-p[1] for p in loop]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys); span = max(maxx - minx, maxy - miny) or 1
    pad = 40; scale = (500 - 2 * pad) / span
    ox = pad + (500 - 2 * pad - (maxx - minx) * scale) / 2; oy = pad + (500 - 2 * pad - (maxy - miny) * scale) / 2
    pts = [(ox + (x - minx) * scale, oy + (y - miny) * scale) for x, y in zip(xs, ys)]
    # thin out points closer than 2px
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) >= 2: out.append(p)
    d = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in out) + (' Z' if loop[0] == loop[-1] else '')
    return d

def outline_for(c):
    """(path, how) for a circuit record, or (None, why)."""
    lat, lon = c.get('lat'), c.get('lng') or c.get('lon')
    if lat is None or lon is None:
        try: lat, lon = geocode(c['name'], c.get('country', ''))
        except Exception: lat = lon = None
    if lat is None or lon is None: return None, 'no coordinates and not found by name'
    for how, fetch in (('raceway 2.5 km', lambda: raceway_ways(lat, lon, 2500)), ('raceway 5 km', lambda: raceway_ways(lat, lon, 5000)), ('route relation 8 km', lambda: route_ways(lat, lon, 8000))):
        ways = fetch()
        if not ways: time.sleep(2); continue
        loop = stitch(ways)
        if loop and len(loop) >= 12:
            km = loop_km(loop)
            if not MIN_LAP_KM <= km <= MAX_LAP_KM: time.sleep(2); continue  # a fragment (a kart track, a pit straight, a piece of a demolished circuit) or a ring road, not a lap
            return to_path(loop), f'{how} · {len(ways)} ways · {len(loop)} points · {km:.1f} km' + ('' if loop[0] == loop[-1] else ' · open')
        time.sleep(2)
    return None, 'no mapped track (no raceway within 5 km, no circuit route relation within 8 km)'

# outlines fetched before the lap-length guard existed that turned out to be fragments; they are dropped and fetched again
REFETCH = {'dundrod-circuit', 'imatra-circuit', 'autodromo-internacional-nelson-piquet', 'shah-alam-circuit', 'phakisa-freeway'} | set(os.environ.get('OUTLINES_REFETCH', '').replace(',', ' ').split())

def main(tags):
    report = ['## Circuit outlines from OpenStreetMap', '']
    failed_all = True; any_error = False
    shared = {}  # cid → path found for another sport in an earlier run: the same venue needs no second query
    for other in ROOT.glob('src/bikes/assets_*.json'):
        for cid, d in json.loads(other.read_text(encoding='utf-8')).get('osm', {}).items():
            if cid not in REFETCH: shared.setdefault(cid, d)
    for tag in tags:
        A = json.loads((ROOT/'data'/f'{tag}.json').read_text(encoding='utf-8'))
        assets_p = ROOT/'src'/'bikes'/f'assets_{tag}.json'; assets = json.loads(assets_p.read_text(encoding='utf-8'))
        osm = assets.setdefault('osm', {}); venues = assets.get('venues', {}); done = []; skipped = []
        for cid in list(osm):
            if cid in REFETCH: osm.pop(cid); print('dropped', cid, '(fragment from an earlier run; fetching again)', flush=True)
        tt = ROOT/'data'/'tt.json'
        stopped = False
        for cid, c in A['circuits'].items():
            if cid in osm or cid in venues: continue
            if cid in shared: osm[cid] = shared[cid]; done.append((c['name'], 'same venue, outline found for the other championship')); failed_all = False; assets_p.write_text(json.dumps(assets, separators=(',', ':')), encoding='utf-8'); continue
            if out_of_time(): stopped = True; skipped.append((c['name'], f'not tried: the run reached its {DEADLINE_MIN:.0f}-minute limit')); continue
            if cid == 'isle-of-man-tt-mountain-course' and tt.exists():
                course = json.loads(tt.read_text(encoding='utf-8')).get('course') or {}
                if course.get('d'): osm[cid] = course['d']; done.append((c['name'], 'Snaefell Mountain Course from the TT archive (OSM relation 188240)')); failed_all = False; assets_p.write_text(json.dumps(assets, separators=(',', ':')), encoding='utf-8'); continue
            try:
                path, how = outline_for(c)
            except OverpassError as e: skipped.append((c['name'], f'Overpass unavailable: {e}')); any_error = True; time.sleep(5); continue
            except Exception as e: skipped.append((c['name'], f'error: {type(e).__name__} {e}')); any_error = True; continue
            failed_all = False
            if path: osm[cid] = path; shared[cid] = path; done.append((c['name'], how)); print('ok ', c['name'], '·', how, flush=True); assets_p.write_text(json.dumps(assets, separators=(',', ':')), encoding='utf-8')
            else: skipped.append((c['name'], how)); print('--- ', c['name'], '·', how, flush=True)
            time.sleep(2)
        assets_p.write_text(json.dumps(assets, separators=(',', ':')), encoding='utf-8')
        if stopped: print(f'{tag}: stopped at the {DEADLINE_MIN:.0f}-minute limit; run the workflow again for the rest', flush=True)
        print(f'{tag}: {len(done)} new outlines, {len(osm)} from OSM in all; skipped {len(skipped)}')
        for n, why in skipped: print('   -', n, '·', why)
        report += [f'### {tag}: {len(done)} new outlines, {len(osm)} from OSM in all, {len(skipped)} without' + (' · stopped at the time limit, run again for the rest' if stopped else ''), '']
        if done: report += ['| Found | How |', '|---|---|'] + [f'| {n} | {how} |' for n, how in done] + ['']
        if skipped: report += ['| Still without an outline | Why |', '|---|---|'] + [f'| {n} | {why} |' for n, why in skipped] + ['']
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as f: f.write('\n'.join(report) + '\n')
    if failed_all and any_error:
        print('every request failed: Overpass could not be reached from this runner', file=sys.stderr); sys.exit(1)

if __name__ == '__main__': main([t for a in sys.argv[1:] for t in a.replace(',', ' ').split()] or ['motogp', 'sbk'])
