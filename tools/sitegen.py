"""Static entity pages for the production site.

Every season, driver/rider/player, constructor/maker/nation, circuit/ground and coach gets a plain HTML page
of its own — crawlable, linkable, permanent — rendered from the same archive the atlas embeds. Each page
opens the interactive atlas at the matching view through a deep link (#tab=…&…).
"""
import html, json, re, collections, datetime, urllib.parse
def longdate(iso):
    try: d = datetime.date.fromisoformat(iso); return f'{d.day} {d.strftime("%B %Y")}'
    except Exception: return iso or ''
E = lambda s: html.escape(str(s if s is not None else ''), quote=True)
def slug(s):
    s = re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-'); return s or 'x'
def fmt(n):
    if n is None: return '—'
    if isinstance(n, float) and n.is_integer(): n = int(n)
    return f'{n:,}' if isinstance(n, int) else (f'{n:.1f}' if isinstance(n, float) else str(n))
def pct(a, b): return round(a / b * 1000) / 10 if b else 0

SITE_CSS = r'''
:root{--bg:#07080a;--panel:#0f1113;--panel2:#151820;--line:#22262e;--line2:#2e333d;--ink:#f4f4f2;--muted:#8b9099;--dim:#5b616b;--accent:#FF8000;--gold:#e8c46a;--display:"Barlow Condensed","Arial Narrow","Helvetica Neue",Arial,sans-serif;--body:"Barlow","Helvetica Neue",Arial,sans-serif;--mono:"JetBrains Mono","SFMono-Regular",Consolas,monospace}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 var(--body);background-image:repeating-linear-gradient(45deg,rgba(255,255,255,.012) 0 2px,transparent 2px 6px),repeating-linear-gradient(-45deg,rgba(255,255,255,.012) 0 2px,transparent 2px 6px)}
a{color:var(--accent)} a.q{color:inherit;text-decoration:none;border-bottom:1px solid var(--line2)} a.q:hover{border-color:var(--accent)}
.wrap{max-width:1480px;margin:0 auto;padding:0 40px}@media (max-width:720px){.wrap{padding:0 16px}}
.mast{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:22px 0;border-bottom:1px solid var(--line);flex-wrap:wrap}
.brand{font-family:var(--display);font-weight:900;font-style:italic;font-size:30px;letter-spacing:-.04em;text-transform:uppercase;line-height:1;color:inherit;text-decoration:none}
.brand i{color:var(--accent);font-style:normal}.brand small{display:block;font:11px/1 var(--mono);letter-spacing:.28em;color:var(--muted);margin-top:8px;font-style:normal;font-weight:400}
nav.top{display:flex;gap:6px;flex-wrap:wrap;font:11px var(--mono);letter-spacing:.16em;text-transform:uppercase}nav.top a{color:var(--muted);text-decoration:none;padding:6px 8px}nav.top a.on,nav.top a:hover{color:var(--accent)}
.crumbs{font:11px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:26px 0 0}.crumbs a{color:var(--muted);text-decoration:none}.crumbs a:hover{color:var(--accent)}
.eyebrow{font-family:var(--mono);font-size:10.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--accent);margin:22px 0 0}
h1{font-family:var(--display);font-weight:900;font-style:italic;font-size:clamp(44px,6.5vw,96px);line-height:.88;letter-spacing:-.035em;text-transform:uppercase;margin:10px 0 0}
h1 span{color:var(--accent)}
.lede{color:var(--muted);font-size:16px;max-width:760px;margin:16px 0 0}.lede b{color:var(--ink);font-weight:600}
.open{display:inline-block;margin-top:18px;background:var(--accent);color:#07080a;text-decoration:none;font:700 12px var(--mono);letter-spacing:.16em;text-transform:uppercase;padding:11px 16px;border-radius:6px}
.open:hover{filter:brightness(1.08)}
.also{display:inline-block;margin:18px 0 0 10px;font:700 12px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--muted);text-decoration:none;border:1px solid var(--line2);padding:10px 14px;border-radius:6px}.also:hover{color:var(--ink);border-color:var(--accent)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-top:26px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}.kpi span{display:block;font:10px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}.kpi b{display:block;font:800 30px/1 var(--display);font-style:italic;letter-spacing:-.02em;margin-top:6px}.kpi small{display:block;color:var(--dim);font-size:11px;margin-top:4px}
h2{font-family:var(--display);font-weight:800;font-style:italic;font-size:26px;text-transform:uppercase;letter-spacing:-.01em;margin:36px 0 10px;display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
h2 small{font:11px var(--mono);letter-spacing:.14em;color:var(--muted);text-transform:uppercase;font-style:normal;font-weight:400}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.tablewrap{overflow:auto;max-height:70vh;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--panel)}th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap;vertical-align:top}th{position:sticky;top:0;background:var(--panel2);font:10.5px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted);z-index:1}tr:hover td{background:var(--panel2)}td.n{text-align:right;font-family:var(--mono);font-size:12.5px}
.dot{display:inline-block;width:10px;height:10px;border-radius:2px;background:var(--c,#555);vertical-align:-1px;margin-right:7px}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}.chips.letters{margin:14px 0 22px}.chip.on{border-color:var(--accent);color:var(--accent)}.chip{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line2);border-radius:999px;padding:5px 11px;font-size:12.5px;color:inherit;text-decoration:none;background:var(--panel)}.chip:hover{border-color:var(--accent)}.chip i{width:9px;height:9px;border-radius:50%;background:var(--c,#555)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media (max-width:900px){.two{grid-template-columns:1fr}}
.W{color:#3bd36b}.L{color:#c8323e}.D{color:#8b9099}
.index{columns:3;column-gap:24px;margin-top:14px}@media (max-width:900px){.index{columns:2}}@media (max-width:560px){.index{columns:1}}.index a{display:block;color:inherit;text-decoration:none;padding:4px 0;border-bottom:1px solid var(--line);break-inside:avoid;font-size:13.5px}.index a small{color:var(--muted);font-family:var(--mono);font-size:11px;margin-left:6px}.index a:hover{color:var(--accent)}
footer{padding:30px 0 60px;color:var(--muted);font:11px var(--mono);letter-spacing:.06em;border-top:1px solid var(--line);margin-top:50px;display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap}footer a{color:var(--muted)}footer .notice{flex-basis:100%;font:12.5px/1.5 var(--body);letter-spacing:0;color:var(--dim);max-width:900px}
.lic h3{font-family:var(--display);font-weight:800;font-style:italic;font-size:22px;text-transform:uppercase;margin:28px 0 8px}.lic p{color:var(--muted);max-width:900px;margin:6px 0}.lic p b{color:var(--ink);font-weight:600}.lic .tag{display:inline-block;font:700 10px var(--mono);letter-spacing:.14em;text-transform:uppercase;border:1px solid var(--line2);border-radius:4px;padding:2px 7px;margin-left:8px;color:var(--accent)}
'''

SPORTS = {'cricket': ('Cricket', 'Cricket'), 'dakar': ('Dakar', 'Dakar Rally'), 'f1': ('F1', 'Formula 1'), 'motogp': ('MotoGP', 'MotoGP'), 'rugby': ('Rugby', 'Rugby union'), 'tennis': ('Tennis', 'Tennis'), 'tt': ('TT', 'Isle of Man TT'), 'ufc': ('UFC', 'UFC bouts'), 'sbk': ('WorldSBK', 'World Superbike')}  # alphabetical by the label shown in the navigation

CONTACT = 'sportsfans.co.za@gmail.com'
NOTICE = 'Independent and non-commercial: no advertising, no sponsorship, no paywall. The names of championships, teams, events and venues are the trademarks of their owners and appear here only to identify them; nothing on this site is affiliated with or endorsed by any of them. A correction, a missing result, a source, a sport you would like to see: <a href="mailto:' + CONTACT + '?subject=sportsfans.co.za">contribute</a>.'
PUBLISHED = None
def icon_links(rel):
    """The site mark for the tab and the home screen: the SVG, the .ico fallback, the touch icon — all at the site root."""
    return f'<link rel="icon" href="{rel}favicon.svg" type="image/svg+xml"><link rel="icon" href="{rel}favicon.ico" sizes="32x32"><link rel="apple-touch-icon" href="{rel}apple-touch-icon.png">'

SITE_NAME = 'APEX / Sportsfans'
ENTITY_TYPES = {'Drivers': 'Person', 'Riders': 'Person', 'Players': 'Person', 'Fighters': 'Person', 'Drivers & riders': 'Person', 'Coaches': 'Person',
                'Circuits': 'Place', 'Grounds': 'Place', 'Venues': 'Place',
                'Nations': 'SportsTeam', 'Teams': 'SportsTeam', 'Constructors': 'SportsOrganization', 'Makers': 'Organization', 'Marques': 'Organization'}
def ld_json(*objs):
    """Structured data for search engines, one script per page; nothing here is shown to readers."""
    obj = objs[0] if len(objs) == 1 else {'@context': 'https://schema.org', '@graph': list(objs)}
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>'
def page_ld(site, path, crumbs, title, desc, entity=True):
    """BreadcrumbList from the crumbs, and a typed entity (Person, Place, team, organisation) when the parent crumb says what the page is about."""
    import urllib.parse
    here = f'{site}/{path}'
    items = [{'@type': 'ListItem', 'position': i + 1, 'name': t, 'item': urllib.parse.urljoin(here, h) if h else here} for i, (t, h) in enumerate(crumbs)]
    graph = [{'@type': 'BreadcrumbList', 'itemListElement': items}]
    if entity and len(crumbs) >= 3 and crumbs[-1][1] is None and ENTITY_TYPES.get(crumbs[-2][0]):
        graph.append({'@type': ENTITY_TYPES[crumbs[-2][0]], 'name': crumbs[-1][0], 'url': here, 'description': desc})
    return {'@context': 'https://schema.org', '@graph': graph}

def page(*, site, sport, depth, title, desc, crumbs, body, path, v, extra_head='', published=None, noindex=False, entity=True):
    """noindex: the page is built and linked but asks not to be indexed (long-tail careers below the threshold); build.py also leaves it out of the sitemap."""
    rel = '../' * depth
    share = f'{site}/share/{sport or "apex"}.png'
    published = published if published is not None else PUBLISHED
    shown = [k for k in SPORTS if published is None or k in published]
    nav = ''.join(f'<a href="{rel}{k}/"{" class=on" if k == sport else ""}>{E(SPORTS[k][0])}</a>' for k in shown) + f'<a href="{rel}licences/">Licences</a>'
    sport_name = SPORTS[sport][1] if sport else 'sports atlases'
    cr = ' · '.join(f'<a href="{E(h)}">{E(t)}</a>' if h else E(t) for t, h in crumbs)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{site}/{path}">{'<meta name="robots" content="noindex,follow">' if noindex else ''}
{icon_links(rel)}
<meta property="og:site_name" content="{SITE_NAME}"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{site}/{path}"><meta property="og:type" content="article"><meta property="og:image" content="{share}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@1,700;1,800;1,900&family=Barlow:wght@400;600&family=JetBrains+Mono:wght@400;700&display=swap">
<link rel="stylesheet" href="{rel}assets/site.css?v={v}">{extra_head}
{ld_json(page_ld(site, path, crumbs, title, desc, entity))}
</head>
<body>
<div class="wrap">
<header class="mast"><a class="brand" href="{rel}">APEX <i>/</i> <small>sportsfans.co.za · {E(sport_name)}</small></a><nav class="top">{nav}</nav></header>
<main>
<p class="crumbs">{cr}</p>
{body}
</main>
<footer><span>APEX / {E(sport_name)} · sportsfans.co.za · figures as recorded in the archive{f', sources inside <a href="{rel}{sport}/">the atlas</a>' if sport else ''} · <a href="{rel}licences/">sources and licences</a></span><span>{f'<a href="{rel}{sport}/reading/">Reading edition</a>' if sport else ''}</span><span class="notice">{NOTICE}</span></footer>
</div>
</body>
</html>'''

def table(cols, rows, num=()):
    th = ''.join(f'<th>{c}</th>' for c in cols)
    body = ''.join('<tr>' + ''.join(f'<td class="n">{c}</td>' if i in num else f'<td>{c}</td>' for i, c in enumerate(r)) + '</tr>' for r in rows)
    return f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'
def kpis(items): return '<div class="kpis">' + ''.join(f'<div class="kpi"><span>{E(t)}</span><b>{v}</b>{f"<small>{s}</small>" if s else ""}</div>' for t, v, s in items) + '</div>'
def index_list(items, rel):
    return '<div class="index">' + ''.join(f'<a href="{rel}{h}">{E(t)}{f"<small>{E(s)}</small>" if s else ""}</a>' for t, h, s in items) + '</div>'
def initial(name):
    """The letter a name files under: the surname's first letter, accents folded, anything else under '#'."""
    import unicodedata
    w = (name or '').split(' ')[-1]; c = unicodedata.normalize('NFKD', w[:1]).encode('ascii', 'ignore').decode('ascii').upper()
    return c if 'A' <= c <= 'Z' else '#'
def index_pages(*, site, sport, title, desc, crumbs, intro, items, dir, v, threshold=1500):
    """A directory index: one page when the list is short; past the threshold, a letter page per surname initial with a letter bar, so no page carries thousands of links."""
    rel = '../../'
    if len(items) <= threshold:
        return [(f'{dir}/index.html', page(site=site, sport=sport, depth=2, title=title, desc=desc, crumbs=crumbs, body=intro + index_list(items, rel), path=f'{dir}/', v=v))]
    groups = collections.OrderedDict()
    for it in items: groups.setdefault(initial(it[0]), []).append(it)
    letters = sorted(groups, key=lambda c: (c == '#', c)); slugof = lambda c: 'other' if c == '#' else c.lower()
    def bar(r, on=None): return '<div class="chips letters">' + ''.join(f'<a class="chip{" on" if c == on else ""}" href="{r}{dir}/{slugof(c)}/">{E(c)} <span style="color:var(--muted)">{len(groups[c]):,}</span></a>' for c in letters) + '</div>'
    out = [(f'{dir}/index.html', page(site=site, sport=sport, depth=2, title=title, desc=desc, crumbs=crumbs, body=intro + '<p class="lede">By surname:</p>' + bar(rel), path=f'{dir}/', v=v))]
    for c in letters:
        r3 = '../../../'; label = 'Other' if c == '#' else c
        out.append((f'{dir}/{slugof(c)}/index.html', page(site=site, sport=sport, depth=3, title=f'{label} · {title}', desc=f'{desc} Surnames beginning with {label}.', crumbs=[(t, h.replace(rel, r3, 1) if h else h) for t, h in crumbs[:-1]] + [(crumbs[-1][0], r3 + dir + '/'), (label, None)], body=intro.replace(rel, r3) + bar(r3, c) + index_list(groups[c], r3), path=f'{dir}/{slugof(c)}/', v=v, entity=False)))
    return out

# ============================================================ F1 ============================================================
def gen_f1(D, *, site, v):
    out = []  # (path, html)
    drivers, teams, circs = D['drivers'], D['teams'], D['circuits']
    seasons = D['seasons']
    col = lambda t: (teams.get(t, {}).get('color') or '#8b9099')
    dl = lambda d, rel: f'<a class="q" href="{rel}f1/drivers/{d}/">{E(drivers.get(d, {}).get("name", d))}</a>'
    tl = lambda t, rel: f'<i class="dot" style="--c:{col(t)}"></i><a class="q" href="{rel}f1/constructors/{t}/">{E(teams.get(t, {}).get("name", t))}</a>'
    cl = lambda c, rel, name=None: f'<a class="q" href="{rel}f1/circuits/{c}/">{E(name or circs.get(c, {}).get("name", c))}</a>'
    def standings(s):
        dr = s['drivers'] if any(str(x['p']).isdigit() for x in s['drivers']) else None
        derived = dr is None
        if derived:
            m = {}
            for r in s['races']:
                for x in r['rows'] + r.get('sprint', []):
                    a = m.setdefault(x['d'], {'id': x['d'], 'pts': 0, 'wins': 0, 'teams': []}); a['pts'] += x['pts']
                    if x['t'] not in a['teams']: a['teams'].append(x['t'])
                for x in r['rows']:
                    if x['dw'] and x['d'] in m: m[x['d']]['wins'] += 1
            dr = sorted(m.values(), key=lambda a: (-a['pts'], -a['wins']))
            for i, a in enumerate(dr): a['p'] = str(i + 1)
        return dr, derived
    by_driver = collections.defaultdict(list); by_team = collections.defaultdict(list); by_circ = collections.defaultdict(list)
    season_champ = {}
    for s in seasons:
        dr, derived = standings(s); season_champ[s['year']] = (dr[0]['id'] if dr else None, derived)
        for r in s['races']:
            if r['rows']: by_circ[r['cid']].append((s['year'], r))
            for x in r['rows']:
                by_driver[x['d']].append((s['year'], r, x)); by_team[x['t']].append((s['year'], r, x))
    # ---- seasons
    for s in seasons:
        y = s['year']; rel = '../../../'; dr, derived = standings(s); done = [r for r in s['races'] if r['rows']]
        champ = dr[0] if dr else None; ct = s['teams'][0] if s.get('teams') else None
        partial = str(y) == (D.get('cutoff') or '')[-4:]
        rows = []
        for r in s['races']:
            w = next((x for x in r['rows'] if x['dw']), None); p = next((x for x in r['rows'] if x.get('g') == 1), None); f = next((x for x in r['rows'] if x.get('fr') == 1), None)
            rows.append([r['round'], E(r['date']), f'<a class="q" href="{rel}f1/#season={y}&tab=race&race={r["round"]}">{E(r["name"])}</a>', cl(r['cid'], rel, r.get('circuit')), dl(w['d'], rel) if w else '<span class="D">not yet run</span>', tl(w['t'], rel) if w else '', dl(p['d'], rel) if p else '—', (E(f['fl']) + ' · ' + dl(f['d'], rel)) if f else '—'])
        st_rows = [[E(a['p']), dl(a['id'], rel), ' / '.join(tl(t, rel) for t in a.get('teams', [])), fmt(a['pts']), a['wins']] for a in dr]
        tm_rows = [[E(a['p']), tl(a['id'], rel), fmt(a['pts']), a['wins']] for a in s.get('teams', [])]
        prev = next((x['year'] for x in seasons if x['year'] == y - 1), None); nxt = next((x['year'] for x in seasons if x['year'] == y + 1), None)
        body = f'''<p class="eyebrow">Formula 1 · Season</p><h1>{y} <span>Formula 1</span></h1>
<p class="lede">{len(done)} of {len(s['races'])} Grands Prix run{' so far' if partial else ''}.{f' <b>{E(drivers[champ["id"]]["name"])}</b> {"leads the standings" if partial else ("finished the year with the most race points" if derived else "won the drivers’ championship")} with {fmt(champ["pts"])} points and {champ["wins"]} wins' if champ else ''}{f'; <b>{E(teams[ct["id"]]["name"])}</b> {"lead" if partial else "took"} the constructors’ table with {fmt(ct["pts"])}.' if ct else '.'}{' No constructors’ championship was awarded this year.' if not ct else ''}</p>
<a class="open" href="{rel}f1/#season={y}&tab=season">Open {y} in the atlas →</a>{f'<a class="also" href="{rel}f1/seasons/{prev}/">← {prev}</a>' if prev else ''}{f'<a class="also" href="{rel}f1/seasons/{nxt}/">{nxt} →</a>' if nxt else ''}
{kpis([('Grands Prix', len(done), f'of {len(s["races"])} scheduled' if len(done) < len(s['races']) else ''), ('Race winners', len({next((x['d'] for x in r['rows'] if x['dw']), None) for r in done} - {None}), ''), ('Drivers classified', len(dr), 'derived from race points' if derived else 'published standings'), ('Constructors', len({x['t'] for r in done for x in r['rows']}), '')])}
<h2>Calendar <small>click a race to replay it in the atlas</small></h2>{table(['Rd', 'Date', 'Grand Prix', 'Circuit', 'Winner', 'Constructor', 'Grid P1', 'Fastest lap'], rows, num=(0,))}
<div class="two"><div><h2>Drivers’ standings <small>{'ordered by race points; no published table' if derived else 'published'}</small></h2>{table(['Pos', 'Driver', 'Constructor', 'Points', 'Wins'], st_rows, num=(0, 3, 4))}</div><div><h2>Constructors’ standings</h2>{table(['Pos', 'Constructor', 'Points', 'Wins'], tm_rows, num=(0, 2, 3)) if tm_rows else '<p class="lede">No constructors’ championship was awarded in ' + str(y) + '.</p>'}</div></div>'''
        out.append((f'f1/seasons/{y}/index.html', page(site=site, sport='f1', depth=3, title=f'{y} Formula 1 season · results and standings · APEX', desc=f'Every Grand Prix of the {y} Formula 1 season with winners, pole positions, fastest laps and the drivers’ and constructors’ standings.', crumbs=[('Sportsfans', rel), ('Formula 1', rel + 'f1/'), ('Seasons', rel + 'f1/seasons/'), (str(y), None)], body=body, path=f'f1/seasons/{y}/', v=v)))
    # ---- drivers
    for d, info in drivers.items():
        rel = '../../../'; rr = by_driver.get(d, [])
        if not rr: continue
        wins = sum(x['dw'] for _, _, x in rr); pod = sum(x['dp'] for _, _, x in rr); poles = sum(1 for _, _, x in rr if x.get('g') == 1); fl = sum(1 for _, _, x in rr if x.get('fr') == 1); pts = sum(x['pts'] for _, _, x in rr)
        titles = [y for y, (c, der) in season_champ.items() if c == d and not der and str(y) != (D.get('cutoff') or '')[-4:]]
        tm = collections.Counter(x['t'] for _, _, x in rr)
        years = sorted({y for y, _, _ in rr})
        seas = []
        for s in seasons:
            if s['year'] not in years: continue
            dr, derived = standings(s); a = next((z for z in dr if z['id'] == d), None); mine = [x for r in s['races'] for x in r['rows'] if x['d'] == d]
            seas.append([f'<a class="q" href="{rel}f1/seasons/{s["year"]}/">{s["year"]}</a>', (('<b style="color:var(--gold)">1 ★</b>' if a['p'] == '1' and not derived else E(a['p'])) if a else '—'), fmt(a['pts'] if a else sum(x['pts'] for x in mine)), sum(x['dw'] for x in mine), sum(x['dp'] for x in mine), len(mine), ' / '.join(tl(t, rel) for t in (a['teams'] if a else sorted({x['t'] for x in mine})))])
        races = [[y, f'<a class="q" href="{rel}f1/#season={y}&tab=race&race={r["round"]}">{E(r["name"])}</a>', tl(x['t'], rel), x.get('g') or '—', E(x['label']), fmt(x['pts']) if x['pts'] else '', E(x['status'])] for y, r, x in rr]
        body = f'''<p class="eyebrow">Formula 1 · Driver · {years[0]}–{years[-1]}</p><h1>{E(info['name'])}</h1>
