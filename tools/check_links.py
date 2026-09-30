#!/usr/bin/env python3
"""Every relative link and asset reference in docs/ must resolve to a file. Run after build.py."""
import pathlib, re, sys, urllib.parse
ROOT = pathlib.Path(__file__).resolve().parent.parent; DOCS = ROOT/'docs'
href = re.compile(r'''(?:href|src)=["']([^"'#?]+)(?:[?#][^"']*)?["']''')
bad = []; n = 0; checked = 0
for f in DOCS.rglob('*.html'):
    n += 1; txt = f.read_text(encoding='utf-8', errors='replace')
    for m in href.finditer(txt):
        u = m.group(1)
        if re.match(r'^(https?:|mailto:|data:|//)', u) or '${' in u: continue
        checked += 1
        target = (DOCS if u.startswith('/') else f.parent) / urllib.parse.unquote(u.lstrip('/'))
        if target.is_dir(): target = target/'index.html'
        if not target.exists(): bad.append((str(f.relative_to(DOCS)), u))
print(f'{n:,} pages, {checked:,} internal references, {len(bad)} broken')
for b in bad[:20]: print('  ', *b)
sys.exit(1 if bad else 0)
