#!/usr/bin/env python3
"""Circuit outlines from OpenStreetMap (© OpenStreetMap contributors, ODbL).

For each circuit in a bikes archive, query Overpass for highway=raceway ways near the circuit's
coordinates, stitch the closed loop, and write a 500×500 SVG path into src/bikes/assets_<sport>.json
under "osm". Run where the network is open (GitHub Actions or a desktop):

    python tools/osm_outlines.py motogp
    python tools/osm_outlines.py sbk

Circuits without coordinates or without a mapped raceway are skipped and keep the ring-of-winners
fallback. Overpass is public infrastructure: the script sends one query per circuit with a
descriptive User-Agent and pauses between calls.
"""
import json, math, pathlib, sys, time, urllib.request, urllib.parse
ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = 'sportsfans.co.za atlas build (https://sportsfans.co.za; contact via the site) python-urllib'
OVERPASS = 'https://overpass-api.de/api/interpreter'

def overpass(query):
    req = urllib.request.Request(OVERPASS, data=urllib.parse.urlencode({'data': query}).encode(), headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=120) as r: return json.loads(r.read().decode('utf-8'))

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
    q = f'[out:json][timeout:60];(way["highway"="raceway"](around:{radius},{lat},{lon}););out geom;'
    return overpass(q).get('elements', [])

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
                nonlocal best, best_a
                if a > best_a: best, best_a = new_path, a
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
    # a closed cycle wins unless it is a fragment (a roundabout, a link) beside a much longer open chain
    if best is not None and best_a > 0 and (longest is None or chain_length(best) >= 0.5 * chain_length(longest)): return best
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

def main(tag):
    A = json.loads((ROOT/'data'/f'{tag}.json').read_text(encoding='utf-8'))
    assets_p = ROOT/'src'/'bikes'/f'assets_{tag}.json'; assets = json.loads(assets_p.read_text(encoding='utf-8'))
    osm = assets.get('osm', {}); done = 0; skipped = []
    for cid, c in A['circuits'].items():
        if cid in osm: continue
        lat, lon = c.get('lat'), c.get('lng') or c.get('lon')
        if lat is None or lon is None:
            try: lat, lon = geocode(c['name'], c.get('country', ''))
            except Exception as e: lat = lon = None
        if lat is None or lon is None: skipped.append((c['name'], 'not found by name')); continue
        try:
            ways = raceway_ways(lat, lon); loop = stitch(ways)
            if not loop or len(loop) < 12: skipped.append((c['name'], 'no mapped raceway')); continue
            osm[cid] = to_path(loop); done += 1; print('ok ', c['name'], len(loop), 'points')
        except Exception as e:
            skipped.append((c['name'], f'error {e}'))
        time.sleep(2)
    assets['osm'] = osm; assets_p.write_text(json.dumps(assets, separators=(',', ':')), encoding='utf-8')
    print(f'{tag}: {done} new outlines, {len(osm)} total; skipped {len(skipped)}')
    for n, why in skipped: print('   -', n, '·', why)

if __name__ == '__main__': main(sys.argv[1])