<p class="lede">{E(info.get('nationality', ''))}{' · born ' + E(info['dob']) if info.get('dob') else ''} · {len(rr)} Grand Prix entries for {', '.join(E(teams.get(t, {}).get('name', t)) for t, _ in tm.most_common(4))}{' and others' if len(tm) > 4 else ''}.{f' World champion {", ".join(map(str, titles))}.' if titles else ''}</p>
<a class="open" href="{rel}f1/#tab=drivers&driver={d}">Open in the atlas →</a>
{kpis([('Titles', len(titles), ''), ('Wins', wins, f'{pct(wins, len(rr))}% of entries'), ('Podiums', pod, ''), ('Grid P1', poles, ''), ('Fastest laps', fl, ''), ('Points', fmt(pts), 'race points as awarded'), ('Grands Prix', len(rr), '')])}
<h2>Season by season</h2>{table(['Season', 'Pos', 'Points', 'Wins', 'Podiums', 'GPs', 'Constructor'], seas, num=(2, 3, 4, 5))}
<h2>Every Grand Prix <small>{len(rr)} entries</small></h2>{table(['Season', 'Grand Prix', 'Constructor', 'Grid', 'Result', 'Pts', 'Status'], races, num=(3, 5))}'''
        out.append((f'f1/drivers/{d}/index.html', page(site=site, sport='f1', depth=3, title=f'{info["name"]} · Formula 1 career, every Grand Prix · APEX', desc=f'{info["name"]}: {len(rr)} Grands Prix, {wins} wins, {pod} podiums, {fmt(pts)} points, {years[0]}–{years[-1]}. Season by season and race by race.', crumbs=[('Sportsfans', rel), ('Formula 1', rel + 'f1/'), ('Drivers', rel + 'f1/drivers/'), (info['name'], None)], body=body, path=f'f1/drivers/{d}/', v=v, noindex=(len(rr) < 3 and not pod and not pts))))
    # ---- constructors
    for t, info in teams.items():
        rel = '../../../'; rr = by_team.get(t, [])
        if not rr: continue
        years = sorted({y for y, _, _ in rr}); wins = sum(1 for y, r, x in rr if x['cw']); pod = sum(x['cp'] for _, _, x in rr); pts = sum(x['pts'] for _, _, x in rr)
        ttitles = [s['year'] for s in seasons if s.get('teams') and s['teams'][0]['id'] == t and str(s['year']) != (D.get('cutoff') or '')[-4:]]
        drs = collections.Counter(x['d'] for _, _, x in rr)
        seas = []
        for s in seasons:
            if s['year'] not in years: continue
            a = next((z for z in s.get('teams', []) if z['id'] == t), None); mine = [x for r in s['races'] for x in r['rows'] if x['t'] == t]
            seas.append([f'<a class="q" href="{rel}f1/seasons/{s["year"]}/">{s["year"]}</a>', ('<b style="color:var(--gold)">1 ★</b>' if a and a['p'] == '1' else E(a['p'])) if a else '—', fmt(a['pts'] if a else sum(x['pts'] for x in mine)), sum(1 for r in s['races'] for x in r['rows'] if x['t'] == t and x['cw']), len({r['round'] for r in s['races'] for x in r['rows'] if x['t'] == t}), ', '.join(dl(dd, rel) for dd in sorted({x['d'] for x in mine}, key=lambda dd: drivers.get(dd, {}).get('name', dd)))])
        winsrows = [[y, f'<a class="q" href="{rel}f1/#season={y}&tab=race&race={r["round"]}">{E(r["name"])}</a>', dl(x['d'], rel), x.get('g') or '—'] for y, r, x in rr if x['dw']]
        body = f'''<p class="eyebrow">Formula 1 · Constructor · {years[0]}–{years[-1]}</p><h1><i class="dot" style="--c:{col(t)};width:.5em;height:.5em;border-radius:6px;vertical-align:.15em"></i>{E(info['name'])}</h1>
<p class="lede">{len({r['round'] for _, r, _ in rr} | set()) and len({(y, r['round']) for y, r, _ in rr})} Grand Prix weekends, {len(drs)} drivers.{f' Constructors’ champions {", ".join(map(str, ttitles))}.' if ttitles else ''} Source identity as recorded in the archive; predecessor and successor teams are not merged.</p>
<a class="open" href="{rel}f1/#tab=teams&team={t}">Open in the atlas →</a>
{kpis([('Titles', len(ttitles), 'constructors’ championships'), ('Wins', wins, ''), ('Podiums', pod, 'car entries on the podium'), ('Points', fmt(pts), 'race points as awarded'), ('Weekends', len({(y, r['round']) for y, r, _ in rr}), ''), ('Drivers', len(drs), '')])}
<h2>Season by season</h2>{table(['Season', 'Pos', 'Points', 'Wins', 'GPs', 'Drivers'], seas, num=(2, 3, 4))}
<h2>Drivers</h2><div class="chips">{''.join(f'<a class="chip" href="{rel}f1/drivers/{dd}/"><i style="--c:{col(t)}"></i>{E(drivers.get(dd, {}).get("name", dd))} <span style="color:var(--muted)">{n}</span></a>' for dd, n in drs.most_common())}</div>
{('<h2>Wins <small>' + str(len(winsrows)) + '</small></h2>' + table(['Season', 'Grand Prix', 'Driver', 'Grid'], winsrows, num=(3,))) if winsrows else ''}'''
        out.append((f'f1/constructors/{t}/index.html', page(site=site, sport='f1', depth=3, title=f'{info["name"]} · Formula 1 constructor record · APEX', desc=f'{info["name"]} in Formula 1, {years[0]}–{years[-1]}: {wins} wins, {fmt(pts)} points, {len(drs)} drivers, season by season.', crumbs=[('Sportsfans', rel), ('Formula 1', rel + 'f1/'), ('Constructors', rel + 'f1/constructors/'), (info['name'], None)], body=body, path=f'f1/constructors/{t}/', v=v)))
    # ---- circuits
    for c, info in circs.items():
        rel = '../../../'; rr = by_circ.get(c, [])
        if not rr: continue
        years = [y for y, _ in rr]; winners = collections.Counter(next((x['d'] for x in r['rows'] if x['dw']), None) for _, r in rr); cons = collections.Counter(next((x['t'] for x in r['rows'] if x['cw']), None) for _, r in rr)
        rows = [[y, f'<a class="q" href="{rel}f1/#season={y}&tab=race&race={r["round"]}">{E(r["name"])}</a>', dl(w['d'], rel) if w else '—', tl(w['t'], rel) if w else '', dl(p['d'], rel) if p else '—', E(r.get('layout') or '')] for y, r in rr for w in [next((x for x in r['rows'] if x['dw']), None)] for p in [next((x for x in r['rows'] if x.get('g') == 1), None)]]
        topd = [(d, n) for d, n in winners.most_common(5) if d]; topt = [(t, n) for t, n in cons.most_common(5) if t]
        body = f'''<p class="eyebrow">Formula 1 · Circuit · {E(info.get('place', ''))}, {E(info.get('country', ''))}</p><h1>{E(info['name'])}</h1>
<p class="lede">{len(rr)} Grands Prix, {years[0]}–{years[-1]}.{f' Most wins: <b>{E(drivers.get(topd[0][0], {}).get("name", topd[0][0]))}</b> ({topd[0][1]}) and <b>{E(teams.get(topt[0][0], {}).get("name", topt[0][0]))}</b> ({topt[0][1]}).' if topd and topt else ''}{f' <a href="{E(info["url"])}" target="_blank" rel="noopener">Circuit on Wikipedia ↗</a>' if info.get('url') else ''}</p>
<a class="open" href="{rel}f1/#tab=circuits&circuit={c}">Open in the atlas →</a>
{kpis([('Grands Prix', len(rr), f'{years[0]}–{years[-1]}'), ('Different winners', len([d for d in winners if d]), ''), ('Layouts used', len({r.get('layout') for _, r in rr} - {None, ''}), '')])}
<div class="two"><div><h2>Most wins · drivers</h2>{table(['Driver', 'Wins'], [[dl(d, rel), n] for d, n in topd], num=(1,))}</div><div><h2>Most wins · constructors</h2>{table(['Constructor', 'Wins'], [[tl(t, rel), n] for t, n in topt], num=(1,))}</div></div>
<h2>Every race here</h2>{table(['Season', 'Grand Prix', 'Winner', 'Constructor', 'Grid P1', 'Layout'], rows, num=(0,))}'''
        out.append((f'f1/circuits/{c}/index.html', page(site=site, sport='f1', depth=3, title=f'{info["name"]} · every Formula 1 Grand Prix held there · APEX', desc=f'{info["name"]}, {info.get("place", "")}: {len(rr)} Grands Prix from {years[0]} to {years[-1]}, winners and constructors race by race.', crumbs=[('Sportsfans', rel), ('Formula 1', rel + 'f1/'), ('Circuits', rel + 'f1/circuits/'), (info['name'], None)], body=body, path=f'f1/circuits/{c}/', v=v)))
    # ---- indexes
    rel = '../../'
    out.append(('f1/seasons/index.html', page(site=site, sport='f1', depth=2, title='Formula 1 seasons 1950–2026 · APEX', desc='Every Formula 1 season from 1950, with champions, on its own page.', crumbs=[('Sportsfans', rel), ('Formula 1', rel + 'f1/'), ('Seasons', None)], body=f'<p class="eyebrow">Formula 1</p><h1>Every <span>season</span></h1><p class="lede">{len(seasons)} seasons. The champion named is the published one; where the archive holds no table (1952–53) the driver with most race points is listed.</p>' + index_list([(str(s['year']), f'f1/seasons/{s["year"]}/', drivers.get(season_champ[s['year']][0], {}).get('name', '') if season_champ[s['year']][0] else '') for s in reversed(seasons)], rel), path='f1/seasons/', v=v)))
    out.append(('f1/drivers/index.html', page(site=site, sport='f1', depth=2, title='Formula 1 drivers A–Z · APEX', desc='Every driver classified in a Formula 1 Grand Prix since 1950, each with a career page.', crumbs=[('Sportsfans', rel), ('Formula 1', rel + 'f1/'), ('Drivers', None)], body=f'<p class="eyebrow">Formula 1</p><h1>Every <span>driver</span></h1><p class="lede">{len(by_driver)} drivers with at least one Grand Prix classification.</p>' + index_list(sorted([(drivers[d]['name'], f'f1/drivers/{d}/', f'{sum(x["dw"] for _, _, x in rr)} wins' if sum(x['dw'] for _, _, x in rr) else f'{len(rr)} GPs') for d, rr in by_driver.items() if d in drivers], key=lambda t: (t[0].split(' ')[-1], t[0], t[1])), rel), path='f1/drivers/', v=v)))
    out.append(('f1/constructors/index.html', page(site=site, sport='f1', depth=2, title='Formula 1 constructors A–Z · APEX', desc='Every constructor entered in a Formula 1 Grand Prix since 1950.', crumbs=[('Sportsfans', rel), ('Formula 1', rel + 'f1/'), ('Constructors', None)], body=f'<p class="eyebrow">Formula 1</p><h1>Every <span>constructor</span></h1><p class="lede">{len(by_team)} source identities.</p>' + index_list(sorted([(teams[t]['name'], f'f1/constructors/{t}/', f'{sum(1 for _, _, x in rr if x["cw"])} wins' if sum(1 for _, _, x in rr if x['cw']) else '') for t, rr in by_team.items() if t in teams]), rel), path='f1/constructors/', v=v)))
    out.append(('f1/circuits/index.html', page(site=site, sport='f1', depth=2, title='Formula 1 circuits · APEX', desc='Every circuit that has hosted a Formula 1 Grand Prix, with every race held there.', crumbs=[('Sportsfans', rel), ('Formula 1', rel + 'f1/'), ('Circuits', None)], body=f'<p class="eyebrow">Formula 1</p><h1>Every <span>circuit</span></h1><p class="lede">{len(by_circ)} venues.</p>' + index_list(sorted([(circs[c]['name'], f'f1/circuits/{c}/', f'{len(rr)} GPs') for c, rr in by_circ.items() if c in circs]), rel), path='f1/circuits/', v=v)))
    return out

# ============================================================ MotoGP / WorldSBK ============================================================
def gen_bikes(tag, A, colours, *, site, v):
    out = []; name = SPORTS[tag][1]; riders, circs = A['riders'], A['circuits']; races = sorted(A['races'], key=lambda r: (r['year'], r['date'], r.get('order', 0), r['type']))
    ismain = (lambda r: r['type'] != 'SPR') if tag == 'motogp' else (lambda r: r['type'] in ('R1', 'R2'))
    col = lambda m: colours.get(m, '#8b9099')
    rid_slug = {rid: f'{slug(info["name"])}-{rid}' for rid, info in riders.items()}
    cslug = {}; used = set()
    for cid, info in circs.items():
        s = slug(info['name']);
        if s in used: s = slug(info['name'] + ' ' + str(info.get('country', '')))
        used.add(s); cslug[cid] = s
    by_rider = collections.defaultdict(list); by_maker = collections.defaultdict(list); by_circ = collections.defaultdict(list)
    for r in races:
        by_circ[r['circuit']].append(r)
        for x in r.get('results', []):
            by_rider[x['rider']].append((r, x)); by_maker[x.get('maker') or '—'].append((r, x))
    st_all = {z['rider'] for y in A['standings'].values() for z in y.get('rows', [])}
    HAS_RIDER = {rid for rid in riders if by_rider.get(rid) or rid in st_all}
    rl = lambda rid, rel: (f'<a class="q" href="{rel}{tag}/riders/{rid_slug.get(rid, rid)}/">{E(riders.get(rid, {}).get("name", rid))}</a>' if rid in HAS_RIDER else E(riders.get(rid, {}).get("name", rid)))
    _ml = lambda m, rel: f'<i class="dot" style="--c:{col(m)}"></i><a class="q" href="{rel}{tag}/makers/{slug(m)}/">{E(m)}</a>'
    ml = lambda m, rel: _ml(m, rel) if m in by_maker else f'<i class="dot" style="--c:{col(m)}"></i>{E(m)}'
    cl = lambda cid, rel: f'<a class="q" href="{rel}{tag}/circuits/{cslug.get(cid, slug(cid))}/">{E(circs.get(cid, {}).get("name", cid))}</a>'
    typ = {'RAC': 'Grand Prix', 'SPR': 'Sprint', 'R1': 'Race 1', 'R2': 'Race 2'}
    years = sorted({r['year'] for r in races}); by_year = collections.defaultdict(list)
    for r in races: by_year[r['year']].append(r)
    st = A['standings']; mst = A.get('manufacturerStandings') or {}

    win = lambda r: next((x for x in r.get('results', []) if x.get('pos') == 1 and x.get('status') in (None, 'Classified', 'Finished')), None) or next((x for x in r.get('results', []) if x.get('pos') == 1), None)
    champs = {y: (st[str(y)]['rows'][0] if st.get(str(y), {}).get('rows') else None) for y in years}
    race_link = lambda r, rel: f'<a class="q" href="{rel}{tag}/#season={r["year"]}&tab=race">{E(r["name"])}{"" if tag == "sbk" else " · " + typ.get(r["type"], r["type"])}</a>'
    # seasons
    for y in years:
        rel = '../../../'; rr = by_year[y]; c = champs[y]; rows_st = st.get(str(y), {}).get('rows', [])
        rows = [[E(r['date']), race_link(r, rel), cl(r['circuit'], rel), rl(w['rider'], rel) if w else '—', ml(w.get('maker'), rel) if w and w.get('maker') else '', (rl(r['pole']['rider'], rel) if r.get('pole') and r['pole'].get('rider') else '—'), (E(r['fast']['time']) + ' · ' + rl(r['fast']['rider'], rel)) if r.get('fast') and r['fast'].get('rider') else '—'] for r in rr for w in [win(r)]]
        strows = [[a.get('pos', i + 1), rl(a['rider'], rel), ml(a['maker'], rel) if a.get('maker') else '', fmt(a.get('points'))] for i, a in enumerate(rows_st)]
        mrows = [[a.get('pos', i + 1), ml(a['maker'], rel), fmt(a.get('points'))] for i, a in enumerate(mst.get(str(y), {}).get('rows', []))]
        prev = y - 1 if y - 1 in by_year else None; nxt = y + 1 if y + 1 in by_year else None
        mains = [r for r in rr if ismain(r)]
        body = f'''<p class="eyebrow">{E(name)} · Season</p><h1>{y} <span>{E(SPORTS[tag][0])}</span></h1>
<p class="lede">{len(mains)} {'Grands Prix' if tag == 'motogp' else 'races'}{f' and {len(rr) - len(mains)} sprints' if len(rr) > len(mains) else ''}.{f' <b>{E(riders.get(c["rider"], {}).get("name", c["rider"]))}</b> heads the published standings with {fmt(c.get("points"))} points on a {E(c.get("maker", ""))}.' if c else ''}</p>
<a class="open" href="{rel}{tag}/#season={y}&tab=season">Open {y} in the atlas →</a>{f'<a class="also" href="{rel}{tag}/seasons/{prev}/">← {prev}</a>' if prev else ''}{f'<a class="also" href="{rel}{tag}/seasons/{nxt}/">{nxt} →</a>' if nxt else ''}
{kpis([('Races', len(rr), ''), ('Winners', len({win(r)['rider'] for r in rr if win(r)}), 'different race winners'), ('Riders classified', len(rows_st), 'in the published standings'), ('Makers', len({x.get('maker') for r in rr for x in r.get('results', [])} - {None}), '')])}
<h2>Calendar <small>every race, in order</small></h2>{table(['Date', 'Race', 'Circuit', 'Winner', 'Maker', 'Pole', 'Fastest lap'], rows)}
<div class="two"><div><h2>Riders’ standings <small>published</small></h2>{table(['Pos', 'Rider', 'Maker', 'Points'], strows, num=(0, 3))}</div><div><h2>Manufacturers</h2>{table(['Pos', 'Maker', 'Points'], mrows, num=(0, 2)) if mrows else '<p class="lede">No manufacturers’ table in the archive for this season.</p>'}</div></div>'''
        out.append((f'{tag}/seasons/{y}/index.html', page(site=site, sport=tag, depth=3, title=f'{y} {name} season · results and standings · APEX', desc=f'Every {name} race of {y} with winners, poles and fastest laps, and the published riders’ standings.', crumbs=[('Sportsfans', rel), (name, rel + tag + '/'), ('Seasons', rel + tag + '/seasons/'), (str(y), None)], body=body, path=f'{tag}/seasons/{y}/', v=v)))
    # riders
    st_years = collections.defaultdict(set)
    for y in years:
        for z in st.get(str(y), {}).get('rows', []): st_years[z['rider']].add(y)
    for rid, info in riders.items():
        rel = '../../../'; rr = by_rider.get(rid, [])
        if not rr and not st_years.get(rid): continue
        mains = [(r, x) for r, x in rr if ismain(r)]
        wins = sum(1 for r, x in mains if x.get('pos') == 1); pod = sum(1 for r, x in mains if x.get('pos') in (1, 2, 3)); ys = sorted({r['year'] for r, _ in rr} | st_years.get(rid, set()))
        titles = [y for y in years if champs[y] and champs[y]['rider'] == rid and str(y) != str(A.get('lastDate', ''))[:4]]
        makers = collections.Counter(x.get('maker') for _, x in rr if x.get('maker'))
        seas = []
        for y in ys:
            a = next((z for z in st.get(str(y), {}).get('rows', []) if z['rider'] == rid), None); mine = [(r, x) for r, x in mains if r['year'] == y]
            seas.append([f'<a class="q" href="{rel}{tag}/seasons/{y}/">{y}</a>', ('<b style="color:var(--gold)">1 ★</b>' if a and a.get('pos') == 1 else E(a.get('pos'))) if a else '—', fmt(a.get('points')) if a else '—', sum(1 for r, x in mine if x.get('pos') == 1), sum(1 for r, x in mine if x.get('pos') in (1, 2, 3)), len(mine), ' / '.join(ml(m, rel) for m in sorted({x.get('maker') for _, x in mine} - {None}))])
        rows = [[r['year'], race_link(r, rel), ml(x['maker'], rel) if x.get('maker') else '', E(x.get('pos') if x.get('pos') is not None else '—'), fmt(x.get('points')) if x.get('points') else '', E(x.get('status') or '')] for r, x in rr]
        body = f'''<p class="eyebrow">{E(name)} · Rider · {ys[0]}–{ys[-1]}</p><h1>{E(info['name'])}</h1>
<p class="lede">{E(info.get('country', ''))}{' · #' + str(info['number']) if info.get('number') else ''} · {len(mains)} race starts for {', '.join(E(m) for m, _ in makers.most_common(3))}{' and others' if len(makers) > 3 else ''}.{f' World champion {", ".join(map(str, titles))}.' if titles else ''}</p>
<a class="open" href="{rel}{tag}/#tab=riders&rider={rid}">Open in the atlas →</a>
{kpis([('Titles', len(titles), ''), ('Wins', wins, f'{pct(wins, len(mains))}% of starts' if mains else ''), ('Podiums', pod, ''), ('Race starts', len(mains), 'sprints excluded'), ('Seasons', len(ys), '')])}
<h2>Season by season</h2>{table(['Season', 'Pos', 'Points', 'Wins', 'Podiums', 'Starts', 'Maker'], seas, num=(2, 3, 4, 5))}
{('<h2>Every race <small>' + str(len(rr)) + ' classifications</small></h2>' + table(['Season', 'Race', 'Maker', 'Result', 'Pts', 'Status'], rows, num=(3, 4))) if rr else '<p class="lede">This rider appears in the published standings but no race-by-race classification is held in the archive.</p>'}'''
        out.append((f'{tag}/riders/{rid_slug[rid]}/index.html', page(site=site, sport=tag, depth=3, title=f'{info["name"]} · {name} career, every race · APEX', desc=f'{info["name"]} in {name}: {len(mains)} starts, {wins} wins, {pod} podiums, {ys[0]}–{ys[-1]}.', crumbs=[('Sportsfans', rel), (name, rel + tag + '/'), ('Riders', rel + tag + '/riders/'), (info['name'], None)], body=body, path=f'{tag}/riders/{rid_slug[rid]}/', v=v, noindex=(len(mains) < 3 and not pod))))
    # makers
    for m, rr in by_maker.items():
        if m == '—': continue
        rel = '../../../'; mains = [(r, x) for r, x in rr if ismain(r)]; ys = sorted({r['year'] for r, _ in rr}); wins = sum(1 for r, x in mains if x.get('pos') == 1)
        titles = [y for y in years if champs[y] and champs[y].get('maker') == m and str(y) != str(A.get('lastDate', ''))[:4]]
        rds = collections.Counter(x['rider'] for _, x in rr)
        seas = []
        for y in ys:
            rows_st = [z for z in st.get(str(y), {}).get('rows', []) if z.get('maker') == m]; best = rows_st[0] if rows_st else None; mine = [(r, x) for r, x in mains if r['year'] == y]; ms_ = next((z for z in mst.get(str(y), {}).get('rows', []) if z.get('maker') == m), None)
            seas.append([f'<a class="q" href="{rel}{tag}/seasons/{y}/">{y}</a>', ('<b style="color:var(--gold)">1 ★</b>' if ms_ and ms_.get('pos') == 1 else E(ms_.get('pos'))) if ms_ else '—', fmt(ms_.get('points')) if ms_ else '—', (rl(best['rider'], rel) + f' (P{best.get("pos")})') if best else '—', sum(1 for r, x in mine if x.get('pos') == 1), len({x['rider'] for _, x in mine})])
        winsrows = [[r['year'], race_link(r, rel), rl(x['rider'], rel)] for r, x in mains if x.get('pos') == 1]
        body = f'''<p class="eyebrow">{E(name)} · Manufacturer · {ys[0]}–{ys[-1]}</p><h1><i class="dot" style="--c:{col(m)};width:.5em;height:.5em;border-radius:6px;vertical-align:.15em"></i>{E(m)}</h1>
