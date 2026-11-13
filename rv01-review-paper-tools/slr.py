#!/usr/bin/env python3
# slr.py - personal systematic-review workflow tool.
#
# One project folder holds everything. Typical order (details: the step-by-step documents):
#   python slr.py init   my_review --title "..." --type systematic
#   python slr.py import                 # read exports from 01_exports/<pubmed|wos|scopus|ieee>/
#   python slr.py dedupe                 # unique + duplicates, logged
#   python slr.py screen [--apply]       # screening sheet + keyword flags (flags only unless --apply)
#   python slr.py number                 # permanent paper numbers P001, P002 ... for selected papers
#   python slr.py access                 # open access vs subscription (Unpaywall)
#   python slr.py batches                # HTML pages of 10 papers; python slr.py tabs open 1
#   python slr.py pdfmatch               # match downloaded PDFs, rename, sort journal/conference
#   python slr.py prisma                 # PRISMA numbers -> prisma.json
#   python slr.py pack                   # PDFs -> compact Word parts for AI upload
#   python slr.py cite draft.docx        # [P012] tags -> numbered citations + reference list, checks tags
#   python slr.py comments draft.docx    # Word comments/highlights -> next revision prompt
#   python slr.py status                 # counts at every stage
#
# Needs only Python 3.9+. Optional: pypdf (PDF text), python-docx (Word files), openpyxl (.xlsx exports).
# Environment: UNPAYWALL_EMAIL (or CONTACT_EMAIL) for `access`. Nothing is sent anywhere else.
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

UNPAYWALL = os.environ.get('UNPAYWALL_BASE', 'https://api.unpaywall.org/v2')
UA = 'slr.py/1.0 (personal systematic review tool)'

DB_LABELS = {'pubmed': 'PubMed', 'wos': 'Web of Science', 'scopus': 'Scopus', 'ieee': 'IEEE Xplore'}
DB_ALIASES = {
    'pubmed': 'pubmed', 'medline': 'pubmed', 'pm': 'pubmed', 'ncbi': 'pubmed',
    'wos': 'wos', 'webofscience': 'wos', 'web_of_science': 'wos', 'web-of-science': 'wos', 'savedrecs': 'wos',
    'scopus': 'scopus',
    'ieee': 'ieee', 'ieeexplore': 'ieee', 'ieee_xplore': 'ieee', 'ieee-xplore': 'ieee',
}
DB_SHORT = {'pubmed': 'PM', 'wos': 'WS', 'scopus': 'SC', 'ieee': 'IE'}
EXPORT_EXT = {'.txt', '.nbib', '.ris', '.bib', '.csv', '.tsv', '.xlsx'}

REC_FIELDS = ['uid', 'db', 'file', 'title', 'authors', 'year', 'venue', 'doi', 'pmid', 'abstract',
              'keywords', 'doc_type_raw', 'doc_type', 'url']
UNIQUE_FIELDS = REC_FIELDS + ['sources', 'n_found', 'merged_uids']
SCREEN_FIELDS = ['pid', 'uid', 'sources', 'title', 'authors', 'year', 'venue', 'doc_type', 'doi', 'pmid',
                 'keywords', 'abstract', 'kw_flag', 'kw_hits', 'ta_decision', 'ft_decision', 'reason', 'role',
                 'access', 'oa_url', 'landing_url', 'pdf_file', 'pdf_folder', 'notes']
TA_VALUES = {'', 'include', 'exclude', 'maybe'}
FT_VALUES = {'', 'include', 'exclude', 'not_retrieved'}
ROLE_VALUES = {'', 'main', 'supplementary'}
DOI_RE = re.compile(r'10\.\d{4,9}/[^\s"<>,;\]]+', re.I)


def die(msg):
    sys.exit('ERROR: ' + msg)


# ---------------------------------------------------------------- project paths / config
class Proj:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.cfg_path = self.root / 'project.json'
        self.exports = self.root / '01_exports'
        self.rec = self.root / '02_records'
        self.screen_dir = self.root / '03_screening'
        self.access_dir = self.root / '04_access'
        self.pdfs = self.root / '05_pdfs'
        self.pack_dir = self.root / '06_pack'
        self.draft = self.root / '07_draft'
        self.all_csv = self.rec / 'records_all.csv'
        self.unique_csv = self.rec / 'records_unique.csv'
        self.dups_csv = self.rec / 'duplicates.csv'
        self.screen_csv = self.screen_dir / 'screening.csv'
        self.import_log = self.rec / 'import_log.json'
        self.dedupe_log = self.rec / 'dedupe_log.json'
        self.keywords_json = self.root / 'keywords.json'

    def require(self):
        if not self.cfg_path.exists():
            die(f'{self.root} is not a project folder (project.json missing). '
                f'Run `python slr.py init <folder>` first, or use --project <folder>.')
        return self

    def cfg(self):
        base = {'title': '', 'review_type': 'systematic', 'research_questions': [], 'proxy_prefix': '',
                'library_home': '', 'library_search': '', 'batch_size': 10}
        if self.cfg_path.exists():
            base.update(json.loads(self.cfg_path.read_text(encoding='utf-8')))
        return base


# ---------------------------------------------------------------- small helpers
def norm_doi(d):
    if not d:
        return ''
    d = str(d).strip().lower()
    d = re.sub(r'^(https?://(dx\.)?doi\.org/|doi:\s*)', '', d)
    return d.strip().rstrip('.,;')


def clean_doi_match(s):
    s = s.rstrip('.,;:')
    while s.endswith(')') and s.count(')') > s.count('('):
        s = s[:-1].rstrip('.,;:')
    return s.lower()


def norm_title(t):
    t = unicodedata.normalize('NFKD', t or '')
    t = ''.join(c for c in t if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '', t.lower())


def clean_title(t):
    t = re.sub(r'\s+', ' ', (t or '').strip())
    if t.startswith('[') and re.search(r'\]\.?$', t):  # PubMed puts translated titles in [ ]
        t = t[1:]
        t = re.sub(r'\]\.?$', '', t)
    return t.rstrip('.').strip() if not t.endswith('...') else t


def get_year(s):
    m = re.search(r'(?<!\d)(19|20)\d{2}(?!\d)', str(s or ''))
    return m.group(0) if m else ''


def first_surname(authors):
    first = (authors or '').split(';')[0].strip()
    if not first:
        return ''
    if ',' in first:
        return first.split(',')[0].strip().lower()
    toks = [t for t in re.split(r'[\s.]+', first) if t]
    for t in toks:
        if len(t) > 2:
            return t.lower()
    return toks[0].lower() if toks else ''


def read_text_file(path):
    raw = Path(path).read_bytes()
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return raw.decode('utf-16')
    if raw[:3] == b'\xef\xbb\xbf':
        return raw[3:].decode('utf-8')
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('cp1252', errors='replace')


def read_csv(path, fields=None):
    p = Path(path)
    if not p.exists():
        return []
    try:
        with open(p, encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
    except UnicodeDecodeError:
        # Excel's plain "CSV (Comma delimited)" is Windows-1252, not UTF-8: read it anyway (the next write converts it to UTF-8)
        print(f'NOTE: {p.name} was not saved as "CSV UTF-8"; reading it as Windows-1252. Next time use Save As > CSV UTF-8.')
        with open(p, encoding='cp1252', errors='replace', newline='') as f:
            rows = list(csv.DictReader(f))
    if fields:
        out = []
        for r in rows:
            out.append({k: (r.get(k) or '') for k in fields})
        return out
    return rows


def write_csv(path, rows, fields):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:  # utf-8-sig: Excel opens it correctly
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')


def table(rows, headers):
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) if rows else len(str(h)) for i, h in enumerate(headers)]
    line = '  '.join(str(h).ljust(w) for h, w in zip(headers, widths))
    out = [line, '  '.join('-' * w for w in widths)]
    for r in rows:
        out.append('  '.join(str(c).ljust(w) for c, w in zip(r, widths)))
    return '\n'.join(out)


# ---------------------------------------------------------------- document type normalisation
def norm_type(raw, venue=''):
    s = (raw or '').lower()
    if re.search(r'conference|proceeding|cpaper|inproceedings|congress|meeting|symposium|workshop|\bconf\b', s):
        return 'conference'
    if re.search(r'preprint|posted-content|arxiv|unpublished', s):
        return 'preprint'
    if re.search(r'\bbook\b|chapter|\bchap\b|incollection|inbook', s):
        return 'book'
    if re.search(r'journal|article|\bjour\b|\bejour\b|review|early access|magazine|letter|editorial|note|short survey', s):
        return 'journal'
    v = (venue or '').lower()
    if re.search(r'\bproc(eedings)?\b|conference|symposium|workshop', v):
        return 'conference'
    return 'other'


# ---------------------------------------------------------------- export parsers
def parse_medline(text):
    """PubMed 'PubMed' format (.txt) and .nbib: tagged lines like 'TI  - Title'."""
    recs, cur, tag = [], None, None
    for line in text.splitlines():
        m = re.match(r'^([A-Z][A-Z0-9]{1,3})\s*-\s(.*)$', line)
        if m:
            tag, val = m.group(1), m.group(2).strip()
            if tag == 'PMID':
                cur = defaultdict(list)
                recs.append(cur)
            if cur is None:
                continue
            cur[tag].append(val)
        elif cur is not None and tag and line.startswith('      ') and cur[tag]:
            cur[tag][-1] += ' ' + line.strip()
    out = []
    for r in recs:
        doi = ''
        for k in ('LID', 'AID'):
            for v in r.get(k, []):
                if v.lower().endswith('[doi]'):
                    doi = v[:-5].strip()
                    break
            if doi:
                break
        authors = r.get('FAU') or r.get('AU') or []
        out.append({
            'title': ' '.join(r.get('TI', [])), 'authors': '; '.join(authors),
            'year': get_year((r.get('DP') or [''])[0]) or get_year((r.get('EDAT') or [''])[0]),
            'venue': (r.get('JT') or r.get('TA') or [''])[0], 'doi': doi, 'pmid': (r.get('PMID') or [''])[0],
            'abstract': ' '.join(r.get('AB', [])), 'keywords': '; '.join(r.get('OT', []) + r.get('MH', [])),
            'doc_type_raw': '; '.join(r.get('PT', [])), 'url': ''})
    return out


