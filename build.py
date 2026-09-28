#!/usr/bin/env python3
"""Build the APEX sports atlases.

Two outputs from one set of sources:
  HTML FILEs/ and docs/downloads/   the self-contained single-file editions (archive embedded byte-for-byte)
  docs/                             the production site: small page shells, shared assets, the archives as
                                    data files, the reading editions as pages, and a static page for every
                                    season, driver/rider/player, constructor/maker/nation, circuit/ground and coach.
Run:  python build.py                       (sportsfans.co.za: CNAME, canonical links, sitemap)
      python build.py --site URL --no-cname (a preview on GitHub's own address)
      python build.py --no-pages            (skip the static entity pages)
"""
import subprocess, argparse, hashlib, json, pathlib, re, shutil, sys, datetime, colorsys, base64, gzip
ROOT = pathlib.Path(__file__).resolve().parent
SRC, DATA, DOCS, DROP = ROOT/'src', ROOT/'data', ROOT/'docs', ROOT/'HTML FILEs'
sys.path.insert(0, str(ROOT/'tools')); import sitegen, reading
ap = argparse.ArgumentParser(); ap.add_argument('--site', default='https://sportsfans.co.za'); ap.add_argument('--no-cname', action='store_true', help='skip docs/CNAME (for a *.github.io preview)'); ap.add_argument('--no-pages', action='store_true', help='skip the static entity pages'); ap.add_argument('--publish', default=None, help='comma-separated sports to publish (default: PUBLISH below)'); args = ap.parse_args()
# Sports whose sources are clear go to docs/; the rest are built into build/held/ and stay off the site until their rights position settles.
PUBLISH = ['f1', 'rugby', 'cricket', 'tennis', 'motogp', 'sbk', 'tt', 'ufc']; HELD = {}
if args.publish: PUBLISH = [k for k in args.publish.split(',') if k]; HELD = {k: v for k, v in HELD.items() if k not in PUBLISH}
HELD_DIR = ROOT/'build'/'held'
SITE = args.site.rstrip('/')
h = lambda b: hashlib.sha256(b).hexdigest()[:10]

def check_embedded(built: bytes, data: bytes, marker: bytes, static: bytes, footer: bytes):
    i = built.index(marker) + len(marker)
    assert built[i:i+len(data)] == data, 'archive not byte-identical'
    assert static in built and footer in built, 'carried parts changed'

# ---------- the parts of each page ----------
def parts_f1():
    d = SRC/'f1'; data = (DATA/'f1.json').read_bytes(); D = json.loads(data.decode('utf-8'))
    # the reading edition and the dated footer are generated from the archive, so a sweep never leaves them stale
    static = reading.reading_f1(D).encode('utf-8'); footer = reading.footer_f1(D, (DATA/'carried/f1_footer.html').read_text(encoding='utf-8')).rstrip('\n').encode('utf-8')
    css = (d/'style.css').read_bytes(); app = b'\n'.join((d/f'app{i}.js').read_bytes() for i in range(1,5)); shell = (d/'shell.html').read_text(encoding='utf-8')
    return dict(key='f1', shell=shell, css=css, app=app, data=data, static=static, footer=footer, marker=b'const DATA=', title='F1 · An Ode to Formula 1 · 1950–2026', global_='DATA', script_block='<script>const DATA=__DATA__;</script>\n<script>\n__APP__\n</script>')

def parts_rugby():
    d = SRC/'rugby'; data = (DATA/'rugby.json').read_bytes(); A = json.loads(data.decode('utf-8'))
    static = reading.reading_rugby(A).encode('utf-8'); footer = reading.footer_rugby(A, (DATA/'carried/rugby_footer.html').read_text(encoding='utf-8')).encode('utf-8')
    css = (d/'style.css').read_bytes(); app = b'\n'.join((d/f'app{i}.js').read_bytes() for i in range(1,5)); shell = (d/'shell.html').read_text(encoding='utf-8')
    assert b'</script>' not in data
    return dict(key='rugby', shell=shell, css=css, app=app, data=data, static=static, footer=footer, marker=b'type="application/json">', title='Rugby · An Ode to the Test Match · 1871–2026', global_='ARCHIVE', script_block='<script id="archive-data" type="application/json">__DATA__</script>\n<script>\n__APP__\n</script>')