<p class="lede">{len({(r['year'], r['id']) for r, _ in rr})} races with {len(rds)} riders.{f' Riders’ champions on this make: {", ".join(map(str, titles))}.' if titles else ''}</p>
<a class="open" href="{rel}{tag}/#tab=teams&team={E(m)}">Open in the atlas →</a>
{kpis([('Riders’ titles', len(titles), 'champion on this make'), ('Wins', wins, ''), ('Seasons', len(ys), ''), ('Riders', len(rds), '')])}
<h2>Season by season</h2>{table(['Season', "Makers’ pos", 'Points', 'Best rider', 'Wins', 'Riders'], seas, num=(2, 4, 5))}
<h2>Riders</h2><div class="chips">{''.join(f'<a class="chip" href="{rel}{tag}/riders/{rid_slug.get(rid, rid)}/"><i style="--c:{col(m)}"></i>{E(riders.get(rid, {}).get("name", rid))} <span style="color:var(--muted)">{n}</span></a>' for rid, n in rds.most_common(60))}</div>
{('<h2>Wins <small>' + str(len(winsrows)) + '</small></h2>' + table(['Season', 'Race', 'Rider'], winsrows)) if winsrows else ''}'''
        out.append((f'{tag}/makers/{slug(m)}/index.html', page(site=site, sport=tag, depth=3, title=f'{m} · {name} record · APEX', desc=f'{m} in {name}, {ys[0]}–{ys[-1]}: {wins} wins, {len(rds)} riders, season by season.', crumbs=[('Sportsfans', rel), (name, rel + tag + '/'), ('Makers', rel + tag + '/makers/'), (m, None)], body=body, path=f'{tag}/makers/{slug(m)}/', v=v)))
    # circuits
    for cid, info in circs.items():
        rel = '../../../'; rr = by_circ.get(cid, [])
        if not rr: continue
        ys = sorted({r['year'] for r in rr}); winners = collections.Counter(win(r)['rider'] for r in rr if win(r)); makers = collections.Counter(win(r).get('maker') for r in rr if win(r))
        rows = [[r['year'], race_link(r, rel), rl(w['rider'], rel) if w else '—', ml(w.get('maker'), rel) if w and w.get('maker') else '', rl(r['pole']['rider'], rel) if r.get('pole') and r['pole'].get('rider') else '—'] for r in rr for w in [win(r)]]
        body = f'''<p class="eyebrow">{E(name)} · Circuit · {E(info.get('place', ''))}, {E(info.get('country', ''))}</p><h1>{E(info['name'])}</h1>
<p class="lede">{len(rr)} races, {ys[0]}–{ys[-1]}.{f' Most wins: <b>{E(riders.get(winners.most_common(1)[0][0], {}).get("name", ""))}</b> ({winners.most_common(1)[0][1]}).' if winners else ''}</p>
<a class="open" href="{rel}{tag}/#tab=circuits&circuit={E(cid)}">Open in the atlas →</a>
{kpis([('Races', len(rr), f'{ys[0]}–{ys[-1]}'), ('Different winners', len(winners), ''), ('Winning makes', len([k for k in makers if k]), '')])}
<div class="two"><div><h2>Most wins · riders</h2>{table(['Rider', 'Wins'], [[rl(r_, rel), n] for r_, n in winners.most_common(6)], num=(1,))}</div><div><h2>Most wins · makers</h2>{table(['Maker', 'Wins'], [[ml(m_, rel), n] for m_, n in makers.most_common(6) if m_], num=(1,))}</div></div>
<h2>Every race here</h2>{table(['Season', 'Race', 'Winner', 'Maker', 'Pole'], rows, num=(0,))}'''
        out.append((f'{tag}/circuits/{cslug[cid]}/index.html', page(site=site, sport=tag, depth=3, title=f'{info["name"]} · every {name} race held there · APEX', desc=f'{info["name"]}: {len(rr)} {name} races from {ys[0]} to {ys[-1]}, winners and makers race by race.', crumbs=[('Sportsfans', rel), (name, rel + tag + '/'), ('Circuits', rel + tag + '/circuits/'), (info['name'], None)], body=body, path=f'{tag}/circuits/{cslug[cid]}/', v=v)))
    rel = '../../'
    out.append((f'{tag}/seasons/index.html', page(site=site, sport=tag, depth=2, title=f'{name} seasons {years[0]}–{years[-1]} · APEX', desc=f'Every {name} season with its champion, on its own page.', crumbs=[('Sportsfans', rel), (name, rel + tag + '/'), ('Seasons', None)], body=f'<p class="eyebrow">{E(name)}</p><h1>Every <span>season</span></h1><p class="lede">{len(years)} seasons; the rider named heads the published standings.</p>' + index_list([(str(y), f'{tag}/seasons/{y}/', riders.get(champs[y]['rider'], {}).get('name', '') if champs[y] else '') for y in reversed(years)], rel), path=f'{tag}/seasons/', v=v)))
    out += index_pages(site=site, sport=tag, title=f'{name} riders A–Z · APEX', desc=f'Every rider classified in a {name} race, each with a career page.', crumbs=[('Sportsfans', rel), (name, rel + tag + '/'), ('Riders', None)], intro=f'<p class="eyebrow">{E(name)}</p><h1>Every <span>rider</span></h1><p class="lede">{len([r for r in (set(by_rider) | set(st_years)) if r in riders])} riders.</p>', items=sorted([(riders[r_]['name'], f'{tag}/riders/{rid_slug[r_]}/', (f'{w} wins' if (w := sum(1 for r, x in by_rider.get(r_, []) if ismain(r) and x.get("pos") == 1)) else f'{len(by_rider.get(r_, []))} races')) for r_ in sorted(set(by_rider) | set(st_years)) if r_ in riders], key=lambda t: (t[0].split(' ')[-1], t[0], t[1])), dir=f'{tag}/riders', v=v)
    out.append((f'{tag}/makers/index.html', page(site=site, sport=tag, depth=2, title=f'{name} manufacturers · APEX', desc=f'Every manufacturer classified in {name}.', crumbs=[('Sportsfans', rel), (name, rel + tag + '/'), ('Makers', None)], body=f'<p class="eyebrow">{E(name)}</p><h1>Every <span>maker</span></h1>' + index_list(sorted([(m, f'{tag}/makers/{slug(m)}/', f'{sum(1 for r, x in rr if ismain(r) and x.get("pos") == 1)} wins') for m, rr in by_maker.items() if m != '—']), rel), path=f'{tag}/makers/', v=v)))
    out.append((f'{tag}/circuits/index.html', page(site=site, sport=tag, depth=2, title=f'{name} circuits · APEX', desc=f'Every circuit that has staged a {name} race.', crumbs=[('Sportsfans', rel), (name, rel + tag + '/'), ('Circuits', None)], body=f'<p class="eyebrow">{E(name)}</p><h1>Every <span>circuit</span></h1>' + index_list(sorted([(circs[c]['name'], f'{tag}/circuits/{cslug[c]}/', f'{len(rr)} races') for c, rr in by_circ.items() if c in circs]), rel), path=f'{tag}/circuits/', v=v)))
    return out

# ============================================================ Rugby ============================================================
def gen_rugby(A, *, site, v):
    out = []; ten = {t['name']: t for t in A['teams']}; M = A['matches']
    OPP = {'British & Irish Lions': '#e75863', 'Japan': '#f48f9a', 'Fiji': '#ecebe6', 'Samoa': '#618fff', 'Tonga': '#d65b5e', 'Georgia': '#a86572', 'Namibia': '#85a8ed', 'USA': '#b482a2', 'Portugal': '#d65965', 'South America': '#d6ba82', 'NZ Cavaliers': '#8faba3', 'World Invitation': '#c09aca', 'Canada': '#ef8d81', 'Romania': '#ecce59', 'Uruguay': '#8bcddd', 'Spain': '#c85a5b'}
    col = lambda n: ten[n]['accent'] if n in ten else OPP.get(n, '#8b9099')
    plays = lambda m, s: (m['home'] == s or m['away'] == s) and (s not in ten or s in m['eligible'])
    winner = lambda m: None if m['hs'] == m['as_'] else (m['home'] if m['hs'] > m['as_'] else m['away'])
    sides = sorted({s for m in M for s in (m['home'], m['away'])})
    nl = lambda n, rel: f'<i class="dot" style="--c:{col(n)}"></i><a class="q" href="{rel}rugby/nations/{slug(n)}/">{E(n)}</a>'
    grounds = {}
    for m in M:
        if m['stadium'].startswith('ground-not-recorded'): continue
        g = grounds.setdefault(m['stadium'], {'names': collections.Counter(), 'city': collections.Counter(), 'country': collections.Counter()}); g['names'][m['venue']] += 1
        if m.get('city'): g['city'][m['city']] += 1
        if m.get('country'): g['country'][m['country']] += 1
    gname = {k: sorted(g['names'], key=lambda n: (len(re.sub(r'[^A-Za-z]', '', n)), len(n)))[0].rstrip(' .-') for k, g in grounds.items()}
    gl = lambda sid, rel: (f'<a class="q" href="{rel}rugby/grounds/{sid}/">{E(gname[sid])}</a>' if sid in gname else '<span class="D">not recorded</span>')
    ml = lambda m, rel: f'<a class="q" href="{rel}rugby/#match={m["id"]}&tab=match">{E(m["date"])}</a>'
    comp = lambda m: (f'RWC {m["worldcup"]}' + (f' · {m["stage"]}' if m.get('stage') else '')) if m.get('worldcup') else {'Six / Five / Home Nations': 'Championship', 'Rugby Championship / Tri Nations': 'Rugby Championship', 'Lions series': 'Lions', 'Historical / Olympic': 'Historical', 'Nations Championship': 'Nations Championship'}.get(m['competition'], 'Test')
    def rec(ms, s):
        w = sum(1 for m in ms if winner(m) == s); d = sum(1 for m in ms if winner(m) is None); return w, len(ms) - w - d, d
    res = lambda m, s: 'D' if winner(m) is None else ('W' if winner(m) == s else 'L')
    score = lambda m, s: f'{m["hs"]}–{m["as_"]}' if m['home'] == s else f'{m["as_"]}–{m["hs"]}'
    mrow = lambda m, rel: [ml(m, rel), nl(m['home'], rel), f'<b>{m["hs"]}–{m["as_"]}</b>' + (' <span class="D">goals</span>' if m['scoreUnit'] == 'goals' else ''), nl(m['away'], rel), E(comp(m)) + (' †' if m['historical'] else ''), gl(m['stadium'], rel)]
    years = sorted({m['year'] for m in M}); by_year = collections.defaultdict(list)
    for m in M: by_year[m['year']].append(m)
    # seasons
    for y in years:
        rel = '../../../'; ms = by_year[y]; st = []
        for s in sorted({s for m in ms for s in (m['home'], m['away'])}):
            mine = [m for m in ms if plays(m, s)]
            if not mine: continue
            w, l, d = rec(mine, s); st.append((s, len(mine), w, l, d, pct(w, len(mine))))
        maxp = max(x[1] for x in st); ranked = sorted([x for x in st if x[1] >= min(3, maxp)], key=lambda x: (-x[5], -x[2])); best = ranked[0] if ranked else None
        final = next((m for m in ms if m.get('stage') == 'Final'), None)
        prev = y - 1 if y - 1 in by_year else None; nxt = y + 1 if y + 1 in by_year else None
        body = f'''<p class="eyebrow">Rugby union · Season</p><h1>{y} <span>Test rugby</span></h1>
<p class="lede">{len(ms)} Tests involving the ten nations.{f' Best record of the year: <b>{E(best[0])}</b>, {best[2]}–{best[3]}–{best[4]} ({best[5]}%).' if best else ''}{f' World Cup: <b>{E(winner(final))}</b> beat {E(final["home"] if winner(final) == final["away"] else final["away"])} {score(final, winner(final))} in the final.' if final and winner(final) else ''}</p>
<a class="open" href="{rel}rugby/#season={y}&tab=season">Open {y} in the atlas →</a>{f'<a class="also" href="{rel}rugby/seasons/{prev}/">← {prev}</a>' if prev else ''}{f'<a class="also" href="{rel}rugby/seasons/{nxt}/">{nxt} →</a>' if nxt else ''}
{kpis([('Tests', len(ms), ''), ('Sides', len(st), ''), ('Grounds', len({m['stadium'] for m in ms if m['stadium'] in gname}), 'recorded'), ('Draws', sum(1 for m in ms if winner(m) is None), '')])}
<h2>Table of the year <small>every side that played · win rate, then wins</small></h2>{table(['Side', 'P', 'W', 'L', 'D', 'Win %'], [[nl(s, rel), p, w, l, d, r] for s, p, w, l, d, r in sorted(st, key=lambda x: (-x[5], -x[2]))], num=(1, 2, 3, 4, 5))}
<h2>Every Test <small>click a date to open it in the atlas</small></h2>{table(['Date', 'Home', 'Score', 'Away', 'Competition', 'Ground'], [mrow(m, rel) for m in ms])}'''
        out.append((f'rugby/seasons/{y}/index.html', page(site=site, sport='rugby', depth=3, title=f'{y} international rugby · every Test of the ten nations · APEX', desc=f'All {len(ms)} Tests of {y} involving South Africa, New Zealand, Australia, Argentina, England, France, Ireland, Wales, Scotland and Italy, with the table of the year.', crumbs=[('Sportsfans', rel), ('Rugby union', rel + 'rugby/'), ('Seasons', rel + 'rugby/seasons/'), (str(y), None)], body=body, path=f'rugby/seasons/{y}/', v=v)))
    # nations
    coaches_by = collections.defaultdict(list)
    for c in A['coaches']: coaches_by[c['team']].append(c)
    players_by = collections.defaultdict(list)
    for p in A['players']: players_by[p['team']].append(p)
    for s in sides:
        rel = '../../../'; mine = [m for m in M if plays(m, s)]
        if not mine: continue
        w, l, d = rec(mine, s); ys = sorted({m['year'] for m in mine}); pts = [m for m in mine if m['scoreUnit'] != 'goals']
        pf = sum((m['hs'] if m['home'] == s else m['as_']) for m in pts); pa = sum((m['as_'] if m['home'] == s else m['hs']) for m in pts)
        opp = collections.defaultdict(list)
        for m in mine: opp[m['away'] if m['home'] == s else m['home']].append(m)
        opprows = sorted([[nl(o, rel), len(ms), *rec(ms, s), pct(rec(ms, s)[0], len(ms))] for o, ms in opp.items()], key=lambda r: -r[1])
        seas = []
        for y in ys:
            ms = [m for m in mine if m['year'] == y]; ww, ll, dd = rec(ms, s); seas.append([f'<a class="q" href="{rel}rugby/seasons/{y}/">{y}</a>', len(ms), ww, ll, dd, pct(ww, len(ms))])
        cups = [m for m in mine if m.get('stage') == 'Final' and winner(m) == s]
        t = ten.get(s)
        coaches = sorted(coaches_by.get(s, []), key=lambda c: c['startYear'])
        players = sorted(players_by.get(s, []), key=lambda p: -(p.get('caps') or 0))[:40]
        body = f'''<p class="eyebrow">Rugby union · {'Nation' if t else 'Opponent'} · {ys[0]}–{ys[-1]}{' · ' + E(t['nickname']) if t else ''}</p><h1><i class="dot" style="--c:{col(s)};width:.5em;height:.5em;border-radius:6px;vertical-align:.15em"></i>{E(s)}</h1>
<p class="lede">{E(t['tag']) + '. ' if t else ''}{len(mine)} Tests against {len(opp)} opponents: {w} won, {l} lost, {d} drawn ({pct(w, len(mine))}%).{f' World champions {", ".join(str(m["worldcup"]) for m in cups)}.' if cups else ''}</p>
<a class="open" href="{rel}rugby/#tab=nations&nation={E(s)}">Open in the atlas →</a>
{kpis([('Tests', len(mine), f'{w}–{l}–{d}'), ('Win rate', f'{pct(w, len(mine))}%', 'draws count as not won'), ('Points for', fmt(pf), f'{fmt(pa)} against, points era'), ('Average margin', f'{"+" if pf >= pa else ""}{round((pf - pa) / len(pts), 1) if pts else 0}', 'per points-era Test'), ('World Cups', len(cups), '')])}
<div class="two"><div><h2>Record by opponent</h2>{table(['Opponent', 'P', 'W', 'L', 'D', 'Win %'], opprows, num=(1, 2, 3, 4, 5))}</div><div><h2>Season by season</h2>{table(['Year', 'P', 'W', 'L', 'D', 'Win %'], list(reversed(seas)), num=(1, 2, 3, 4, 5))}</div></div>
{('<h2>Coaches <small>published coaching list</small></h2>' + table(['Coach', 'Tenure', 'Published record'], [[f'<a class="q" href="{rel}rugby/coaches/{c["id"]}/">{E(c["name"])}</a>', E(c['tenure']), f'{c["reported"]["w"]}–{c["reported"]["l"]}–{c["reported"]["d"]} in {c["reported"]["n"]}' if c.get('reported') else '—'] for c in coaches])) if coaches else ''}
{('<h2>Careers <small>most caps, published snapshots</small></h2><div class="chips">' + ''.join(f'<a class="chip" href="{rel}rugby/players/{p["id"]}/"><i style="--c:{col(s)}"></i>{E(p["name"])} <span style="color:var(--muted)">{p["caps"]}</span></a>' for p in players) + '</div>') if players else ''}
<h2>Every Test <small>{len(mine)}</small></h2>{table(['Date', 'Home', 'Score', 'Away', 'Competition', 'Ground'], [mrow(m, rel) for m in reversed(mine)])}'''
        out.append((f'rugby/nations/{slug(s)}/index.html', page(site=site, sport='rugby', depth=3, title=f'{s} · every Test match, record by opponent · APEX', desc=f'{s} in Test rugby, {ys[0]}–{ys[-1]}: {len(mine)} matches, {w} won, {l} lost, {d} drawn; record by opponent and season by season.', crumbs=[('Sportsfans', rel), ('Rugby union', rel + 'rugby/'), ('Nations', rel + 'rugby/nations/'), (s, None)], body=body, path=f'rugby/nations/{slug(s)}/', v=v)))
    # players
    persp = {t: [m for m in M if t in m['eligible']] for t in ten}
    for p in A['players']:
        rel = '../../../'; games = [(h, persp[p['team']][h['match']]) for h in p['history'] if h.get('match') is not None and h['match'] < len(persp[p['team']])]
        rows = [[ml(m, rel), nl(h['opponent'], rel), f'<b class="{res(m, p["team"])}">{score(m, p["team"])}</b>', E(h.get('position') or ''), E(h.get('scoring') or ''), gl(m['stadium'], rel)] for h, m in games]
        body = f'''<p class="eyebrow">Rugby union · Player · {nl(p['team'], rel)} · {E(p.get('span') or '')}</p><h1>{E(p['name'])}</h1>
<p class="lede">{E(p.get('position') or '')}{' · born ' + E(p['dob']) if p.get('dob') else ''}{', ' + E(p['birthplace']) if p.get('birthplace') else ''}. {fmt(p.get('caps'))} caps{f', {p["tries"]} tries' if p.get('tries') is not None else ''}{f', {p["points"]} points' if p.get('points') is not None else ''} — career totals as published.</p>
<a class="open" href="{rel}rugby/#tab=players&player={p['id']}">Open in the atlas →</a>
{kpis([('Caps', fmt(p.get('caps')), 'as published'), ('Tries', fmt(p.get('tries')), ''), ('Points', fmt(p.get('points')), '' if p.get('points') is not None else 'not published'), ('First Test', E(p['first']) if p.get('first') else E(p.get('startYear') or '—'), ''), ('Last Test', E(p['last']) if p.get('last') else E(p.get('endYear') or '—'), '')])}
{('<h2>Every linked Test <small>' + str(len(games)) + (' · complete history' if p.get('complete') else ' · partial history') + '</small></h2>' + table(['Date', 'Opponent', 'Score', 'Position', 'Scoring', 'Ground'], rows)) if games else '<p class="lede">No match-by-match history is captured for this career; the totals above are the published snapshot.</p>'}
<p class="lede" style="font-size:12px">{' · '.join(f'<a href="{E(u)}" target="_blank" rel="noopener">{E(u.split("/")[2])} ↗</a>' for u in (p.get('sources') or [])[:3])}</p>'''
        out.append((f'rugby/players/{p["id"]}/index.html', page(site=site, sport='rugby', depth=3, title=f'{p["name"]} · {p["team"]} Test career · APEX', desc=f'{p["name"]}, {p["team"]}: {fmt(p.get("caps"))} Test caps, {p.get("span") or ""}.', crumbs=[('Sportsfans', rel), ('Rugby union', rel + 'rugby/'), ('Players', rel + 'rugby/players/'), (p['name'], None)], body=body, path=f'rugby/players/{p["id"]}/', v=v, noindex=((p.get('caps') or 0) < 3 and not games))))
    # grounds
    for sid, g in grounds.items():
        rel = '../../../'; ms = [m for m in M if m['stadium'] == sid]; ys = sorted({m['year'] for m in ms}); wins = collections.Counter(winner(m) for m in ms if winner(m))
        city = g['city'].most_common(1)[0][0] if g['city'] else ''; country = g['country'].most_common(1)[0][0] if g['country'] else ''
        body = f'''<p class="eyebrow">Rugby union · Ground · {E(', '.join(x for x in (city, country) if x))}</p><h1>{E(gname[sid])}</h1>
