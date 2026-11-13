#!/usr/bin/env python3
# litsearch.py - optional helper: a small literature-search tool (OpenAlex + PubMed + Crossref).
# In the review workflow it is used mainly for `verify` (does each reference really exist?).
#
# Usage:
#   python litsearch.py search  --q '("type 2 diabetes") AND (yoga OR "yogic practice")' --from 2015 --max 200
#   python litsearch.py chase   --ids W2741809807,10.1000/xyz --dir both --into results.csv
#   python litsearch.py verify  refs.txt            (one reference or DOI per line)
#   python litsearch.py export  results.csv --format ris --only include --out refs.ris
#   python litsearch.py prisma  results.csv         (writes prisma.json; picture: python visuals.py prisma prisma.json img/prisma.png --lang en)
#
# Keys (optional, set as environment variables):
#   OPENALEX_API_KEY  - OpenAlex now needs an API key (free: create an account at openalex.org)
#   NCBI_API_KEY      - makes PubMed faster (works without it)
#   CONTACT_EMAIL     - a polite contact address sent to Crossref / NCBI (sent only if you set it yourself)
import argparse
import csv
import difflib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

OPENALEX = os.environ.get('OPENALEX_BASE', 'https://api.openalex.org')
EUTILS = os.environ.get('EUTILS_BASE', 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils')
CROSSREF = os.environ.get('CROSSREF_BASE', 'https://api.crossref.org')
UA = 'litsearch.py/0.1 (personal literature search tool)'
FIELDS = ['id', 'source', 'doi', 'pmid', 'title', 'year', 'journal', 'authors', 'abstract',
          'cited_by', 'type', 'ta_decision', 'ft_decision', 'reason']
DOI_RE = re.compile(r'10\.\d{4,9}/[^\s"<>,;]+', re.I)


# ---------- HTTP ----------
class ApiError(Exception):
    pass


def http_get(url, params=None, as_json=True, tries=4):
    if params:
        url += ('&' if '?' in url else '?') + urllib.parse.urlencode(params, safe=',:|*')
    delay = 1.0
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                body = r.read().decode('utf-8')
                return json.loads(body) if as_json else body
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 409) and 'openalex' in url:
                raise ApiError('OpenAlex key problem (HTTP %d). Is OPENALEX_API_KEY set correctly? The free daily credits may have run out.' % e.code)
            if e.code == 404:
                raise ApiError('404')
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise ApiError(f'HTTP {e.code}: {url[:120]}')
        except urllib.error.URLError as e:
            if attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise ApiError(f'Network error: {e.reason}')


# ---------- general helpers ----------
def norm_doi(d):
    if not d:
        return ''
    d = d.strip().lower()
    d = re.sub(r'^(https?://(dx\.)?doi\.org/|doi:\s*)', '', d)
    return d.rstrip('.')


def norm_title(t):
    return re.sub(r'[^a-z0-9]+', '', (t or '').lower())


def new_rec(**kw):
    r = {k: '' for k in FIELDS}
    r.update(kw)
    return r


def abstract_from_inverted(inv):
    if not inv:
        return ''
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return ' '.join(pos[i] for i in sorted(pos))


# ---------- OpenAlex ----------
OA_SELECT = 'id,doi,title,publication_year,primary_location,authorships,abstract_inverted_index,cited_by_count,type,ids'


def parse_oa(w):
    loc = w.get('primary_location') or {}
    src = (loc.get('source') or {}).get('display_name') or ''
    authors = '; '.join((a.get('author') or {}).get('display_name', '') for a in (w.get('authorships') or []))
    pmid = (w.get('ids') or {}).get('pmid') or ''
    return new_rec(
        id=(w.get('id') or '').rsplit('/', 1)[-1], source='openalex', doi=norm_doi(w.get('doi')),
        pmid=pmid.rsplit('/', 1)[-1], title=w.get('title') or '', year=w.get('publication_year') or '',
        journal=src, authors=authors, abstract=abstract_from_inverted(w.get('abstract_inverted_index')),
        cited_by=w.get('cited_by_count') or 0, type=w.get('type') or '')