def parts_bike(tag):
    d = SRC/'bikes'; data = (DATA/f'{tag}.json').read_bytes()
    D = json.loads(subprocess.check_output(['node', str(ROOT/'tools'/'adapt_bikes.js'), tag])); A = json.loads(data.decode('utf-8'))
    static = reading.reading_bikes(tag, D).encode('utf-8'); footer = reading.footer_bikes(tag, A).encode('utf-8')
    cfg = (d/f'config_{tag}.js').read_text(encoding='utf-8'); assets = json.loads((d/f'assets_{tag}.json').read_text(encoding='utf-8'))
    assets_js = 'SPORT.osm=' + json.dumps(assets.get('osm', {}), separators=(',',':')) + ';SPORT.venues=' + json.dumps(assets['venues'], separators=(',',':')) + ';'
    adapter = (d/'adapter.js').read_text(encoding='utf-8'); app = (d/f'app_{tag}.js').read_text(encoding='utf-8'); css = (d/'style_bikes.css').read_text(encoding='utf-8'); shell = (d/'shell_bikes.html').read_text(encoding='utf-8')
    meta = {'motogp': ('APEX / An Ode to MotoGP · 1949–2026', 'Seventy-eight seasons of the premier class drawn as a river of manufacturer colours, every circuit drawn to its own line, every race replayed grid to flag. 1949–2026.', 'An ode to MotoGP · 1949–2026', 'Seventy-eight <span>seasons</span> in one current'),
            'sbk': ('APEX / An Ode to World Superbike · 1988–2026', 'Thirty-nine seasons of World Superbike drawn as a river of manufacturer colours, every circuit drawn to its own line, every race replayed grid to flag. 1988–2026.', 'An ode to World Superbike · 1988–2026', 'Thirty-nine <span>seasons</span> in one current')}[tag]
    lede = re.search(r"riverLede:'(.*?)',\n", cfg).group(1)
    shell = shell.replace('__TITLE__', meta[0]).replace('__DESC__', meta[1]).replace('__BRANDTAG__', meta[2]).replace('__HERO__', meta[3]).replace('__RIVERLEDE__', lede)
    shell = shell.replace('__CONFIG__\n__ASSETS__\n__ADAPTER__\n__APP__', '__APP__')
    bundle = '\n'.join((cfg, assets_js, adapter, app))
    for blob in (bundle, css): assert '</script>' not in blob and '</style>' not in blob
    assert '</script>' not in data.decode('utf-8')
    return dict(key=tag, shell=shell, css=css.encode('utf-8'), app=bundle.encode('utf-8'), data=data, static=static, footer=footer, marker=b'type="application/json">', title={'motogp': 'MotoGP · An Ode to MotoGP · 1949–2026', 'sbk': 'WorldSBK · An Ode to World Superbike · 1988–2026'}[tag], global_='ARCHIVE', script_block='<script id="archive-data" type="application/json">__DATA__</script>\n<script>\n__APP__\n</script>')

HOME_CSS = '.switch{display:flex;gap:6px;flex-wrap:wrap;padding:12px 0 0;font:11px var(--mono);letter-spacing:.16em;text-transform:uppercase}.switch a{color:var(--muted);text-decoration:none;padding:6px 10px;border:1px solid var(--line);border-radius:6px}.switch a.on{color:var(--accent);border-color:var(--accent)}.switch a:hover{color:var(--ink);border-color:var(--muted)}.switch a.go{margin-left:auto;color:var(--accent);border-color:var(--accent)}.switch a.go:hover{background:var(--accent);color:var(--on-accent,#07080a)}.brand a.home{color:inherit;text-decoration:none}.brand small a{white-space:nowrap}.brand a.home:hover i{color:var(--ink,#fff)}.brand small a{color:inherit;text-decoration:none;border-bottom:1px solid var(--line,#2a2d33)}.brand small a:hover{color:var(--accent,#FF8000)}footer p.small a{color:inherit}'
NOTICE_HTML = '<div class="wrap"><p class="small dim" style="margin:-30px 0 40px;max-width:900px">' + sitegen.NOTICE + ' Sources and licences: <a href="https://sportsfans.co.za/licences/">sportsfans.co.za/licences</a>.</p></div>'
def parts_cricket():
    d = SRC/'cricket'; data = (DATA/'cricket.json').read_bytes(); core = json.loads(data.decode('utf-8'))
    details = {int(f.stem): json.loads(f.read_text(encoding='utf-8')) for f in sorted((DATA/'cricket_details').glob('*.json'))}
    pack = base64.b64encode(gzip.compress(json.dumps({'core': core, 'details': details}, ensure_ascii=False, separators=(',', ':')).encode('utf-8'), compresslevel=9, mtime=0))
    static = reading.reading_cricket(core).encode('utf-8'); footer = reading.footer_cricket(core).encode('utf-8')
    css = (d/'style.css').read_bytes(); app = b'\n'.join((d/f'app{i}.js').read_bytes() for i in range(1,5)); shell = (d/'shell.html').read_text(encoding='utf-8')
    pako = '<script>\n' + (d/'pako.min.js').read_text(encoding='utf-8') + '\n</script>'
    assert '</script>' not in pako[8:-9]
    return dict(key='cricket', shell=shell, css=css, app=app, data=data, pack=pack, pako=pako, details=details, static=static, footer=footer, marker=b'type="application/octet-stream">', title='Cricket · An Ode to the International Game · 1877–2026', global_='PACK', script_block='__PAKO__\n<script id="archive-data" type="application/octet-stream">__DATA__</script>\n<script>\n__APP__\n</script>', detail_dir='cricket_details')