def parse_wos_tagged(text):
    """Web of Science 'Plain text file': two-letter tags, records end with 'ER'."""
    recs, cur, tag = [], None, None
    for line in text.splitlines():
        if line.startswith(('FN ', 'VR ')) or not line.strip():
            continue
        if line.strip() == 'EF':
            break
        if line.strip() == 'ER':
            if cur is not None:
                recs.append(cur)
            cur, tag = None, None
            continue
        if line.startswith('   ') and cur is not None and tag:
            cur[tag].append(line.strip())
            continue
        m = re.match(r'^([A-Z][A-Z0-9]) (.*)$', line)
        if m:
            tag = m.group(1)
            if cur is None:
                cur = defaultdict(list)
            cur[tag].append(m.group(2).strip())
    out = []
    for r in recs:
        join = lambda k: ' '.join(r.get(k, []))
        authors = r.get('AF') or r.get('AU') or []
        kws = [x.strip() for x in join('DE').split(';') if x.strip()] + [x.strip() for x in join('ID').split(';') if x.strip()]
        out.append({'title': join('TI'), 'authors': '; '.join(authors), 'year': get_year(join('PY')),
                    'venue': join('SO'), 'doi': join('DI'), 'pmid': join('PM'), 'abstract': join('AB'),
                    'keywords': '; '.join(kws), 'doc_type_raw': join('DT'), 'url': ''})
    return out


def parse_ris(text):
    recs, cur, tag = [], None, None
    for line in text.lstrip('\ufeff').splitlines():
        m = re.match(r'^([A-Z][A-Z0-9])\s{1,2}-\s?(.*)$', line)
        if m:
            tag, val = m.group(1), m.group(2).strip()
            if tag == 'TY':
                cur = defaultdict(list)
            if cur is None:
                continue
            if tag == 'ER':
                recs.append(cur)
                cur, tag = None, None
                continue
            cur[tag].append(val)
        elif cur is not None and tag and line.strip() and cur[tag]:
            cur[tag][-1] += ' ' + line.strip()
    out = []
    for r in recs:
        first = lambda *ks: next((r[k][0] for k in ks if r.get(k) and r[k][0]), '')
        doi = first('DO')
        if not doi:
            for v in r.get('UR', []) + r.get('L3', []):
                mm = DOI_RE.search(v)
                if mm:
                    doi = clean_doi_match(mm.group(0))
                    break
        out.append({'title': first('TI', 'T1'), 'authors': '; '.join(r.get('AU', []) or r.get('A1', [])),
                    'year': get_year(first('PY', 'Y1', 'DA')), 'venue': first('JF', 'T2', 'JO', 'JA', 'J2', 'BT'),
                    'doi': doi, 'pmid': '', 'abstract': first('AB', 'N2'), 'keywords': '; '.join(r.get('KW', [])),
                    'doc_type_raw': first('TY'), 'url': first('UR')})
    return out


_ACC = {"'": '\u0301', '`': '\u0300', '^': '\u0302', '"': '\u0308', '~': '\u0303', '=': '\u0304', '.': '\u0307'}


def bib_clean(v):
    v = re.sub(r"\\(['`^\"~=.])\{?\\?([A-Za-z])\}?", lambda m: unicodedata.normalize('NFC', m.group(2) + _ACC[m.group(1)]), v)
    v = v.replace('\\&', '&').replace('\\_', '_').replace('\\%', '%').replace('\\#', '#').replace('~', ' ')
    v = v.replace('{', '').replace('}', '')
    return re.sub(r'\s+', ' ', v).strip()


def parse_bibtex(text):
    out, i, n = [], 0, len(text)
    start_re = re.compile(r'@(\w+)\s*[{(]')
    while True:
        m = start_re.search(text, i)
        if not m:
            break
        etype, j, depth, k = m.group(1).lower(), m.end(), 1, m.end()
        while k < n and depth > 0:
            c = text[k]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            k += 1
        body, i = text[j:k - 1], k
        if etype in ('comment', 'preamble', 'string'):
            continue
        fields = {}
        p = body.find(',') + 1
        while p < len(body):
            while p < len(body) and body[p] in ' \t\r\n,':
                p += 1
            q = p
            while q < len(body) and (body[q].isalnum() or body[q] in '_-:'):
                q += 1
            name = body[p:q].lower()
            while q < len(body) and body[q] in ' \t\r\n':
                q += 1
            if not name or q >= len(body) or body[q] != '=':
                break
            q += 1
            while q < len(body) and body[q] in ' \t\r\n':
                q += 1
            if q >= len(body):
                break
            if body[q] == '{':
                d, r = 1, q + 1
                while r < len(body) and d > 0:
                    d += (body[r] == '{') - (body[r] == '}')
                    r += 1
                val, p = body[q + 1:r - 1], r
            elif body[q] == '"':
                r, d = q + 1, 0
                while r < len(body) and not (body[r] == '"' and d == 0):
                    d += (body[r] == '{') - (body[r] == '}')
                    r += 1
                val, p = body[q + 1:r], r + 1
            else:
                r = q
                while r < len(body) and body[r] not in ',\r\n':
                    r += 1
                val, p = body[q:r], r
            fields[name] = bib_clean(val)
        authors = [a.strip() for a in re.split(r'\s+and\s+', fields.get('author', '')) if a.strip()]
        kw = fields.get('keywords') or fields.get('author_keywords') or ''
        out.append({'title': fields.get('title', ''), 'authors': '; '.join(authors), 'year': get_year(fields.get('year', '')),
                    'venue': fields.get('journal') or fields.get('booktitle') or fields.get('series') or '',
                    'doi': fields.get('doi', ''), 'pmid': fields.get('pmid', ''), 'abstract': fields.get('abstract', ''),
                    'keywords': '; '.join(x.strip() for x in re.split(r'[;,]', kw) if x.strip()),
                    'doc_type_raw': ' '.join(x for x in (etype, fields.get('document_type', ''), fields.get('type', '')) if x),
                    'url': fields.get('url', '')})
    return out


CSV_ALIASES = {
    'title': ['title', 'article title', 'document title', 'titles', 'ti'],
    'authors': ['authors', 'author names', 'author full names', 'af', 'au', 'author(s)'],
    'year': ['year', 'publication year', 'py', 'publication_year', 'pubyear', 'create date'],
    'venue': ['source title', 'publication title', 'journal/book', 'journal', 'so', 'conference title', 'booktitle'],
    'doi': ['doi', 'di'],
    'pmid': ['pmid', 'pubmed id', 'pm'],
    'abstract': ['abstract', 'ab'],
    'keywords': ['author keywords', 'de', 'keywords', 'index keywords', 'keywords plus', 'ieee terms'],
    'doc_type_raw': ['document type', 'dt', 'document identifier', 'publication type', 'pt'],
    'url': ['link', 'pdf link', 'url', 'ur'],
}


def parse_table(rows_iter_headers_rows):
    headers, rows = rows_iter_headers_rows
    low = {h.strip().lower(): h for h in headers if h}
    colmap = {k: [low[a] for a in al if a in low] for k, al in CSV_ALIASES.items()}
    if not colmap['title']:
        die('could not find a title column. Columns found: ' + ', '.join(h for h in headers if h)
            + '. Re-export as RIS or BibTeX, or send me the header line and I will add it.')
    out = []
    for r in rows:
        def pick(k):
            for h in colmap[k]:
                v = (r.get(h) or '').strip()
                if v:
                    return v
            return ''
        kws = []
        for h in colmap['keywords']:
            v = (r.get(h) or '').strip()
            if v:
                kws.append(v)
        out.append({'title': pick('title'), 'authors': pick('authors'), 'year': get_year(pick('year')),
                    'venue': pick('venue'), 'doi': pick('doi'), 'pmid': pick('pmid'), 'abstract': pick('abstract'),
                    'keywords': '; '.join(kws), 'doc_type_raw': pick('doc_type_raw'), 'url': pick('url')})
    return out


def parse_csv_text(text):
    first = text.lstrip('\ufeff').split('\n', 1)[0]
    delim = max([',', '\t', ';'], key=lambda d: first.count(d))
    rd = csv.DictReader(text.lstrip('\ufeff').splitlines(), delimiter=delim)
    headers = rd.fieldnames or []
    return parse_table((headers, list(rd)))


def parse_xlsx(path):
    try:
        import openpyxl
    except ImportError:
        die(f'{path.name}: reading .xlsx needs openpyxl (pip install openpyxl). Easier: export RIS or CSV instead.')
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    headers = [str(h or '') for h in next(it)]
    rows = [{headers[i]: ('' if v is None else str(v)) for i, v in enumerate(row) if i < len(headers)} for row in it]
    return parse_table((headers, rows))


def parse_export(path):
    path = Path(path)
    ext = path.suffix.lower()
    if ext == '.xlsx':
        return parse_xlsx(path), 'xlsx'
    text = read_text_file(path)
    head = text.lstrip('\ufeff').lstrip()[:400]
    if re.match(r'PMID-\s', head) or re.search(r'^PMID-\s', text[:5000], re.M):
        return parse_medline(text), 'medline'
    if re.match(r'(FN |VR |PT )', head):
        return parse_wos_tagged(text), 'wos-tagged'
    if re.match(r'TY\s{1,2}-', head):
        return parse_ris(text), 'ris'
    if head.startswith('@'):
        return parse_bibtex(text), 'bibtex'
    if ext == '.txt' and re.match(r'\d+:\s', head):
        die(f'{path.name}: this looks like a PubMed "Summary (text)" or "Abstract (text)" file, which has no tags the tool can read. '
            'In PubMed use  Save > Selection: All results > Format: PubMed  (a .txt file whose lines start with PMID- and TI  -), then replace this file.')
    if ext in ('.csv', '.tsv', '.txt'):
        try:
            return parse_csv_text(text), 'csv'
        except SystemExit as e:
            die(f'{path.name}: ' + str(e).removeprefix('ERROR: '))
    die(f'{path.name}: unknown export format.')


def db_for(path, exports_dir):
    rel = path.relative_to(exports_dir)
    cands = []
    if len(rel.parts) > 1:
        cands.append(rel.parts[0])
    stem = path.stem.lower()
    cands += [re.split(r'[_\-\s\d.]', stem)[0], stem]
    for c in cands:
        key = c.lower().strip()
        if key in DB_ALIASES:
            return DB_ALIASES[key]
    for k, v in DB_ALIASES.items():
        if len(k) > 3 and k in stem:
            return v
    if len(rel.parts) > 1:
        return re.sub(r'\W+', '_', rel.parts[0].lower())  # a custom database folder (embase, acm ...)
    die(f'cannot tell which database "{path.name}" came from. Put it in a folder named pubmed, wos, scopus or ieee '
        f'(for example 01_exports/scopus/{path.name}) or start its file name with the database name.')


def db_label(key):
    return DB_LABELS.get(key, key.replace('_', ' ').title())


def make_uid(db, rec):
    key = f"{db}|{rec['doi'] or rec['pmid']}|{norm_title(rec['title'])}|{rec['year']}"
    return DB_SHORT.get(db, db[:2].upper()) + '-' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:10]


