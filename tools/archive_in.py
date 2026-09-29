"""Read an archive from whatever a reader produced: a .json file, a gzipped .json.gz, or a prototype page with the
archive embedded in one of its <script> blocks (plain JSON, a `const X = {...};` assignment, or a gzip+base64 string).

    from archive_in import load_archive
    D = load_archive(path, need=('games', 'teams'))   # the first object that carries every key in `need`

Nothing is changed; the object comes back exactly as the reader wrote it.
"""
import base64, gzip, json, pathlib, re

def _parse(text):
    try: return json.loads(text)
    except (ValueError, TypeError): return None

def _candidates(body):
    t = body.strip()
    yield t
    m = re.match(r'^(?:window\.[\w$]+|(?:const|let|var)\s+[\w$]+)\s*=\s*', t)   # const DATA = {...};
    if m: yield t[m.end():].rstrip().rstrip(';')
    for b64 in re.findall(r'["\'`](H4sI[A-Za-z0-9+/=\s]{80,})["\'`]', t):       # gzip, base64
        try: yield gzip.decompress(base64.b64decode(re.sub(r'\s+', '', b64))).decode('utf-8')
        except Exception: pass
    if re.fullmatch(r'[A-Za-z0-9+/=\s]{200,}', t) and t.lstrip().startswith('H4sI'):
        try: yield gzip.decompress(base64.b64decode(re.sub(r'\s+', '', t))).decode('utf-8')
        except Exception: pass

def load_archive(path, need):
    p = pathlib.Path(path); raw = p.read_bytes()
    if raw[:2] == b'\x1f\x8b': raw = gzip.decompress(raw)
    text = raw.decode('utf-8-sig', 'replace'); found = []
    if text.lstrip().startswith(('{', '[')):
        d = _parse(text)
        if isinstance(d, dict) and all(k in d for k in need): return d
        if isinstance(d, dict): found.append(sorted(d)[:12])
    for body in re.findall(r'<script\b[^>]*>(.*?)</script>', text, re.S | re.I):
        if len(body) < 200: continue
        for cand in _candidates(body):
            d = _parse(cand) if isinstance(cand, str) else None
            if isinstance(d, dict):
                if all(k in d for k in need): return d
                found.append(sorted(d)[:12])
    raise SystemExit(f'{p.name}: no archive carrying {", ".join(need)} was found in it'
                     + (f' (objects seen had keys like {found[:3]})' if found else ' (no JSON object in the file or its script blocks)'))