def parts_tennis():
    d = SRC/'tennis'; data = (DATA/'tennis.json').read_bytes(); core = json.loads(data.decode('utf-8'))
    details = {int(f.stem): json.loads(f.read_text(encoding='utf-8')) for f in sorted((DATA/'tennis_matches').glob('*.json'))}
    pack = base64.b64encode(gzip.compress(json.dumps({'core': core, 'details': details}, ensure_ascii=False, separators=(',', ':')).encode('utf-8'), compresslevel=9, mtime=0))
    static = reading.reading_tennis(core).encode('utf-8'); footer = reading.footer_tennis(core).encode('utf-8')
    css = (d/'style.css').read_bytes(); app = b'\n'.join((d/f'app{i}.js').read_bytes() for i in range(1,5)); shell = (d/'shell.html').read_text(encoding='utf-8')
    pako = '<script>\n' + (d/'pako.min.js').read_text(encoding='utf-8') + '\n</script>'
    assert '</script>' not in pako[8:-9]
    return dict(key='tennis', shell=shell, css=css, app=app, data=data, pack=pack, pako=pako, details=details, static=static, footer=footer, marker=b'type="application/octet-stream">', title='Tennis · An Ode to the Tour · 1877–2026', global_='PACK', script_block='__PAKO__\n<script id="archive-data" type="application/octet-stream">__DATA__</script>\n<script>\n__APP__\n</script>', detail_dir='tennis_matches')

def parts_tt():
    d = SRC/'tt'; data = (DATA/'tt.json').read_bytes(); core = json.loads(data.decode('utf-8'))
    static = reading.reading_tt(core).encode('utf-8'); footer = reading.footer_tt(core).encode('utf-8')
    css = (d/'style.css').read_bytes(); app = b'\n'.join((d/f'app{i}.js').read_bytes() for i in range(1,4)); shell = (d/'shell.html').read_text(encoding='utf-8')
    assert b'</script>' not in data
    return dict(key='tt', shell=shell, css=css, app=app, data=data, static=static, footer=footer, marker=b'type="application/json">', title='Isle of Man TT · An Ode to the Mountain · 1907–2026', global_='ARCHIVE', script_block='<script id="archive-data" type="application/json">__DATA__</script>\n<script>\n__APP__\n</script>')

def parts_ufc():
    d = SRC/'ufc'; data = (DATA/'ufc.json').read_bytes(); core = json.loads(data.decode('utf-8'))
    static = reading.reading_ufc(core).encode('utf-8'); footer = reading.footer_ufc(core).encode('utf-8')
    css = (d/'style.css').read_bytes(); app = b'\n'.join((d/f'app{i}.js').read_bytes() for i in range(1,4)); shell = (d/'shell.html').read_text(encoding='utf-8')
    assert b'</script>' not in data
    return dict(key='ufc', shell=shell, css=css, app=app, data=data, static=static, footer=footer, marker=b'type="application/json">', title='UFC · An Ode to the Cage · 1993–2026', global_='ARCHIVE', script_block='<script id="archive-data" type="application/json">__DATA__</script>\n<script>\n__APP__\n</script>')

def standalone(p):
    shell = p['shell'].replace('__FOOTER__', '__FOOTER__\n' + NOTICE_HTML.replace('<div class="wrap">', '').replace('</p></div>', '</p>'), 1).encode('utf-8')
    for ph in (b'__DATA__', b'__STATIC__', b'__FOOTER__', b'__CSS__', b'__APP__'): assert shell.count(ph) == 1, (p['key'], ph)
    blob = p.get('pack', p['data'])
    out = shell.replace(b'__CSS__', p['css'], 1).replace(b'__APP__', p['app'], 1).replace(b'__STATIC__', p['static'], 1).replace(b'__FOOTER__', p['footer'], 1).replace(b'__PAKO__', p.get('pako', '').encode('utf-8'), 1).replace(b'__DATA__', blob, 1)
    check_embedded(out, blob, p['marker'], p['static'], p['footer'])
    return out