# ---------------------------------------------------------------- init
BRIEF_TEMPLATE = """# Review brief (give this file to the AI together with the paper files)

## 1. Role and task
You are helping me write a {review_type} review paper. I have read and screened the papers; you draft, I decide.

## 2. Review type and target
- Review type: {review_type}
- Target journal / venue: <fill>
- Abstract length: <for example 250 words, structured: Background, Methods, Results, Conclusion>
- Total length: <fill> words (excluding references)
- Citation style in the draft: cite ONLY with paper tags such as [P012] or [P012, P015]. Never write author-year citations and never invent a reference.

## 3. Research questions
{rq_lines}

## 4. Section plan (use exactly these headings)
1. Introduction - background, gap, research questions, and OUR contribution (3-4 bullet points)
2. Methods - databases searched, search strings, inclusion/exclusion criteria, screening, PRISMA numbers (I will supply the numbers)
3. Results - one subsection per research question; describe each included paper fairly; compare, do not just list
4. Discussion - synthesis, limitations of the evidence, limitations of this review
5. Future directions
6. Conclusion

## 5. Main body vs supplementary
- Files named main_part*.docx contain the papers to analyse in the main text.
- Files named supplementary_part*.docx are background only: use them for context, cite sparingly.

## 6. Analysis rules
- State only what the paper itself says. If a detail (sample size, metric, dataset) is not in the text, write "not reported".
- When papers disagree, say so and name the tags on each side.
- Do not copy sentences from the papers; paraphrase.

## 7. Figures and tables
- Do not create or describe images from other papers. List the figures/tables I should draw myself (title, what each axis/column shows, which paper tags feed it).

## 8. Output format
- Return the draft as plain text with headings. Put open questions for me at the end under "Questions for the author".
"""

KEYWORDS_TEMPLATE = {
    '_help': 'Each group is one concept. A record passes when it matches at least one term in EVERY group. '
             'A trailing * means any ending (diabet* matches diabetes, diabetic). Matching is case-insensitive.',
    'fields': ['title', 'abstract', 'keywords'],
    'require_groups': {'concept_1': ['example term*', 'another term'], 'concept_2': ['second concept']},
    'exclude_terms': [],
    'year_from': None,
    'year_to': None,
    'doc_types': [],
}


def cmd_init(a):
    p = Proj(a.folder)
    if p.cfg_path.exists():
        die(f'{p.root} already has a project.json')
    for d in (p.exports, p.rec, p.screen_dir, p.access_dir, p.pdfs / 'inbox', p.pack_dir, p.draft):
        d.mkdir(parents=True, exist_ok=True)
    for db in DB_LABELS:
        (p.exports / db).mkdir(exist_ok=True)
    rq = a.rq or []
    cfg = {'title': a.title, 'review_type': a.type, 'research_questions': rq, 'proxy_prefix': a.proxy or '',
           'library_home': a.library_home or '', 'library_search': a.library_search or '',
           'batch_size': 10, 'created': date.today().isoformat()}
    write_json(p.cfg_path, cfg)
    write_json(p.keywords_json, KEYWORDS_TEMPLATE)
    rq_lines = '\n'.join(f'- RQ{i + 1}: {q}' for i, q in enumerate(rq)) or '- RQ1: <fill>\n- RQ2: <fill>'
    (p.draft / 'review_brief.md').write_text(BRIEF_TEMPLATE.format(review_type=a.type, rq_lines=rq_lines), encoding='utf-8')
    print(f'Project created: {p.root}')
    print('  Put database exports in 01_exports/pubmed, wos, scopus, ieee (one folder per database).')
    print('  Edit keywords.json (your concept groups) and 07_draft/review_brief.md.')


# ---------------------------------------------------------------- import
def cmd_import(a):
    p = Proj(a.project).require()
    files = sorted(f for f in p.exports.rglob('*') if f.is_file() and f.suffix.lower() in EXPORT_EXT and not f.name.startswith(('.', '~')))
    if not files:
        die(f'no export files found under {p.exports}. Put them in 01_exports/pubmed, wos, scopus, ieee.')
    seen, out, file_log = {}, [], []
    per_db = defaultdict(lambda: {'records': 0, 'files': 0, 'repeats_removed': 0})
    for f in files:
        db = db_for(f, p.exports)
        recs, fmt = parse_export(f)
        n_parsed, no_title, repeats = len(recs), 0, 0
        added = []
        for r in recs:
            r = {k: (r.get(k) or '').strip() if isinstance(r.get(k), str) else (r.get(k) or '') for k in
                 ('title', 'authors', 'year', 'venue', 'doi', 'pmid', 'abstract', 'keywords', 'doc_type_raw', 'url')}
            r['title'] = clean_title(r['title'])
            r['doi'] = norm_doi(r['doi'])
            r['abstract'] = re.sub(r'\s+', ' ', r['abstract'])
            if not r['title']:
                no_title += 1
                continue
            key = (db, r['doi'] or r['pmid'] or (norm_title(r['title']) + r['year']))
            if key in seen:
                repeats += 1
                continue
            seen[key] = True
            r.update({'db': db, 'file': str(f.relative_to(p.exports)).replace('\\', '/')})
            r['doc_type'] = norm_type(r['doc_type_raw'], r['venue'])
            r['uid'] = make_uid(db, r)
            added.append(r)
        out += added
        d = per_db[db]
        d['records'] += len(added)
        d['files'] += 1
        d['repeats_removed'] += repeats
        file_log.append({'file': str(f.relative_to(p.exports)).replace('\\', '/'), 'db': db, 'format': fmt, 'parsed': n_parsed,
                         'kept': len(added), 'repeats_in_same_db': repeats, 'no_title_skipped': no_title,
                         'with_abstract': sum(1 for r in added if r['abstract']), 'with_doi': sum(1 for r in added if r['doi']),
                         'with_year': sum(1 for r in added if r['year'])})
    write_csv(p.all_csv, out, REC_FIELDS)
    log = {'imported_on': date.today().isoformat(), 'files': file_log,
           'per_db': {db_label(k): v for k, v in per_db.items()}, 'total_records': len(out)}
    write_json(p.import_log, log)
    rows = [[x['file'], db_label(x['db']), x['format'], x['kept'], x['with_abstract'], x['with_doi'], x['repeats_in_same_db']] for x in file_log]
    print(table(rows, ['file', 'database', 'format', 'records', 'abstract', 'doi', 'repeats']))
    print()
    print(table([[k, v['files'], v['records']] for k, v in log['per_db'].items()], ['database', 'files', 'records']))
    print(f"\nTotal records: {len(out)}  ->  {p.all_csv.relative_to(p.root)}")
    for x in file_log:
        if x['kept'] and x['with_abstract'] / x['kept'] < 0.5:
            print(f"WARNING: {x['file']}: only {x['with_abstract']}/{x['kept']} records have an abstract. "
                  f"Re-export with abstracts included (PubMed: 'PubMed' format, not CSV).")
        if x['no_title_skipped']:
            print(f"WARNING: {x['file']}: {x['no_title_skipped']} records without a title were skipped.")
        if x['kept'] and x['with_year'] / x['kept'] < 0.8:
            print(f"WARNING: {x['file']}: many records have no year; check the export columns.")


# ---------------------------------------------------------------- dedupe
def completeness(r):
    return (4 if r['abstract'] else 0) + (2 if r['doi'] else 0) + (1 if r['year'] else 0) + min(len(r['abstract']), 3000) / 10000.0


def year_close(y1, y2):
    if not y1 or not y2:
        return True
    return abs(int(y1) - int(y2)) <= 1


class UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def cmd_dedupe(a):
    p = Proj(a.project).require()
    recs = read_csv(p.all_csv, REC_FIELDS)
    if not recs:
        die('records_all.csv is empty or missing. Run `python slr.py import` first.')
    n = len(recs)
    nt = [norm_title(r['title']) for r in recs]
    sur = [first_surname(r['authors']) for r in recs]
    uf = UF(n)
    review_pairs = []
    by_doi, by_ty = {}, {}
    for i, r in enumerate(recs):
        if r['doi']:
            if r['doi'] in by_doi:
                uf.union(by_doi[r['doi']], i)
            else:
                by_doi[r['doi']] = i
    for i, r in enumerate(recs):
        key = nt[i]
        if len(key) < 20 and not sur[i]:
            continue
        cand = by_ty.setdefault(key, [])
        for j in cand:
            if uf.find(i) == uf.find(j):
                continue
            if not year_close(recs[i]['year'], recs[j]['year']):
                continue
            if len(key) < 20 and sur[i] != sur[j]:
                continue
            if recs[i]['doi'] and recs[j]['doi'] and recs[i]['doi'] != recs[j]['doi']:
                review_pairs.append((i, j, 1.0, 'same title, different DOIs'))
                continue
            uf.union(i, j)
        cand.append(i)
    # fuzzy pass inside a year window
    by_year = defaultdict(list)
    for i, r in enumerate(recs):
        by_year[r['year'] or '?'].append(i)
    for i in range(n):
        if recs[i]['year']:
            pool = set(by_year.get('?', []))
            for dy in (-1, 0, 1):
                pool.update(by_year.get(str(int(recs[i]['year']) + dy), []))
        else:
            pool = set(range(n))
        for j in sorted(pool):
            if j <= i or uf.find(i) == uf.find(j) or len(nt[i]) < 20 or len(nt[j]) < 20:
                continue
            if abs(len(nt[i]) - len(nt[j])) > 0.2 * max(len(nt[i]), len(nt[j])):
                continue
            sm = difflib.SequenceMatcher(None, nt[i], nt[j], autojunk=False)
            if sm.real_quick_ratio() < 0.85 or sm.quick_ratio() < 0.85:
                continue
            ratio = sm.ratio()
            if ratio < 0.85:
                continue
            same_author = (not sur[i] or not sur[j] or sur[i] == sur[j])
            dois_differ = recs[i]['doi'] and recs[j]['doi'] and recs[i]['doi'] != recs[j]['doi']
            if ratio >= a.fuzzy and same_author and year_close(recs[i]['year'], recs[j]['year']) and not dois_differ:
                uf.union(i, j)
            else:
                review_pairs.append((i, j, ratio, 'similar title' + (', different DOIs' if dois_differ else '') + ('' if same_author else ', different first author')))
    groups = defaultdict(list)
    for i in range(n):
        groups[uf.find(i)].append(i)
    unique, dups = [], []
    for root in sorted(groups):
        idx = groups[root]
        keep = max(idx, key=lambda k: (completeness(recs[k]), -k))
        kept = dict(recs[keep])
        for k in idx:
            if k == keep:
                continue
            o = recs[k]
            for f in ('abstract', 'doi', 'pmid', 'keywords', 'venue', 'year', 'url', 'authors'):
                if not kept[f] and o[f]:
                    kept[f] = o[f]
            if kept['doc_type'] == 'other' and o['doc_type'] != 'other':
                kept['doc_type'], kept['doc_type_raw'] = o['doc_type'], o['doc_type_raw']
            if recs[k]['doi'] and recs[k]['doi'] == recs[keep]['doi']:
                mt, score = 'doi', 1.0
            elif nt[k] == nt[keep]:
                mt, score = 'title_year', 1.0
            else:
                mt, score = 'fuzzy_title', round(difflib.SequenceMatcher(None, nt[k], nt[keep], autojunk=False).ratio(), 3)
            dups.append({'dup_uid': o['uid'], 'dup_db': db_label(o['db']), 'dup_title': o['title'], 'dup_doi': o['doi'],
                         'kept_uid': kept['uid'], 'match_type': mt, 'score': score})
        kept['sources'] = '+'.join(dict.fromkeys(db_label(recs[k]['db']) for k in sorted(idx, key=lambda k: (k != keep, k))))
        kept['n_found'] = len(idx)
        kept['merged_uids'] = '|'.join(recs[k]['uid'] for k in idx if k != keep)
        unique.append(kept)
    write_csv(p.unique_csv, unique, UNIQUE_FIELDS)
    write_csv(p.dups_csv, dups, ['dup_uid', 'dup_db', 'dup_title', 'dup_doi', 'kept_uid', 'match_type', 'score'])
    rev, seen_pairs = [], set()
    for i, j, s, why in review_pairs:
        key = (min(i, j), max(i, j))
        if uf.find(i) == uf.find(j) or key in seen_pairs:
            continue
        seen_pairs.add(key)
        rev.append({'record_a': recs[key[0]]['uid'], 'title_a': recs[key[0]]['title'], 'doi_a': recs[key[0]]['doi'],
                    'record_b': recs[key[1]]['uid'], 'title_b': recs[key[1]]['title'], 'doi_b': recs[key[1]]['doi'],
                    'similarity': round(s, 3), 'why': why})
    review_path = p.rec / 'dedupe_review.csv'
    if rev:
        write_csv(review_path, rev, list(rev[0].keys()))
    elif review_path.exists():
        review_path.unlink()
    by_type = Counter(d['match_type'] for d in dups)
    log = {'run_on': date.today().isoformat(), 'records_in': n, 'unique': len(unique), 'duplicates_removed': len(dups),
           'by_match_type': dict(by_type), 'pairs_for_manual_review': len(rev),
           'found_in_n_databases': dict(Counter(len(set(u['sources'].split('+'))) for u in unique))}
    write_json(p.dedupe_log, log)
    print(f'Records in: {n}\nUnique: {len(unique)}\nDuplicates removed: {len(dups)} {dict(by_type)}')
    print('Found in 1/2/3/4 databases:', log['found_in_n_databases'])
    if rev:
        print(f'{len(rev)} borderline pairs were NOT merged: check {review_path.relative_to(p.root)}')
    print(f'Written: {p.unique_csv.relative_to(p.root)}, {p.dups_csv.relative_to(p.root)}')


