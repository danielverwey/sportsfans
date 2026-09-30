"""What the Summer Olympics tools share: the slug, the event lineage key (the same event across Games, whatever a year's
list called it) and the category read from an event's name or its section heading. Used by tools/prepare_olympics.py,
tools/sweepers/olympics.py and tools/audit_olympics.py so that all three agree."""
import re, unicodedata

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('ascii').lower().replace('’', '').replace("'", '')).strip('-')

def lineage(sport, gender, name):
    """'100 metres', '100 m' and '100m' are one event; 'Men's 100 metres' under Athletics is the same as '100 metres' under 'Men's events'."""
    n = name.strip()
    n = re.sub(r"^(Men's|Women's|Mixed|Open|Men|Women)\s+", '', n, flags=re.I)
    n = re.sub(r'(\d),(\d{3})', r'\1\2', n)
    n = re.sub(r'(\d)\s*[×x]\s*(\d)', r'\1×\2', n)
    n = re.sub(r'(\d)\s*(metres|meters|metre|meter|m)\b', r'\1 m', n, flags=re.I)
    n = re.sub(r'\bmeter\b', 'metre', n, flags=re.I)
    n = re.sub(r'\s+', ' ', n).strip(' :').lower()
    return f'{slug(sport)}|{gender.lower()}|{slug(n) or "event"}'

def gender_of(name, section='', url=''):
    """Men, Women, Mixed or Open: from the event's own name first, then from the title of the event's article (the part
    after the dash in 'Wrestling at the 1980 Summer Olympics – Men's freestyle 48 kg'), then from the heading the table sits under."""
    import urllib.parse
    tail = urllib.parse.unquote(str(url or '')).replace('_', ' ')
    tail = tail.split('–', 1)[1] if '–' in tail else ''
    for t in (name or '', tail, section or ''):
        m = re.match(r"\s*(men|women|mixed|open)\b", t, re.I)
        if m: return m.group(1).capitalize()
        if re.search(r"\bwomen'?s?\b|\bgirls?\b|\bladies\b", t, re.I): return 'Women'
        if re.search(r"\bmen'?s?\b|\bboys?\b", t, re.I): return 'Men'
        if re.search(r'\bmixed\b', t, re.I): return 'Mixed'
        if re.search(r'\bopen\b', t, re.I): return 'Open'
    return 'Open'