LIGHT_KEYS = "['apex-lights','apex-kickoff','apex-toss','apex-serve','apex-tt','apex-ufc']"
def production(p, vcss, vjs, vdata):
    """The same shell, but the stylesheet, the application and the archive come from files — small HTML, cached assets."""
    key = p['key']; s = p['shell']
    assert s.count('<style>\n__CSS__\n</style>') == 1 and s.count(p['script_block']) == 1 and s.count('__STATIC__') == 1 and s.count('__FOOTER__') == 1
    s = s.replace('<style>\n__CSS__\n</style>', f'<link rel="stylesheet" href="../assets/{key}.css?v={vcss}">\n<style>{HOME_CSS}</style>\n<link rel="canonical" href="{SITE}/{key}/">\n<meta property="og:url" content="{SITE}/{key}/">')
    # the way back: the brand is a link to the landing page, the strap line names it, the footer repeats it
    assert s.count('<div class="brand">APEX <i>/</i> <small>') == 1, key
    s = s.replace('<div class="brand">APEX <i>/</i> <small>', '<div class="brand"><a class="home" href="../" title="sportsfans.co.za · all atlases">APEX <i>/</i></a> <small>')
    s = s.replace('</small></div>\n  <div class="ctl">', ' · <a href="../">all atlases</a></small></div>\n  <div class="ctl">', 1)
    # the sport switcher: every published atlas, one row under the masthead
    assert s.count('\n<main id="main">') == 1, key
    switch = '<nav class="switch" aria-label="Other atlases"><a href="../">All atlases</a>' + ''.join(f'<a href="../{k}/"{" class=on" if k == key else ""}>{sitegen.SPORTS[k][0]}</a>' for k in sitegen.SPORTS if k in PUBLISH) + '<a class="go" href="#stage" onclick="document.getElementById(\'stage\').scrollIntoView({behavior:\'smooth\',block:\'start\'});return false">Explore the data ↓</a></nav>'
    s = s.replace('\n<main id="main">', '\n' + switch + '\n<main id="main">', 1)
    loader = f'''<script>
(async()=>{{const L=document.getElementById('lights');try{{if({LIGHT_KEYS}.some(k=>sessionStorage.getItem(k)==='1')&&L)L.style.display='none';}}catch(e){{}}
const fail=m=>{{if(L)L.remove();const v=document.getElementById('view');if(v)v.innerHTML='<p class="muted" style="margin-top:22px">The archive could not be loaded ('+m+'). <a href="reading/">Open the reading edition</a> or <a href="../downloads/">download the self-contained atlas</a>.</p>';}};
try{{const r=await fetch('../data/{key}.json?v={vdata}');if(!r.ok)throw new Error('HTTP '+r.status);{"window.PACK={core:await r.json(),details:{},detailUrl:'../data/" + p['detail_dir'] + "/'};" if p['global_'] == 'PACK' else "window." + p['global_'] + "=await r.json();"}}}catch(e){{fail(e.message);return;}}
const s=document.createElement('script');s.src='../assets/{key}.js?v={vjs}';s.onerror=()=>fail('script');document.body.appendChild(s);}})();
</script>'''
    s = s.replace(p['script_block'], loader)
    s = s.replace('__STATIC__', f'''<div class="panel" style="margin-top:16px"><p style="margin:0">The reading edition is its own page — every table of the archive as plain HTML, with no scripts needed: <a href="reading/">open the reading edition →</a></p><p class="small muted" style="margin:8px 0 0">Also: <a href="../downloads/">the self-contained offline atlas</a> (one HTML file with everything inside), and the static pages for every <a href="seasons/">season</a>{', <a href="drivers/">driver</a>, <a href="constructors/">constructor</a> and <a href="circuits/">circuit</a>' if key == 'f1' else (', <a href="nations/">nation</a>, <a href="players/">player</a>, <a href="grounds/">ground</a> and <a href="coaches/">coach</a>' if key == 'rugby' else (', <a href="teams/">team</a>, <a href="players/">player</a> and <a href="grounds/">ground</a>' if key == 'cricket' else (', <a href="players/">player</a>, <a href="tournaments/">tournament</a> and <a href="nations/">nation</a>' if key == 'tennis' else (', <a href="riders/">rider</a> and <a href="marques/">marque</a>' if key == 'tt' else (', <a href="events/">event</a>, <a href="fighters/">fighter</a>, <a href="divisions/">division</a> and <a href="venues/">venue</a>' if key == 'ufc' else ', <a href="riders/">rider</a>, <a href="makers/">maker</a> and <a href="circuits/">circuit</a>')))))}.</p></div>''')
    s = s.replace('__FOOTER__', p['footer'].decode('utf-8').replace('Self-contained offline HTML', 'sportsfans.co.za edition').replace('fixed offline snapshot', 'dated snapshot') + '\n' + NOTICE_HTML.replace('<div class="wrap">', '').replace('</p></div>', '</p>').replace('https://sportsfans.co.za/licences/', '../licences/').replace('max-width:900px">', 'max-width:900px"><a href="../">sportsfans.co.za · all atlases</a> · <a href="../downloads/">offline editions</a> · <a href="reading/">reading edition</a>. ', 1))
    return s.encode('utf-8')

def reading_page(p, vsite):
    """The carried reading edition, verbatim, on its own page in the site chrome."""
    key = p['key']; name = sitegen.SPORTS[key][1]
    body = f'<p class="eyebrow">{name} · Reading edition</p><h1>The <span>reading</span> edition</h1><p class="lede">The whole archive as plain HTML, exactly as carried in the self-contained atlas — every table it holds, no scripts. <a class="q" href="../">Back to the atlas</a>.</p>\n__CARRIED__'
    html = sitegen.page(site=SITE, sport=key, depth=2, title=f'{name} · reading edition · APEX', desc=f'The complete {name} archive of the atlas as plain reading matter — every season and every table, no scripts needed.', crumbs=[('Sportsfans', '../../'), (name, '../'), ('Reading edition', None)], body=body, path=f'{key}/reading/', v=vsite, extra_head=f'\n<link rel="stylesheet" href="../../assets/{key}.css?v={vsite}">', published=PUBLISH)
    # the carried HTML is inserted as bytes so it stays byte-identical
    a, b = html.encode('utf-8').split(b'__CARRIED__')
    return a + p['static'] + b'\n' + p['footer'] + b

import colorsys
def _smooth(pts):
    if len(pts) < 3: return ''.join(('L' if i else '') + f'{x:.0f} {y:.0f}' for i, (x, y) in enumerate(pts))
    d = ''
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6); c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{c1[0]:.0f} {c1[1]:.0f} {c2[0]:.0f} {c2[1]:.0f} {p2[0]:.0f} {p2[1]:.0f}'
    return d
