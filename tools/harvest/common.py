"""Shared pieces for the sweepers: a polite HTTP client, JSON helpers, a change report."""
import json, pathlib, time, urllib.request, urllib.error, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DATA = ROOT/'data'
UA = 'sportsfans.co.za atlas sweeper (https://sportsfans.co.za/licences/; non-commercial) python-urllib'

def get(url, *, retries=3, pause=0.6, timeout=60, headers=None):
    """GET with a descriptive User-Agent, a pause between calls and a short retry on 5xx/429."""
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json, text/plain, */*', **(headers or {})})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read(); time.sleep(pause); return body
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504): time.sleep(5 * (attempt + 1)); continue
            raise
        except urllib.error.URLError as e:
            last = e; time.sleep(5 * (attempt + 1))
    raise RuntimeError(f'{url}: {last}')

def get_json(url, **kw): return json.loads(get(url, **kw).decode('utf-8'))

def load(name): return json.loads((DATA/f'{name}.json').read_text(encoding='utf-8'))
def save(name, obj):
    """Write compact JSON exactly as the atlases embed it (no trailing newline, UTF-8, keys in insertion order)."""
    (DATA/f'{name}.json').write_text(json.dumps(obj, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

def today_long(): return datetime.date.today().strftime('%-d %B %Y')
def report(lines, path):
    path = ROOT/'build'/'harvest'/path; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('\n'.join(lines) + '\n', encoding='utf-8'); print('\n'.join(lines))
