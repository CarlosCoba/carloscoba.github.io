#!/usr/bin/env python3
"""Convert _bibliography/publications.bib into _data/publications.json.

Jekyll (Minimal Mistakes) then renders the list on the Publications page, with
every entry linking to its NASA ADS record. Standard library only.

Usage:  python3 scripts/bib2json.py
"""
import html
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "_bibliography" / "publications.bib"
OUT = ROOT / "_data" / "publications.json"

# Surnames that identify you in author lists (accents and case are ignored).
AUTHOR_SURNAMES = ["López-Cobá", "López Cobá", "Coba"]
MAX_AUTHORS_SHOWN = 8

# --------------------------------------------------------------------------
# BibTeX parsing (small, dependency-free; handles ADS exports)
# --------------------------------------------------------------------------
# Journal macros used in ADS / AAS BibTeX exports.
JOURNALS = {
    "aj": "AJ", "actaa": "Acta Astron.", "araa": "ARA&A", "apj": "ApJ",
    "apjl": "ApJL", "apjs": "ApJS", "ao": "Appl. Opt.", "apss": "Ap&SS",
    "aap": "A&A", "aapr": "A&A Rev.", "aaps": "A&AS", "azh": "AZh",
    "baas": "BAAS", "jrasc": "JRASC", "memras": "MmRAS", "mnras": "MNRAS",
    "pra": "Phys. Rev. A", "prb": "Phys. Rev. B", "prc": "Phys. Rev. C",
    "prd": "Phys. Rev. D", "pre": "Phys. Rev. E", "prl": "Phys. Rev. Lett.",
    "pasp": "PASP", "pasj": "PASJ", "pasa": "PASA", "qjras": "QJRAS",
    "skytel": "Sky & Telescope", "solphys": "Sol. Phys.", "sovast": "Soviet Ast.",
    "ssr": "Space Sci. Rev.", "zap": "ZAp", "nat": "Nature", "iaucirc": "IAU Circ.",
    "aplett": "Astrophys. Lett.", "apspr": "Astrophys. Space Phys. Res.",
    "bain": "Bull. Astron. Inst. Netherlands", "fcp": "Fund. Cosmic Phys.",
    "gca": "Geochim. Cosmochim. Acta", "grl": "Geophys. Res. Lett.",
    "jcp": "J. Chem. Phys.", "jgr": "J. Geophys. Res.", "jqsrt": "JQSRT",
    "memsai": "Mem. Soc. Astron. Italiana", "nphysa": "Nucl. Phys. A",
    "physrep": "Phys. Rep.", "physscr": "Phys. Scr.", "planss": "Planet. Space Sci.",
    "procspie": "Proc. SPIE", "rmxaa": "RMxAA", "rmxac": "RMxAC", "jcap": "JCAP",
    "na": "New Astron.", "nar": "New Astron. Rev.", "icarus": "Icarus",
}

ACCENTS = {"'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308",
           "~": "\u0303", "=": "\u0304", ".": "\u0307", "u": "\u0306",
           "v": "\u030c", "H": "\u030b", "c": "\u0327", "k": "\u0328"}
SYMBOLS = {r"\ss": "ß", r"\o": "ø", r"\O": "Ø", r"\aa": "å", r"\AA": "Å",
           r"\ae": "æ", r"\AE": "Æ", r"\l": "ł", r"\L": "Ł", r"\i": "ı",
           r"\&": "&", r"\%": "%", r"\$": "$", r"\_": "_", "~": "\u00a0",
           "---": "\u2014", "--": "\u2013"}
GREEK = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
         "kappa", "lambda", "mu", "nu", "xi", "pi", "rho", "sigma", "tau",
         "phi", "chi", "psi", "omega", "Gamma", "Delta", "Theta", "Lambda",
         "Xi", "Pi", "Sigma", "Phi", "Psi", "Omega"]
MATH = {r"\sim": "~", r"\approx": "≈", r"\lesssim": "≲", r"\gtrsim": "≳",
        r"\leq": "≤", r"\geq": "≥", r"\le": "≤", r"\ge": "≥", r"\times": "×",
        r"\pm": "±", r"\odot": "⊙", r"\sun": "☉", r"\prime": "′", r"\AA": "Å",
        r"\,": "\u2009", r"\ ": " ", r"\infty": "∞"}


