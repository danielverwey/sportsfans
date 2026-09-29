"""Bring a Wikipedia-built MotoGP or WorldSBK archive into the site.

  python3 tools/prepare_bikes.py motogp /path/to/motogp_race_atlas_1949_2026.html
  python3 tools/prepare_bikes.py sbk    /path/to/worldsbk_race_atlas_1988_2026.html

Reads the prototype page's embedded <script id="archive-data"> (results, standings, riders, circuits — Wikipedia, CC BY-SA 4.0)
and <script id="map-data"> (raceway geometry — OpenStreetMap, ODbL), writes data/<sport>.json unchanged, and refreshes
src/bikes/assets_<sport>.json: the OpenStreetMap outlines normalised into the 500×500 box the atlas draws, and the F1DB
venue surveys re-keyed from the previous archive's circuit ids to the new ones by venue name. Nothing in the archive is edited.
"""
import json, re, sys, pathlib, unicodedata
ROOT = pathlib.Path(__file__).resolve().parent.parent
sport, src = sys.argv[1], pathlib.Path(sys.argv[2])
html = src.read_text(encoding='utf-8')
def block(sid):
    m = re.search(r'<script id="%s" type="[^"]*">(.*?)</script>' % sid, html, flags=re.S)
    return json.loads(m.group(1)) if m else None
A = block('archive-data'); M = block('map-data') or {'venues': {}}
assert A and A.get('races') and A.get('licence', '').startswith('CC BY-SA'), 'not a Wikipedia-built archive'
# ---- outlines: every venue's raceway paths, joined and fitted into 500×500 with a margin
NUM = re.compile(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)')
def fit(paths, box=500, pad=24):
    pts = [(float(x), float(y)) for p in paths for x, y in NUM.findall(p)]
    if not pts: return ''
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]; x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    span = max(x1 - x0, y1 - y0) or 1; s = (box - 2 * pad) / span; ox = pad + (box - 2 * pad - (x1 - x0) * s) / 2; oy = pad + (box - 2 * pad - (y1 - y0) * s) / 2
    def tr(m): return f'{(float(m.group(1)) - x0) * s + ox:.1f},{(float(m.group(2)) - y0) * s + oy:.1f}'
    return ''.join(NUM.sub(tr, p) for p in paths)
sys.path.insert(0, str(ROOT/'tools')); import osm_outlines
def outline(v):
    feats = (v.get('geojson') or {}).get('features') or []
    ways = [{'geometry': [{'lon': c[0], 'lat': c[1]} for c in f['geometry']['coordinates']], 'tags': f.get('properties', {})} for f in feats if f.get('geometry', {}).get('type') == 'LineString']
    loop = osm_outlines.stitch(ways) if ways else None
    if loop and len(loop) >= 12: return osm_outlines.to_path(loop), loop[0] == loop[-1]
    return fit(v.get('paths', [])), False
raw = {cid: outline(v) for cid, v in M.get('venues', {}).items() if v.get('paths') or v.get('geojson')}
# ---- F1DB surveys: re-key by venue name from whatever ids the previous assets file used
assets_path = ROOT/'src'/'bikes'/f'assets_{sport}.json'
old = json.loads(assets_path.read_text(encoding='utf-8')) if assets_path.exists() else {'osm': {}, 'venues': {}}
def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'\b(circuit|circuito|autodromo|autódromo|international|raceway|motor|speedway|park|de|del|di|du|the|of|circuit de)\b', ' ', s)
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()
names = {}
for cid, c in A['circuits'].items():
    for n in [c.get('name', '')] + [a.get('name', '') for a in c.get('aliases', [])]:
        if n: names.setdefault(norm(n), cid)
# a few F1DB venue names carry no word the motorcycle archive uses (the circuits are named for their towns)
BY_HAND = {'scandinavian': 'anderstorp-raceway', 'enzo e dino ferrari': 'imola-circuit', 'juan y oscar galvez': 'autodromo-oscar-y-juan-galvez', 'jose carlos pace': 'interlagos-circuit'}
venues = {}; unmatched = []
for oid, v in old.get('venues', {}).items():
    key = norm(v.get('name', '')); cid = names.get(key) or next((c for k, c in BY_HAND.items() if k in key and c in A['circuits']), None)
    if not cid:
        for k, c in names.items():
            if key and (key in k or k in key) and len(key) > 4: cid = c; break
    if cid: venues[cid] = v
    else: unmatched.append(v.get('name'))
# an open OpenStreetMap chain yields to a closed F1DB survey of the same venue; otherwise the mapped geometry is used
osm = {cid: d for cid, (d, closed) in raw.items() if closed or cid not in venues}
# outlines already in the assets file — found by the OpenStreetMap workflow (tools/osm_outlines.py), checked for lap length —
# are kept: a new read of the archive only adds outlines for circuits that have none yet, it never takes one away
kept = {cid: d for cid, d in old.get('osm', {}).items() if d}
added_osm = [cid for cid in osm if cid not in kept]
osm = {**kept, **{cid: d for cid, d in osm.items() if cid not in kept}}   # the file's own order first, so an unchanged read leaves it byte-identical
assets_path.write_text(json.dumps({'osm': osm, 'venues': venues}, separators=(',', ':')), encoding='utf-8')   # written exactly as tools/osm_outlines.py writes it
(ROOT/'data'/f'{sport}.json').write_text(json.dumps(A, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
mapped = [c for c in A['circuits'] if c in osm or c in venues]
print(f'{sport}: {len(A["races"]):,} races · {sum(len(r["results"]) for r in A["races"]):,} results · {len(A["riders"]):,} riders · {len(A["circuits"])} circuits · outlines: {len(osm)} from OpenStreetMap, {len(venues)} F1DB surveys re-keyed ({len(set(venues) - set(osm))} circuits get one only from F1DB), {len(A["circuits"]) - len(mapped)} without an outline · snapshot {A.get("snapshot")} · through {A.get("lastDate")}')
print(f'  outlines kept from the assets file: {len(kept)} · added from this archive: {len(added_osm)}{" (" + ", ".join(added_osm[:6]) + ("…" if len(added_osm) > 6 else "") + ")" if added_osm else ""}')
if unmatched: print('  F1DB venues with no match in the new archive (dropped):', ', '.join(unmatched))