<p class="lede">{len(ms)} Tests, {ys[0]}–{ys[-1]}.{f' Most wins here: <b>{E(wins.most_common(1)[0][0])}</b> ({wins.most_common(1)[0][1]}).' if wins else ''}</p>
<a class="open" href="{rel}rugby/#tab=grounds&ground={sid}">Open in the atlas →</a>
{kpis([('Tests', len(ms), f'{ys[0]}–{ys[-1]}'), ('Sides', len({s for m in ms for s in (m['home'], m['away'])}), ''), ('Draws', sum(1 for m in ms if winner(m) is None), '')])}
{('<h2>Most wins here</h2>' + table(['Side', 'Wins'], [[nl(s, rel), n] for s, n in wins.most_common(8)], num=(1,))) if wins else ''}
<h2>Every Test here</h2>{table(['Date', 'Home', 'Score', 'Away', 'Competition', 'Ground'], [mrow(m, rel) for m in reversed(ms)])}'''
        out.append((f'rugby/grounds/{sid}/index.html', page(site=site, sport='rugby', depth=3, title=f'{gname[sid]} · every Test match played there · APEX', desc=f'{gname[sid]}, {city}: {len(ms)} Tests from {ys[0]} to {ys[-1]}.', crumbs=[('Sportsfans', rel), ('Rugby union', rel + 'rugby/'), ('Grounds', rel + 'rugby/grounds/'), (gname[sid], None)], body=body, path=f'rugby/grounds/{sid}/', v=v)))
    # coaches
    for c in A['coaches']:
        rel = '../../../'; ms = [M[i] for i in c.get('matchIds', []) if i < len(M)]; r = c.get('reported') or {}; lk = c.get('linkedRecord')
        body = f'''<p class="eyebrow">Rugby union · {E(c.get('role') or 'Coach')} · {nl(c['team'], rel)} · {E(c['tenure'])}</p><h1>{E(c['name'])}</h1>
<p class="lede">{f'Published record {r["w"]}–{r["l"]}–{r["d"]} in {r["n"]} Tests.' if r else 'No published record.'}{f' Linked record {lk["w"]}–{lk["l"]}–{lk["d"]} in {lk["n"]}.' if lk else ''}{' ' + E(c['method']) if c.get('method') else ''}</p>
<a class="open" href="{rel}rugby/#tab=coaches&coach={c['id']}">Open in the atlas →</a>
{kpis([('Published', f'{r["w"]}–{r["l"]}–{r["d"]}' if r else '—', f'{r["n"]} Tests · {pct(r["w"], r["n"])}% won' if r else ''), ('Linked', f'{lk["w"]}–{lk["l"]}–{lk["d"]}' if lk else '—', f'{lk["n"]} linked Tests' if lk else 'no match linkage captured'), ('Spells', E(' · '.join(c.get('spells') or [])), '')])}
{('<h2>Every linked Test</h2>' + table(['Date', 'Home', 'Score', 'Away', 'Competition', 'Ground'], [mrow(m, rel) for m in reversed(ms)])) if ms else ''}
{('<p class="lede">' + E(' '.join(c['notes'])) + '</p>') if c.get('notes') else ''}'''
        out.append((f'rugby/coaches/{c["id"]}/index.html', page(site=site, sport='rugby', depth=3, title=f'{c["name"]} · {c["team"]} coaching record · APEX', desc=f'{c["name"]}, {c["team"]} {c.get("role") or "coach"} {c["tenure"]}.', crumbs=[('Sportsfans', rel), ('Rugby union', rel + 'rugby/'), ('Coaches', rel + 'rugby/coaches/'), (c['name'], None)], body=body, path=f'rugby/coaches/{c["id"]}/', v=v)))
    rel = '../../'
    best_of = {}
    for y in years:
        ms = by_year[y]; st = []
        for s in sorted({s for m in ms for s in (m['home'], m['away'])}):
            mine = [m for m in ms if plays(m, s)]
            if mine: w, l, d = rec(mine, s); st.append((s, len(mine), w, pct(w, len(mine))))
        maxp = max(x[1] for x in st); r = sorted([x for x in st if x[1] >= min(3, maxp)], key=lambda x: (-x[3], -x[2], x[0])); best_of[y] = r[0][0] if r else ''
    out.append(('rugby/seasons/index.html', page(site=site, sport='rugby', depth=2, title='International rugby, year by year, 1871–2026 · APEX', desc='Every year of Test rugby involving the ten nations, on its own page.', crumbs=[('Sportsfans', rel), ('Rugby union', rel + 'rugby/'), ('Seasons', None)], body=f'<p class="eyebrow">Rugby union</p><h1>Every <span>year</span></h1><p class="lede">{len(years)} years with Tests; the side named had the best record of the year.</p>' + index_list([(str(y), f'rugby/seasons/{y}/', best_of[y]) for y in reversed(years)], rel), path='rugby/seasons/', v=v)))
    out.append(('rugby/nations/index.html', page(site=site, sport='rugby', depth=2, title='Rugby nations · APEX', desc='The ten nations and every side they have met.', crumbs=[('Sportsfans', rel), ('Rugby union', rel + 'rugby/'), ('Nations', None)], body=f'<p class="eyebrow">Rugby union</p><h1>Every <span>side</span></h1>' + index_list(sorted([(s, f'rugby/nations/{slug(s)}/', f'{sum(1 for m in M if plays(m, s))} Tests') for s in sides if any(plays(m, s) for m in M)]), rel), path='rugby/nations/', v=v)))
    out.append(('rugby/players/index.html', page(site=site, sport='rugby', depth=2, title='Rugby players · APEX', desc='Published Test careers across the ten nations.', crumbs=[('Sportsfans', rel), ('Rugby union', rel + 'rugby/'), ('Players', None)], body=f'<p class="eyebrow">Rugby union</p><h1>Every <span>career</span></h1><p class="lede">{len(A["players"])} published career snapshots; South Africa carries the fullest coverage.</p>' + index_list(sorted([(p['name'], f'rugby/players/{p["id"]}/', f'{p["team"]} · {fmt(p.get("caps"))}') for p in A['players']], key=lambda t: (t[0].split(' ')[-1], t[0], t[1])), rel), path='rugby/players/', v=v)))
    out.append(('rugby/grounds/index.html', page(site=site, sport='rugby', depth=2, title='Rugby grounds · APEX', desc='Every recorded Test ground.', crumbs=[('Sportsfans', rel), ('Rugby union', rel + 'rugby/'), ('Grounds', None)], body=f'<p class="eyebrow">Rugby union</p><h1>Every <span>ground</span></h1><p class="lede">{len(grounds)} recorded grounds; early fixtures often have none.</p>' + index_list(sorted([(gname[s], f'rugby/grounds/{s}/', f'{sum(1 for m in M if m["stadium"] == s)} Tests') for s in grounds]), rel), path='rugby/grounds/', v=v)))
    out.append(('rugby/coaches/index.html', page(site=site, sport='rugby', depth=2, title='Rugby coaches · APEX', desc='Published coaching records of the ten nations.', crumbs=[('Sportsfans', rel), ('Rugby union', rel + 'rugby/'), ('Coaches', None)], body=f'<p class="eyebrow">Rugby union</p><h1>Every <span>coach</span></h1><p class="lede">{len(A["coaches"])} tenures.</p>' + index_list(sorted([(c['name'], f'rugby/coaches/{c["id"]}/', f'{c["team"]} · {c["tenure"]}') for c in A['coaches']], key=lambda t: (t[0].split(' ')[-1], t[0], t[1])), rel), path='rugby/coaches/', v=v)))
    return out

# ============================================================ Licences page ============================================================
def gen_licences(*, site, v, published, held):
    """Every source, the terms it states, and what that means for each data file. Checked 29 September 2026."""
    rel = '../'
    def src(title, url, terms, use, tag=''):
        return f'<p><b><a class="q" href="{E(url)}" target="_blank" rel="noopener">{E(title)}</a></b>{f"<span class=tag>{E(tag)}</span>" if tag else ""}<br>{terms}<br><span style="color:var(--dim)">Used for: {use}</span></p>'
    dakar_lic = ('<h3 id="dakar">Dakar Rally</h3>\n' + src('Wikipedia', 'https://en.wikipedia.org/wiki/Dakar_Rally', 'Creative Commons Attribution-ShareAlike 4.0 (Wikipedia contributors): attribution and share-alike, both given.', 'every edition of the Dakar Rally article at a recorded revision — the route as the article names it, the era, and the first three of every class with the crew and the make. Nothing is taken from the organiser’s own site, results service or artwork.', 'CC BY-SA 4.0') + src('Natural Earth', 'https://www.naturalearthdata.com/about/terms-of-use/', 'Public domain.', 'the 1:110m land silhouette behind every route map; routes are drawn schematically between their named towns, not from any official course.', 'Public domain') + '<p><b>The data file <code>/data/dakar.json</code></b> is CC BY-SA 4.0: attribute Wikipedia contributors and share alike; the land geometry inside it is public domain. No logos, marks or official artwork are included; the rally’s name appears only to identify the event.</p>\n') if 'dakar' in (published or []) else ''
    ufc_lic = ('<h3 id="ufc">UFC</h3>\n' + src('Wikipedia', 'https://en.wikipedia.org/wiki/List_of_UFC_events', 'Creative Commons Attribution-ShareAlike 4.0 (Wikipedia contributors): attribution and share-alike, both given.', 'every past event in the list of UFC events and each event’s own article — the results table (weight class, fighters, result, method, round, time, notes), the infobox (date, venue, city, attendance) and the bonus awards. Nothing is taken from the promotion’s own site or its statistics partner.', 'CC BY-SA 4.0') + src('Wikidata', 'https://www.wikidata.org/', 'CC0 1.0.', 'fighter nationality, date of birth and height, where the fighter has an article.', 'CC0 1.0') + '<p><b>The data file <code>/data/ufc.json</code></b> is CC BY-SA 4.0: attribute Wikipedia contributors and share alike. No logos, marks or official artwork are included; the promotion’s names appear only to identify the events.</p>\n') if 'ufc' in (published or []) else ''
    body = f'''<p class="eyebrow">Sources and licences</p><h1>Where the numbers <span>come from</span></h1>
<p class="lede">Every atlas is built from sources that state their terms, or from facts that belong to no one. This page lists each source, the terms it publishes, and the licence that applies to each data file this site serves. The site itself is <b>non-commercial for good</b>: two of its backbone sources permit nothing else, and the rest are honoured in the same spirit. Checked 29 September 2026.</p>
<div class="lic">
<h3>The site’s own commitments</h3>
<p>{NOTICE}</p>
<p>The page code is released under the MIT licence (see the repository). Fonts are served from Google Fonts under the SIL Open Font License. No logos are used anywhere; team, national and manufacturer colours are editorial interpretations of racing and playing identities.</p>

<h3 id="f1">Formula 1</h3>
{src('F1DB', 'https://github.com/f1db/f1db', 'Creative Commons Attribution 4.0 (CC BY 4.0).', 'circuit outlines (the white survey SVGs), track specifications, supplementary fastest laps.', 'CC BY 4.0')}
{src('Jolpica F1 (Ergast-compatible API)', 'https://github.com/jolpica/jolpica-f1', 'Data under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0); the API is free for non-commercial use.', 'race results, sprint results, championship standings.', 'CC BY-NC-SA 4.0')}
{src('Wikipedia', 'https://en.wikipedia.org/', 'Text and tables under CC BY-SA 4.0; the facts are free.', 'reference links from each race and circuit.')}
{src('Formula1.com', 'https://www.formula1.com/', 'Reference only; nothing is reproduced.', 'links for historical cross-checks and era notes.')}
<p><b>The data file <code>/data/f1.json</code></b> is therefore offered under <b>CC BY-NC-SA 4.0</b>: attribute F1DB and Jolpica, use it non-commercially, and share any derivative under the same licence.</p>

{dakar_lic}
<h3 id="rugby">Rugby union</h3>
{src('Nuck’s Rugby Archive', 'https://rugbyarchive.github.io/about.html', 'An independent hobby archive that states no licence. Match results are facts; the compilation is the author’s work and is used with credit while permission is sought.', 'the ten nations’ international match archive.')}
{src('Springbok Rugby History (bokhist.com)', 'https://bokhist.com/', 'A private South African archive that states no licence; used with credit while permission is sought.', 'the Springbok match record, player histories and World Cup squads.')}
{src('Pick & Go', 'https://www.lassen.co.nz/pickandgo.php', 'Public results tables, used only as a cross-check.', 'verification of recent results.')}
{src('Wikipedia', 'https://en.wikipedia.org/', 'CC BY-SA 4.0.', 'national-team coaching lists.')}
<p><b>The data file <code>/data/rugby.json</code></b> carries no licence for reuse: the scores are facts anyone may use, but the compilations behind them belong to their authors, who are credited on the atlas.</p>

<h3 id="motogp">MotoGP, World Superbike and the Isle of Man TT</h3><span id="sbk"></span><span id="tt"></span>
{src('Wikipedia', 'https://en.wikipedia.org/', 'Creative Commons Attribution-ShareAlike 4.0 (Wikipedia contributors): attribution and share-alike, both given.', 'every result, calendar and published standing of the premier-class world championship (1949 on) and the Superbike World Championship (1988 on), transcribed from the English season articles; every Isle of Man TT winner and classification, transcribed from the German list of TT winners and the English race and year articles. Each race links to the article it came from and the data files record every page’s revision, retrieval date and hash. Nothing from the series’ own results services or artwork is carried.', 'CC BY-SA 4.0')}
{src('Wikidata', 'https://www.wikidata.org/', 'CC0 1.0.', 'circuit coordinates and countries.', 'CC0 1.0')}
{src('OpenStreetMap', 'https://www.openstreetmap.org/copyright', '© OpenStreetMap contributors, Open Database License 1.0.', 'circuit outlines (the mapped raceway around each venue) and the Snaefell Mountain Course with its named places (relation 188240).', 'ODbL 1.0')}
{src('F1DB', 'https://github.com/f1db/f1db', 'CC BY 4.0.', 'circuit surveys at venues Formula 1 has raced, used where OpenStreetMap has no raceway mapped.', 'CC BY 4.0')}
<p><b>The data files <code>/data/motogp.json</code>, <code>/data/sbk.json</code> and <code>/data/tt.json</code></b> are CC BY-SA 4.0: attribute Wikipedia contributors and share alike; the geometry inside them is ODbL. No logos, marks or official artwork are included.</p>

{ufc_lic}
<h3 id="cricket">Cricket</h3>
{src('Cricsheet', 'https://cricsheet.org/', 'Open Data Commons Attribution License (ODC-By 1.0): attribution required, which this page and the atlas give.', 'ball-by-ball scorecards of every international it covers (men’s Tests and ODIs from 2001–02, T20Is from 2005, the women’s game from its first recorded matches); the innings worms, and every batting, bowling and line-up figure of those matches, are computed from them.', 'ODC-By 1.0')}
{src('Historical results (Kaggle: “Cricket match dataset, Test nations 1877–2025”, Qammar Shahzad)', 'https://www.kaggle.com/datasets/qammarshahzad/cricket-match-dataset-test-nations-18772025', 'Match results are facts; the compilation is credited here and its own licence is stated on its Kaggle page.', 'dates, sides, results and margins of internationals before the Cricsheet era.')}
{src('International Cricket Council', 'https://www.icc-cricket.com/', 'Published results of ICC events, used as facts.', 'World Cup, T20 World Cup, Champions Trophy and World Test Championship winners, runners-up and finals.')}
{src('Historical scorecards (Hugging Face: “Test cricket dataset 1877–2014”, “ODI cricket dataset 1971–2014”, “T20I cricket dataset 2005–2014”, Bhuvanesh Prasad)', 'https://huggingface.co/bhuvaneshprasad', 'No licence is stated on the datasets; the figures in a scorecard are facts. Credited here and on every scorecard they supply; no licence is granted for those parts.', 'batting, bowling, dismissals, extras and line-ups of 3,934 internationals before Cricsheet’s coverage, each read at a recorded dataset revision and checked against its result and innings totals.', 'no licence stated')}
{src('Cricbuzz scorecards', 'https://www.cricbuzz.com/', 'No reuse licence is established; the figures are facts. Credited on each of the 54 scorecards it supplies, with a link to the page it was read from.', 'the scorecards of 54 internationals the datasets above lack or hold incompletely.', 'no licence stated')}
{src('Wikipedia national player lists', 'https://en.wikipedia.org/wiki/Lists_of_cricketers', 'Creative Commons Attribution-ShareAlike 4.0 (Wikipedia contributors): attribution and share-alike, both given.', 'the published career of every Test and ODI player (74 lists, each at a recorded revision) and the full names of players the scorecards know by initials.', 'CC BY-SA 4.0')}
{src('Wikidata', 'https://www.wikidata.org/', 'CC0 1.0.', 'full names confirmed by a stable Cricinfo identifier.', 'CC0 1.0')}
{src('CricketWeb', 'https://www.cricketweb.net/statsspider/', 'Used only to cross-check; nothing is taken.', 'an independent check of the first fifty Test scorecards.')}
<p><b>The data files <code>/data/cricket.json</code> and <code>/data/cricket_details/</code></b>: the Cricsheet-derived parts are ODC-By 1.0 (attribute Cricsheet); the published career register and the names drawn from Wikipedia are CC BY-SA 4.0 (attribute Wikipedia contributors, share alike); the historical results and the historical scorecards are facts compiled from the sources above, credited, with no licence granted for them. No logos or marks are included.</p>

<h3 id="tennis">Tennis</h3>
{src('Jeff Sackmann / Tennis Abstract', 'https://github.com/JeffSackmann', 'Creative Commons Attribution-NonCommercial-ShareAlike 4.0: attribution, no commercial use, share alike. This site is non-commercial and shares its data files under the same terms.', 'every tour-level match of the ATP and WTA from 1968 — results, seedings, rankings, durations and serve statistics — from the tennis_atp and tennis_wta repositories.', 'CC BY-NC-SA 4.0')}
{src('The Wimbledon Compendium', 'https://www.wimbledon.com/', 'The club’s published roll of honour, used as facts.', 'champions and finalists at Wimbledon before 1968.')}
<p><b>The data files <code>/data/tennis.json</code> and <code>/data/tennis_matches/</code></b> are CC BY-NC-SA 4.0: attribute Jeff Sackmann / Tennis Abstract, no commercial use, share alike. No logos or marks are included; tournament names appear only to identify the events.</p>

<h3>In preparation</h3>
{src('FiveThirtyEight', 'https://github.com/fivethirtyeight/data', 'CC BY 4.0.', 'historical NBA/BAA game results and Elo (basketball).', 'CC BY 4.0')}
<p>Basketball box scores are facts recorded from public sources; the atlas will name its sources and their terms here when it is published.</p>

<h3 id="updates">How the archives stay current</h3>
<p>Each atlas is extended by a small reader that runs on a schedule in the site’s public repository. It reads only the source already credited above for that atlas — Jolpica for Formula 1; the English Wikipedia articles through the MediaWiki API for MotoGP, World Superbike, UFC, the Isle of Man TT and the Dakar Rally; Cricsheet for cricket; Jeff Sackmann’s repositories for tennis; and, once permission is given, the data file Nuck’s Rugby Archive publishes for its own pages. Each run makes a handful of requests, pauses between them and names this site in its user agent. Before it writes anything, a reader must reproduce what the archive already holds from that source; results before the current season are never rewritten. Anything a reader adds carries the same licence as the rest of that data file.</p>

<h3>The data files</h3>
<p>Each atlas serves its archive as one JSON file, under the licence stated above: {' · '.join(f'<a class="q" href="{rel}data/{k}.json">{k}.json</a>' for k in SPORTS if k in (published or []))}.</p>