def latex_to_text(s):
    """Convert the LaTeX commonly found in titles/authors to plain Unicode."""
    if not s:
        return ""
    s = re.sub(r"\\ensuremath\s*", "", s)
    s = re.sub(r"\{\\\^a\}[\u0080-\u009f]+", "\u2009", s)  # ADS mojibake of a thin space ("H II")
    s = re.sub(r"[\u0080-\u009f]", "", s)
    # \'{e}, \'e, {\'e}
    s = re.sub(r"\\([`'^\"~=.])\s*\{?\\?([A-Za-z])\}?",
               lambda m: unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)]), s)
    s = re.sub(r"\\([uvHck])\s*\{\\?([A-Za-z])\}",
               lambda m: unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)]), s)
    s = re.sub(r"\\([uvHck]) ([A-Za-z])",
               lambda m: unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)]), s)
    for g in GREEK:
        s = re.sub(r"\\" + g + r"(?![A-Za-z])", unicodedata.lookup(
            ("GREEK CAPITAL LETTER " if g[0].isupper() else "GREEK SMALL LETTER ")
            + ("LAMDA" if g.lower() == "lambda" else g.upper())), s)
    for k, v in MATH.items():
        s = s.replace(k, v)
    for k, v in sorted(SYMBOLS.items(), key=lambda kv: -len(kv[0])):
        s = re.sub(re.escape(k) + (r"(?![A-Za-z])" if k[-1].isalpha() else ""), v, s)
    # \textit{...}, \emph{...}, \rm etc. -> keep content
    s = re.sub(r"\\(?:textit|textbf|emph|textrm|mathrm|mathit|text|rm|it|bf|mbox)\b\s*", "", s)
    # math sub/superscripts: keep them readable
    s = re.sub(r"\^\{?([^{}\s$])\}?", r"^\1", s)
    s = s.replace("$", "")
    s = re.sub(r"\\([A-Za-z]+)", r"\1", s)  # unknown macros: drop the backslash
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def _read_value(text, i):
    """Read a BibTeX field value starting at text[i]. Returns (value, new_i)."""
    parts = []
    n = len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        c = text[i]
        if c == "{":
            depth, j = 0, i
            while j < n:
                if text[j] == "{" and text[j - 1] != "\\":
                    depth += 1
                elif text[j] == "}" and text[j - 1] != "\\":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            parts.append(("lit", text[i + 1:j]))
            i = j + 1
        elif c == '"':
            j, depth = i + 1, 0
            while j < n and not (text[j] == '"' and depth == 0 and text[j - 1] != "\\"):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                j += 1
            parts.append(("lit", text[i + 1:j]))
            i = j + 1
        else:
            m = re.match(r"[^\s,#}]+", text[i:])
            tok = m.group(0) if m else ""
            parts.append(("lit", tok) if tok.isdigit() else ("macro", tok))
            i += len(tok)
        while i < n and text[i].isspace():
            i += 1
        if i < n and text[i] == "#":
            i += 1
            continue
        break
    return parts, i


def parse_bib(text):
    entries, strings = [], {}
    for m in re.finditer(r"@(\w+)\s*[{(]", text):
        etype = m.group(1).lower()
        i = m.end()
        if etype in ("comment", "preamble"):
            continue
        fields = {}
        if etype == "string":
            fm = re.match(r"\s*([\w\-:.]+)\s*=\s*", text[i:])
            if fm:
                parts, _ = _read_value(text, i + fm.end())
                strings[fm.group(1).lower()] = "".join(v for _, v in parts)
            continue
        km = re.match(r"\s*([^,\s]+)\s*,", text[i:])
        if not km:
            continue
        key = km.group(1)
        i += km.end()
        while True:
            fm = re.match(r"\s*([\w\-:.]+)\s*=\s*", text[i:])
            if not fm:
                break
            name = fm.group(1).lower()
            parts, i = _read_value(text, i + fm.end())
            fields[name] = parts
            cm = re.match(r"\s*,", text[i:])
            if not cm:
                break
            i += cm.end()
        entries.append((etype, key, fields))

    resolved = []
    for etype, key, fields in entries:
        rec = {"type": etype, "key": key}
        for name, parts in fields.items():
            out = []
            for kind, v in parts:
                if kind == "macro":
                    low = v.lower().lstrip("\\")
                    out.append(strings.get(low, JOURNALS.get(low, MONTHS_TXT.get(low, v))))
                else:
                    out.append(v)
            rec[name] = "".join(out)
        resolved.append(rec)
    return resolved


MONTHS_TXT = {m: m for m in ["jan", "feb", "mar", "apr", "may", "jun",
                             "jul", "aug", "sep", "oct", "nov", "dec"]}
MONTH_NUM = {m: i + 1 for i, m in enumerate(MONTHS_TXT)}


# --------------------------------------------------------------------------
# Publication formatting
# --------------------------------------------------------------------------
ADS = "https://ui.adsabs.harvard.edu"
BIBCODE_RE = re.compile(r"^\d{4}[A-Za-z&.]{1,5}[\w.&]{4}[\w.]{5}[A-Z.]$")


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(s):
    return re.sub(r"[^a-z]", "", strip_accents(s).lower())