def oa_params(key):
    p = {'select': OA_SELECT}
    if key:
        p['api_key'] = key
    return p


def search_openalex(q, y_from, y_to, max_n, key):
    params = oa_params(key)
    params.update({'search': q, 'per-page': min(100, max_n), 'cursor': '*'})
    flt = []
    if y_from:
        flt.append(f'from_publication_date:{y_from}-01-01')
    if y_to:
        flt.append(f'to_publication_date:{y_to}-12-31')
    if flt:
        params['filter'] = ','.join(flt)
    out, total = [], None
    while len(out) < max_n:
        data = http_get(OPENALEX + '/works', params)
        total = (data.get('meta') or {}).get('count', total)
        res = data.get('results') or []
        out += [parse_oa(w) for w in res]
        cur = (data.get('meta') or {}).get('next_cursor')
        if not cur or not res:
            break
        params['cursor'] = cur
    return out[:max_n], total


# ---------- PubMed ----------
def parse_pm(art):
    mc = art.find('MedlineCitation')
    a = mc.find('Article')
    t = a.find('ArticleTitle')
    title = ''.join(t.itertext()).strip() if t is not None else ''
    parts = []
    for x in a.findall('Abstract/AbstractText'):
        txt = ''.join(x.itertext()).strip()
        lab = x.get('Label')
        parts.append(f'{lab}: {txt}' if lab else txt)
    names = []
    for au in a.findall('AuthorList/Author'):
        ln, fn = au.findtext('LastName'), au.findtext('ForeName') or au.findtext('Initials')
        if ln:
            names.append(f'{ln} {fn}'.strip() if fn else ln)
        elif au.findtext('CollectiveName'):
            names.append(au.findtext('CollectiveName'))
    year = a.findtext('Journal/JournalIssue/PubDate/Year')
    if not year:
        m = re.search(r'(19|20)\d{2}', a.findtext('Journal/JournalIssue/PubDate/MedlineDate') or '')
        year = m.group(0) if m else ''
    doi = ''
    for e in a.findall('ELocationID'):
        if e.get('EIdType') == 'doi' and e.text:
            doi = e.text
    if not doi:
        for aid in art.findall('PubmedData/ArticleIdList/ArticleId'):
            if aid.get('IdType') == 'doi' and aid.text:
                doi = aid.text
    pmid = mc.findtext('PMID') or ''
    return new_rec(id='PMID' + pmid, source='pubmed', doi=norm_doi(doi), pmid=pmid, title=title, year=year,
                   journal=a.findtext('Journal/Title') or '', authors='; '.join(names),
                   abstract=' '.join(parts), type=(a.findtext('PublicationTypeList/PublicationType') or ''))


def search_pubmed(q, y_from, y_to, max_n, key):
    params = {'db': 'pubmed', 'term': q, 'retmode': 'json', 'retmax': max_n, 'sort': 'relevance', 'tool': 'litsearch'}
    if y_from or y_to:
        params.update({'datetype': 'pdat', 'mindate': str(y_from or 1900), 'maxdate': str(y_to or 3000)})
    if key:
        params['api_key'] = key
    if os.environ.get('CONTACT_EMAIL'):
        params['email'] = os.environ['CONTACT_EMAIL']
    r = http_get(EUTILS + '/esearch.fcgi', params)['esearchresult']
    ids, total = r.get('idlist', []), int(r.get('count', 0))
    out = []
    for i in range(0, len(ids), 100):
        p = {'db': 'pubmed', 'id': ','.join(ids[i:i + 100]), 'retmode': 'xml', 'tool': 'litsearch'}
        if key:
            p['api_key'] = key
        xml = http_get(EUTILS + '/efetch.fcgi', p, as_json=False)
        for art in ET.fromstring(xml).iter('PubmedArticle'):
            out.append(parse_pm(art))
        time.sleep(0.11 if key else 0.35)
    return out, total