def _hue(name):
    h = 0
    for ch in name: h = (h * 31 + ord(ch)) & 0xffffffff
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, .58, .38); return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
def river_svg(years, shares, colours, weights=None, W=640, H=150, top=8, bottom=8):
    """A miniature of the page's River: stacked, smoothed bands of each side's share per year, thickness by activity."""
    totals = [sum(sh.values()) for sh in shares]; n = len(years); weights = weights or totals; maxT = max(weights) or 1
    order = {}
    for sh in shares:
        for t, v in sh.items(): order[t] = order.get(t, 0) + v
    teams = sorted(order, key=lambda t: -order[t])
    if len(teams) > 14:  # the landing card is a glimpse: the fourteen biggest bands, everything else as one grey band
        rest = teams[14:]; teams = teams[:14] + ['·other']
        shares = [dict(sh, **{'·other': sum(sh.get(t, 0) for t in rest)}) for sh in shares]; colours = dict(colours, **{'·other': '#3a3f48'})
    x = lambda i: 6 + i * (W - 12) / max(1, n - 1); thick = lambda i: (H - top - bottom) * (0.25 + 0.75 * weights[i] / maxT); y0 = lambda i: top + ((H - top - bottom) - thick(i)) / 2
    cum = [0.0] * n; out = []
    for t in teams:
        up, down = [], []
        for i in range(n):
            sh = (shares[i].get(t, 0) / totals[i]) if totals[i] else 0; a = y0(i) + cum[i] * thick(i); b = a + sh * thick(i); cum[i] += sh
            up.append((x(i), a)); down.append((x(i), b))
        dn = down[::-1]
        d = f'M{up[0][0]:.0f} {up[0][1]:.0f}' + _smooth(up) + f'L{dn[0][0]:.0f} {dn[0][1]:.0f}' + _smooth(dn) + 'Z'
        out.append(f'<path d="{d}" fill="{colours.get(t) or _hue(t)}" stroke="#07080a" stroke-width=".4"/>')
    return f'<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" aria-hidden="true">' + ''.join(out) + '</svg>'
def preview(key):
    if key == 'f1':
        D = json.loads((DATA/'f1.json').read_text(encoding='utf-8')); years, shares, weights = [], [], []
        col = {k: (v.get('color') if v.get('color', '').lower() != '#b5a5ed' else None) for k, v in D['teams'].items()}
        for s in D['seasons']:
            sh = {}
            for r in s['races']:
                for x in r['rows'] + r.get('sprint', []): sh[x['t']] = sh.get(x['t'], 0) + x['pts']
            if sh: years.append(s['year']); shares.append(sh); weights.append(sum(1 for r in s['races'] if r['rows']))
        return river_svg(years, shares, col, weights)
    if key == 'cricket':
        A = json.loads((DATA/'cricket.json').read_text(encoding='utf-8')); col = {k: v['c'] for k, v in A['teams'].items()}; by = {}
        for m in A['games']:
            if m['g'] != 'M' or m['result'] == 'no result': continue
            sh = by.setdefault(m['y'], {})
            if m['result'] in ('draw', 'tie'): sh[m['teams'][0]] = sh.get(m['teams'][0], 0) + .5; sh[m['teams'][1]] = sh.get(m['teams'][1], 0) + .5
            elif m['winner']: sh[m['winner']] = sh.get(m['winner'], 0) + 1
        years = sorted(by); return river_svg(years, [by[y] for y in years], col, [len([m for m in A['games'] if m['y'] == y and m['g'] == 'M']) for y in years])
    if key == 'tennis':
        A = json.loads((DATA/'tennis.json').read_text(encoding='utf-8')); by = {}; NAT = {'USA':'#d62839','AUS':'#ffcc00','GBR':'#2c4ec7','FRA':'#7aa6ff','ESP':'#ff8c1a','GER':'#c9ccd1','FRG':'#c9ccd1','SWE':'#3ec6b8','ARG':'#9dd2f2','CZE':'#7b3fa0','TCH':'#7b3fa0','SUI':'#ff2e63','ITA':'#3aaa5c','RUS':'#c81e6e','URS':'#c81e6e','SRB':'#e8967a','BEL':'#b58900','NED':'#ff9e80','CRO':'#a8dadc','ROU':'#c5a3ff','POL':'#ff7b7b','JPN':'#f4f4f2','CAN':'#ff8a80','BRA':'#a4ff4f','CHN':'#ff5a36','RSA':'#0f9d58','NZL':'#9e9e9e'}
        for r in A['champions']:
            c = dict(zip(A['cFields'], r))
            if c['c'] not in ('MS', 'WS'): continue
            for w in c['w']:
                ioc = A['players'].get(w, {}).get('ioc') or '—'; sh = by.setdefault(c['y'], {}); sh[ioc] = sh.get(ioc, 0) + 1
        years = sorted(by); return river_svg(years, [by[y] for y in years], NAT)
    if key == 'tt':
        A = json.loads((DATA/'tt.json').read_text(encoding='utf-8')); by = {}; COL = {'Honda':'#f34d54','Yamaha':'#507dff','Suzuki':'#ffd23f','Kawasaki':'#79d455','BMW':'#66b5ff','Triumph':'#4dd0b0','Norton':'#c9ccd1','Ducati':'#ff3642','MV Agusta':'#e8c473','Moto Guzzi':'#a3bacc','BSA':'#c9a86a','Velocette':'#7fa08c','Paton':'#ff9ecb','AJS':'#b9cfdd','Rudge':'#d5c39f','Sunbeam':'#ffe08a','Matchless':'#c1ac91','Gilera':'#e97a75','Indian':'#c0392b'}
        for r in A['races']:
            w = next((x for x in r['results'] if x[1] == 1), None)
            if w: sh = by.setdefault(r['y'], {}); m = w[4] or 'Unrecorded'; sh[m] = sh.get(m, 0) + 1
        years = sorted(by); return river_svg(years, [by[y] for y in years], COL)
    if key == 'ufc':
        A = json.loads((DATA/'ufc.json').read_text(encoding='utf-8')); by = {}; BF = A['boutFields']; iy = BF.index('y'); idv = BF.index('div')
        COL = {'hw':'#ff3642','lhw':'#ff8a3d','mw':'#ffd23f','ww':'#79d455','lw':'#2fd0c2','fw':'#4da3ff','bw':'#8f7bff','flw':'#ff7ad9','wsw':'#ffb3c7','wflw':'#c9a0ff','wbw':'#9fe0ff','wfw':'#ffe08a','wat':'#f4c2ff','open':'#c9ccd1','shw':'#a3bacc','catch':'#8b9099'}
        for b in A['bouts']: sh = by.setdefault(b[iy], {}); sh[b[idv]] = sh.get(b[idv], 0) + 1
        years = sorted(by); return river_svg(years, [by[y] for y in years], COL)
    if key == 'rugby':
        A = json.loads((DATA/'rugby.json').read_text(encoding='utf-8')); col = {t['name']: t['accent'] for t in A['teams']}
        col.update({'British & Irish Lions': '#e75863', 'Japan': '#f48f9a', 'Fiji': '#ecebe6', 'Samoa': '#618fff', 'Tonga': '#d65b5e', 'Romania': '#ecce59', 'Canada': '#ef8d81', 'USA': '#b482a2', 'Uruguay': '#8bcddd', 'Georgia': '#a86572'})
        by = {}
        for m in A['matches']:
            sh = by.setdefault(m['year'], {})
            if m['hs'] == m['as_']: sh[m['home']] = sh.get(m['home'], 0) + .5; sh[m['away']] = sh.get(m['away'], 0) + .5
            else: w = m['home'] if m['hs'] > m['as_'] else m['away']; sh[w] = sh.get(w, 0) + 1
        years = sorted(by); return river_svg(years, [by[y] for y in years], col)
    A = json.loads((DATA/f'{key}.json').read_text(encoding='utf-8')); cfg = (SRC/f'bikes/config_{key}.js').read_text(encoding='utf-8')
    col = dict(re.findall(r"'([^']+)':'(#[0-9a-fA-F]{6})'", re.search(r'colours:\{[^}]*\}', cfg).group(0)))
    years, shares, weights = [], [], []; races = {}
    for r in A['races']: races[r['year']] = races.get(r['year'], 0) + 1
    for y in sorted(A['standings'], key=int):
        sh = {}
        for row in A['standings'][y]['rows']:
            if row.get('maker') and row.get('points'): sh[row['maker']] = sh.get(row['maker'], 0) + row['points']
        if sh: years.append(int(y)); shares.append(sh); weights.append(races.get(int(y), 1))
    return river_svg(years, shares, col, weights)