<h3>Trademarks</h3>
<p>Formula 1, F1, Grand Prix, MotoGP, WorldSBK, Isle of Man TT, TT, UFC, Dakar, Dakar Rally, Rugby World Cup, Springboks, All Blacks, ICC, Cricket World Cup, ATP, WTA, Wimbledon, Roland-Garros and every other championship, team, event, venue and manufacturer name on this site are the trademarks of their respective owners. They appear here only to identify what the numbers describe. This site is an independent, fan-made record; it is not affiliated with, sponsored by or endorsed by any rights holder, federation, union, league or team.</p>
</div>'''
    return sitegen_page(site=site, v=v, body=body, published=published)
DATASETS = {
    'cricket': ('Cricket internationals 1877–2026', 'Every men’s and women’s international with its result and scorecard — ball by ball from Cricsheet from the 2000s, historical scorecards before that — plus the published career of every Test and ODI player.', 'https://opendatacommons.org/licenses/by/1-0/', '1877/2026', ['Cricsheet', 'Qammar Shahzad (Kaggle)', 'Bhuvanesh Prasad (Hugging Face)', 'Cricbuzz', 'Wikipedia contributors']),
    'dakar': ('Dakar Rally editions and class podiums 1979–2026', 'Every edition’s route, era and the first three of every class, transcribed from Wikipedia; Natural Earth land silhouette for the route maps.', 'https://creativecommons.org/licenses/by-sa/4.0/', '1979/2026', ['Wikipedia contributors', 'Natural Earth']),
    'f1': ('Formula 1 results and standings 1950–2026', 'Every Grand Prix and sprint result, championship standings, circuit outlines and specifications.', 'https://creativecommons.org/licenses/by-nc-sa/4.0/', '1950/2026', ['Jolpica F1', 'F1DB']),
    'motogp': ('MotoGP premier-class results 1949–2026', 'Every premier-class race result, calendar and published standing, transcribed from Wikipedia; circuit outlines from OpenStreetMap.', 'https://creativecommons.org/licenses/by-sa/4.0/', '1949/2026', ['Wikipedia contributors', 'OpenStreetMap contributors']),
    'rugby': ('Rugby union Test matches of ten nations 1871–2026', 'Every Test match of the ten nations with scores, grounds, published careers and coaching records.', None, '1871/2026', ['Nuck’s Rugby Archive', 'Springbok Rugby History']),
    'sbk': ('World Superbike results 1988–2026', 'Every Superbike World Championship race result and standing, transcribed from Wikipedia; circuit outlines from OpenStreetMap.', 'https://creativecommons.org/licenses/by-sa/4.0/', '1988/2026', ['Wikipedia contributors', 'OpenStreetMap contributors']),
    'tennis': ('Tennis titles and tour-level matches 1877–2026', 'Every tour-level ATP and WTA match from 1968 and every major and tour title from 1877.', 'https://creativecommons.org/licenses/by-nc-sa/4.0/', '1877/2026', ['Jeff Sackmann / Tennis Abstract']),
    'tt': ('Isle of Man TT winners and classifications 1907–2026', 'Every TT race with its winner, machine, course and race average, and the classifications where the sources hold them.', 'https://creativecommons.org/licenses/by-sa/4.0/', '1907/2026', ['Wikipedia contributors', 'OpenStreetMap contributors']),
    'ufc': ('UFC bouts and events 1993–2026', 'Every UFC event and bout with result, method, round, time, venue and bonus awards, transcribed from Wikipedia.', 'https://creativecommons.org/licenses/by-sa/4.0/', '1993/2026', ['Wikipedia contributors', 'Wikidata']),
}
def datasets_ld(site, published):
    """One schema.org Dataset per published data file, so the archives are findable in Google Dataset Search; the licences page is the landing page."""
    out = []
    for k in SPORTS:
        if k not in published or k not in DATASETS: continue
        name, desc, lic, span, creators = DATASETS[k]
        d = {'@type': 'Dataset', 'name': name, 'description': desc, 'url': f'{site}/licences/#{k}', 'sameAs': f'{site}/{k}/', 'temporalCoverage': span, 'isAccessibleForFree': True, 'creator': [{'@type': 'Organization', 'name': c} for c in creators], 'publisher': {'@type': 'Organization', 'name': SITE_NAME, 'url': f'{site}/'},
             'distribution': [{'@type': 'DataDownload', 'encodingFormat': 'application/json', 'contentUrl': f'{site}/data/{k}.json'}]}
        if lic: d['license'] = lic
        out.append(d)
    return out

def sitegen_page(*, site, v, body, published):
    return page(site=site, sport=None, depth=1, title='Sources and licences · APEX sports atlases', desc='Every source behind the atlases at sportsfans.co.za, the terms it publishes, and the licence that applies to each data file.', crumbs=[('Sportsfans', '../'), ('Sources and licences', None)], body=body, path='licences/', v=v, published=published, extra_head='\n' + ld_json(*datasets_ld(site, published or [])))

# ============================================================ Cricket ============================================================
def gen_cricket(A, *, site, v):
    out = []; T = A['teams']; V = A['venues']; P = A['players']; games = A['games']
    col = lambda t: T.get(t, {}).get('c', '#8b9099')
    nl = lambda n, rel: f'<i class="dot" style="--c:{col(n)}"></i><a class="q" href="{rel}cricket/teams/{slug(n)}/">{E(n)}</a>'
    gl = lambda vid, rel: (f'<a class="q" href="{rel}cricket/grounds/{vid}/">{E(V[vid]["n"])}</a>' if vid and vid in V else '<span class="D">not recorded</span>')
    pl = lambda pid, rel: f'<a class="q" href="{rel}cricket/players/{pid}/">{E(P.get(pid, {}).get("n", pid))}</a>'
    ml = lambda g, rel: f'<a class="q" href="{rel}cricket/#gender={g["g"]}&match={g["id"]}&tab=match">{E(g["date"])}</a>'
    scs = lambda g, t: ' & '.join(('forfeited' if i[5] else f"{i[1]}{'/' + str(i[2]) if i[2] < 10 else ''}{'d' if i[4] else ''}") for i in g.get('sc', []) if i[0] == t and not i[6])
    res = lambda g: 'No result' if g['result'] == 'no result' else 'Tied' if g['result'] == 'tie' else 'Drawn' if g['result'] == 'draw' else (f"{g['winner']} won by {g['margin']}" if g.get('margin') else f"{g['winner']} won")
    rc = lambda g, t: 'N' if g['result'] == 'no result' else 'D' if g['result'] in ('draw', 'tie') else ('W' if g['winner'] == t else 'L')
    grow = lambda g, rel: [ml(g, rel), E(g['f']) + (' (W)' if g['g'] == 'W' else ''), f'{nl(g["teams"][0], rel)} v {nl(g["teams"][1], rel)}', E(scs(g, g['teams'][0])) + (' · ' if scs(g, g['teams'][0]) and scs(g, g['teams'][1]) else '') + E(scs(g, g['teams'][1])), E(res(g)), gl(g.get('v'), rel)]
    def rec(ms, t):
        w = sum(1 for g in ms if rc(g, t) == 'W'); l = sum(1 for g in ms if rc(g, t) == 'L'); d = sum(1 for g in ms if rc(g, t) == 'D'); n = len(ms) - w - l - d; return w, l, d, n
    years = sorted({g['y'] for g in games}); by_year = collections.defaultdict(list)
    for g in games: by_year[g['y']].append(g)
    PSF = A['psFields']; PS = [dict(zip(PSF, r)) for r in A['ps']]
    # seasons
    for y in years:
        rel = '../../../'; ms = by_year[y]; men = [g for g in ms if g['g'] == 'M']; women = [g for g in ms if g['g'] == 'W']
        st = []
        for t in sorted({t for g in ms for t in g['teams']}):
            for gen in ('M', 'W'):
                mine = [g for g in ms if t in g['teams'] and g['g'] == gen]
                if mine: w, l, d, n = rec(mine, t); st.append((t, gen, len(mine), w, l, d, n, pct(w, len(mine))))
        cups = [c for c in A['champions'] if c['y'] == y]
        prev = y - 1 if y - 1 in by_year else None; nxt = y + 1 if y + 1 in by_year else None
        body = f'''<p class="eyebrow">Cricket · Season</p><h1>{y} <span>internationals</span></h1>
<p class="lede">{len(ms)} internationals{f': {len(men)} men’s and {len(women)} women’s' if women else ''}.{''.join(f' <b>{E(c["w"][0] if len(c["w"]) == 1 else " & ".join(c["w"]))}</b> won the {E(c["label"])}{" (" + E(c["note"]) + ")" if c.get("note") else ""}.' for c in cups)}</p>
<a class="open" href="{rel}cricket/#season={y}&tab=season">Open {y} in the atlas →</a>{f'<a class="also" href="{rel}cricket/seasons/{prev}/">← {prev}</a>' if prev else ''}{f'<a class="also" href="{rel}cricket/seasons/{nxt}/">{nxt} →</a>' if nxt else ''}
{kpis([('Matches', len(ms), ''), ('Tests', sum(1 for g in ms if g['f'] == 'Test'), ''), ('ODIs', sum(1 for g in ms if g['f'] == 'ODI'), ''), ('T20Is', sum(1 for g in ms if g['f'] == 'T20I'), ''), ('Sides', len({t for g in ms for t in g['teams']}), '')])}
<h2>Table of the year <small>every side, by win rate</small></h2>{table(['Side', 'Game', 'P', 'W', 'L', 'D/T', 'NR', 'Win %'], [[nl(t, rel), 'Men' if gen == 'M' else 'Women', p_, w, l, d, n, r] for t, gen, p_, w, l, d, n, r in sorted(st, key=lambda x: (x[1], -x[7], -x[3]))], num=(2, 3, 4, 5, 6, 7))}
<h2>Every match</h2>{table(['Date', 'Format', 'Sides', 'Scores', 'Result', 'Ground'], [grow(g, rel) for g in ms])}'''
        out.append((f'cricket/seasons/{y}/index.html', page(site=site, sport='cricket', depth=3, title=f'{y} international cricket · every Test, ODI and T20I · APEX', desc=f'All {len(ms)} internationals of {y} with results, innings totals and grounds, plus the table of the year.', crumbs=[('Sportsfans', rel), ('Cricket', rel + 'cricket/'), ('Seasons', rel + 'cricket/seasons/'), (str(y), None)], body=body, path=f'cricket/seasons/{y}/', v=v)))
    # teams
    sides = sorted({t for g in games for t in g['teams']})
    for t in sides:
        rel = '../../../'; mine = [g for g in games if t in g['teams']]
        if not mine: continue
        info = T.get(t, {}); ys = sorted({g['y'] for g in mine})
        parts = []
        for gen in ('M', 'W'):
            for f in ('Test', 'ODI', 'T20I'):
                ms = [g for g in mine if g['g'] == gen and g['f'] == f]
                if ms: w, l, d, n = rec(ms, t); parts.append([('Men' if gen == 'M' else 'Women'), f, len(ms), w, l, d, n, pct(w, len(ms)), f'{min(g["y"] for g in ms)}–{max(g["y"] for g in ms)}'])
        opp = collections.defaultdict(list)
        for g in mine: opp[g['teams'][1] if g['teams'][0] == t else g['teams'][0]].append(g)
        opprows = sorted([[nl(o, rel), len(ms), *rec(ms, t), pct(rec(ms, t)[0], len(ms))] for o, ms in opp.items()], key=lambda r: -r[1])
        cups = [c for c in A['champions'] if t in c['w']]
        w_all, l_all, d_all, n_all = rec(mine, t)
        topp = sorted([p for p in PS if p['t'] == t], key=lambda p: -p['runs'])[:12]
        cuptxt = (' ICC titles: ' + ', '.join(c['label'] + ' ' + str(c['y']) for c in cups) + '.') if cups else ''
        body = f'''<p class="eyebrow">Cricket · {'Full member' if info.get('major') else 'Side'} · {ys[0]}–{ys[-1]}{' · ' + E(info['abbr']) if info.get('abbr') else ''}</p><h1><i class="dot" style="--c:{col(t)};width:.5em;height:.5em;border-radius:6px;vertical-align:.15em"></i>{E(t)}</h1>
<p class="lede">{len(mine)} internationals against {len(opp)} opponents: {w_all} won, {l_all} lost, {d_all} drawn or tied, {n_all} without a result.{cuptxt}</p>
<a class="open" href="{rel}cricket/#tab=nations&nation={E(t)}">Open in the atlas →</a>
{kpis([('Matches', len(mine), f'{w_all}–{l_all}–{d_all}'), ('Win rate', f'{pct(w_all, len(mine))}%', 'draws and no-results count as not won'), ('ICC titles', len(cups), '')])}
<h2>By game and format</h2>{table(['Game', 'Format', 'P', 'W', 'L', 'D/T', 'NR', 'Win %', 'Years'], parts, num=(2, 3, 4, 5, 6, 7))}
<div class="two"><div><h2>Record by opponent</h2>{table(['Opponent', 'P', 'W', 'L', 'D/T', 'NR', 'Win %'], opprows, num=(1, 2, 3, 4, 5, 6))}</div><div>{('<h2>Run-scorers <small>recorded player-seasons</small></h2><div class="chips">' + ''.join(f'<a class="chip" href="{rel}cricket/players/{p["p"]}/"><i style="--c:{col(t)}"></i>{E(P.get(p["p"], {}).get("n", p["p"]))} <span style="color:var(--muted)">{p["runs"]} · {p["y"]} {p["f"]}</span></a>' for p in topp) + '</div>') if topp else ''}</div></div>
<h2>Every match <small>{len(mine)}</small></h2>{table(['Date', 'Format', 'Sides', 'Scores', 'Result', 'Ground'], [grow(g, rel) for g in reversed(mine)])}'''
        out.append((f'cricket/teams/{slug(t)}/index.html', page(site=site, sport='cricket', depth=3, title=f'{t} · every international, record by opponent · APEX', desc=f'{t} in international cricket, {ys[0]}–{ys[-1]}: {len(mine)} matches, {w_all} won; by format and by opponent.', crumbs=[('Sportsfans', rel), ('Cricket', rel + 'cricket/'), ('Teams', rel + 'cricket/teams/'), (t, None)], body=body, path=f'cricket/teams/{slug(t)}/', v=v)))
    # players: those with recorded figures, and those known only by a published career
    by_p = collections.defaultdict(list)
    for r in PS: by_p[r['p']].append(r)
    CF = A.get('careerFields'); CAR = collections.defaultdict(list); CSRC = A.get('careerSources') or []
    for c in (A.get('careers') or []): c = dict(zip(CF, c)) if CF else c; CAR[c['p']].append(c)
    def career_table(pid, rel):
        cs = sorted(CAR.get(pid, []), key=lambda c: (c['first'], c['f']))
        if not cs: return ''
        cv = lambda x: '—' if x is None or x == '' else (fmt(x) if isinstance(x, int) else E(str(x)))
        av = lambda x: '—' if x is None else f'{x:.2f}'
        srcs = [CSRC[i] for i in dict.fromkeys(c['source'] for c in cs) if isinstance(i, int) and i < len(CSRC)]
        links = ', '.join(f'<a href="{E("https://en.wikipedia.org/w/index.php?title=" + urllib.parse.quote(s_["slug"]) + "&oldid=" + s_["revision"] if s_.get("revision") else s_["url"])}" target="_blank" rel="noopener">{E(s_["t"])} {"women’s " if s_["g"] == "W" else ""}{E(s_["f"])} players</a>' for s_ in srcs)
        return ('<h2>Published career <small>as the national player lists give it</small></h2>' + table(['Team', 'Format', 'Years', 'Cap', 'M', 'Runs', 'Avg', 'HS', 'Wkts', 'Avg', 'BB', 'Ct/St'],
                [[(nl(c['t'], rel) if c['t'] in sides else f'<i class="dot" style="--c:{col(c["t"])}"></i>{E(c["t"])}'), c['f'] + (' (W)' if c['g'] == 'W' else ''), f"{c['first']}–{'' if c.get('ongoing') else c['last']}", cv(c.get('cap')), cv(c.get('games')), cv(c.get('runs')), av(c.get('batavg')), cv(c.get('hs')), cv(c.get('wickets')), av(c.get('bowlavg')), cv(c.get('best')), f"{cv(c.get('catches'))}/{cv(c.get('stumps'))}"] for c in cs], num=(4, 5, 6, 8, 9))
                + f'<p class="lede" style="font-size:12px">From {links} (Wikipedia contributors, <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a>), shown as published; never added to the recorded figures.</p>')
    ext = lambda info: ' · '.join(x for x in ((f'<a href="https://www.espncricinfo.com/cricketers/{E(info["espn"])}" target="_blank" rel="noopener">Cricinfo profile ↗</a>' if info.get('espn') else ''), (f'<a href="https://en.wikipedia.org/wiki/{E(urllib.parse.quote(info["wiki"]))}" target="_blank" rel="noopener">Wikipedia ↗</a>' if info.get('wiki') else '')) if x)
    full = lambda info: (E(info['fullName']) + ' · ') if info.get('fullName') and info['fullName'] != info.get('n') else ''
    for pid, rows in by_p.items():
        rel = '../../../'; info = P.get(pid, {}); rows.sort(key=lambda r: (r['y'], r['f']))
        runs = sum(r['runs'] for r in rows); outs = sum(r['outs'] for r in rows); wk = sum(r['wickets'] for r in rows); conc = sum(r['conceded'] for r in rows); gm = sum(r['games'] for r in rows)
        hs = max(rows, key=lambda r: (r['hs'], r['hsno'])); team = collections.Counter(r['t'] for r in rows).most_common(1)[0][0]
        body = f'''<p class="eyebrow">Cricket · Player · {nl(team, rel)} · {rows[0]['y']}–{rows[-1]['y']}</p><h1>{E(info.get('n', pid))}</h1>
<p class="lede">{full(info)}{E(info.get('short', ''))} · recorded figures from {gm} internationals with scorecards ({rows[0]['y']}–{rows[-1]['y']}), added up from the cards.</p>
<a class="open" href="{rel}cricket/#tab=players&player={pid}">Open in the atlas →</a>
{kpis([('Matches', gm, 'with recorded figures'), ('Runs', fmt(runs), f'avg {round(runs / outs, 2) if outs else "—"}'), ('Highest', f'{hs["hs"]}{"*" if hs["hsno"] else ""}', f'{sum(r["hundreds"] for r in rows)} hundreds · {sum(r["fifties"] for r in rows)} fifties'), ('Wickets', wk, f'avg {round(conc / wk, 2) if wk else "—"}'), ('Catches', sum(r['catches'] for r in rows), f'{sum(r["stumps"] for r in rows)} stumpings')])}
<h2>Season by season</h2>{table(['Year', 'Format', 'Team', 'M', 'Inns', 'Runs', 'Avg', 'HS', '100/50', 'Wkts', 'Avg', 'BB', 'Ct'], [[f'<a class="q" href="{rel}cricket/seasons/{r["y"]}/">{r["y"]}</a>', r['f'] + (' (W)' if r['g'] == 'W' else ''), nl(r['t'], rel), r['games'], r['inns'], r['runs'], round(r['runs'] / r['outs'], 1) if r['outs'] else '—', f'{r["hs"]}{"*" if r["hsno"] else ""}', f'{r["hundreds"]}/{r["fifties"]}', r['wickets'], round(r['conceded'] / r['wickets'], 1) if r['wickets'] else '—', f'{r["bbw"]}/{r["bbr"]}' if r['bbw'] else '—', r['catches']] for r in reversed(rows)], num=(3, 4, 5, 6, 9, 10, 12))}
{career_table(pid, rel)}
{f'<p class="lede" style="font-size:12px">{ext(info)}</p>' if ext(info) else ''}'''
        out.append((f'cricket/players/{pid}/index.html', page(site=site, sport='cricket', depth=3, title=f'{info.get("n", pid)} · recorded international figures · APEX', desc=f'{info.get("n", pid)} ({team}): {fmt(runs)} runs and {wk} wickets in {gm} recorded internationals, season by season.', crumbs=[('Sportsfans', rel), ('Cricket', rel + 'cricket/'), ('Players', rel + 'cricket/players/'), (info.get('n', pid), None)], body=body, path=f'cricket/players/{pid}/', v=v, noindex=(gm < 3))))
    only = {pid: cs for pid, cs in CAR.items() if pid not in by_p and pid in P}
    for pid, cs in only.items():
        rel = '../../../'; info = P[pid]; team = max(cs, key=lambda c: c.get('games') or 0)['t']; y0 = min(c['first'] for c in cs); y1 = max(c['last'] for c in cs)
        gm = sum(c.get('games') or 0 for c in cs)
        tl = nl(team, rel) if team in sides else f'<i class="dot" style="--c:{col(team)}"></i>{E(team)}'
        body = f'''<p class="eyebrow">Cricket · Player · {tl} · {y0}–{y1}</p><h1>{E(info.get('n', pid))}</h1>
<p class="lede">{full(info)}{'women’s' if 'W' in (info.get('gender') or []) else 'men’s'} internationals · no scorecard of this career is in the archive (it holds the women’s game from its first recorded scorecards), so the published career is the record here.</p>
<a class="open" href="{rel}cricket/#tab=players&player={pid}">Open in the atlas →</a>
{career_table(pid, rel)}
{f'<p class="lede" style="font-size:12px">{ext(info)}</p>' if ext(info) else ''}'''
        out.append((f'cricket/players/{pid}/index.html', page(site=site, sport='cricket', depth=3, title=f'{info.get("n", pid)} · published international career · APEX', desc=f'{info.get("n", pid)} ({team}), {y0}–{y1}: {gm} internationals in the published career.', crumbs=[('Sportsfans', rel), ('Cricket', rel + 'cricket/'), ('Players', rel + 'cricket/players/'), (info.get('n', pid), None)], body=body, path=f'cricket/players/{pid}/', v=v, noindex=(gm < 3))))
    # grounds
    by_v = collections.defaultdict(list)
    for g in games:
        if g.get('v') and g['v'] in V: by_v[g['v']].append(g)
    for vid, ms in by_v.items():
        rel = '../../../'; vi = V[vid]; ys = sorted({g['y'] for g in ms}); wins = collections.Counter(g['winner'] for g in ms if g['winner'])
        body = f'''<p class="eyebrow">Cricket · Ground{' · ' + E(vi['city']) if vi.get('city') else ''}{' · recorded as a city only' if vi.get('locationOnly') else ''}</p><h1>{E(vi['n'])}</h1>