# ---------------------------------------------------------------- screening sheet + keyword flags
def term_regex(term):
    t = term.strip()
    if not t:
        return None
    star = t.endswith('*')
    body = re.escape(t.rstrip('*'))
    return re.compile(r'(?<![A-Za-z0-9])' + body + (r'\w*' if star else r'(?![A-Za-z0-9])'), re.I)


def kw_check(rec, cfg):
    fields = cfg.get('fields') or ['title', 'abstract', 'keywords']
    text = ' \n '.join(rec.get(f, '') for f in fields)
    hits, missing = [], []
    for g, terms in (cfg.get('require_groups') or {}).items():
        found = [t for t in terms if (rx := term_regex(t)) and rx.search(text)]
        (hits if found else missing).append((g, found))
    hit_txt = '; '.join(f"{g}:{'|'.join(f)}" for g, f in hits)
    for t in cfg.get('exclude_terms') or []:
        rx = term_regex(t)
        if rx and rx.search(text):
            return 'exclude_term', hit_txt + f'; EXCLUDE:{t}'
    y = int(rec['year']) if rec.get('year', '').isdigit() else None
    if y and ((cfg.get('year_from') and y < int(cfg['year_from'])) or (cfg.get('year_to') and y > int(cfg['year_to']))):
        return 'out_of_range', hit_txt
    if cfg.get('doc_types') and rec.get('doc_type') not in cfg['doc_types']:
        return 'type', hit_txt
    if missing:
        if not rec.get('abstract'):
            return 'no_abstract', hit_txt
        return 'fail', hit_txt + ('; MISSING:' + ','.join(g for g, _ in missing))
    return 'pass', hit_txt


def load_screen(p):
    rows = read_csv(p.screen_csv, SCREEN_FIELDS)
    for i, r in enumerate(rows, 2):
        for fld, allowed in (('ta_decision', TA_VALUES), ('ft_decision', FT_VALUES), ('role', ROLE_VALUES)):
            r[fld] = r[fld].strip().lower()
            if r[fld] not in allowed:
                die(f'screening.csv row {i}: {fld} = "{r[fld]}" is not allowed. Use one of: '
                    + ', '.join(sorted(v for v in allowed if v)) + ' (or leave blank).')
    return rows


def cmd_screen(a):
    p = Proj(a.project).require()
    uniq = read_csv(p.unique_csv, UNIQUE_FIELDS)
    if not uniq:
        die('records_unique.csv missing. Run import and dedupe first.')
    cfg = json.loads(p.keywords_json.read_text(encoding='utf-8')) if p.keywords_json.exists() else {}
    have_cfg = bool(cfg.get('require_groups')) and 'concept_1' not in cfg['require_groups']
    if not have_cfg:
        print('NOTE: keywords.json still has the template groups; keyword flags are skipped. Edit it, then run again.')
    old = {r['uid']: r for r in load_screen(p)} if p.screen_csv.exists() else {}
    rows, applied = [], 0
    for u in uniq:
        r = {f: '' for f in SCREEN_FIELDS}
        r.update({k: u.get(k, '') for k in ('uid', 'sources', 'title', 'authors', 'year', 'venue', 'doc_type', 'doi', 'pmid', 'keywords', 'abstract')})
        if u['uid'] in old:
            for k in ('pid', 'ta_decision', 'ft_decision', 'reason', 'role', 'access', 'oa_url', 'landing_url', 'pdf_file', 'pdf_folder', 'notes'):
                r[k] = old[u['uid']].get(k, '')
        if have_cfg:
            r['kw_flag'], r['kw_hits'] = kw_check(u, cfg)
        if a.apply and r['kw_flag'] in ('fail', 'exclude_term', 'out_of_range', 'type') and not r['ta_decision']:
            r['ta_decision'], r['reason'] = 'exclude', 'automation: ' + r['kw_flag']
            applied += 1
        rows.append(r)
    orphans = [uid for uid in old if uid not in {r['uid'] for r in rows}]
    write_csv(p.screen_csv, rows, SCREEN_FIELDS)
    flags = Counter(r['kw_flag'] for r in rows)
    print(f'Screening sheet: {p.screen_csv.relative_to(p.root)}  ({len(rows)} records)')
    if have_cfg:
        print('Keyword flags:', dict(flags))
        print('  pass = all concept groups matched; fail = a group has no match; no_abstract = fail but no abstract (read it yourself)')
        if a.apply:
            print(f'  --apply: {applied} records marked ta_decision=exclude with reason "automation: ..." (counted separately in PRISMA)')
        else:
            print('  Flags only. Nothing was excluded. Use --apply if you want clear failures marked as excluded by automation.')
    if orphans:
        print(f'WARNING: {len(orphans)} rows in the old sheet are no longer in records_unique.csv (their decisions were dropped).')
    print('Now open the sheet in Excel/LibreOffice, fill ta_decision (include/exclude/maybe) and reason, save as CSV UTF-8.')


def cmd_number(a):
    p = Proj(a.project).require()
    rows = load_screen(p)
    nums = [int(r['pid'][1:]) for r in rows if re.fullmatch(r'P\d+', r['pid'] or '')]
    nxt = max(nums, default=0) + 1
    new = 0
    for r in rows:
        if r['ta_decision'] in ('include', 'maybe') and not r['pid']:
            r['pid'] = f'P{nxt:03d}'
            nxt += 1
            new += 1
    write_csv(p.screen_csv, rows, SCREEN_FIELDS)
    total = sum(1 for r in rows if r['pid'])
    print(f'{new} new paper numbers assigned; {total} numbered papers in total (numbers never change once given).')
    und = sum(1 for r in rows if not r['ta_decision'])
    if und:
        print(f'NOTE: {und} records still have an empty ta_decision.')


# ---------------------------------------------------------------- access (open access vs subscription)
def http_json(url, tries=3):
    delay = 1.0
    for k in range(tries):
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (429, 500, 502, 503, 504) and k < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except urllib.error.URLError:
            if k < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise


def cmd_access(a):
    p = Proj(a.project).require()
    email = os.environ.get('UNPAYWALL_EMAIL') or os.environ.get('CONTACT_EMAIL')
    if not email:
        die('set UNPAYWALL_EMAIL (your real email; Unpaywall asks for it). Example (Windows PowerShell): $env:UNPAYWALL_EMAIL="you@uni.edu"')
    rows = load_screen(p)
    cache_path = p.access_dir / 'unpaywall_cache.json'
    cache = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
    todo = [r for r in rows if r['pid'] and (a.refresh or not r['access'])]
    counts = Counter()
    for k, r in enumerate(todo, 1):
        doi = norm_doi(r['doi'])
        r['landing_url'] = f'https://doi.org/{doi}' if doi else ''
        if not doi:
            r['access'], r['oa_url'] = 'unknown', ''
        else:
            if doi not in cache:
                try:
                    cache[doi] = http_json(f'{UNPAYWALL}/{urllib.parse.quote(doi, safe="/")}?email={urllib.parse.quote(email)}') or {'_not_found': True}
                except Exception as e:  # network trouble: leave this one for the next run
                    print(f'  {r["pid"]}: lookup failed ({e}); will retry next run')
                    continue
                time.sleep(0.12)
            d = cache[doi]
            loc = d.get('best_oa_location') or {}
            url = loc.get('url_for_pdf') or loc.get('url') or ''
            if d.get('is_oa') and url:
                r['access'], r['oa_url'] = 'open', url
            elif d.get('_not_found'):
                r['access'], r['oa_url'] = 'unknown', ''
            else:
                r['access'], r['oa_url'] = 'subscription', ''
        counts[r['access']] += 1
        if k % 25 == 0:
            print(f'  {k}/{len(todo)} checked')
    write_json(cache_path, cache)
    write_csv(p.screen_csv, rows, SCREEN_FIELDS)
    allc = Counter(r['access'] for r in rows if r['pid'])
    print('Access (all numbered papers):', dict(allc))
    print('open = free full text found; subscription = not open access (use university access); unknown = no DOI / not found')