# ---------- dedupe, CSV ----------
def merge_records(existing, new):
    """Merge duplicates (by DOI or title) and count how many were removed."""
    by_doi, by_title = {}, {}
    out = []
    for r in existing:
        out.append(r)
        if r['doi']:
            by_doi[r['doi']] = r
        if r['title']:
            by_title[norm_title(r['title'])] = r
    dups = 0
    for r in new:
        hit = (by_doi.get(r['doi']) if r['doi'] else None) or by_title.get(norm_title(r['title']))
        if hit is not None:
            dups += 1
            for k in ('abstract', 'doi', 'pmid', 'journal', 'authors', 'year'):
                if not hit[k] and r[k]:
                    hit[k] = r[k]
            if r['source'] not in hit['source'].split('+'):
                hit['source'] += '+' + r['source']
            continue
        out.append(r)
        if r['doi']:
            by_doi[r['doi']] = r
        if r['title']:
            by_title[norm_title(r['title'])] = r
    return out, dups


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8-sig', newline='') as f:
        rows = []
        for row in csv.DictReader(f):
            r = new_rec()
            r.update({k: (row.get(k) or '') for k in FIELDS})
            rows.append(r)
        return rows


def write_csv(path, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:  # utf-8-sig: Excel shows accents and non-English letters correctly
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def load_log(path):
    if os.path.exists(path):
        return json.load(open(path, encoding='utf-8'))
    return {'searches': [], 'duplicates_removed': 0}


# ---------- commands ----------
def cmd_search(a):
    oa_key, pm_key = os.environ.get('OPENALEX_API_KEY'), os.environ.get('NCBI_API_KEY')
    rows = read_csv(a.out)
    log = load_log(a.log)
    new_all = []
    for src in [s.strip() for s in a.sources.split(',') if s.strip()]:
        try:
            if src == 'openalex':
                if not oa_key:
                    print('Warning: OPENALEX_API_KEY is not set; OpenAlex now almost never works without a key.', file=sys.stderr)
                recs, total = search_openalex(a.q, a.year_from, a.year_to, a.max, oa_key)
            elif src == 'pubmed':
                recs, total = search_pubmed(a.q, a.year_from, a.year_to, a.max, pm_key)
            else:
                print('Unknown source:', src)
                continue
        except ApiError as e:
            print(f'[{src}] failed: {e}', file=sys.stderr)
            continue
        print(f'[{src}] total hits: {total}, fetched: {len(recs)}')
        log['searches'].append({'date': date.today().isoformat(), 'source': src, 'query': a.q,
                                'year_from': a.year_from, 'year_to': a.year_to,
                                'total_hits': total, 'retrieved': len(recs)})
        new_all += recs
    rows, dups = merge_records(rows, new_all)
    log['duplicates_removed'] += dups
    write_csv(a.out, rows)
    json.dump(log, open(a.log, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'Duplicates removed: {dups} | {a.out} now has {len(rows)} records | log: {a.log}')


def resolve_oa_id(x, key):
    x = x.strip()
    if re.fullmatch(r'W\d+', x, re.I):
        return x.upper()
    d = norm_doi(x)
    p = {'select': 'id'}
    if key:
        p['api_key'] = key
    data = http_get(OPENALEX + '/works/' + urllib.parse.quote('https://doi.org/' + d, safe=':/'), p)
    return data['id'].rsplit('/', 1)[-1]


def cmd_chase(a):
    key = os.environ.get('OPENALEX_API_KEY')
    rows = read_csv(a.into)
    log = load_log(a.log)
    found = []
    for x in a.ids.split(','):
        try:
            wid = resolve_oa_id(x, key)
        except ApiError as e:
            print(f'{x}: could not be resolved ({e})', file=sys.stderr)
            continue
        if a.dir in ('back', 'both'):
            p = {'select': 'referenced_works'}
            if key:
                p['api_key'] = key
            refs = [r.rsplit('/', 1)[-1] for r in http_get(OPENALEX + '/works/' + wid, p).get('referenced_works', [])]
            for i in range(0, len(refs), 50):
                p = oa_params(key)
                p.update({'filter': 'openalex:' + '|'.join(refs[i:i + 50]), 'per-page': 50})
                found += [parse_oa(w) for w in http_get(OPENALEX + '/works', p).get('results', [])]
            print(f'{wid}: backward (references) {len(refs)}')
        if a.dir in ('forward', 'both'):
            p = oa_params(key)
            p.update({'filter': 'cites:' + wid, 'per-page': min(100, a.max), 'cursor': '*'})
            got = []
            while len(got) < a.max:
                data = http_get(OPENALEX + '/works', p)
                res = data.get('results') or []
                got += [parse_oa(w) for w in res]
                cur = (data.get('meta') or {}).get('next_cursor')
                if not cur or not res:
                    break
                p['cursor'] = cur
            found += got[:a.max]
            print(f'{wid}: forward (cited by) {len(got[:a.max])}')
    for r in found:
        r['source'] = 'openalex-chase'
    rows, dups = merge_records(rows, found)
    log['duplicates_removed'] += dups
    log['searches'].append({'date': date.today().isoformat(), 'source': 'openalex-chase', 'query': a.ids,
                            'total_hits': len(found), 'retrieved': len(found)})
    write_csv(a.into, rows)
    json.dump(log, open(a.log, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'Newly added: {len(found) - dups} (duplicates {dups}) | total {len(rows)}')


def crossref_params():
    p = {}
    if os.environ.get('CONTACT_EMAIL'):
        p['mailto'] = os.environ['CONTACT_EMAIL']
    return p


def verify_one(line):
    """Check one reference line against Crossref and return (status, doi, detail)."""
    m = DOI_RE.search(line)
    guess_title = re.sub(DOI_RE, '', line).strip(' .;,')
    if m:
        doi = norm_doi(m.group(0))
        try:
            msg = http_get(CROSSREF + '/works/' + urllib.parse.quote(doi, safe='/'), crossref_params())['message']
        except ApiError as e:
            if str(e) == '404':
                return 'DOI not found', doi, 'Crossref does not know this DOI: the reference may be invented'
            return 'check failed', doi, str(e)
        real = (msg.get('title') or [''])[0]
        note = ''
        upd = msg.get('updated-by') or []
        if upd:
            note = ' | notices: ' + ', '.join(sorted({u.get('type', '?') for u in upd}))
        ratio = difflib.SequenceMatcher(None, norm_title(guess_title), norm_title(real)).ratio() if guess_title else None
        retracted = any('retract' in (u.get('type') or '') for u in upd)
        if retracted:
            return 'retracted', doi, real + note
        if ratio is not None and ratio < 0.55 and norm_title(real) not in norm_title(guess_title):
            return 'title mismatch', doi, f'Crossref title: {real}{note}'
        return 'matched', doi, real + note
    try:
        p = crossref_params()
        p.update({'query.bibliographic': line, 'rows': 1})
        items = http_get(CROSSREF + '/works', p)['message']['items']
    except ApiError as e:
        return 'check failed', '', str(e)
    if not items:
        return 'not found', '', 'Crossref has no matching reference'
    it = items[0]
    real = (it.get('title') or [''])[0]
    ratio = difflib.SequenceMatcher(None, norm_title(line), norm_title(real)).ratio()
    return ('possible match (no DOI)' if ratio >= 0.5 else 'not found'), it.get('DOI', ''), f'closest match: {real}'


def cmd_verify(a):
    lines = [l.strip() for l in open(a.file, encoding='utf-8') if l.strip() and not l.startswith('#')]
    report = []
    for i, line in enumerate(lines, 1):
        status, doi, detail = verify_one(line)
        report.append({'n': i, 'status': status, 'doi': doi, 'detail': detail, 'reference': line})
        print(f'{i:3}. [{status}] {doi}  {detail}')
        time.sleep(0.1)
    out = a.out or os.path.splitext(a.file)[0] + '_verify.csv'
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['n', 'status', 'doi', 'detail', 'reference'])
        w.writeheader()
        w.writerows(report)
    bad = sum(1 for r in report if r['status'] not in ('matched',))
    print(f'\nTotal {len(report)}; to check by hand {bad}; report: {out}')


def cmd_export(a):
    rows = read_csv(a.file)
    if a.only:
        rows = [r for r in rows if a.only in (r['ft_decision'], r['ta_decision']) and r['ft_decision'] != 'exclude']
    lines = []
    for r in rows:
        authors = [x.strip() for x in r['authors'].split(';') if x.strip()]
        if a.format == 'ris':
            lines += ['TY  - JOUR', f'TI  - {r["title"]}'] + [f'AU  - {x}' for x in authors]
            lines += [f'PY  - {r["year"]}', f'JO  - {r["journal"]}']
            if r['doi']:
                lines.append(f'DO  - {r["doi"]}')
            if r['abstract']:
                lines.append(f'AB  - {r["abstract"]}')
            lines += ['ER  - ', '']
        else:
            last = re.sub(r'\W', '', authors[0].split()[0]) if authors else 'anon'
            first = re.sub(r'\W', '', (r['title'].split() or ['x'])[0]).lower()
            lines += ['@article{%s%s%s,' % (last.lower(), r['year'], first),
                      '  title = {%s},' % r['title'], '  author = {%s},' % ' and '.join(authors),
                      '  year = {%s},' % r['year'], '  journal = {%s},' % r['journal'],
                      '  doi = {%s}' % r['doi'], '}', '']
    out = a.out or ('refs.' + ('ris' if a.format == 'ris' else 'bib'))
    open(out, 'w', encoding='utf-8').write('\n'.join(lines))
    print(f'{len(rows)} records -> {out} (in Zotero: File > Import)')


def cmd_prisma(a):
    rows = read_csv(a.file)
    log = load_log(a.log)
    ident = {}
    for s in log['searches']:
        ident[s['source']] = ident.get(s['source'], 0) + int(s.get('retrieved') or 0)
    n = len(rows)
    ex_ta = sum(1 for r in rows if r['ta_decision'] == 'exclude')
    sought = sum(1 for r in rows if r['ta_decision'] in ('include', 'maybe'))
    not_ret = sum(1 for r in rows if r['ft_decision'] == 'not_retrieved')
    ex_ft = [r for r in rows if r['ft_decision'] == 'exclude']
    reasons = {}
    for r in ex_ft:
        reasons[r['reason'] or 'reason not written'] = reasons.get(r['reason'] or 'reason not written', 0) + 1
    undecided = sum(1 for r in rows if not r['ta_decision'])
    out = {'identified': ident, 'duplicates': log['duplicates_removed'], 'screened': n,
           'excluded_ta': ex_ta, 'sought': sought, 'not_retrieved': not_ret,
           'assessed': sought - not_ret, 'excluded_ft': reasons,
           'included': sum(1 for r in rows if r['ft_decision'] == 'include')}
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if undecided:
        print(f'Note: {undecided} records have an empty ta_decision; these numbers are final only after screening is complete.', file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description='Literature search helper')
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('search')
    s.add_argument('--q', required=True)
    s.add_argument('--from', dest='year_from', type=int)
    s.add_argument('--to', dest='year_to', type=int)
    s.add_argument('--max', type=int, default=200)
    s.add_argument('--sources', default='openalex,pubmed')
    s.add_argument('--out', default='results.csv')
    s.add_argument('--log', default='search_log.json')
    s.set_defaults(fn=cmd_search)
    c = sub.add_parser('chase')
    c.add_argument('--ids', required=True)
    c.add_argument('--dir', choices=['back', 'forward', 'both'], default='both')
    c.add_argument('--max', type=int, default=100)
    c.add_argument('--into', default='results.csv')
    c.add_argument('--log', default='search_log.json')
    c.set_defaults(fn=cmd_chase)
    v = sub.add_parser('verify')
    v.add_argument('file')
    v.add_argument('--out')
    v.set_defaults(fn=cmd_verify)
    e = sub.add_parser('export')
    e.add_argument('file')
    e.add_argument('--format', choices=['ris', 'bibtex'], default='ris')
    e.add_argument('--only', choices=['include'], default=None)
    e.add_argument('--out')
    e.set_defaults(fn=cmd_export)
    p = sub.add_parser('prisma')
    p.add_argument('file')
    p.add_argument('--log', default='search_log.json')
    p.add_argument('--out', default='prisma.json')
    p.set_defaults(fn=cmd_prisma)
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