<p class="lede">{len(ms)} internationals, {ys[0]}–{ys[-1]}.{f' Most wins here: <b>{E(wins.most_common(1)[0][0])}</b> ({wins.most_common(1)[0][1]}).' if wins else ''}</p>
<a class="open" href="{rel}cricket/#tab=grounds&ground={vid}">Open in the atlas →</a>
{kpis([('Matches', len(ms), f'{ys[0]}–{ys[-1]}'), ('Tests', sum(1 for g in ms if g['f'] == 'Test'), ''), ('ODIs', sum(1 for g in ms if g['f'] == 'ODI'), ''), ('T20Is', sum(1 for g in ms if g['f'] == 'T20I'), ''), ('Sides', len({t for g in ms for t in g['teams']}), '')])}
{('<h2>Most wins here</h2>' + table(['Side', 'Wins'], [[nl(t, rel), n] for t, n in wins.most_common(8)], num=(1,))) if wins else ''}
<h2>Every match here</h2>{table(['Date', 'Format', 'Sides', 'Scores', 'Result', 'Ground'], [grow(g, rel) for g in reversed(ms)])}'''
        out.append((f'cricket/grounds/{vid}/index.html', page(site=site, sport='cricket', depth=3, title=f'{vi["n"]} · every international played there · APEX', desc=f'{vi["n"]}{", " + vi["city"] if vi.get("city") else ""}: {len(ms)} internationals from {ys[0]} to {ys[-1]}.', crumbs=[('Sportsfans', rel), ('Cricket', rel + 'cricket/'), ('Grounds', rel + 'cricket/grounds/'), (vi['n'], None)], body=body, path=f'cricket/grounds/{vid}/', v=v)))
    rel = '../../'
    out.append(('cricket/seasons/index.html', page(site=site, sport='cricket', depth=2, title='International cricket, year by year, 1877–2026 · APEX', desc='Every year of international cricket on its own page.', crumbs=[('Sportsfans', rel), ('Cricket', rel + 'cricket/'), ('Seasons', None)], body=f'<p class="eyebrow">Cricket</p><h1>Every <span>year</span></h1><p class="lede">{len(years)} years with internationals.</p>' + index_list([(str(y), f'cricket/seasons/{y}/', f'{len(by_year[y])} matches') for y in reversed(years)], rel), path='cricket/seasons/', v=v)))
    out.append(('cricket/teams/index.html', page(site=site, sport='cricket', depth=2, title='Cricket teams · APEX', desc='Every side in the international archive.', crumbs=[('Sportsfans', rel), ('Cricket', rel + 'cricket/'), ('Teams', None)], body=f'<p class="eyebrow">Cricket</p><h1>Every <span>side</span></h1>' + index_list(sorted([(t, f'cricket/teams/{slug(t)}/', f'{sum(1 for g in games if t in g["teams"])} matches') for t in sides]), rel), path='cricket/teams/', v=v)))
    out += index_pages(site=site, sport='cricket', title='Cricket players · APEX', desc='Every player with recorded international figures.', crumbs=[('Sportsfans', rel), ('Cricket', rel + 'cricket/'), ('Players', None)], intro=f'<p class="eyebrow">Cricket</p><h1>Every <span>player</span></h1><p class="lede">{len(by_p):,} players with recorded figures from the scorecards (men’s Tests from 1877, ODIs from 1971, T20Is and the women’s game from their first recorded cards){f", and {len(only):,} known by their published careers" if only else ""}.</p>', items=sorted([(P.get(pid, {}).get('n', pid), f'cricket/players/{pid}/', f'{sum(r["runs"] for r in rows)} runs · {sum(r["wickets"] for r in rows)} wkts') for pid, rows in by_p.items()] + [(P[pid].get('n', pid), f'cricket/players/{pid}/', f'published career · {sum(c.get("games") or 0 for c in cs)} matches') for pid, cs in only.items()], key=lambda t: (t[0].split(' ')[-1], t[0], t[1])), dir='cricket/players', v=v)
    out.append(('cricket/grounds/index.html', page(site=site, sport='cricket', depth=2, title='Cricket grounds · APEX', desc='Every recorded international ground.', crumbs=[('Sportsfans', rel), ('Cricket', rel + 'cricket/'), ('Grounds', None)], body=f'<p class="eyebrow">Cricket</p><h1>Every <span>ground</span></h1><p class="lede">{len(by_v)} recorded grounds and cities.</p>' + index_list(sorted([(V[vid]['n'], f'cricket/grounds/{vid}/', f'{len(ms)} matches') for vid, ms in by_v.items()], key=lambda t: (t[0], t[1])), rel), path='cricket/grounds/', v=v)))
    return out

# ============================================================ Tennis ============================================================
def gen_tennis(A, *, site, v):
    out = []; P = A['players']; T = {k: dict(zip(A['tFields'], r)) for k, r in A['tournaments'].items()}; ED = {k: dict(zip(A['eFields'], r)) for k, r in A['editions'].items()}
    C = [dict(zip(A['cFields'], r)) for r in A['champions']]; PSF = A['psFields']; PS = [dict(zip(PSF, r)) for r in A['ps']]; IOC = A.get('ioc', {})
    NAT = {'USA':'#d62839','AUS':'#ffcc00','GBR':'#2c4ec7','FRA':'#7aa6ff','ESP':'#ff8c1a','GER':'#c9ccd1','FRG':'#c9ccd1','SWE':'#3ec6b8','ARG':'#9dd2f2','CZE':'#7b3fa0','TCH':'#7b3fa0','SUI':'#ff2e63','ITA':'#3aaa5c','RUS':'#c81e6e','URS':'#c81e6e','SRB':'#e8967a','BEL':'#b58900','NED':'#ff9e80','CRO':'#a8dadc','ROU':'#c5a3ff','POL':'#ff7b7b','JPN':'#f4f4f2','CAN':'#ff8a80','BRA':'#a4ff4f','CHN':'#ff5a36','RSA':'#0f9d58','NZL':'#9e9e9e'}
    SURF = {'Hard': '#3b82f6', 'Clay': '#d2622b', 'Grass': '#4caf50', 'Carpet': '#8b7bb5'}
    def hue(s):
        h = 0
        for ch in str(s or '?'): h = (h * 31 + ord(ch)) & 0xffffffff
        import colorsys; r, g, b = colorsys.hls_to_rgb((h % 360) / 360, .62, .45); return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
    ncol = lambda c: NAT.get(c) or hue(c)
    natn = lambda c: IOC.get(c, c or 'Unlisted')
    pnat = lambda pid: P.get(pid, {}).get('ioc', '')
    pn = lambda pid: P.get(pid, {}).get('n', pid)
    circ = {'MS': 'ATP singles', 'WS': 'WTA singles', 'MD': 'ATP doubles', 'WD': 'WTA doubles', 'XD': 'Mixed doubles'}
    tour = lambda c: 'W' if c[0] == 'W' else 'M'
    HAS_PAGE = set()
    pl = lambda pid, rel: f'<i class="dot" style="--c:{ncol(pnat(pid))}"></i>' + (f'<a class="q" href="{rel}tennis/players/{pid}/">{E(pn(pid))}</a>' if pid in HAS_PAGE else E(pn(pid)))
    pls = lambda ids, rel: ' / '.join(pl(p, rel) for p in (ids or [])) or '—'
    tl = lambda tid, rel: f'<a class="q" href="{rel}tennis/tournaments/{slug(tid)}/">{E(T.get(tid, {}).get("n", tid))}</a>'
    NAT_PAGE = {A['players'][p].get('ioc', '') for r in A['champions'] for p in dict(zip(A['cFields'], r))['w'] if p in A['players']}
    nl = lambda c, rel: f'<i class="dot" style="--c:{ncol(c)}"></i>' + (f'<a class="q" href="{rel}tennis/nations/{slug(c or "unlisted")}/">{E(natn(c))}</a>' if c in NAT_PAGE else E(natn(c)))
    el = lambda c, rel: (f'<a class="q" href="{rel}tennis/#tour={tour(c["c"])}{"&draw=D" if c["c"][1] == "D" else ""}&edition={c["id"]}&tab=draw">{c["y"]}</a>' if c['id'] in ED else str(c['y']))
    lvl = {'G': 'Grand Slam', 'M': 'Masters 1000', 'PM': 'Premier Mandatory', 'P': 'Premier', 'I': 'International', 'W': 'WTA Tour', 'A': 'Tour', 'F': 'Tour Finals', 'O': 'Olympic Games', 'T1': 'Tier I', 'T2': 'Tier II', 'T3': 'Tier III', 'T4': 'Tier IV', 'T5': 'Tier V', 'D': 'Team', 'CC': 'Team cup', 'E': 'Exhibition'}
    majors = [k for k, t in T.items() if t.get('major')]
    by_year = collections.defaultdict(list)
    for c in C: by_year[c['y']].append(c)
    for y in by_year: by_year[y].sort(key=lambda c: (ED.get(c['id'], {}).get('date', f'{c["y"]}-00'), c['c']))
    years = sorted(by_year)
    # per-player aggregates
    pagg = collections.defaultdict(lambda: {'w': 0, 'l': 0, 't': 0, 'f': 0, 'mj': 0, 'first': 9999, 'last': 0, 'rows': []})
    for r in PS:
        a = pagg[r['p']]; a['w'] += r['w']; a['l'] += r['l']; a['t'] += r['t']; a['f'] += r['f']; a['mj'] += r['mj']; a['first'] = min(a['first'], r['y']); a['last'] = max(a['last'], r['y']); a['rows'].append(r)
    titles_of = collections.defaultdict(list); finals_of = collections.defaultdict(list)
    for c in C:
        for p in c['w']: titles_of[p].append(c)
        for p in c['l']: finals_of[p].append(c)
    crow = lambda c, rel: [el(c, rel), E(ED.get(c['id'], {}).get('date', '')), tl(c['t'], rel), E(circ.get(c['c'], c['c'])), E(ED.get(c['id'], {}).get('surface') or T.get(c['t'], {}).get('s', '') or ''), pls(c['w'], rel), pls(c['l'], rel), E(c['s'])]
    CH = ['Year', 'Date', 'Tournament', 'Draw', 'Surface', 'Champion', 'Runner-up', 'Score']
    pids = sorted({p for p in titles_of} | {p for p, a in pagg.items() if a['w'] + a['l'] >= 50}); HAS_PAGE.update(pids)
    # seasons
    for y in years:
        rel = '../../../'; cs = by_year[y]; prev = y - 1 if y - 1 in by_year else None; nxt = y + 1 if y + 1 in by_year else None
        lead = collections.Counter(p for c in cs if c['c'] in ('MS', 'WS') for p in c['w']); top = lead.most_common(6)
        mj = [c for c in cs if c['t'] in majors]; eds = [e for e in ED.values() if e['y'] == y and not e['team'] and e['level'] != 'D']
        nat = collections.Counter(pnat(p) for c in cs for p in c['w'])
        body = f'''<p class="eyebrow">Tennis · Season</p><h1>{y} <span>on the tour</span></h1>
<p class="lede">{len(cs)} titles{f' across {len(eds)} tournaments' if eds else ' from Wimbledon’s records'}.{''.join(f' <b>{E(pn(c["w"][0]))}</b> won {E(T[c["t"]]["n"])} ({E(circ.get(c["c"], c["c"]))}).' for c in mj if len(c['w']) == 1)}</p>
<a class="open" href="{rel}tennis/#season={y}&tab=season">Open {y} in the atlas →</a>{f'<a class="also" href="{rel}tennis/seasons/{prev}/">← {prev}</a>' if prev else ''}{f'<a class="also" href="{rel}tennis/seasons/{nxt}/">{nxt} →</a>' if nxt else ''}
{kpis([('Titles', len(cs), ''), ('Majors', len(mj), ''), ('Tournaments', len(eds), 'with a draw' if eds else 'no draws before 1968'), ('Nations with a title', len([n for n in nat if n]), '')])}
{('<h2>Most titles <small>singles</small></h2><div class="chips">' + ''.join(f'<a class="chip" href="{rel}tennis/players/{p}/"><i style="--c:{ncol(pnat(p))}"></i>{E(pn(p))} <span style="color:var(--muted)">{n}</span></a>' for p, n in top) + '</div>') if top else ''}
<h2>Nations of the year</h2>{table(['Nation', 'Titles'], [[nl(n, rel), k] for n, k in nat.most_common(12) if n], num=(1,))}
<h2>Every title</h2>{table(CH, [crow(c, rel) for c in cs])}'''
        out.append((f'tennis/seasons/{y}/index.html', page(site=site, sport='tennis', depth=3, title=f'{y} tennis season · every title · APEX', desc=f'Every tour-level title of {y}: champion, finalist and score, with the majors and the nations of the year.', crumbs=[('Sportsfans', rel), ('Tennis', rel + 'tennis/'), ('Seasons', rel + 'tennis/seasons/'), (str(y), None)], body=body, path=f'tennis/seasons/{y}/', v=v)))
    # players: anyone with a title or 50+ recorded matches
    for pid in pids:
        rel = '../../../'; info = P.get(pid, {}); a = pagg.get(pid) or {'w': 0, 'l': 0, 't': 0, 'f': 0, 'mj': 0, 'first': None, 'last': None, 'rows': []}; ts = sorted(titles_of.get(pid, []), key=lambda c: (-c['y'], -int((ED.get(c['id'], {}).get('date') or '0000-00-00').replace('-', '') or 0), c['c'])); fl = finals_of.get(pid, [])
        nsing = sum(1 for c in ts if c['c'] in ('MS', 'WS')); ndbl = len(ts) - nsing; tsplit = f' ({nsing} singles, {ndbl} doubles)' if ndbl and nsing else ''
        mjb = collections.Counter(c['t'] for c in ts if c['t'] in majors); rows = sorted(a['rows'], key=lambda r: (-r['y'], r['c']))
        span = f"{min(a['first'] or 9999, *(c['y'] for c in ts)) if ts else a['first']}–{max(a['last'] or 0, *(c['y'] for c in ts)) if ts else a['last']}" if (ts or a['first']) else ''
        born = f"{info['dob'][6:8]}/{info['dob'][4:6]}/{info['dob'][0:4]}" if info.get('dob') and len(info['dob']) >= 8 else ''
        mjtxt = (', ' + str(sum(mjb.values())) + ' of them majors (' + ', '.join(T[t]['n'] + ' ' + str(n) for t, n in mjb.most_common()) + ')') if mjb else ''
        body = f'''<p class="eyebrow">Tennis · Player · {nl(pnat(pid), rel)}{' · ' + span if span else ''}{' · ' + ('left-handed' if info.get('hand') == 'L' else 'right-handed') if info.get('hand') in ('L', 'R') else ''}{' · born ' + E(born) if born else ''}</p><h1>{E(pn(pid))}</h1>
<p class="lede">{len(ts)} title{'' if len(ts) == 1 else 's'}{tsplit}{mjtxt}; {len(fl)} final{'' if len(fl) == 1 else 's'} lost.{f' Match record {a["w"]}–{a["l"]} at tour level from 1968.' if a['w'] + a['l'] else ' Match records begin in 1968.'}</p>
<a class="open" href="{rel}tennis/#tab=players&player={pid}">Open in the atlas →</a>
{kpis([('Titles', len(ts), ''), ('Majors', sum(mjb.values()), ''), ('Finals', len(ts) + len(fl), f'{len(fl)} lost'), ('Matches', f"{a['w']}–{a['l']}", f"{pct(a['w'], a['w'] + a['l'])}% won" if a['w'] + a['l'] else '')])}
{('<h2>Titles</h2>' + table(CH, [crow(c, rel) for c in ts])) if ts else ''}
{('<h2>Season by season <small>recorded matches</small></h2>' + table(['Year', 'Draw', 'W', 'L', 'Win %', 'Titles', 'Finals', 'Majors'], [[f'<a class="q" href="{rel}tennis/seasons/{r["y"]}/">{r["y"]}</a>' if r['y'] in by_year else r['y'], E(circ.get(r['c'], r['c'])), r['w'], r['l'], pct(r['w'], r['w'] + r['l']) if r['w'] + r['l'] else '—', r['t'], r['f'], r['mj']] for r in rows], num=(2, 3, 4, 5, 6, 7))) if rows else ''}'''
        out.append((f'tennis/players/{pid}/index.html', page(site=site, sport='tennis', depth=3, title=f'{pn(pid)} · titles and record · APEX', desc=f'{pn(pid)} ({natn(pnat(pid))}): {len(ts)} tour-level titles, {sum(mjb.values())} majors, {a["w"]}–{a["l"]} in recorded matches.', crumbs=[('Sportsfans', rel), ('Tennis', rel + 'tennis/'), ('Players', rel + 'tennis/players/'), (pn(pid), None)], body=body, path=f'tennis/players/{pid}/', v=v)))
    # tournaments with a title on record (team ties excluded)
    by_t = collections.defaultdict(list)
    for c in C: by_t[c['t']].append(c)
    for tid, cs in by_t.items():
        rel = '../../../'; t = T.get(tid, {}); cs = sorted(cs, key=lambda c: (-c['y'], c['c'])); wins = collections.Counter(p for c in cs for p in c['w']); eds = [e for e in ED.values() if e['t'] == tid]
        surfs = collections.Counter(e['surface'] for e in eds) or collections.Counter({t.get('s') or 'Unknown': 1})
        body = f'''<p class="eyebrow">Tennis · Tournament{' · major' if t.get('major') else ''} · {E(t.get('city', ''))}</p><h1>{E(t.get('n', tid))}</h1>
<p class="lede">{len(cs)} titles on record, {min(c['y'] for c in cs)}–{max(c['y'] for c in cs)}; played on {', '.join(f'{E(s)} ({n} editions)' if len(surfs) > 1 else E(s) for s, n in surfs.most_common())}.{f' Most titles: <b>{E(pn(wins.most_common(1)[0][0]))}</b> ({wins.most_common(1)[0][1]}).' if wins else ''}</p>
<a class="open" href="{rel}tennis/#tab=tournaments&tourn={tid}">Open in the atlas →</a>
{kpis([('Titles', len(cs), ''), ('Editions', len(eds) or len(cs), ''), ('Different champions', len(wins), ''), ('Surface', surfs.most_common(1)[0][0], '')])}
<h2>Most titles here</h2>{table(['Player', 'Titles', 'Years'], [[pl(p, rel), n, ', '.join(str(c['y']) for c in sorted(cs, key=lambda c: c['y']) if p in c['w'])] for p, n in wins.most_common(10)], num=(1,))}
<h2>Roll of honour</h2>{table(CH, [crow(c, rel) for c in cs])}'''
        out.append((f'tennis/tournaments/{slug(tid)}/index.html', page(site=site, sport='tennis', depth=3, title=f'{t.get("n", tid)} · roll of honour · APEX', desc=f'{t.get("n", tid)}: every champion and finalist on record, {min(c["y"] for c in cs)}–{max(c["y"] for c in cs)}.', crumbs=[('Sportsfans', rel), ('Tennis', rel + 'tennis/'), ('Tournaments', rel + 'tennis/tournaments/'), (t.get('n', tid), None)], body=body, path=f'tennis/tournaments/{slug(tid)}/', v=v)))
    # nations
    by_n = collections.defaultdict(list)
    for c in C:
        for p in c['w']: by_n[pnat(p)].append(c)
    nplayers = collections.defaultdict(set)
    for r in PS: nplayers[pnat(r['p'])].add(r['p'])
    for code, cs in by_n.items():
        rel = '../../../'; cs = sorted(cs, key=lambda c: (-c['y'], c['c'])); wins = collections.Counter(p for c in cs for p in c['w'] if pnat(p) == code); mj = [c for c in cs if c['t'] in majors]
        body = f'''<p class="eyebrow">Tennis · Nation · {E(code or '—')}</p><h1><i class="dot" style="--c:{ncol(code)};width:.5em;height:.5em;border-radius:6px;vertical-align:.15em"></i>{E(natn(code))}</h1>
<p class="lede">{len(cs)} titles by {len(wins)} players, {min(c['y'] for c in cs)}–{max(c['y'] for c in cs)}; {len(mj)} of them majors. {len(nplayers.get(code, ()))} players with recorded matches.</p>
<a class="open" href="{rel}tennis/#tab=nations&nation={E(code)}">Open in the atlas →</a>
{kpis([('Titles', len(cs), ''), ('Majors', len(mj), ''), ('Title winners', len(wins), ''), ('Players', len(nplayers.get(code, ())), 'with recorded matches')])}
<h2>Most titles</h2>{table(['Player', 'Titles', 'Majors', 'Years'], [[pl(p, rel), n, sum(1 for c in cs if p in c['w'] and c['t'] in majors), f'{min(c["y"] for c in cs if p in c["w"])}–{max(c["y"] for c in cs if p in c["w"])}'] for p, n in wins.most_common(20)], num=(1, 2))}
<h2>Majors</h2>{table(CH, [crow(c, rel) for c in mj]) if mj else '<p class="lede">No major titles on record.</p>'}
<h2>Every title <small>{len(cs)}</small></h2>{table(CH, [crow(c, rel) for c in cs[:600]])}{f'<p class="lede">The first 600 of {len(cs)} are listed; the atlas holds them all.</p>' if len(cs) > 600 else ''}'''
        out.append((f'tennis/nations/{slug(code or "unlisted")}/index.html', page(site=site, sport='tennis', depth=3, title=f'{natn(code)} in tennis · every title · APEX', desc=f'{natn(code)}: {len(cs)} tour-level titles by {len(wins)} players, {len(mj)} majors.', crumbs=[('Sportsfans', rel), ('Tennis', rel + 'tennis/'), ('Nations', rel + 'tennis/nations/'), (natn(code), None)], body=body, path=f'tennis/nations/{slug(code or "unlisted")}/', v=v)))
    rel = '../../'
    out.append(('tennis/seasons/index.html', page(site=site, sport='tennis', depth=2, title='Tennis, year by year, 1877–2026 · APEX', desc='Every season of tennis on its own page.', crumbs=[('Sportsfans', rel), ('Tennis', rel + 'tennis/'), ('Seasons', None)], body=f'<p class="eyebrow">Tennis</p><h1>Every <span>season</span></h1><p class="lede">{len(years)} years with a title on record.</p>' + index_list([(str(y), f'tennis/seasons/{y}/', f'{len(by_year[y])} titles') for y in reversed(years)], rel), path='tennis/seasons/', v=v)))
    out += index_pages(site=site, sport='tennis', title='Tennis players · APEX', desc='Every title winner and every player with fifty recorded matches.', crumbs=[('Sportsfans', rel), ('Tennis', rel + 'tennis/'), ('Players', None)], intro=f'<p class="eyebrow">Tennis</p><h1>Every <span>player</span></h1><p class="lede">{len(pids):,} players: every title winner, and everyone with fifty or more recorded matches.</p>', items=sorted([(pn(pid), f'tennis/players/{pid}/', f'{len(titles_of.get(pid, []))} titles · {pagg[pid]["w"] if pid in pagg else 0}–{pagg[pid]["l"] if pid in pagg else 0}') for pid in pids], key=lambda t: (t[0].split(' ')[-1], t[0], t[1])), dir='tennis/players', v=v)
    out.append(('tennis/tournaments/index.html', page(site=site, sport='tennis', depth=2, title='Tennis tournaments · APEX', desc='Every tournament with a title on record.', crumbs=[('Sportsfans', rel), ('Tennis', rel + 'tennis/'), ('Tournaments', None)], body=f'<p class="eyebrow">Tennis</p><h1>Every <span>tournament</span></h1><p class="lede">{len(by_t):,} tournaments with a title on record.</p>' + index_list(sorted([(T.get(tid, {}).get('n', tid), f'tennis/tournaments/{slug(tid)}/', f'{len(cs)} titles') for tid, cs in by_t.items()], key=lambda t: (t[0], t[1])), rel), path='tennis/tournaments/', v=v)))
    out.append(('tennis/nations/index.html', page(site=site, sport='tennis', depth=2, title='Tennis nations · APEX', desc='Every nation with a title on record.', crumbs=[('Sportsfans', rel), ('Tennis', rel + 'tennis/'), ('Nations', None)], body=f'<p class="eyebrow">Tennis</p><h1>Every <span>nation</span></h1><p class="lede">{len(by_n)} nations with a title on record.</p>' + index_list(sorted([(natn(code), f'tennis/nations/{slug(code or "unlisted")}/', f'{len(cs)} titles') for code, cs in by_n.items()], key=lambda t: (t[0], t[1])), rel), path='tennis/nations/', v=v)))
    return out


# ============================================================ Isle of Man TT ============================================================
def gen_tt(A, *, site, v):
    out = []; RF = A['resultFields']; R = A['riders']; races = A['races']
    COL = {'Honda':'#f34d54','Yamaha':'#507dff','Suzuki':'#ffd23f','Kawasaki':'#79d455','BMW':'#66b5ff','Triumph':'#4dd0b0','Norton':'#c9ccd1','Ducati':'#ff3642','MV Agusta':'#e8c473','Moto Guzzi':'#a3bacc','BSA':'#c9a86a','Velocette':'#7fa08c','Paton':'#ff9ecb','AJS':'#b9cfdd','Rudge':'#d5c39f','Sunbeam':'#ffe08a','Matchless':'#c1ac91','Gilera':'#e97a75','Indian':'#c0392b'}
    def hue(t):
        h = 0
        for ch in str(t or '?'): h = (h * 31 + ord(ch)) & 0xffffffff
        import colorsys; r, g, b = colorsys.hls_to_rgb((h % 360) / 360, .64, .4); return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
    col = lambda m: COL.get(m) or ('#5b616b' if m in (None, 'Unrecorded') else hue(m))
    pn = lambda i: R.get(i, {}).get('name', i)
    rows_of = lambda r: [dict(zip(RF, x)) for x in r['results']]
    for r in races:
        for x in r['results']:
            if not x[4]: x[4] = 'Unrecorded'
    rl = lambda i, rel: f'<a class="q" href="{rel}tt/riders/{slug(i)}/">{E(pn(i))}</a>'
    crew = lambda ids, rel: ' / '.join(rl(i, rel) for i in ids)
    ml = lambda m, rel: f'<i class="dot" style="--c:{col(m)}"></i>' + (f'<a class="q" href="{rel}tt/marques/{slug(m)}/">{E(m)}</a>' if m != 'Unrecorded' else E(m))
    racelink = lambda r, rel: f'<a class="q" href="{rel}tt/#season={r["y"]}&tab=race&race={r["id"]}">{E(r["name"])}</a>'
    win = lambda r: next((x for x in rows_of(r) if x['pos'] == 1), None)
    by_year = collections.defaultdict(list)
    for r in races: by_year[r['y']].append(r)
    years = sorted(by_year)
    rrow = lambda r, rel: (lambda w: [f'<a class="q" href="{rel}tt/seasons/{r["y"]}/">{r["y"]}</a>', racelink(r, rel), E(r['course']), r['laps'] or '', crew(w['crew'], rel) if w else '—', E(w['machine'] or '') if w else '', ml(w['marque'], rel) if w else '', f'{w["mph"]:.2f}' if w and w['mph'] else '', E(w['time'] or '') if w else ''])(win(r))
    RH = ['Year', 'Race', 'Course', 'Laps', 'Winner', 'Machine', 'Marque', 'mph', 'Time']
    # seasons
    for y in years:
        rel = '../../../'; rs = by_year[y]; prev = next((x for x in reversed(years) if x < y), None); nxt = next((x for x in years if x > y), None)
        wins = collections.Counter(i for r in rs for x in rows_of(r) if x['pos'] == 1 for i in x['crew']); mq = collections.Counter(win(r)['marque'] for r in rs if win(r))
        fast = max((r for r in rs if win(r) and win(r)['mph']), key=lambda r: win(r)['mph'], default=None); senior = next((r for r in rs if r['family'] == 'Senior' and win(r)), None)
        body = f'''<p class="eyebrow">Isle of Man TT · TT week</p><h1>{y} <span>TT</span></h1>