# ---------------------------------------------------------------- batches of 10 tabs
PUBLISHER_PDF = [  # DOI prefix -> direct article/PDF address (used only when no proxy prefix is set)
    ('10.1145/', 'https://dl.acm.org/doi/pdf/{doi}'),
    ('10.1007/', 'https://link.springer.com/content/pdf/{doi}.pdf'),
    ('10.1002/', 'https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}'),
    ('10.1111/', 'https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}'),
    ('10.1177/', 'https://journals.sagepub.com/doi/pdf/{doi}'),
]
PUBLISHERS = [  # DOI prefix -> (short name, search word for the library portal)
    ('10.1109/', 'IEEE', 'IEEE'), ('10.1145/', 'ACM', 'ACM Digital Library'), ('10.1007/', 'Springer', 'Springer'),
    ('10.1016/', 'ScienceDirect', 'ScienceDirect Elsevier'), ('10.1002/', 'Wiley', 'Wiley'), ('10.1111/', 'Wiley', 'Wiley'),
    ('10.1142/', 'World Scientific', 'World Scientific'), ('10.1515/', 'De Gruyter', 'De Gruyter'),
    ('10.1177/', 'SAGE', 'SAGE'), ('10.1098/', 'Royal Society', 'Royal Society'), ('10.1049/', 'IET', 'IET'),
    ('10.1080/', 'Taylor & Francis', 'Taylor Francis'),
]


def publisher_of(doi):
    d = (doi or '').lower()
    for prefix, name, query in PUBLISHERS:
        if d.startswith(prefix):
            return name, query
    return None


def batch_url(r, kind, proxy):
    if kind == 'open':
        return r['oa_url'] or r['landing_url']
    base = r['landing_url'] or ('https://scholar.google.com/scholar?q=' + urllib.parse.quote(r['title']))
    if proxy and r['landing_url']:
        return proxy + base
    doi = (r.get('doi') or '').strip()
    if doi and not proxy:  # library access comes from the browser (extension / campus network / logged-in portal)
        for prefix, pattern in PUBLISHER_PDF:
            if doi.lower().startswith(prefix):
                return pattern.format(doi=doi)
    return base


def cmd_batches(a):
    p = Proj(a.project).require()
    cfg = p.cfg()
    size = a.size or int(cfg.get('batch_size', 10))
    proxy = a.proxy if a.proxy is not None else cfg.get('proxy_prefix', '')
    rows = [r for r in load_screen(p) if r['pid'] and not r['pdf_file'] and r['ft_decision'] != 'not_retrieved']
    if not rows:
        die('no numbered papers waiting for a PDF. Run `number` (and `access`) first.')
    if any(not r['access'] for r in rows):
        print('NOTE: some papers have no access status yet; run `python slr.py access` first for open/subscription split.')
    groups = {'open': [r for r in rows if r['access'] == 'open'], 'sub': [r for r in rows if r['access'] != 'open']}
    p.access_dir.mkdir(exist_ok=True)
    for old in p.access_dir.glob('*_[0-9][0-9][0-9].html'):
        old.unlink()
    manifest, index = {}, []
    for kind, lst in groups.items():
        chunks = [lst[i:i + size] for i in range(0, len(lst), size)]
        manifest[kind] = [[r['pid'] for r in c] for c in chunks]
        for bi, c in enumerate(chunks, 1):
            name = f'{"open_access" if kind == "open" else "subscription"}_{bi:03}.html'
            items = [(r['pid'], r['title'], r['authors'], r['year'], batch_url(r, kind, proxy), r.get('doi', '')) for r in c]
            lib = {'home': cfg.get('library_home', ''), 'search': cfg.get('library_search', '')}
            (p.access_dir / name).write_text(batch_page(kind, bi, len(chunks), items, bool(proxy), lib), encoding='utf-8')
            index.append((name, kind, bi, len(c)))
    write_json(p.access_dir / 'batches.json', manifest)
    li = ''.join(f'<li><a href="{n}">{n}</a> - {c} papers</li>' for n, k, b, c in index)
    (p.access_dir / 'index.html').write_text(
        f'<!doctype html><meta charset="utf-8"><title>Batches</title><body style="font-family:sans-serif;max-width:760px;margin:2rem auto">'
        f'<h1>Download batches</h1><p>Open access first, then subscription.</p><ul>{li}</ul></body>', encoding='utf-8')
    print(f'Open access papers: {len(groups["open"])} in {len(manifest["open"])} batches; '
          f'subscription/unknown: {len(groups["sub"])} in {len(manifest["sub"])} batches (size {size}).')
    print(f'Pages: {p.access_dir.relative_to(p.root)}/index.html')
    print('Open ten tabs at once with: python slr.py tabs open 1     (or: tabs sub 1)')
    if groups['sub'] and not proxy and not cfg.get('library_home'):
        print('TIP: for subscription papers, either set your university proxy prefix (project.json "proxy_prefix" or --proxy),')
        print('     or, if your library works through a browser extension / portal login (a university library portal), set "library_home" and "library_search" in project.json.')


BATCH_JS = """<script>
const KEY='slr_done_'+__PAGE__;let done={};try{done=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
function paint(){document.querySelectorAll('tr[data-pid]').forEach(tr=>{const d=!!done[tr.dataset.pid];tr.style.opacity=d?'.4':'1';
 const b=tr.querySelector('[data-d]');if(b)b.textContent=d?'Undo done':'Mark done'});
 const n=Object.values(done).filter(Boolean).length;document.getElementById('cnt').textContent=n+' of '+document.querySelectorAll('tr[data-pid]').length+' done'}
document.addEventListener('click',e=>{const t=e.target;
 if(t.dataset.n||t.dataset.c){navigator.clipboard.writeText(t.dataset.n||t.dataset.c);const o=t.textContent;t.textContent='Copied';setTimeout(()=>t.textContent=o,900)}
 if(t.dataset.d){done[t.dataset.d]=!done[t.dataset.d];try{localStorage.setItem(KEY,JSON.stringify(done))}catch(e){}paint()}});
document.getElementById('q').oninput=ev=>{const f=ev.target.value.toLowerCase();document.querySelectorAll('tr[data-pid]').forEach(tr=>{tr.style.display=tr.textContent.toLowerCase().includes(f)?'':'none'})};
paint();
</script>"""


def batch_page(kind, bi, total, items, proxied, lib=None):
    lib = lib or {}
    page_name = f'{"open_access" if kind == "open" else "subscription"}_{bi:03}'
    title = ('Open access' if kind == 'open' else 'Subscription (university access)') + f' - batch {bi} of {total}'
    rows = ''.join(
        f'<tr data-pid="{html.escape(pid)}"><td><b>{html.escape(pid)}</b></td>'
        f'<td>{html.escape(t)}<br><small>{html.escape(au.split(";")[0] + (" et al." if ";" in au else ""))} {html.escape(y)}'
        f'{" - " + html.escape(doi) if doi else ""}</small></td>'
        f'<td><a href="{html.escape(u, quote=True)}" target="_blank" rel="noopener">open</a></td>'
        f'<td><code>{html.escape(pid)}.pdf</code><br>'
        f'<button data-n="{html.escape(pid)}.pdf">Copy name</button> <button data-c="{html.escape(t, quote=True)}">Copy title</button> '
        f'<button data-d="{html.escape(pid)}">Mark done</button></td></tr>'
        for pid, t, au, y, u, doi in items)
    urls = json.dumps([it[4] for it in items])
    note = ''
    if kind != 'open':
        if proxied:
            note = '<p>Links go through your university proxy. Log in once if asked.</p>'
        elif lib.get('home'):
            counts = {}
            for it in items:
                pub = publisher_of(it[5])
                if pub:
                    counts.setdefault(pub, 0)
                    counts[pub] += 1
            btns = ''
            if lib.get('search'):
                for (name, query), n in sorted(counts.items()):
                    link = lib['search'].replace('{q}', urllib.parse.quote(query))
                    btns += f'<a href="{html.escape(link, quote=True)}" target="_blank" rel="noopener"><button>{html.escape(name)} ({n})</button></a> '
            note = ('<div style="background:#fff7e6;border:1px solid #e5c07b;padding:.6rem 1rem;border-radius:8px">'
                    '<b>Before opening the tabs:</b> '
                    f'1) <a href="{html.escape(lib["home"], quote=True)}" target="_blank" rel="noopener">open your library portal and log in</a>. '
                    + ('2) click each publisher below once and open its card, so your institutional access is active in this browser. ' if btns else '')
                    + '3) Come back here and press "Open all".'
                    + (f'<div style="margin-top:.5rem">{btns}</div>' if btns else '') + '</div>')
    return (f'<!doctype html><meta charset="utf-8"><title>{html.escape(title)}</title>'
            '<style>body{font-family:system-ui,sans-serif;max-width:980px;margin:2rem auto;padding:0 1rem}'
            'td,th{border-bottom:1px solid #ddd;padding:.5rem;text-align:left;vertical-align:top}button{padding:.4rem .8rem;font-size:.9rem;cursor:pointer}'
            'input[type=search]{padding:.4rem;min-width:240px}</style>'
            f'<h1>{html.escape(title)}</h1>{note}<p>Download each PDF by hand and save it into <code>05_pdfs/inbox/</code>. '
            'Naming it with the paper number (right column) makes matching exact; any other name also works. '
            'Download manually - do not bulk-download subscription journals with scripts (publishers block that).</p>'
            f'<p><button style="padding:.6rem 1rem;font-size:1rem" onclick="{{const u={html.escape(urls, quote=True)};u.forEach(x=>window.open(x,\'_blank\'))}}">Open all {len(items)} tabs</button> '
            '<small>(if the browser blocks pop-ups, allow them for this page, or run <code>python slr.py tabs</code>)</small> '
            '<input type="search" id="q" placeholder="Filter"> <span id="cnt"></span></p>'
            f'<table><tr><th>No.</th><th>Paper</th><th>Link</th><th>Save as</th></tr>{rows}</table>'
            + BATCH_JS.replace('__PAGE__', json.dumps(page_name)))


