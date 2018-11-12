"""
Parsing of properties out of notes.
"""
import re
import urllib
import uuid


PROP_NAMES = {
    "title",
    "folder",
    "tag",
}
PTN_PROP = re.compile(r'(%s):\s*(.*)' % "|".join(PROP_NAMES))
PTN_DURATION = re.compile(r"\s*(\d+(\.\d*)?)\s*(s|sec|m|min|h|hr|hour|d|dy|day|w|wk|week|mo|mon|month|y|yr|year)")


def parse_note(content):
    """
    Parse a note into a set of properties.
    :returns:  A {} with named properties.
    """
    lines = content.split("\n")
    raw = []
    props = {}
    for line in lines:
        m = PTN_PROP.match(line)
        if m is None:
            if not line.strip():
                line = ""
            raw.append(line)
        else:
            prop_name = m.group(1)
            prop_value = m.group(2).lower().strip()
            if prop_name == "tag":
                tags = re.split(r'[\s,;]+', prop_value)
                if "tag" in props:
                    props["tag"] += tags
                else:
                    props["tag"] = tags
            else:
                props[prop_name] = prop_value
    # remove initial/trailing blank lines
    while raw[:1] == [""]:
        raw.pop(0)
    while raw[-1:] == [""]:
        raw.pop(-1)
    # default title
    if "title" not in props:
        # initial line by itself
        if len(raw) == 1 or raw[1:2] == [""] and len(raw[0]) < 100:
            props["title"] = raw[0]
    if "title" not in props:
        # try harder
        if raw:
            props["title"] = raw[0][:40] + "..."
        else:
            props["title"] = ""
    props["raw"] = "\n".join(raw)
    return props

def note_filename(note_props):
    """
    Generate a relative path/filename for a note, given its properties.
    :returns:  relative path/filename, or None.
    """
    path = None
    title = note_props.get("title")
    if title:
        path = urllib.quote_plus(title)
    folder = note_props.get("folder")
    if folder:
        folder = urllib.quote(folder)
        if not path:
            path = random_name()
        path = folder + "/" + path
    return path

def random_name():
    """
    Random placeholder name.
    """
    return str(uuid.uuid4()).replace("-", "")[:16]

def parse_duration(spec):
    spec = spec.lower()
    m = PTN_DURATION.match(spec)
    if m is not None:
        amt = float(m.group(1))
        unit = m.group(3)
        if unit in {"s", "sec"}:
            return amt
        if unit in {"m", "min"}:
            return amt*60
        if unit in {"h", "hr", "hour"}:
            return amt*3600
        if unit in {"d", "dy", "day"}:
            return amt*86400
        if unit in {"w", "wk", "week"}:
            return amt*86400*7
        if unit in {"mo", "mon", "month"}:
            return amt*86400*30
        if unit in {"y", "yr", "year"}:
            return amt*86400*30

def parse_search_spec(spec):
    """
    Generate a function to test a given parsed note, as returned from parse_note().
    """
    spec = spec.lower()
    filters = []
    highlights = []
    spec2 = ""
    def f_tag(v):
        return lambda r: v in r.get("tag",[])
    def f_folder(v):
        return lambda r: r.get("folder", "") == v
    def f_age_lt(v):
        return lambda r: r.get("age", 0) < v
    def f_age_gt(v):
        return lambda r: r.get("age", 0) > v
    def f_word(v):
        return lambda r: v in r.get("raw", "").lower() or v in r.get("tag",[])
    p_last = 0
    for m in re.finditer(r'(tag|folder|recent|older)=([^,;\s]+)', spec):
        spec2 += spec[p_last:m.start()]
        p_last = m.end()
        prop_name = m.group(1)
        prop_value = m.group(2)
        if prop_name == "tag":
            filters.append(f_tag(prop_value))
            highlights.append(r'^tag:.*[,;\s](%s)([,;\s]|$)' % re.escape(prop_value))
        elif prop_name == "folder":
            filters.append(f_folder(prop_value))
            highlights.append(r'^(folder:.*)')
        elif prop_name == "recent":
            amount = parse_duration(prop_value)
            if amount:
                filters.append(f_age_lt(amount))
        elif prop_name == "older":
            amount = parse_duration(prop_value)
            if amount:
                filters.append(f_age_gt(amount))
    spec2 += spec[p_last:]
    for part in re.split(r'[,;]', spec2):
        part = re.sub(r'\s+', part, " ")
        part = part.strip().lower()
        if part:
            filters.append(f_word(part))
            highlights.append(r'(%s)' % re.escape(part))
    def overall(r):
        for f in filters:
            if not f(r):
                return False
        return True
    return overall, highlights