<p class="lede">{len(rs)} race{'' if len(rs) == 1 else 's'}{' on the ' + E(rs[0]['course']) if len({r['course'] for r in rs}) == 1 else ''}.{f' Senior TT: <b>{E(" / ".join(pn(i) for i in win(senior)["crew"]))}</b> ({E(win(senior)["marque"])}{", " + str(win(senior)["mph"]) + " mph" if win(senior)["mph"] else ""}).' if senior else ''}{f' Most wins of the week: <b>{E(pn(wins.most_common(1)[0][0]))}</b> ({wins.most_common(1)[0][1]}).' if wins and wins.most_common(1)[0][1] > 1 else ''}{f' Fastest race: {E(win(fast)["mph"])} mph in the {E(fast["name"])}.' if fast else ''}</p>
<a class="open" href="{rel}tt/#season={y}&tab=season">Open {y} in the atlas →</a>{f'<a class="also" href="{rel}tt/seasons/{prev}/">← {prev}</a>' if prev else ''}{f'<a class="also" href="{rel}tt/seasons/{nxt}/">{nxt} →</a>' if nxt else ''}
{kpis([('Races', len(rs), ''), ('Winning marques', len(mq), ''), ('Recorded results', sum(len(r['results']) for r in rs), ''), ('Fastest average', f'{win(fast)["mph"]} mph' if fast else '—', E(fast['name']) if fast else '')])}
<h2>Marques of the week</h2>{table(['Marque', 'Wins', 'Races'], [[ml(m, rel), n, ', '.join(E(r['name']) for r in rs if win(r) and win(r)['marque'] == m)] for m, n in mq.most_common()], num=(1,))}
<h2>Every race</h2>{table(RH, [rrow(r, rel) for r in rs], num=(3, 7))}'''
        out.append((f'tt/seasons/{y}/index.html', page(site=site, sport='tt', depth=3, title=f'{y} Isle of Man TT · every race and winner · APEX', desc=f'The {y} TT: {len(rs)} races with winners, machines, courses and race averages.', crumbs=[('Sportsfans', rel), ('Isle of Man TT', rel + 'tt/'), ('Years', rel + 'tt/seasons/'), (str(y), None)], body=body, path=f'tt/seasons/{y}/', v=v)))
    # riders
    by_r = collections.defaultdict(list)
    for r in races:
        for x in rows_of(r):
            for i in x['crew']: by_r[i].append((r, x))
    for rid, rr in by_r.items():
        rel = '../../../'; wins = [(r, x) for r, x in rr if x['pos'] == 1]; pod = sum(1 for r, x in rr if x['pos'] and x['pos'] <= 3); ys = sorted({r['y'] for r, _ in rr}); best = max((x['mph'] for _, x in rr if x['mph']), default=None)
        fams = collections.Counter(r['family'] for r, x in wins); mqs = collections.Counter(x['marque'] for r, x in rr)
        body = f'''<p class="eyebrow">Isle of Man TT · Rider · {ys[0]}{"–" + str(ys[-1]) if ys[-1] != ys[0] else ""}</p><h1>{E(pn(rid))}</h1>
<p class="lede">{len(wins)} win{'' if len(wins) == 1 else 's'}, {pod} podium{'' if pod == 1 else 's'} and {len(rr)} recorded start{'' if len(rr) == 1 else 's'} over {len(ys)} TT week{'' if len(ys) == 1 else 's'}.{f' Wins by class: {", ".join(f"{E(f)} {n}" for f, n in fams.most_common())}.' if fams else ''}{f' Fastest race average {best} mph.' if best else ''} Recorded starts are what the archive holds, not a complete career.</p>
<a class="open" href="{rel}tt/#tab=riders&rider={rid}">Open in the atlas →</a>
{kpis([('Wins', len(wins), ''), ('Podiums', pod, ''), ('Recorded starts', len(rr), ''), ('Fastest average', f'{best} mph' if best else '—', '')])}
{('<h2>Machines</h2><div class="chips">' + ''.join(f'<a class="chip" href="{rel}tt/marques/{slug(m)}/"><i style="--c:{col(m)}"></i>{E(m)} <span style="color:var(--muted)">{n}</span></a>' if m != 'Unrecorded' else f'<span class="chip"><i style="--c:{col(m)}"></i>{E(m)} <span style="color:var(--muted)">{n}</span></span>' for m, n in mqs.most_common()) + '</div>') if mqs else ''}
<h2>Every recorded result</h2>{table(['Year', 'Race', 'Pos', 'Status', 'Machine', 'Marque', 'mph', 'Time'], [[f'<a class="q" href="{rel}tt/seasons/{r["y"]}/">{r["y"]}</a>', racelink(r, rel), x['pos'] or '—', E(x['status']), E(x['machine'] or ''), ml(x['marque'], rel), f'{x["mph"]:.2f}' if x['mph'] else '', E(x['time'] or '')] for r, x in sorted(rr, key=lambda t: (-t[0]['y'], t[0]['name']))], num=(2, 6))}'''
        out.append((f'tt/riders/{slug(rid)}/index.html', page(site=site, sport='tt', depth=3, title=f'{pn(rid)} · Isle of Man TT record · APEX', desc=f'{pn(rid)} at the TT: {len(wins)} wins, {pod} podiums, {len(rr)} recorded starts, {ys[0]}–{ys[-1]}.', crumbs=[('Sportsfans', rel), ('Isle of Man TT', rel + 'tt/'), ('Riders', rel + 'tt/riders/'), (pn(rid), None)], body=body, path=f'tt/riders/{slug(rid)}/', v=v, noindex=(len(rr) < 3 and not pod))))
    # marques
    by_m = collections.defaultdict(list)
    for r in races:
        for x in rows_of(r): by_m[x['marque']].append((r, x))
    for m, rr in by_m.items():
        if m == 'Unrecorded': continue
        rel = '../../../'; wins = sorted([(r, x) for r, x in rr if x['pos'] == 1], key=lambda t: -t[0]['y']); ys = sorted({r['y'] for r, _ in rr}); riders = collections.Counter(i for r, x in wins for i in x['crew'])
        body = f'''<p class="eyebrow">Isle of Man TT · Marque · {ys[0]}–{ys[-1]}</p><h1><i class="dot" style="--c:{col(m)};width:.5em;height:.5em;border-radius:6px;vertical-align:.15em"></i>{E(m)}</h1>
<p class="lede">{len(wins)} TT win{'' if len(wins) == 1 else 's'} from {len(rr)} recorded starts, {ys[0]}–{ys[-1]}{f'; most wins on the marque: <b>{E(pn(riders.most_common(1)[0][0]))}</b> ({riders.most_common(1)[0][1]})' if riders else ''}.</p>
<a class="open" href="{rel}tt/#tab=marques&marque={E(m)}">Open in the atlas →</a>
{kpis([('Wins', len(wins), ''), ('Recorded starts', len(rr), ''), ('Different winners', len(riders), ''), ('Years', len(ys), f'{ys[0]}–{ys[-1]}')])}
{('<h2>Winners on the marque</h2>' + table(['Rider', 'Wins', 'Years'], [[rl(i, rel), n, ', '.join(str(r['y']) for r, x in sorted(wins, key=lambda t: t[0]['y']) if i in x['crew'])] for i, n in riders.most_common(20)], num=(1,))) if riders else ''}
{('<h2>Every win</h2>' + table(RH, [rrow(r, rel) for r, x in wins], num=(3, 7))) if wins else '<p class="lede">No wins on record.</p>'}'''
        out.append((f'tt/marques/{slug(m)}/index.html', page(site=site, sport='tt', depth=3, title=f'{m} at the Isle of Man TT · every win · APEX', desc=f'{m} at the TT: {len(wins)} wins from {len(rr)} recorded starts, {ys[0]}–{ys[-1]}.', crumbs=[('Sportsfans', rel), ('Isle of Man TT', rel + 'tt/'), ('Marques', rel + 'tt/marques/'), (m, None)], body=body, path=f'tt/marques/{slug(m)}/', v=v)))
    rel = '../../'
    out.append(('tt/seasons/index.html', page(site=site, sport='tt', depth=2, title='The Isle of Man TT, year by year, 1907–2026 · APEX', desc='Every TT week on its own page.', crumbs=[('Sportsfans', rel), ('Isle of Man TT', rel + 'tt/'), ('Years', None)], body=f'<p class="eyebrow">Isle of Man TT</p><h1>Every <span>TT week</span></h1><p class="lede">{len(years)} years with a TT.</p>' + index_list([(str(y), f'tt/seasons/{y}/', f'{len(by_year[y])} races') for y in reversed(years)], rel), path='tt/seasons/', v=v)))
    out += index_pages(site=site, sport='tt', title='Isle of Man TT riders · APEX', desc='Every rider with a recorded TT result.', crumbs=[('Sportsfans', rel), ('Isle of Man TT', rel + 'tt/'), ('Riders', None)], intro=f'<p class="eyebrow">Isle of Man TT</p><h1>Every <span>rider</span></h1><p class="lede">{len(by_r):,} riders with a recorded result.</p>', items=sorted([(pn(i), f'tt/riders/{slug(i)}/', f'{sum(1 for r, x in rr if x["pos"] == 1)} wins · {len(rr)} starts') for i, rr in by_r.items()], key=lambda t: (t[0].split(' ')[-1], t[0], t[1])), dir='tt/riders', v=v)
    out.append(('tt/marques/index.html', page(site=site, sport='tt', depth=2, title='Isle of Man TT marques · APEX', desc='Every marque with a recorded TT result.', crumbs=[('Sportsfans', rel), ('Isle of Man TT', rel + 'tt/'), ('Marques', None)], body=f'<p class="eyebrow">Isle of Man TT</p><h1>Every <span>marque</span></h1>' + index_list(sorted([(m, f'tt/marques/{slug(m)}/', f'{sum(1 for r, x in rr if x["pos"] == 1)} wins · {len(rr)} starts') for m, rr in by_m.items() if m != 'Unrecorded'], key=lambda t: (t[0], t[1])), rel), path='tt/marques/', v=v)))
    return out

# ============================================================ Dakar Rally (the desert edition) ============================================================
def gen_dakar(A, *, site, v):
    """Static pages for the Dakar atlas: every edition, every driver or rider on a podium, every marque, every class."""
    out = []; RF = A['resultFields']; P = A['people']; eds = A['editions']; COLS = A.get('colours', {})
    def hue(t):
        h = 0
        for ch in str(t or '?'): h = (h * 31 + ord(ch)) & 0xffffffff
        import colorsys; r, g, b = colorsys.hls_to_rgb((h % 360) / 360, .62, .42); return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
    col = lambda m: COLS.get(m) or hue(m)
    pn = lambda i: P.get(i, {}).get('name', i)
    rows_of = lambda e: [dict(zip(RF, x)) for x in e['results']]
    dl = lambda i, rel: f'<a class="q" href="{rel}dakar/drivers/{slug(i)}/">{E(pn(i))}</a>'
    crew = lambda r, rel: ' / '.join(dl(i, rel) for i in r['crew'] if i != r['driver'])
    ml = lambda m, rel: f'<i class="dot" style="--c:{col(m)}"></i><a class="q" href="{rel}dakar/marques/{slug(m)}/">{E(m)}</a>'
    cl = lambda c, rel: f'<a class="q" href="{rel}dakar/classes/{slug(c)}/">{E(c)}</a>'
    yl = lambda y, rel: f'<a class="q" href="{rel}dakar/editions/{y}/">{y}</a>'
    held = [e for e in eds if not e['cancelled']]; years = [e['y'] for e in eds]
    RH = ['Year', 'Class', 'Place', 'Driver / rider', 'Crew', 'Make', 'Route']
    rrow = lambda e, r, rel: [yl(e['y'], rel), cl(r['cat'], rel), r['rank'], dl(r['driver'], rel), crew(r, rel), ml(r['make'], rel), E(e['route'])]
    # editions
    for e in eds:
        y = e['y']; rel = '../../../'; rows = rows_of(e); prev = next((x for x in reversed(years) if x < y), None); nxt = next((x for x in years if x > y), None)
        wins = [r for r in rows if r['rank'] == 1]; mq = collections.Counter(r['make'] for r in rows); car = next((r for r in wins if r['cat'] == 'Cars'), None); bike = next((r for r in wins if r['cat'] == 'Bikes'), None)
        lede = 'The rally was cancelled before the start and has no results.' if e['cancelled'] else f'{len(e["cats"])} class{"" if len(e["cats"]) == 1 else "es"}, {len(rows)} podium places, {len(mq)} marques on the podium.' + (f' Cars: <b>{E(pn(car["driver"]))}</b> ({E(car["make"])}).' if car else '') + (f' Bikes: <b>{E(pn(bike["driver"]))}</b> ({E(bike["make"])}).' if bike else '')
        body = f"""<p class="eyebrow">Dakar Rally · {E(e['era'])}</p><h1>{y} <span>Dakar</span></h1>
<p class="lede">{E(e['route'])}. {lede}</p>
<a class="open" href="{rel}dakar/#season={y}&tab=season">Open {y} in the atlas →</a>{f'<a class="also" href="{rel}dakar/editions/{prev}/">← {prev}</a>' if prev else ''}{f'<a class="also" href="{rel}dakar/editions/{nxt}/">{nxt} →</a>' if nxt else ''}
{kpis([('Classes', len(e['cats']), ''), ('Podium places', len(rows), ''), ('Marques on the podium', len(mq), ''), ('Named towns', len(e['stops']), E(' · '.join(e['stops'])) if e['stops'] else '')])}
{('<h2>The podium of every class</h2>' + table(['Class', 'Place', 'Driver / rider', 'Crew', 'Make'], [[cl(r['cat'], rel), r['rank'], dl(r['driver'], rel), crew(r, rel), ml(r['make'], rel)] for r in rows], num=(1,))) if rows else ''}
{('<h2>Marques on the podium</h2>' + table(['Marque', 'Places', 'Wins'], [[ml(m, rel), n, sum(1 for r in wins if r['make'] == m)] for m, n in mq.most_common()], num=(1, 2))) if mq else ''}"""
        out.append((f'dakar/editions/{y}/index.html', page(site=site, sport='dakar', depth=3, title=f'{y} Dakar Rally · route and every class podium · APEX', desc=f'The {y} Dakar Rally: {e["route"]}. ' + ('Cancelled before the start.' if e['cancelled'] else f'{len(e["cats"])} classes, {len(rows)} podium places.'), crumbs=[('Sportsfans', rel), ('Dakar Rally', rel + 'dakar/'), ('Editions', rel + 'dakar/editions/'), (str(y), None)], body=body, path=f'dakar/editions/{y}/', v=v)))
    # drivers and riders (every crew member credited)
    by_d = collections.defaultdict(list)
    for e in held:
        for r in rows_of(e):
            for i in r['crew']: by_d[i].append((e, r))
    for d, rr in by_d.items():
        rel = '../../../'; wins = [(e, r) for e, r in rr if r['rank'] == 1]; lead = sum(1 for e, r in rr if r['driver'] == d); ys = sorted({e['y'] for e, _ in rr}); cats = collections.Counter(r['cat'] for e, r in wins); mqs = collections.Counter(r['make'] for e, r in rr)
        body = f"""<p class="eyebrow">Dakar Rally · {'Driver / rider' if lead else 'Crew'} · {ys[0]}{'–' + str(ys[-1]) if ys[-1] != ys[0] else ''}</p><h1>{E(pn(d))}</h1>
<p class="lede">{len(wins)} class win{'' if len(wins) == 1 else 's'} and {len(rr)} podium place{'' if len(rr) == 1 else 's'} over {len(ys)} edition{'' if len(ys) == 1 else 's'}{f', {lead} as the lead name and {len(rr) - lead} in the crew' if 0 < lead < len(rr) else ' as a crew member' if not lead else ''}.{f' Wins by class: {", ".join(f"{E(c)} {n}" for c, n in cats.most_common())}.' if cats else ''} Podium places are what the archive holds; starts and retirements are not carried.</p>
<a class="open" href="{rel}dakar/#tab=drivers&driver={E(d)}">Open in the atlas →</a>
{kpis([('Class wins', len(wins), ''), ('Podium places', len(rr), ''), ('Editions', len(ys), f'{ys[0]}–{ys[-1]}'), ('Marques', len(mqs), '')])}
{('<h2>Marques</h2><div class="chips">' + ''.join(f'<a class="chip" href="{rel}dakar/marques/{slug(m)}/"><i style="--c:{col(m)}"></i>{E(m)} <span style="color:var(--muted)">{n}</span></a>' for m, n in mqs.most_common()) + '</div>') if mqs else ''}
<h2>Every podium place</h2>{table(RH, [rrow(e, r, rel) for e, r in sorted(rr, key=lambda t: (-t[0]['y'], t[1]['cat']))], num=(2,))}"""
        out.append((f'dakar/drivers/{slug(d)}/index.html', page(site=site, sport='dakar', depth=3, title=f'{pn(d)} · Dakar Rally record · APEX', desc=f'{pn(d)} at the Dakar: {len(wins)} class wins, {len(rr)} podium places, {ys[0]}–{ys[-1]}.', crumbs=[('Sportsfans', rel), ('Dakar Rally', rel + 'dakar/'), ('Drivers & riders', rel + 'dakar/drivers/'), (pn(d), None)], body=body, path=f'dakar/drivers/{slug(d)}/', v=v)))
    # marques
    by_m = collections.defaultdict(list)
    for e in held:
        for r in rows_of(e): by_m[r['make']].append((e, r))
    for m, rr in by_m.items():
        rel = '../../../'; wins = sorted([(e, r) for e, r in rr if r['rank'] == 1], key=lambda t: -t[0]['y']); ys = sorted({e['y'] for e, _ in rr}); people = collections.Counter(i for e, r in wins for i in r['crew']); cats = collections.Counter(r['cat'] for e, r in wins)
        body = f"""<p class="eyebrow">Dakar Rally · Marque · {ys[0]}–{ys[-1]}</p><h1><i class="dot" style="--c:{col(m)};width:.5em;height:.5em;border-radius:6px;vertical-align:.15em"></i>{E(m)}</h1>
<p class="lede">{len(wins)} class win{'' if len(wins) == 1 else 's'} from {len(rr)} podium place{'' if len(rr) == 1 else 's'}, {ys[0]}–{ys[-1]}{f'; wins by class: {", ".join(f"{E(c)} {n}" for c, n in cats.most_common())}' if cats else ''}{f'; most wins on the marque: <b>{E(pn(people.most_common(1)[0][0]))}</b> ({people.most_common(1)[0][1]})' if people else ''}.</p>
<a class="open" href="{rel}dakar/#tab=marques&marque={E(m)}">Open in the atlas →</a>
{kpis([('Class wins', len(wins), ''), ('Podium places', len(rr), ''), ('Different winners', len(people), ''), ('Editions', len(ys), f'{ys[0]}–{ys[-1]}')])}
{('<h2>Winners on the marque</h2>' + table(['Driver / rider', 'Wins', 'Years'], [[dl(i, rel), n, ', '.join(str(e['y']) for e, r in sorted(wins, key=lambda t: t[0]['y']) if i in r['crew'])] for i, n in people.most_common(20)], num=(1,))) if people else ''}
{('<h2>Every win</h2>' + table(RH, [rrow(e, r, rel) for e, r in wins], num=(2,))) if wins else '<p class="lede">No class wins on record; podium places only.</p>'}
<h2>Every podium place</h2>{table(RH, [rrow(e, r, rel) for e, r in sorted(rr, key=lambda t: (-t[0]['y'], t[1]['cat'], t[1]['rank']))], num=(2,))}"""
        out.append((f'dakar/marques/{slug(m)}/index.html', page(site=site, sport='dakar', depth=3, title=f'{m} at the Dakar Rally · every podium · APEX', desc=f'{m} at the Dakar: {len(wins)} class wins from {len(rr)} podium places, {ys[0]}–{ys[-1]}.', crumbs=[('Sportsfans', rel), ('Dakar Rally', rel + 'dakar/'), ('Marques', rel + 'dakar/marques/'), (m, None)], body=body, path=f'dakar/marques/{slug(m)}/', v=v)))
    # classes
    NOTE = {c['key']: c.get('note', '') for c in A.get('categories', [])}
    by_c = collections.defaultdict(list)
    for e in held:
        for r in rows_of(e): by_c[r['cat']].append((e, r))
    for c, rr in by_c.items():
        rel = '../../../'; wins = sorted([(e, r) for e, r in rr if r['rank'] == 1], key=lambda t: -t[0]['y']); ys = sorted({e['y'] for e, _ in rr}); people = collections.Counter(i for e, r in wins for i in r['crew']); mqs = collections.Counter(r['make'] for e, r in wins)
        body = f"""<p class="eyebrow">Dakar Rally · Class · {ys[0]}–{ys[-1]}</p><h1>{E(c)}</h1>
<p class="lede">{E(NOTE.get(c, ''))} {len(wins)} edition{'' if len(wins) == 1 else 's'} won, {ys[0]}–{ys[-1]}{f'; most wins: <b>{E(pn(people.most_common(1)[0][0]))}</b> ({people.most_common(1)[0][1]})' if people else ''}{f'; most successful marque: <b>{E(mqs.most_common(1)[0][0])}</b> ({mqs.most_common(1)[0][1]})' if mqs else ''}.</p>
<a class="open" href="{rel}dakar/#class={E(c)}&tab=classes&cls={E(c)}">Open in the atlas →</a>
{kpis([('Editions', len(ys), f'{ys[0]}–{ys[-1]}'), ('Podium places', len(rr), ''), ('Different winners', len(people), ''), ('Winning marques', len(mqs), '')])}
{('<h2>Most wins</h2>' + table(['Driver / rider', 'Wins', 'Years'], [[dl(i, rel), n, ', '.join(str(e['y']) for e, r in sorted(wins, key=lambda t: t[0]['y']) if i in r['crew'])] for i, n in people.most_common(15)], num=(1,))) if people else ''}
{('<h2>Winning marques</h2>' + table(['Marque', 'Wins', 'Years'], [[ml(m, rel), n, ', '.join(str(e['y']) for e, r in sorted(wins, key=lambda t: t[0]['y']) if r['make'] == m)] for m, n in mqs.most_common()], num=(1,))) if mqs else ''}
<h2>Every winner</h2>{table(RH, [rrow(e, r, rel) for e, r in wins], num=(2,))}"""
        out.append((f'dakar/classes/{slug(c)}/index.html', page(site=site, sport='dakar', depth=3, title=f'{c} at the Dakar Rally · every winner · APEX', desc=f'The {c} class of the Dakar Rally: every winner and podium, {ys[0]}–{ys[-1]}.', crumbs=[('Sportsfans', rel), ('Dakar Rally', rel + 'dakar/'), ('Classes', rel + 'dakar/classes/'), (c, None)], body=body, path=f'dakar/classes/{slug(c)}/', v=v)))
    rel = '../../'
    out.append(('dakar/editions/index.html', page(site=site, sport='dakar', depth=2, title=f'The Dakar Rally, edition by edition, {years[0]}–{years[-1]} · APEX', desc='Every Dakar Rally on its own page: route, era and the podium of every class.', crumbs=[('Sportsfans', rel), ('Dakar Rally', rel + 'dakar/'), ('Editions', None)], body=f'<p class="eyebrow">Dakar Rally</p><h1>Every <span>edition</span></h1><p class="lede">{len(held)} editions run and {len(eds) - len(held)} cancelled, {years[0]}–{years[-1]}.</p>' + index_list([(str(e['y']), f'dakar/editions/{e["y"]}/', 'cancelled' if e['cancelled'] else f'{E(e["route"])} · {len(e["cats"])} classes') for e in reversed(eds)], rel), path='dakar/editions/', v=v)))
    out.append(('dakar/drivers/index.html', page(site=site, sport='dakar', depth=2, title='Dakar Rally drivers and riders · APEX', desc='Everyone with a Dakar Rally podium place, in any class, as driver, rider or crew.', crumbs=[('Sportsfans', rel), ('Dakar Rally', rel + 'dakar/'), ('Drivers & riders', None)], body=f'<p class="eyebrow">Dakar Rally</p><h1>Every <span>name on a podium</span></h1><p class="lede">{len(by_d):,} drivers, riders and crew with a podium place.</p>' + index_list(sorted([(pn(i), f'dakar/drivers/{slug(i)}/', f'{sum(1 for e, r in rr if r["rank"] == 1)} wins · {len(rr)} podiums') for i, rr in by_d.items()], key=lambda t: (t[0].split(' ')[-1], t[0], t[1])), rel), path='dakar/drivers/', v=v)))
    out.append(('dakar/marques/index.html', page(site=site, sport='dakar', depth=2, title='Dakar Rally marques · APEX', desc='Every marque with a Dakar Rally podium place.', crumbs=[('Sportsfans', rel), ('Dakar Rally', rel + 'dakar/'), ('Marques', None)], body=f'<p class="eyebrow">Dakar Rally</p><h1>Every <span>marque</span></h1>' + index_list(sorted([(m, f'dakar/marques/{slug(m)}/', f'{sum(1 for e, r in rr if r["rank"] == 1)} wins · {len(rr)} podiums') for m, rr in by_m.items()], key=lambda t: (t[0], t[1])), rel), path='dakar/marques/', v=v)))
    out.append(('dakar/classes/index.html', page(site=site, sport='dakar', depth=2, title='Dakar Rally classes · APEX', desc='Every class the Dakar Rally has crowned, with its winners.', crumbs=[('Sportsfans', rel), ('Dakar Rally', rel + 'dakar/'), ('Classes', None)], body=f'<p class="eyebrow">Dakar Rally</p><h1>Every <span>class</span></h1>' + index_list([(c, f'dakar/classes/{slug(c)}/', f'{sum(1 for e, r in rr if r["rank"] == 1)} editions · {min(e["y"] for e, _ in rr)}–{max(e["y"] for e, _ in rr)}') for c, rr in sorted(by_c.items(), key=lambda t: -len(t[1]))], rel), path='dakar/classes/', v=v)))
    return out

# ============================================================ UFC (the cage edition) ============================================================
def gen_ufc(A, *, site, v):
    out = []; BF = A['boutFields']; F = A['fighters']; DL = {d['key']: d['label'] for d in A['divisions']}; V = A['venues']
    COL = {'hw': '#ff3642', 'lhw': '#ff8a3d', 'mw': '#ffd23f', 'ww': '#79d455', 'lw': '#2fd0c2', 'fw': '#4da3ff', 'bw': '#8f7bff', 'flw': '#ff7ad9', 'wsw': '#ffb3c7', 'wflw': '#c9a0ff', 'wbw': '#9fe0ff', 'wfw': '#ffe08a', 'wat': '#f4c2ff', 'open': '#c9ccd1', 'shw': '#a3bacc', 'catch': '#8b9099'}
    col = lambda k: COL.get(k, '#8b9099'); pn = lambda i: F.get(i, {}).get('name', i); dlab = lambda k: DL.get(k, k)
    bouts = [dict(zip(BF, x)) for x in A['bouts']]; E_ = {e['id']: e for e in A['events']}
    by_e = collections.defaultdict(list)
    for b in bouts: by_e[b['e']].append(b)
    fl = lambda i, rel: f'<a class="q" href="{rel}ufc/fighters/{slug(i)}/">{E(pn(i))}</a>'
    dl = lambda k, rel: f'<i class="dot" style="--c:{col(k)}"></i><a class="q" href="{rel}ufc/divisions/{k}/">{E(dlab(k))}</a>'
    el = lambda e, rel: f'<a class="q" href="{rel}ufc/events/{e["id"]}/">{E(e["name"])}</a>'
    vl = lambda vid, rel: f'<a class="q" href="{rel}ufc/venues/{vid}/">{E(V[vid]["name"])}</a>' if vid in V else ''
    who = lambda b, rel: f'<b>{fl(b["w"], rel)}</b> def. {fl(b["b"] if b["w"] == b["a"] else b["a"], rel)}' if b['res'] == 'W' else f'{fl(b["a"], rel)} vs. {fl(b["b"], rel)}'
    mk = lambda b: E(b['method'])
    belt = lambda b: ' <span class="tag">title</span>' if b['title'] else ''
    brow = lambda b, rel: [f'<a class="q" href="{rel}ufc/seasons/{b["y"]}/">{E(b["date"])}</a>', el(E_[b['e']], rel), dl(b['div'], rel), who(b, rel) + belt(b), mk(b), b['round'] if b['round'] is not None else '', E(b['time'] or '')]
    BH = ['Date', 'Event', 'Division', 'Result', 'Method', 'R', 'Time']
    by_year = collections.defaultdict(list)
    for e in A['events']: by_year[e['y']].append(e)
    years = sorted(by_year)
    fin = lambda b: b['mk'] in ('KO', 'SUB')
    # seasons
    for y in years:
        rel = '../../../'; es = by_year[y]; bs = [b for e in es for b in by_e[e['id']]]; prev = next((x for x in reversed(years) if x < y), None); nxt = next((x for x in years if x > y), None)
        wins = collections.Counter(b['w'] for b in bs if b['w']); titles = [b for b in bs if b['title']]; divs = collections.Counter(b['div'] for b in bs)
        top = wins.most_common(1)[0] if wins else None
        body = f'''<p class="eyebrow">UFC bouts · the year</p><h1>{y} <span>in the cage</span></h1>