def cmd_tabs(a):
    p = Proj(a.project).require()
    man_path = p.access_dir / 'batches.json'
    if not man_path.exists():
        die('run `python slr.py batches` first.')
    man = json.loads(man_path.read_text(encoding='utf-8'))
    kind = 'open' if a.kind == 'open' else 'sub'
    if a.batch < 1 or a.batch > len(man.get(kind, [])):
        die(f'batch {a.batch} does not exist; there are {len(man.get(kind, []))} {a.kind} batches.')
    proxy = p.cfg().get('proxy_prefix', '')
    by_pid = {r['pid']: r for r in load_screen(p) if r['pid']}
    pids = man[kind][a.batch - 1]
    print(f'Opening {len(pids)} tabs ({a.kind} batch {a.batch}) ...')
    tab_log = os.environ.get('SLR_TABS_LOG')  # used only by the self-test: write the links to a file instead of opening a browser
    for pid in pids:
        url = batch_url(by_pid[pid], kind, proxy)
        print(f'  {pid}: {url}')
        if tab_log:
            with open(tab_log, 'a', encoding='utf-8') as f:
                f.write(url + '\n')
        else:
            webbrowser.open_new_tab(url)
        time.sleep(a.delay)
    print('Save each PDF into 05_pdfs/inbox/ (name it Pxxx.pdf if you can), then run: python slr.py pdfmatch')


# ---------------------------------------------------------------- PDF text
_XML_BAD = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]')


def xml_clean(text):
    """Word (XML) refuses control characters that real PDFs often contain; drop them."""
    return _XML_BAD.sub('', text or '')


def pdf_text(path, engine='auto', first_pages=None):
    """Returns (text, n_pages). pdftotext (poppler) if available - better with two-column papers - else pypdf."""
    path = str(path)
    if engine in ('auto', 'pdftotext') and shutil.which('pdftotext'):
        args = ['pdftotext', '-enc', 'UTF-8', '-q']
        if first_pages:
            args += ['-f', '1', '-l', str(first_pages)]
        r = subprocess.run(args + [path, '-'], capture_output=True)
        if r.returncode == 0:
            t = r.stdout.decode('utf-8', 'replace')
            return t, t.count('\f')
    elif engine == 'pdftotext':
        die('pdftotext is not installed (part of poppler). Use --engine pypdf.')
    try:
        from pypdf import PdfReader
    except ImportError:
        die('reading PDFs needs pypdf: pip install pypdf   (or install poppler for pdftotext)')
    try:
        rd = PdfReader(path)
        if rd.is_encrypted:
            rd.decrypt('')
        pages = rd.pages[:first_pages] if first_pages else rd.pages
        return '\n\f'.join((pg.extract_text() or '') for pg in pages), len(rd.pages)
    except Exception as e:
        return '', 0


# ---------------------------------------------------------------- pdfmatch
def safe_name(s):
    return re.sub(r'[^A-Za-z0-9]+', '', s)[:20] or 'x'


def cmd_pdfmatch(a):
    p = Proj(a.project).require()
    inbox = p.pdfs / 'inbox'
    rows = load_screen(p)
    by_pid = {r['pid']: r for r in rows if r['pid']}
    by_uid = {r['uid']: r for r in rows}
    doi_pid = {norm_doi(r['doi']): r['pid'] for r in rows if r['pid'] and r['doi']}
    for d in read_csv(p.dups_csv):
        k = by_uid.get(d['kept_uid'])
        if k and k['pid'] and d['dup_doi']:
            doi_pid.setdefault(norm_doi(d['dup_doi']), k['pid'])
    titles = [(norm_title(r['title']), r['pid']) for r in rows if r['pid'] and len(norm_title(r['title'])) >= 25]
    files = [f for f in sorted(inbox.iterdir()) if f.is_file() and f.suffix.lower() == '.pdf'] if inbox.exists() else []
    if not files:
        die(f'no PDFs in {inbox}. Save your downloads there.')
    report, matched = [], 0
    for f in files:
        pid, how = '', ''
        m = re.match(r'^[Pp](\d{3,})(?!\d)', f.stem)
        if m and f'P{m.group(1)}' in by_pid:
            pid, how = f'P{m.group(1)}', 'filename'
        if not pid:
            text, _ = pdf_text(f, a.engine, first_pages=2)
            dois = [clean_doi_match(x) for x in DOI_RE.findall(text)]
            for d in dois:
                if d in doi_pid:
                    pid, how = doi_pid[d], 'doi'
                    break
            if not pid:
                nt = norm_title(text[:6000])
                hits = [(len(t), pd) for t, pd in titles if t in nt]
                if hits:
                    pid, how = max(hits)[1], 'title'
        if not pid:
            dest = p.pdfs / 'unmatched'
            dest.mkdir(exist_ok=True)
            shutil.move(str(f), str(dest / f.name))
            report.append({'file': f.name, 'status': 'unmatched', 'pid': '', 'dest': f'unmatched/{f.name}'})
            continue
        r = by_pid[pid]
        folder = {'journal': 'journal', 'conference': 'conference'}.get(r['doc_type'], 'other')
        name = f"{pid}_{safe_name(first_surname(r['authors']).title())}_{r['year'] or 'nd'}.pdf"
        if r['pdf_file']:
            dest_dir = p.pdfs / 'duplicates'
            dest_dir.mkdir(exist_ok=True)
            dest = dest_dir / f'{pid}_dup_{f.name}'
            shutil.move(str(f), str(dest))
            report.append({'file': f.name, 'status': f'duplicate of {r["pdf_file"]}', 'pid': pid, 'dest': f'duplicates/{dest.name}'})
            continue
        dest_dir = p.pdfs / folder
        dest_dir.mkdir(exist_ok=True)
        shutil.move(str(f), str(dest_dir / name))
        r['pdf_file'], r['pdf_folder'] = f'{folder}/{name}', folder
        matched += 1
        report.append({'file': f.name, 'status': f'matched by {how}', 'pid': pid, 'dest': f'{folder}/{name}'})
    write_csv(p.screen_csv, rows, SCREEN_FIELDS)
    write_csv(p.pdfs / 'pdf_report.csv', report, ['file', 'status', 'pid', 'dest'])
    missing = [r for r in rows if r['pid'] and not r['pdf_file'] and r['ft_decision'] != 'not_retrieved']
    write_csv(p.pdfs / 'missing_pdfs.csv', missing, ['pid', 'title', 'year', 'doi', 'access', 'landing_url', 'oa_url'])
    c = Counter(x['status'].split(' by ')[0] if x['status'].startswith('matched') else x['status'].split(' of ')[0] for x in report)
    print(f'PDFs processed: {len(files)}  matched: {matched}  other: {dict(c)}')
    print(f'Still missing a PDF: {len(missing)} (list: 05_pdfs/missing_pdfs.csv). If a paper truly cannot be obtained set ft_decision=not_retrieved.')
    um = [x for x in report if x['status'] == 'unmatched']
    if um:
        print(f'{len(um)} PDFs could not be matched (moved to 05_pdfs/unmatched/). Rename them to Pxxx.pdf and put them back in inbox.')
    counts = Counter(r['pdf_folder'] for r in rows if r['pdf_file'])
    print('By type:', dict(counts))


# ---------------------------------------------------------------- prisma
def cmd_prisma(a):
    p = Proj(a.project).require()
    il = json.loads(p.import_log.read_text(encoding='utf-8')) if p.import_log.exists() else None
    dl = json.loads(p.dedupe_log.read_text(encoding='utf-8')) if p.dedupe_log.exists() else None
    if not il or not dl:
        die('run import and dedupe first (their logs hold the identification numbers).')
    rows = load_screen(p)
    auto = [r for r in rows if r['ta_decision'] == 'exclude' and r['reason'].startswith('automation')]
    manual_ta_ex = [r for r in rows if r['ta_decision'] == 'exclude' and not r['reason'].startswith('automation')]
    undecided = [r for r in rows if not r['ta_decision']]
    sought = [r for r in rows if r['ta_decision'] in ('include', 'maybe')]
    notret = [r for r in sought if r['ft_decision'] == 'not_retrieved']
    assessed = [r for r in sought if r['ft_decision'] != 'not_retrieved']
    ex_ft = [r for r in assessed if r['ft_decision'] == 'exclude']
    inc = [r for r in assessed if r['ft_decision'] == 'include']
    undecided_ft = [r for r in assessed if not r['ft_decision']]
    reasons = Counter((r['reason'] or 'reason not written') for r in ex_ft)
    ident = {k: v['records'] for k, v in il['per_db'].items()}
    out = {'identified': ident, 'duplicates': dl['duplicates_removed'], 'automation_excluded': len(auto),
           'screened': len(rows) - len(auto), 'excluded_ta': len(manual_ta_ex), 'sought': len(sought),
           'not_retrieved': len(notret), 'assessed': len(assessed), 'excluded_ft': dict(reasons), 'included': len(inc)}
    write_json(p.root / 'prisma.json', out)
    print(json.dumps(out, indent=2))
    warn = []
    if sum(ident.values()) - dl['duplicates_removed'] != dl['unique']:
        warn.append('identified - duplicates != unique records; did you re-import after dedupe? Run import and dedupe again.')
    if undecided:
        warn.append(f'{len(undecided)} records have an empty ta_decision (title/abstract screening not finished).')
    if undecided_ft:
        warn.append(f'{len(undecided_ft)} sought papers have an empty ft_decision (full-text decision missing).')
    if not rows:
        warn.append('screening sheet is empty.')
    for w in warn:
        print('WARNING:', w, file=sys.stderr)
    print('\nPicture:  python visuals.py prisma prisma.json prisma.png --lang en')
    print('Check:', 'numbers are final only after screening is complete.' if warn else 'all stages add up.')


# ---------------------------------------------------------------- pack (PDF -> Word parts)
HEAD_RE = re.compile(r'^(\d+(\.\d+)*\.?\s+)?[A-Z][A-Za-z0-9 ,:&/()\-]{2,70}$')
REFS_RE = re.compile(r'^\s*(\d+\.?\s*)?(references|bibliography|literature cited|works cited)\s*:?\s*$', re.I)


def pdf_to_paragraphs(text):
    text = text.replace('\r', '')
    text = re.sub(r'(?<=[a-z])-\n(?=[a-z])', '', text)
    paras, cur = [], []

    def flush():
        if cur:
            paras.append(' '.join(cur))
            cur.clear()
    for line in re.split(r'\n|\f', text):
        s = line.strip()
        if not s or re.fullmatch(r'\d{1,4}', s):
            flush() if not s else None
            continue
        if len(s.split()) <= 8 and not s.endswith(('.', ',', ';')) and HEAD_RE.match(s) and (s[0].isdigit() or s.isupper() or s.istitle() or len(s.split()) <= 3):
            flush()
            paras.append(s)
            continue
        cur.append(s)
    flush()
    return [re.sub(r'\s+', ' ', x).strip() for x in paras if x.strip()]