PARTS = {'f1': parts_f1, 'rugby': parts_rugby, 'cricket': parts_cricket, 'tennis': parts_tennis, 'tt': parts_tt, 'motogp': lambda: parts_bike('motogp'), 'sbk': lambda: parts_bike('sbk'), 'ufc': parts_ufc}
STANDALONE = {'f1': 'apex_f1_ode_1950_2026.html', 'rugby': 'apex_rugby_ode_1871_2026.html', 'cricket': 'apex_cricket_ode_1877_2026.html', 'tennis': 'apex_tennis_ode_1877_2026.html', 'tt': 'apex_isle_of_man_tt_ode_1907_2026.html', 'motogp': 'apex_motogp_ode_1949_2026.html', 'sbk': 'apex_worldsbk_ode_1988_2026.html', 'ufc': 'apex_ufc_ode_1993_2026.html'}
COLOURS = {}
def maker_colours(tag):
    cfg = (SRC/f'bikes/config_{tag}.js').read_text(encoding='utf-8')
    return dict(re.findall(r"'([^']+)':'(#[0-9a-fA-F]{6})'", re.search(r'colours:\{[^}]*\}', cfg).group(0)))

def write(path: pathlib.Path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode('utf-8'))

if __name__ == '__main__':
    # a clean docs/ so nothing stale survives a rename
    for sub in ('assets', 'data', 'downloads', 'licences', *PARTS):
        shutil.rmtree(DOCS/sub, ignore_errors=True)
    DOCS.mkdir(exist_ok=True); DROP.mkdir(exist_ok=True)
    sitegen.PUBLISHED = PUBLISH
    site_css = sitegen.SITE_CSS.encode('utf-8'); vsite = h(site_css); write(DOCS/'assets/site.css', site_css)
    urls = [f'{SITE}/']; today = datetime.date.today().isoformat(); pages_n = 0
    shutil.rmtree(HELD_DIR, ignore_errors=True)
    for key, fn in PARTS.items():
        if not (DATA/f'{key}.json').exists(): print(f'{key:7s} no data file yet · skipped'); continue
        p = fn(); single = standalone(p)
        write(DROP/STANDALONE[key], single)
        if key not in PUBLISH:
            write(HELD_DIR/key/STANDALONE[key], single); print(f'{key:7s} HELD ({HELD.get(key, "not published")}) · offline edition in build/held/'); continue
        write(DOCS/'downloads'/STANDALONE[key], single)
        vcss, vjs, vdata = h(p['css']), h(p['app']), h(p['data'])
        write(DOCS/f'assets/{key}.css', p['css']); write(DOCS/f'assets/{key}.js', p['app']); write(DOCS/f'data/{key}.json', p['data'])
        for y, shard in (p.get('details') or {}).items(): write(DOCS/'data'/p['detail_dir']/f'{y}.json', json.dumps(shard, ensure_ascii=False, separators=(',', ':')))
        write(DOCS/key/'index.html', production(p, vcss, vjs, vdata)); write(DOCS/key/'reading/index.html', reading_page(p, vsite))
        urls += [f'{SITE}/{key}/', f'{SITE}/{key}/reading/']
        n = 0
        if not args.no_pages:
            if key == 'f1': pages = sitegen.gen_f1(json.loads(p['data'].decode('utf-8')), site=SITE, v=vsite)
            elif key == 'rugby': pages = sitegen.gen_rugby(json.loads(p['data'].decode('utf-8')), site=SITE, v=vsite)
            elif key == 'cricket': pages = sitegen.gen_cricket(json.loads(p['data'].decode('utf-8')), site=SITE, v=vsite)
            elif key == 'tennis': pages = sitegen.gen_tennis(json.loads(p['data'].decode('utf-8')), site=SITE, v=vsite)
            elif key == 'tt': pages = sitegen.gen_tt(json.loads(p['data'].decode('utf-8')), site=SITE, v=vsite)
            elif key == 'ufc': pages = sitegen.gen_ufc(json.loads(p['data'].decode('utf-8')), site=SITE, v=vsite)
            else: pages = sitegen.gen_bikes(key, json.loads(p['data'].decode('utf-8')), maker_colours(key), site=SITE, v=vsite)
            for path, html in pages: write(DOCS/path, html); urls.append(f'{SITE}/{path[:-len("index.html")]}'); n += 1
        pages_n += n
        print(f'{key:7s} standalone {len(single):>11,} B · shell {(DOCS/key/"index.html").stat().st_size:>7,} B · data {len(p["data"]):>10,} B · {n:,} static pages  {p["title"]}')
    # hub, downloads index, plumbing
    hub = (SRC/'hub/index.html').read_text(encoding='utf-8').replace('__SITE__', SITE)
    for key in PARTS:
        hub = hub.replace(f'__PREVIEW_{key.upper()}__', preview(key) if key in PUBLISH else '')
        if key not in PUBLISH and key not in HELD: hub = re.sub(f'<!--{key.upper()}-->.*?<!--/{key.upper()}-->', '', hub, flags=re.S)  # a sport that is not on the site yet leaves no card
    if 'ufc' in PUBLISH:
        U = json.loads((DATA/'ufc.json').read_text(encoding='utf-8')); hub = hub.replace('__UFC_EVENTS__', f'{len(U["events"]):,}').replace('__UFC_BOUTS__', f'{len(U["bouts"]):,}').replace('__UFC_FIGHTERS__', f'{len(U["fighters"]):,}')
    for key, why in HELD.items():  # a held card is not a link and says why
        hub = re.sub(r'<a class="sport" href="' + key + r'/"(.*?)<span class="go">Enter →</span></a>', lambda m: '<div class="sport held"' + m.group(1).replace('<span class="tag">', '<span class="tag">held · ') + f'<span class="go">{why} →</span></div>', hub, flags=re.S)
        hub = hub.replace(f'<a href="{key}/" style="color:var(--muted);text-decoration:none;padding:6px 8px">', f'<span style="color:var(--dim);padding:6px 8px" title="{why}">').replace(f'</a><a href="', '</a><a href="')
    hub = hub.replace('<footer><span>sportsfans.co.za · APEX sports atlases · independent, fan-made, self-contained pages · each carries its own sources and coverage notes</span><span>Data credits inside each atlas</span></footer>', '<footer><span>sportsfans.co.za · APEX sports atlases · independent, fan-made, self-contained pages · each carries its own sources and coverage notes</span><span><a href="licences/" style="color:var(--muted)">Sources and licences</a> · <a href="downloads/" style="color:var(--muted)">Offline editions</a> · <a href="mailto:sportsfans.co.za@gmail.com" style="color:var(--muted)">Contribute</a></span><span style="flex-basis:100%;font:12.5px/1.5 var(--body);letter-spacing:0;color:var(--dim);max-width:900px">' + sitegen.NOTICE + '</span></footer>')
    write(DOCS/'index.html', hub)
    write(DOCS/'licences/index.html', sitegen.gen_licences(site=SITE, v=vsite, published=PUBLISH, held=HELD)); urls.append(f'{SITE}/licences/')
    (DOCS/'data').mkdir(exist_ok=True); (DOCS/'data/LICENCE.txt').write_text('Data files served by sportsfans.co.za\n\nf1.json        CC BY-NC-SA 4.0 — results and standings from Jolpica F1 (CC BY-NC-SA 4.0); circuit outlines, specifications and supplementary laps from F1DB (CC BY 4.0). Attribute both; non-commercial; share alike.\nrugby.json     No licence granted for reuse. Scores are facts; the compilations are credited to Nuck\u2019s Rugby Archive and Springbok Rugby History.\ncricket.json, cricket_details/   Scorecards and player figures from Cricsheet (ODC-By 1.0: attribute Cricsheet); historical results are facts, compiled from the Kaggle Test-nations dataset; ICC titles as published.\ntennis.json, tennis_matches/     CC BY-NC-SA 4.0 — Jeff Sackmann / Tennis Abstract. Attribute; non-commercial; share alike.\nmotogp.json, sbk.json, tt.json   CC BY-SA 4.0 — results transcribed from Wikipedia (Wikipedia contributors); attribute, share alike. Circuit and course geometry © OpenStreetMap contributors, ODbL 1.0.\nufc.json       CC BY-SA 4.0 — events, bouts and results transcribed from Wikipedia’s event articles (Wikipedia contributors); fighter facts from Wikidata (CC0). Attribute, share alike.\n\nFull statement: https://sportsfans.co.za/licences/\n', encoding='utf-8')
    dl = ''.join(f'<a class="chip" href="{STANDALONE[k]}" download><i style="--c:{c}"></i>{n} · {(DOCS/"downloads"/STANDALONE[k]).stat().st_size/1e6:.1f} MB</a>' for k, n, c in [('f1', 'Formula 1 · 1950–2026', '#FF8000'), ('rugby', 'Rugby union · 1871–2026', '#5cd4a1'), ('cricket', 'Cricket · 1877–2026', '#2fbf8f'), ('tennis', 'Tennis · 1877–2026', '#c8e06a'), ('tt', 'Isle of Man TT · 1907–2026', '#c9ccd1'), ('motogp', 'MotoGP · 1949–2026', '#ff3642'), ('sbk', 'WorldSBK · 1988–2026', '#7ae02a'), ('ufc', 'UFC bouts · 1993–2026', '#ff5a5f')] if k in PUBLISH)
    write(DOCS/'downloads/index.html', sitegen.page(site=SITE, sport=None, depth=1, title='Offline editions · APEX sports atlases', desc='Each atlas as one self-contained HTML file: the whole archive inside, works from disk, no server needed.', crumbs=[('Sportsfans', '../'), ('Offline editions', None)], body=f'<p class="eyebrow">Offline editions</p><h1>One file, <span>everything inside</span></h1><p class="lede">Each atlas is also published as a single HTML file with its archive embedded: save it, open it from disk, send it on. It is the same page as the live one, only self-contained. The data inside carries the same licences as the site’s data files — see <a class="q" href="../licences/">sources and licences</a>.</p><div class="chips" style="margin-top:22px">{dl}</div>', path='downloads/', v=vsite, published=PUBLISH))
    urls.append(f'{SITE}/downloads/')
    (DOCS/'.nojekyll').write_text('')
    (DOCS/'robots.txt').write_text(f'User-agent: *\nAllow: /\nDisallow: /data/\nSitemap: {SITE}/sitemap.xml\n')
    # sitemap index → one sitemap per atlas (Search Console then reports coverage per sport; each file stays far below the 50,000-url limit)
    pri = lambda u: '1.0' if u == f'{SITE}/' else '0.9' if u.count('/') == 4 else '0.6'
    groups = {}
    for u in urls:
        seg = u[len(SITE) + 1:].split('/')[0]; groups.setdefault(seg if seg in PUBLISH else 'site', []).append(u)
    for g in [f.name for f in DOCS.glob('sitemap-*.xml')]: (DOCS/g).unlink()
    for g, us in groups.items():
        (DOCS/f'sitemap-{g}.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{u}</loc><priority>{pri(u)}</priority></url>\n' for u in us) + '</urlset>\n')
    (DOCS/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<sitemap><loc>{SITE}/sitemap-{g}.xml</loc></sitemap>\n' for g in ['site'] + [k for k in PUBLISH if k in groups]) + '</sitemapindex>\n')
    (DOCS/'404.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>APEX / Not found</title><style>body{margin:0;background:#07080a;color:#f4f4f2;font:16px/1.5 Barlow,Arial,sans-serif;display:grid;place-items:center;min-height:100vh;text-align:center}h1{font:900 italic 72px/1 "Barlow Condensed","Arial Narrow",sans-serif;text-transform:uppercase;letter-spacing:-.03em;margin:0 0 12px}a{color:#FF8000}</style></head><body><div><h1>Off the racing line</h1><p>That page is not in the atlas. <a href="/">Back to the atlases</a></p></div></body></html>')
    if not args.no_cname and '.github.io' not in SITE: (DOCS/'CNAME').write_text(SITE.replace('https://', '').replace('http://', '').split('/')[0] + '\n')
    elif (DOCS/'CNAME').exists(): (DOCS/'CNAME').unlink()
    print(f'hub, reading editions, {pages_n:,} static pages, {len(urls):,} sitemap urls, robots, 404 → {DOCS}')