MY_NAMES = {norm(n) for n in AUTHOR_SURNAMES}


def split_authors(raw):
    depth, cur, out, i = 0, "", [], 0
    while i < len(raw):
        c = raw[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if depth == 0 and raw[i:i + 5].lower() == " and " :
            out.append(cur)
            cur, i = "", i + 5
            continue
        cur += c
        i += 1
    out.append(cur)
    return [a.strip() for a in out if a.strip()]


def format_author(a):
    a = latex_to_text(a)
    if a.lower() == "others":
        return "et al.", "", False
    if "," in a:
        last, first = [p.strip() for p in a.split(",", 1)]
        first = first.split(",")[-1].strip()  # drop Jr. etc.
    else:
        bits = a.split()
        last, first = bits[-1], " ".join(bits[:-1])
    initials = " ".join(
        "-".join(p[0] + "." for p in w.split("-") if p) if not w.endswith(".") else w
        for w in first.replace(".", ". ").split() if w)
    is_me = norm(last) in MY_NAMES
    return last, initials, is_me


def ads_link(p):
    """Best NASA ADS link for an entry: adsurl > bibcode > DOI > arXiv > title search."""
    if p.get("adsurl"):
        url = p["adsurl"].strip()
        return url.replace("http://adsabs.harvard.edu", ADS).replace(
            "https://adsabs.harvard.edu", ADS)
    for cand in (p.get("bibcode", ""), p["key"]):
        cand = cand.strip()
        if len(cand) == 19 and BIBCODE_RE.match(cand):
            return f"{ADS}/abs/{cand.replace('&', '%26')}/abstract"
    if p.get("doi"):
        return f'{ADS}/search/q=doi%3A%22{p["doi"].strip()}%22'
    if p.get("eprint"):
        return f'{ADS}/search/q=arXiv%3A{p["eprint"].strip()}'
    return f'{ADS}/search/q=title%3A%22{html.escape(latex_to_text(p.get("title", "")))}%22'


def venue(p):
    raw = (p.get("journal") or p.get("booktitle") or p.get("school") or p.get("howpublished") or "").strip()
    m = re.fullmatch(r"\\(\w+)", raw)
    j = JOURNALS.get(m.group(1).lower(), m.group(1)) if m else latex_to_text(raw)
    if p["type"] == "phdthesis" and not j:
        j = "PhD thesis"
    if j.lower() in ("arxiv e-prints", "arxiv") and p.get("eprint"):
        return f"arXiv:{p['eprint']}"
    bits = [j] if j else []
    if p.get("volume"):
        bits.append(p["volume"])
    if p.get("pages"):
        bits.append(latex_to_text(p["pages"]))
    return ", ".join(bits)


def is_refereed(p):
    j = venue(p).lower()
    return (p["type"] == "article" and bool(j) and not any(x in j for x in ("arxiv", "abstracts", "vizier", "data catalog", "e-prints")) and "yCat" not in p["key"])


def author_list(p):
    authors = [format_author(a) for a in split_authors(p.get("author", ""))]
    shown = authors[:MAX_AUTHORS_SHOWN]
    names = []
    for last, ini, me in shown:
        txt = html.escape(f"{last}, {ini}" if ini else last)
        names.append(f"<strong>{txt}</strong>" if me else txt)
    out = "; ".join(names)
    if len(authors) > MAX_AUTHORS_SHOWN:
        out += f"; et al. ({len(authors)} authors"
        hidden = [a for a in authors[MAX_AUTHORS_SHOWN:] if a[2]]
        if hidden:
            out += f", incl. <strong>{html.escape(hidden[0][0] + ', ' + hidden[0][1])}</strong>"
        out += ")"
    return out, bool(authors) and authors[0][2]


def main():
    pubs = parse_bib(BIB.read_text(encoding="utf-8"))

    def sort_key(p):
        y = int(re.sub(r"\D", "", p.get("year", "0")) or 0)
        m = p.get("month", "").strip().lower()
        return (y, MONTH_NUM.get(m[:3], int(m) if m.isdigit() else 0))

    pubs.sort(key=sort_key, reverse=True)
    records = []
    for p in pubs:
        authors, first = author_list(p)
        records.append({
            "year": p.get("year", "n.d."),
            "title": latex_to_text(p.get("title", "Untitled")),
            "authors": authors,
            "venue": venue(p),
            "ads": ads_link(p),
            "doi": p.get("doi", "").strip(),
            "arxiv": p.get("eprint", "").strip(),
            "first_author": first,
            "refereed": is_refereed(p),
        })
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(records)} publications "
          f"({sum(r['refereed'] for r in records)} refereed, "
          f"{sum(r['first_author'] for r in records)} first-author) -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