def strip_refs(paras):
    for i in range(len(paras) - 1, -1, -1):
        if REFS_RE.match(paras[i]) and i > len(paras) * 0.4:
            return paras[:i], True
    return paras, False


def need_docx():
    try:
        import docx
        return docx
    except ImportError:
        die('Word files need python-docx: pip install python-docx')


def cmd_pack(a):
    docx = need_docx()
    p = Proj(a.project).require()
    rows = [r for r in load_screen(p) if r['pdf_file']]
    if a.stage == 'included':
        rows = [r for r in rows if r['ft_decision'] == 'include']
        if not rows:
            die('no rows with ft_decision = include and a PDF. Mark the papers you keep (ft_decision=include), or use --stage any.')
    rows.sort(key=lambda r: r['pid'])
    p.pack_dir.mkdir(exist_ok=True)
    for old in list(p.pack_dir.glob('main_part*.docx')) + list(p.pack_dir.glob('supplementary_part*.docx')):
        old.unlink()
    index, parts_written = [], []
    for role in ('main', 'supplementary'):
        sel = [r for r in rows if (r['role'] or 'main') == role]
        if not sel:
            continue
        parts, cur, cur_w = [], [], 0
        for r in sel:
            path = p.pdfs / r['pdf_file']
            text, npages = pdf_text(path, a.engine)
            paras = pdf_to_paragraphs(text)
            cut = False
            if a.strip_refs:
                paras, cut = strip_refs(paras)
            words = sum(len(x.split()) for x in paras)
            warn = []
            if npages and len(text.strip()) / max(npages, 1) < 300:
                warn.append('little text: scanned PDF? needs OCR')
            if a.strip_refs and not cut:
                warn.append('no References heading found; refs kept')
            item = (r, paras, words, npages, warn)
            if cur and cur_w + words > a.words:
                parts.append(cur)
                cur, cur_w = [], 0
            cur.append(item)
            cur_w += words
        if cur:
            parts.append(cur)
        for pi, part in enumerate(parts, 1):
            name = f'{role}_part{pi:02}.docx'
            d = docx.Document()
            d.core_properties.title = f'{role} papers, part {pi}'
            d.add_heading(f'{role.capitalize()} papers - part {pi} of {len(parts)}', 0)
            d.add_paragraph('Cite papers ONLY by their tags, for example [P012]. Contents:')
            for r, *_ in part:
                d.add_paragraph(xml_clean(f"[{r['pid']}] {r['title']} ({r['year']})"), style='List Bullet')
            for r, paras, words, npages, warn in part:
                d.add_page_break()
                d.add_heading(xml_clean(f"[{r['pid']}] {r['title']}"), level=1)
                meta = f"{r['authors']} | {r['year']} | {r['venue']} | {r['doc_type']}" + (f" | doi:{r['doi']}" if r['doi'] else '')
                d.add_paragraph().add_run(xml_clean(meta)).italic = True
                for para in paras:
                    d.add_paragraph(xml_clean(para))
                index.append({'file': name, 'pid': r['pid'], 'role': role, 'words': words, 'pages': npages, 'warnings': '; '.join(warn)})
            d.save(p.pack_dir / name)
            parts_written.append((name, sum(w for _, _, w, _, _ in part), len(part)))
    write_csv(p.pack_dir / 'pack_index.csv', index, ['file', 'pid', 'role', 'words', 'pages', 'warnings'])
    print(table([[n, w, c] for n, w, c in parts_written], ['file', 'words', 'papers']))
    bad = [x for x in index if x['warnings']]
    if bad:
        print(f'{len(bad)} papers have warnings (see 06_pack/pack_index.csv):')
        for x in bad[:10]:
            print(f"  {x['pid']}: {x['warnings']}")
    print('Open one part in Word and spot-check a two-column paper before uploading anything.')


# ---------------------------------------------------------------- cite (tags -> numbered references)
TAG_RE = re.compile(r'\[\s*(P\d{3,}(?:\s*(?:,|;|\u2013|\u2014|-)\s*P\d{3,})*)\s*\]')
NUM_BRACKET_RE = re.compile(r'\[\s*\d+(?:\s*[,\u2013-]\s*\d+)*\s*\]')
AUTHOR_YEAR_RE = re.compile(r'\(([A-Z][A-Za-z\-\']+(?: et al\.| and [A-Z][A-Za-z\-\']+)?,? (?:19|20)\d{2}[a-z]?(?:; [^)]{3,60})?)\)')


def expand_tag(inner, known):
    pids, parts = [], re.split(r'\s*([,;])\s*', inner)
    for part in parts:
        if part in (',', ';') or not part:
            continue
        m = re.fullmatch(r'(P\d{3,})\s*[\u2013\u2014-]\s*(P\d{3,})', part)
        if m:
            lo, hi = int(m.group(1)[1:]), int(m.group(2)[1:])
            pids += [q for q in sorted(known, key=lambda x: int(x[1:])) if lo <= int(q[1:]) <= hi]
        else:
            pids.append(part)
    return pids


def compress_numbers(nums):
    nums = sorted(set(nums))
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        if j - i >= 2:
            out.append(f'{nums[i]}\u2013{nums[j]}')
        else:
            out += [str(x) for x in nums[i:j + 1]]
        i = j + 1
    return ', '.join(out)


def format_ref(n, r):
    au = [x.strip() for x in r['authors'].split(';') if x.strip()]
    au_s = '; '.join(au[:6]) + ('; et al.' if len(au) > 6 else '')
    parts = [x.strip().rstrip('.') for x in (au_s, r['title'], r['venue'], r['year']) if x and x.strip()]
    s = '. '.join(parts)
    if r['doi']:
        s += f". doi:{r['doi']}"
    return f'[{n}] {s}'


def iter_docx_paragraphs(doc):
    for par in doc.paragraphs:
        yield par

    def walk(tables):
        for t in tables:
            for row in t.rows:
                for cell in row.cells:
                    for par in cell.paragraphs:
                        yield par
                    yield from walk(cell.tables)
    yield from walk(doc.tables)


def replace_in_paragraph(par, rx, fn):
    runs = par.runs
    if not runs:
        return 0
    parts = [r.text for r in runs]
    full = ''.join(parts)
    matches = list(rx.finditer(full))
    if not matches:
        return 0
    bounds, pos = [], 0
    for t in parts:
        bounds.append((pos, pos + len(t)))
        pos += len(t)
    for m in reversed(matches):
        s, e, new, placed = m.start(), m.end(), fn(m), False
        for i, (lo_b, hi_b) in enumerate(bounds):
            if hi_b <= s or lo_b >= e:
                continue
            lo, hi = max(s, lo_b) - lo_b, min(e, hi_b) - lo_b
            parts[i] = parts[i][:lo] + (new if not placed else '') + parts[i][hi:]
            placed = True
    for r, t in zip(runs, parts):
        r.text = t
    return len(matches)


def cmd_cite(a):
    p = Proj(a.project).require()
    rows = [r for r in load_screen(p) if r['pid']]
    known = {r['pid']: r for r in rows}
    src = Path(a.draft)
    if not src.exists():
        die(f'{src} not found')
    is_docx = src.suffix.lower() == '.docx'
    if is_docx:
        docx = need_docx()
        doc = docx.Document(str(src))
        texts = [par.text for par in iter_docx_paragraphs(doc)]
    else:
        raw = read_text_file(src)
        texts = raw.splitlines()
    order, unknown = {}, Counter()
    for t in texts:
        for m in TAG_RE.finditer(t):
            for pid in expand_tag(m.group(1), known):
                if pid not in known:
                    unknown[pid] += 1
                elif pid not in order:
                    order[pid] = len(order) + 1
    untagged_num = sum(len(NUM_BRACKET_RE.findall(t)) for t in texts)
    untagged_ay = [m.group(0) for t in texts for m in AUTHOR_YEAR_RE.finditer(t)]

    def repl(m):
        pids = expand_tag(m.group(1), known)
        nums = [order[x] for x in pids if x in order]
        bad = [x for x in pids if x not in order]
        return '[' + compress_numbers(nums) + ((' ' if nums else '') + '?' + ','.join(bad) if bad else '') + ']'
    out_dir = Path(a.out_dir) if a.out_dir else p.draft
    out_dir.mkdir(parents=True, exist_ok=True)
    refs = [format_ref(n, known[pid]) for pid, n in sorted(order.items(), key=lambda kv: kv[1])]
    if is_docx:
        for par in iter_docx_paragraphs(doc):
            replace_in_paragraph(par, TAG_RE, repl)
        try:
            doc.add_heading('References', level=1)
        except KeyError:  # Word only stores the styles a document uses; this file has no "Heading 1"
            from docx.shared import Pt
            hp = doc.add_paragraph()
            hr = hp.add_run('References')
            hr.bold = True
            hr.font.size = Pt(16)
        for line in refs:
            doc.add_paragraph(xml_clean(line))
        out_path = out_dir / (src.stem + '_numbered.docx')
        doc.save(str(out_path))
    else:
        body = TAG_RE.sub(repl, raw)
        out_path = out_dir / (src.stem + '_numbered' + src.suffix)
        out_path.write_text(body + '\n\nReferences\n\n' + '\n'.join(refs) + '\n', encoding='utf-8')
    (out_dir / 'references.txt').write_text('\n'.join(refs) + '\n', encoding='utf-8')
    ris = []
    for pid, n in sorted(order.items(), key=lambda kv: kv[1]):
        r = known[pid]
        ty = {'conference': 'CPAPER', 'book': 'BOOK', 'preprint': 'UNPB'}.get(r['doc_type'], 'JOUR')
        ris += [f'TY  - {ty}', f"TI  - {r['title']}"] + [f'AU  - {x.strip()}' for x in r['authors'].split(';') if x.strip()]
        ris += [f"PY  - {r['year']}", f"T2  - {r['venue']}"] + ([f"DO  - {r['doi']}"] if r['doi'] else []) + ['ER  - ', '']
    (out_dir / 'references.ris').write_text('\n'.join(ris), encoding='utf-8')
    cited = set(order)
    uncited = [r['pid'] for r in rows if r['ft_decision'] == 'include' and r['pid'] not in cited]
    not_included = [pid for pid in cited if known[pid]['ft_decision'] == 'exclude']
    rep = [f'Draft: {src.name}', f'Distinct papers cited: {len(order)}', '']
    if unknown:
        rep.append('ERROR - tags that do not exist in your screening sheet (possible invented citations): ' + ', '.join(f'{k} (x{v})' for k, v in unknown.items()))
    if not_included:
        rep.append('WARNING - cited but marked ft_decision=exclude: ' + ', '.join(sorted(not_included)))
    if untagged_ay:
        rep.append(f'WARNING - {len(untagged_ay)} author-year citations without tags, e.g. ' + '; '.join(untagged_ay[:3]))
    if untagged_num:
        rep.append(f'WARNING - {untagged_num} numeric [n] citations without tags (the AI may have invented them).')
    if uncited:
        rep.append(f'NOTE - included papers never cited ({len(uncited)}): ' + ', '.join(uncited[:40]))
    if len(rep) == 3:
        rep.append('All citations are valid tags.')
    (out_dir / 'cite_report.txt').write_text('\n'.join(rep) + '\n', encoding='utf-8')
    print('\n'.join(rep))
    print(f'\nWrote: {out_path}, references.txt, references.ris (import the .ris into Zotero for final journal style), cite_report.txt')
    if unknown:
        sys.exit(1)


