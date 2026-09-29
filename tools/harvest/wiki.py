"""Shared Wikipedia reading for the sweepers: the rendered article through the MediaWiki API (with its revision and a
hash of what was read), tables expanded into plain grids, and the small cell readers every sweeper needs."""
import hashlib, html, re, sys, pathlib, unicodedata, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import get_json

API = 'https://en.wikipedia.org/w/api.php'

class Page:
    def __init__(self, title, soup, revid, sha256): self.title, self.soup, self.revid, self.sha256 = title, soup, revid, sha256
    @property
    def url(self): return 'https://en.wikipedia.org/wiki/' + self.title.replace(' ', '_')

def parse_page(title):
    """The article as rendered HTML (BeautifulSoup), following redirects; None if it does not exist."""
    from bs4 import BeautifulSoup
    j = get_json(API + '?' + urllib.parse.urlencode({'action': 'parse', 'prop': 'text|revid', 'format': 'json', 'formatversion': 2, 'redirects': 1, 'disabletoc': 1, 'page': title}), pause=1.0)
    if 'error' in j or 'parse' not in j: return None
    text = j['parse']['text']
    return Page(j['parse'].get('title') or title, BeautifulSoup(text, 'lxml'), j['parse'].get('revid'), hashlib.sha256(text.encode('utf-8')).hexdigest())

def page_from_html(title, text, revid=None):
    from bs4 import BeautifulSoup
    return Page(title, BeautifulSoup(text, 'lxml'), revid, hashlib.sha256(text.encode('utf-8')).hexdigest())

def grid(table):
    """Expand rowspans and colspans into a plain matrix of cells (the same cell object repeats where it spans)."""
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
            for _ in range(cs):
                row.append(cell)
                if rs > 1: pending[col] = (cell, rs - 1)
                col += 1
        matrix.append(row)
    return matrix

def text(cell, keep_sup=False):
    """The cell's text, footnote markers and (unless asked) superscripts left out; the cell itself is not altered."""
    if cell is None: return ''
    import copy
    c = copy.copy(cell)
    for x in c.find_all(['style', 'script']): x.decompose()
    for x in c.find_all('sup'):
        if keep_sup and 'reference' not in (x.get('class') or []): continue
        x.decompose()
    for x in c.find_all(class_=re.compile(r'reference|sortkey|mw-ref')): x.decompose()
    return re.sub(r'\s+', ' ', c.get_text(' ', strip=True)).replace(' ,', ',').strip()

def sups(cell):
    """Superscripts that are not footnote markers (a sprint position in a MotoGP standings cell, for instance)."""
    if cell is None: return []
    return [re.sub(r'\s+', '', s.get_text('', strip=True)) for s in cell.find_all('sup') if 'reference' not in (s.get('class') or []) and not s.find_parent(class_='reference')]

def link_title(cell):
    """The first article the cell links to (not files, flags, footnotes or red links)."""
    if cell is None: return None
    for a in cell.find_all('a', href=True):
        h = a['href']
        if a.find_parent(class_=re.compile('flagicon|reference')) or 'redlink' in h: continue
        if h.startswith('/wiki/') and ':' not in h[6:]: return urllib.parse.unquote(html.unescape(h[6:].split('#')[0])).replace('_', ' ')
    return None

def flag(cell):
    """The country a cell's flag icon stands for, if any."""
    if cell is None: return ''
    f = cell.find(class_=re.compile('flagicon'))
    if f:
        img = f.find('img'); a = f.find('a')
        for v in ((a.get('title') if a else None), (img.get('alt') if img else None)):
            if v: return re.sub(r'^Flag of (the )?', '', v).strip()
    return ''

def headed(soup, words, tag=('h2', 'h3', 'h4')):
    """Tables under a heading that contains every word in words (case-insensitive), in page order."""
    out = []
    for t in soup.find_all('table', class_=re.compile('wikitable')):
        h = t.find_previous(list(tag)); ht = text(h).lower() if h else ''
        if all(w in ht for w in words): out.append(t)
    return out

fold = lambda s: re.sub(r'[^a-z0-9]+', '', unicodedata.normalize('NFKD', (s or '').replace('ı', 'i')).encode('ascii', 'ignore').decode().lower())
slug = lambda s: re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', (s or '').replace('ı', '')).encode('ascii', 'ignore').decode().lower()).strip('-')
title_of_url = lambda u: urllib.parse.unquote(u.split('/wiki/')[-1]).replace('_', ' ') if u and '/wiki/' in u else None