<p class="lede">{len(es)} event{'' if len(es) == 1 else 's'} and {len(bs)} bouts, {len(titles)} of them title bouts; {pct(sum(1 for b in bs if fin(b)), len(bs))}% ended inside the distance.{f' Most wins of the year: <b>{E(pn(top[0]))}</b> ({top[1]}).' if top and top[1] > 1 else ''}</p>
<a class="open" href="{rel}ufc/#season={y}&tab=season">Open {y} in the atlas →</a>{f'<a class="also" href="{rel}ufc/seasons/{prev}/">← {prev}</a>' if prev else ''}{f'<a class="also" href="{rel}ufc/seasons/{nxt}/">{nxt} →</a>' if nxt else ''}
{kpis([('Events', len(es), ''), ('Bouts', len(bs), ''), ('Title bouts', len(titles), ''), ('Finishes', f'{pct(sum(1 for b in bs if fin(b)), len(bs))}%', '')])}
<h2>The year’s cards</h2>{table(['Date', 'Event', 'Venue', 'Main event', 'Bouts'], [[E(e['date']), el(e, rel), (vl(e.get('venueId'), rel) + (' · ' + E(e['city']) if e['city'] else '')), (who(by_e[e['id']][0], rel) + belt(by_e[e['id']][0])) if by_e[e['id']] else '—', len(by_e[e['id']])] for e in es], num=(4,))}
<h2>Divisions of the year</h2>{table(['Division', 'Bouts', 'Title bouts', 'Finish rate'], [[dl(d, rel), n, sum(1 for b in bs if b['div'] == d and b['title']), f'{pct(sum(1 for b in bs if b["div"] == d and fin(b)), n)}%'] for d, n in divs.most_common()], num=(1, 2, 3))}'''
        out.append((f'ufc/seasons/{y}/index.html', page(site=site, sport='ufc', depth=3, title=f'UFC in {y} · every event and bout · APEX', desc=f'UFC in {y}: {len(es)} events, {len(bs)} bouts, {len(titles)} title bouts, with every result.', crumbs=[('Sportsfans', rel), ('UFC bouts', rel + 'ufc/'), ('Years', rel + 'ufc/seasons/'), (str(y), None)], body=body, path=f'ufc/seasons/{y}/', v=v)))
    # events
    for e in A['events']:
        rel = '../../../'; bs = by_e[e['id']]; m = bs[0] if bs else None
        body = f'''<p class="eyebrow">UFC bouts · Event · {E(longdate(e['date']))}</p><h1>{E(e['short'])}{f' <span>{E(e["sub"])}</span>' if e['sub'] else ''}</h1>
<p class="lede">{' · '.join(E(x) for x in (e['venue'], e['city'], e['country']) if x)}{f' · attendance {e["att"]:,}' if e.get('att') else ''}.{f' Main event: {who(m, rel)}, {E(m["method"])}{", round " + str(m["round"]) if m["round"] else ""}{" at " + E(m["time"]) if m["time"] else ""}.' if m else ''} {len(bs)} bout{'' if len(bs) == 1 else 's'}, {sum(1 for b in bs if b['title'])} title bout{'' if sum(1 for b in bs if b['title']) == 1 else 's'}, {sum(1 for b in bs if fin(b))} finish{'' if sum(1 for b in bs if fin(b)) == 1 else 'es'}.</p>
<a class="open" href="{rel}ufc/#season={e['y']}&tab=event&event={e['id']}">Open in the atlas →</a>{f'<a class="also" href="{E(e["url"])}" target="_blank" rel="noopener">Wikipedia ↗</a>' if e.get('url') else ''}
{kpis([('Bouts', len(bs), ''), ('Title bouts', sum(1 for b in bs if b['title']), ''), ('Finishes', sum(1 for b in bs if fin(b)), ''), ('Venue', vl(e.get('venueId'), rel) or '—', E(e['city']))])}
<h2>The card</h2>{table(['Card', 'Division', 'Result', 'Method', 'R', 'Time'], [[E(b['card']), dl(b['div'], rel), who(b, rel) + belt(b), mk(b), b['round'] if b['round'] is not None else '', E(b['time'] or '')] for b in bs], num=(4,))}
{('<h2>Bonus awards</h2><ul>' + ''.join(f'<li>{E(bn["t"])}: {", ".join(E(w) for w in bn["who"])}</li>' for bn in e['bonuses']) + '</ul>') if e.get('bonuses') else ''}'''
        out.append((f'ufc/events/{e["id"]}/index.html', page(site=site, sport='ufc', depth=3, title=f'{e["name"]} · results · APEX', desc=f'{e["name"]}, {longdate(e["date"])}{", " + e["city"] if e["city"] else ""}: every bout with method, round and time.', crumbs=[('Sportsfans', rel), ('UFC bouts', rel + 'ufc/'), ('Events', rel + 'ufc/events/'), (e['short'], None)], body=body, path=f'ufc/events/{e["id"]}/', v=v)))
    # fighters
    by_f = collections.defaultdict(list)
    for b in bouts: by_f[b['a']].append(b); by_f[b['b']].append(b)
    for fid, bb in by_f.items():
        rel = '../../../'; f = F.get(fid, {'name': fid, 'rec': [0, 0, 0, 0]}); rec = f.get('rec', [0, 0, 0, 0]); wins = [b for b in bb if b['w'] == fid]; fins = [b for b in wins if fin(b)]; ys = sorted({b['y'] for b in bb}); divs = collections.Counter(b['div'] for b in bb); titles = [b for b in bb if b['title']]
        body = f'''<p class="eyebrow">UFC bouts · Fighter · {ys[0]}{"–" + str(ys[-1]) if ys[-1] != ys[0] else ""}{" · " + E(f["nat"]) if f.get("nat") else ""}</p><h1>{E(f['name'])}</h1>
<p class="lede">{rec[0]}–{rec[1]}{"–" + str(rec[2]) if rec[2] else ""}{f" ({rec[3]} no contest{'' if rec[3] == 1 else 's'})" if rec[3] else ""} in the archive over {len(bb)} bout{'' if len(bb) == 1 else 's'}; {len(fins)} finish{'' if len(fins) == 1 else 'es'}{f", {sum(1 for b in titles if b['w'] == fid)} title-bout win{'' if sum(1 for b in titles if b['w'] == fid) == 1 else 's'} from {len(titles)}" if titles else ''}. Divisions: {', '.join(f'{E(dlab(d))} {n}' for d, n in divs.most_common())}.{f' Born {E(longdate(f["dob"]))}.' if f.get('dob') else ''} The record is what the archive holds, not a career elsewhere.</p>
<a class="open" href="{rel}ufc/#tab=fighters&fighter={fid}">Open in the atlas →</a>{f'<a class="also" href="{E(f["url"])}" target="_blank" rel="noopener">Wikipedia ↗</a>' if f.get('url') else ''}
{kpis([('Wins', rec[0], ''), ('Losses', rec[1], ''), ('Finishes', len(fins), f'{sum(1 for b in fins if b["mk"] == "KO")} KO/TKO · {sum(1 for b in fins if b["mk"] == "SUB")} submissions'), ('Title bouts', len(titles), f'{sum(1 for b in titles if b["w"] == fid)} won')])}
<h2>Every bout</h2>{table(['Date', 'Event', 'Division', 'Result', 'Method', 'R', 'Time'], [brow(b, rel) for b in sorted(bb, key=lambda b: b['date'], reverse=True)], num=(5,))}'''
        out.append((f'ufc/fighters/{slug(fid)}/index.html', page(site=site, sport='ufc', depth=3, title=f'{f["name"]} · UFC record · APEX', desc=f'{f["name"]} in the UFC: {rec[0]}–{rec[1]}{"–" + str(rec[2]) if rec[2] else ""} over {len(bb)} bouts, {ys[0]}–{ys[-1]}, with every result.', crumbs=[('Sportsfans', rel), ('UFC bouts', rel + 'ufc/'), ('Fighters', rel + 'ufc/fighters/'), (f['name'], None)], body=body, path=f'ufc/fighters/{slug(fid)}/', v=v, noindex=(len(bb) < 3 and not titles))))
    # divisions
    by_d = collections.defaultdict(list)
    for b in bouts: by_d[b['div']].append(b)
    for k, bb in by_d.items():
        rel = '../../../'; ys = sorted({b['y'] for b in bb}); wins = collections.Counter(b['w'] for b in bb if b['w']); titles = sorted([b for b in bb if b['title']], key=lambda b: b['date'])
        body = f'''<p class="eyebrow">UFC bouts · Division · {ys[0]}–{ys[-1]}</p><h1><i class="dot" style="--c:{col(k)};width:.5em;height:.5em;border-radius:6px;vertical-align:.15em"></i>{E(dlab(k))}</h1>
<p class="lede">{len(bb):,} bouts, {len(titles)} of them title bouts, {ys[0]}–{ys[-1]}; {pct(sum(1 for b in bb if fin(b)), len(bb))}% ended inside the distance.{f' Most wins in the division: <b>{E(pn(wins.most_common(1)[0][0]))}</b> ({wins.most_common(1)[0][1]}).' if wins else ''}</p>
<a class="open" href="{rel}ufc/#tab=divisions&dv={k}">Open in the atlas →</a>
{kpis([('Bouts', f'{len(bb):,}', ''), ('Title bouts', len(titles), ''), ('Finish rate', f'{pct(sum(1 for b in bb if fin(b)), len(bb))}%', ''), ('Fighters', len({x for b in bb for x in (b['a'], b['b'])}), '')])}
{('<h2>Most wins</h2>' + table(['Fighter', 'Wins', 'Finishes'], [[fl(i, rel), n, sum(1 for b in bb if b['w'] == i and fin(b))] for i, n in wins.most_common(25)], num=(1, 2))) if wins else ''}
{('<h2>Title bouts, in order</h2>' + table(BH, [brow(b, rel) for b in reversed(titles)], num=(5,))) if titles else ''}'''
        out.append((f'ufc/divisions/{k}/index.html', page(site=site, sport='ufc', depth=3, title=f'UFC {dlab(k)} · every title bout and record · APEX', desc=f'The UFC {dlab(k)} division: {len(bb):,} bouts, {len(titles)} title bouts, {ys[0]}–{ys[-1]}.', crumbs=[('Sportsfans', rel), ('UFC bouts', rel + 'ufc/'), ('Divisions', rel + 'ufc/divisions/'), (dlab(k), None)], body=body, path=f'ufc/divisions/{k}/', v=v)))
    # venues
    for vid, vv in V.items():
        rel = '../../../'; es = [E_[i] for i in vv['events'] if i in E_]; bs = [b for e in es for b in by_e[e['id']]]; divs = collections.Counter(b['div'] for b in bs)
        body = f'''<p class="eyebrow">UFC bouts · Venue · {vv['first']}–{vv['last']}</p><h1>{E(vv['name'])}</h1>
<p class="lede">{' · '.join(E(x) for x in (vv['city'], vv['country']) if x and x != vv['name'])}. {len(es)} event{'' if len(es) == 1 else 's'} and {len(bs)} bouts, {sum(1 for b in bs if b['title'])} of them title bouts.{f' Busiest division: {E(dlab(divs.most_common(1)[0][0]))}.' if divs else ''} Venues are listed as the sources name them, never drawn.</p>
<a class="open" href="{rel}ufc/#tab=venues&venue={vid}">Open in the atlas →</a>
{kpis([('Events', len(es), ''), ('Bouts', len(bs), ''), ('Title bouts', sum(1 for b in bs if b['title']), ''), ('Years', f'{vv["first"]}–{vv["last"]}', '')])}
<h2>Every card here</h2>{table(['Date', 'Event', 'Main event', 'Bouts'], [[f'<a class="q" href="{rel}ufc/seasons/{e["y"]}/">{E(e["date"])}</a>', el(e, rel), (who(by_e[e['id']][0], rel) + belt(by_e[e['id']][0])) if by_e[e['id']] else '—', len(by_e[e['id']])] for e in sorted(es, key=lambda e: e['date'], reverse=True)], num=(3,))}'''
        out.append((f'ufc/venues/{vid}/index.html', page(site=site, sport='ufc', depth=3, title=f'{vv["name"]} · UFC events · APEX', desc=f'UFC at {vv["name"]}: {len(es)} events, {len(bs)} bouts, {vv["first"]}–{vv["last"]}.', crumbs=[('Sportsfans', rel), ('UFC bouts', rel + 'ufc/'), ('Venues', rel + 'ufc/venues/'), (vv['name'], None)], body=body, path=f'ufc/venues/{vid}/', v=v)))
    rel = '../../'
    out.append(('ufc/seasons/index.html', page(site=site, sport='ufc', depth=2, title='UFC year by year, 1993–2026 · APEX', desc='Every year of UFC bouts on its own page.', crumbs=[('Sportsfans', rel), ('UFC bouts', rel + 'ufc/'), ('Years', None)], body=f'<p class="eyebrow">UFC bouts</p><h1>Every <span>year</span></h1><p class="lede">{len(years)} years with a card.</p>' + index_list([(str(y), f'ufc/seasons/{y}/', f'{len(by_year[y])} events · {sum(len(by_e[e["id"]]) for e in by_year[y])} bouts') for y in reversed(years)], rel), path='ufc/seasons/', v=v)))
    out.append(('ufc/events/index.html', page(site=site, sport='ufc', depth=2, title='Every UFC event · APEX', desc='Every UFC event on its own page, with every bout.', crumbs=[('Sportsfans', rel), ('UFC bouts', rel + 'ufc/'), ('Events', None)], body=f'<p class="eyebrow">UFC bouts</p><h1>Every <span>event</span></h1><p class="lede">{len(A["events"])} events.</p>' + index_list([(e['name'], f'ufc/events/{e["id"]}/', f'{e["date"]} · {len(by_e[e["id"]])} bouts') for e in reversed(A['events'])], rel), path='ufc/events/', v=v)))
    out += index_pages(site=site, sport='ufc', title='UFC fighters · APEX', desc='Every fighter with a bout in the archive.', crumbs=[('Sportsfans', rel), ('UFC bouts', rel + 'ufc/'), ('Fighters', None)], intro=f'<p class="eyebrow">UFC bouts</p><h1>Every <span>fighter</span></h1><p class="lede">{len(by_f):,} fighters with a bout.</p>', items=sorted([(pn(i), f'ufc/fighters/{slug(i)}/', f'{sum(1 for b in bb if b["w"] == i)}–{sum(1 for b in bb if b["res"] == "W" and b["w"] != i)} · {len(bb)} bouts') for i, bb in by_f.items()], key=lambda t: (t[0].split(' ')[-1], t[0], t[1])), dir='ufc/fighters', v=v)
    out.append(('ufc/divisions/index.html', page(site=site, sport='ufc', depth=2, title='UFC divisions · APEX', desc='Every division with a bout in the archive.', crumbs=[('Sportsfans', rel), ('UFC bouts', rel + 'ufc/'), ('Divisions', None)], body=f'<p class="eyebrow">UFC bouts</p><h1>Every <span>division</span></h1>' + index_list([(dlab(d['key']), f'ufc/divisions/{d["key"]}/', f'{len(by_d[d["key"]]):,} bouts') for d in A['divisions'] if by_d[d['key']]], rel), path='ufc/divisions/', v=v)))
    out.append(('ufc/venues/index.html', page(site=site, sport='ufc', depth=2, title='UFC venues · APEX', desc='Every venue that has staged a UFC event, listed.', crumbs=[('Sportsfans', rel), ('UFC bouts', rel + 'ufc/'), ('Venues', None)], body=f'<p class="eyebrow">UFC bouts</p><h1>Every <span>venue</span></h1><p class="lede">{len(V)} venues, listed as the sources name them.</p>' + index_list(sorted([(vv['name'], f'ufc/venues/{vid}/', f'{vv["n"]} events · {", ".join(x for x in (vv["city"], vv["country"]) if x and x != vv["name"])}') for vid, vv in V.items()], key=lambda t: (-int(t[2].split(' ')[0]), t[0])), rel), path='ufc/venues/', v=v)))
    return out