# ---------------------------------------------------------------- comments (Word -> next prompt)
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def cmd_comments(a):
    src = Path(a.draft)
    if not src.exists() or src.suffix.lower() != '.docx':
        die('give a .docx file that has comments/highlights')
    with zipfile.ZipFile(src) as z:
        names = z.namelist()
        doc_xml = ET.fromstring(z.read('word/document.xml'))
        com_xml = ET.fromstring(z.read('word/comments.xml')) if 'word/comments.xml' in names else None
    comments = {}
    if com_xml is not None:
        for c in com_xml.iter(W + 'comment'):
            cid = c.get(W + 'id')
            txt = '\n'.join(''.join(t.text or '' for t in par.iter(W + 't')) for par in c.iter(W + 'p')).strip()
            comments[cid] = {'author': c.get(W + 'author', ''), 'date': (c.get(W + 'date') or '')[:10], 'text': txt, 'anchor': '', 'section': ''}
    active, section, hl, hl_color = set(), '', [], ''
    body = doc_xml.find(W + 'body')
    for par in body.iter(W + 'p'):
        ppr = par.find(W + 'pPr')
        style = ppr.find(W + 'pStyle').get(W + 'val') if (ppr is not None and ppr.find(W + 'pStyle') is not None) else ''
        ptxt = ''.join(t.text or '' for t in par.iter(W + 't'))
        if re.match(r'(?i)heading\s*\d|title', style or '') and ptxt.strip():
            section = ptxt.strip()
        cur_hl = ''
        for el in par.iter():
            if el.tag == W + 'commentRangeStart':
                active.add(el.get(W + 'id'))
                comments.setdefault(el.get(W + 'id'), {'author': '', 'date': '', 'text': '(comment text missing)', 'anchor': '', 'section': ''})
                comments[el.get(W + 'id')]['section'] = comments[el.get(W + 'id')]['section'] or section
            elif el.tag == W + 'commentRangeEnd':
                active.discard(el.get(W + 'id'))
            elif el.tag == W + 'r':
                t = ''.join(x.text or '' for x in el.iter(W + 't'))
                for cid in active:
                    comments[cid]['anchor'] += t
                rpr = el.find(W + 'rPr')
                h = rpr.find(W + 'highlight') if rpr is not None else None
                if h is not None and h.get(W + 'val') not in (None, 'none') and t:
                    cur_hl += t
                    hl_color = h.get(W + 'val')
                elif cur_hl:
                    hl.append((section, cur_hl.strip(), hl_color))
                    cur_hl = ''
        if cur_hl:
            hl.append((section, cur_hl.strip(), hl_color))
        for cid in active:
            comments[cid]['anchor'] += ' '
    commented_text = ' '.join(c['anchor'] for c in comments.values())
    hl = [(s, t, c) for s, t, c in hl if t and t not in commented_text]
    rnd = f'Round {a.round}' if a.round else 'Revision round'
    lines = [f'# {rnd}: author feedback on {src.name}', '',
             'Revise the draft below. Handle every item. Change ONLY the passages named in the items; keep everything else word for word.',
             'Keep every [P###] citation tag. Do not add citations that are not in the supplied papers. If an item needs a fact that is not in the papers, write "not reported" and ask me.', '']
    ordered = sorted(comments.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0)
    if ordered:
        lines.append('## Comments')
        for i, (cid, c) in enumerate(ordered, 1):
            anchor = re.sub(r'\s+', ' ', c['anchor']).strip()
            lines += [f"{i}. Section: {c['section'] or '(start)'}",
                      f'   Passage: "{anchor[:400]}"' if anchor else '   Passage: (whole paragraph / not anchored)',
                      f"   Request ({c['author'] or 'author'}): {c['text']}", '']
    if hl:
        lines.append('## Highlighted passages without a comment (check them for accuracy, clarity and wording)')
        for s, t, c in hl:
            lines.append(f'- Section: {s or "(start)"} | {c}: "{t[:300]}"')
        lines.append('')
    lines += ['## Output', 'Return the full revised text, then a short list "What I changed" mapping each item number to the change made.']
    out = Path(a.out) if a.out else src.with_name(f'revision_request_{a.round or "next"}.md')
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{len(ordered)} comments, {len(hl)} extra highlighted passages -> {out}')
    print('Paste this file after the current draft into your AI chat (draft first, then this request).')


# ---------------------------------------------------------------- status / stats
def cmd_status(a):
    p = Proj(a.project).require()
    cfg = p.cfg()
    print(f"Project: {cfg.get('title') or p.root.name}  ({cfg.get('review_type')})")
    il = json.loads(p.import_log.read_text(encoding='utf-8')) if p.import_log.exists() else None
    dl = json.loads(p.dedupe_log.read_text(encoding='utf-8')) if p.dedupe_log.exists() else None
    print('Imported :', ({k: v['records'] for k, v in il['per_db'].items()}, il['total_records']) if il else 'not yet')
    print('Dedupe   :', f"unique {dl['unique']}, duplicates {dl['duplicates_removed']}" if dl else 'not yet')
    if p.screen_csv.exists():
        rows = load_screen(p)
        print('Records  :', len(rows), ' by type:', dict(Counter(r['doc_type'] for r in rows)))
        print('Keywords :', dict(Counter(r['kw_flag'] or '-' for r in rows)))
        print('Title/abs:', dict(Counter(r['ta_decision'] or 'undecided' for r in rows)))
        num = [r for r in rows if r['pid']]
        print('Numbered :', len(num), ' access:', dict(Counter(r['access'] or '-' for r in num)))
        print('PDFs     :', sum(1 for r in num if r['pdf_file']), 'of', len(num), ' by folder:', dict(Counter(r['pdf_folder'] for r in num if r['pdf_file'])))
        print('Full text:', dict(Counter(r['ft_decision'] or 'undecided' for r in num)))
        print('Role     :', dict(Counter(r['role'] or 'main' for r in num if r['ft_decision'] == 'include')))
    else:
        print('Screening: not yet')


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description='Systematic review workflow tool')
    ap.add_argument('-p', '--project', dest='project_pre', default=None, help='project folder (may also be given after the command)')
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('-p', '--project', default=None,
                        help='project folder (default: current folder, or the SLR_PROJECT variable)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    _orig_add = sub.add_parser

    def add_parser(name, **kw):
        return _orig_add(name, parents=[common], **kw)
    sub.add_parser = add_parser
    s = sub.add_parser('init', help='create a project folder')
    s.add_argument('folder')
    s.add_argument('--title', default='')
    s.add_argument('--type', default='systematic', choices=['systematic', 'scoping', 'narrative'])
    s.add_argument('--rq', action='append', help='research question (repeat for several)')
    s.add_argument('--proxy', default='', help='university proxy prefix, e.g. https://login.ezproxy.myuni.edu/login?url=')
    s.add_argument('--library-home', default='', help='library portal address for browser-extension/portal logins (your library portal home page)')
    s.add_argument('--library-search', default='', help='portal search address with {q} where the publisher name goes')
    s.set_defaults(fn=cmd_init)
    sub.add_parser('import', help='read database exports').set_defaults(fn=cmd_import)
    d = sub.add_parser('dedupe', help='find duplicates')
    d.add_argument('--fuzzy', type=float, default=0.93, help='title similarity needed to merge (default 0.93)')
    d.set_defaults(fn=cmd_dedupe)
    sc = sub.add_parser('screen', help='build/refresh screening sheet with keyword flags')
    sc.add_argument('--apply', action='store_true', help='mark clear keyword failures as excluded by automation')
    sc.set_defaults(fn=cmd_screen)
    sub.add_parser('number', help='assign permanent paper numbers').set_defaults(fn=cmd_number)
    ac = sub.add_parser('access', help='open access vs subscription (Unpaywall)')
    ac.add_argument('--refresh', action='store_true')
    ac.set_defaults(fn=cmd_access)
    b = sub.add_parser('batches', help='HTML pages with 10 papers each')
    b.add_argument('--size', type=int, default=0)
    b.add_argument('--proxy', default=None)
    b.set_defaults(fn=cmd_batches)
    t = sub.add_parser('tabs', help='open one batch in browser tabs')
    t.add_argument('kind', choices=['open', 'sub'])
    t.add_argument('batch', type=int)
    t.add_argument('--delay', type=float, default=0.6)
    t.set_defaults(fn=cmd_tabs)
    pm = sub.add_parser('pdfmatch', help='match PDFs in 05_pdfs/inbox to records')
    pm.add_argument('--engine', choices=['auto', 'pypdf', 'pdftotext'], default='auto')
    pm.set_defaults(fn=cmd_pdfmatch)
    sub.add_parser('prisma', help='PRISMA numbers').set_defaults(fn=cmd_prisma)
    pk = sub.add_parser('pack', help='PDFs -> Word parts for AI upload')
    pk.add_argument('--words', type=int, default=45000, help='approximate words per Word file (default 45000)')
    pk.add_argument('--stage', choices=['included', 'any'], default='included')
    pk.add_argument('--engine', choices=['auto', 'pypdf', 'pdftotext'], default='auto')
    pk.add_argument('--keep-refs', dest='strip_refs', action='store_false', help='keep reference lists of each paper')
    pk.set_defaults(fn=cmd_pack, strip_refs=True)
    ci = sub.add_parser('cite', help='[P012] tags -> numbered citations + references')
    ci.add_argument('draft')
    ci.add_argument('--out-dir', default='')
    ci.set_defaults(fn=cmd_cite)
    co = sub.add_parser('comments', help='Word comments and highlights -> revision prompt')
    co.add_argument('draft')
    co.add_argument('--round', type=int, default=0)
    co.add_argument('--out', default='')
    co.set_defaults(fn=cmd_comments)
    sub.add_parser('status', help='counts at every stage').set_defaults(fn=cmd_status)
    a = ap.parse_args()
    a.project = a.project or a.project_pre or os.environ.get('SLR_PROJECT') or '.'
    a.fn(a)


if __name__ == '__main__':
    main()
