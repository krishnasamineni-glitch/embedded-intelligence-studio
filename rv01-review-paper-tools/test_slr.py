#!/usr/bin/env python3
# test_slr.py - end-to-end test of slr.py with made-up data (no internet, no API keys).
# Usage: python test_slr.py        (needs: pip install python-docx pypdf reportlab)
import csv
import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

HERE = Path(__file__).resolve().parent
SLR = str(HERE / 'slr.py')

A_ABS = 'Yoga practice lowered HbA1c in adults with type 2 diabetes over 12 weeks.'
B_ABS = 'This review covers lifestyle interventions in diabetes including yoga, diet and walking.'
C_ABS = 'We use wearable sensors and machine learning for glucose monitoring in diabetes.'
D_ABS = 'Breathing exercises were tested in a small pilot of people with type 2 diabetes.'
F_ABS = 'A deep network grades diabetic retinopathy from retinal photographs.'
G_ABS = 'Meditation lowered blood pressure in patients with diabetes.'
H_ABS = 'Pranayama improved lung function in diabetics.'

PUBMED = f"""PMID- 111
OWN - NLM
DP  - 2019 Jan
TI  - Yoga for glycaemic control in type 2 diabetes: a randomised trial.
LID - 10.1000/a1 [doi]
AB  - {A_ABS}
FAU - Rao, Kiran
FAU - Devi, Sita
AU  - Rao K
AU  - Devi S
JT  - Journal of Examples
PT  - Journal Article
PT  - Randomized Controlled Trial
OT  - yoga
MH  - Diabetes Mellitus, Type 2

PMID- 222
DP  - 2020 Jan-Feb
TI  - [Breathing exercises and type 2 diabetes: a pilot study].
AB  - {D_ABS}
FAU - Lee, Jae
JT  - Other Journal
LID - 10.2000/d4 [doi]
PT  - Journal Article
"""

SCOPUS_HEAD = ['Authors', 'Author full names', 'Title', 'Year', 'Source title', 'DOI', 'Link', 'Abstract',
               'Author Keywords', 'Index Keywords', 'Document Type', 'Source', 'EID']
SCOPUS_ROWS = [
    ['Rao K.; Devi S.', 'Rao, Kiran (1); Devi, Sita (2)', 'Yoga for glycaemic control in type 2 diabetes: a randomised trial', '2019', 'Journal of Examples', '10.1000/A1', 'https://x/1', A_ABS, 'yoga; diabetes', '', 'Article', 'Scopus', 'e1'],
    ['Kumar P.', 'Kumar, P.', 'Lifestyle interventions in diabetes: a review', '2021', 'Review Journal', '10.1000/b2', 'https://x/2', B_ABS, '', '', 'Review', 'Scopus', 'e2'],
    ['Lee J.', 'Lee, J.', 'Wearable sensors for glucose monitoring using machine learning', '2020', '2020 IEEE International Conference on Health', '10.1109/c3', 'https://x/3', C_ABS, '', '', 'Conference Paper', 'Scopus', 'e3'],
    ['Chen L.', 'Chen, L.', 'Deep learning for retinal image analysis', '2022', 'IEEE Access', '10.1109/f6', 'https://x/4', F_ABS, '', '', 'Article', 'Scopus', 'e4'],
    ['Singh A.', 'Singh, A.', 'Meditation and blood pressure', '2018', 'Hypertension Letters', '10.1000/g7', 'https://x/5', G_ABS, '', '', 'Article', 'Scopus', 'e5'],
    ['Rao K.; Devi S.', 'Rao, Kiran (1); Devi, Sita (2)', 'Yoga for glycaemic control in type 2 diabetes: a randomised trial', '2019', 'Journal of Examples', '10.1000/a1', 'https://x/1', A_ABS, 'yoga; diabetes', '', 'Article', 'Scopus', 'e1'],
]
WOS = f"""FN Clarivate Analytics Web of Science
VR 1.0
PT J
AU Rao, K
   Devi, S
AF Rao, Kiran
   Devi, Sita
TI Yoga for glycaemic control in type 2 diabetes: a randomised trial
SO JOURNAL OF EXAMPLES
AB {A_ABS}
DE yoga; diabetes
DI 10.1000/a1
PY 2019
DT Article
ER

PT J
AF Kumar, P
TI Lifestyle interventions in diabetes: a review
SO REVIEW JOURNAL
AB {B_ABS}
DI 10.1000/b2
PY 2021
DT Review
ER

PT J
AF Rao, Kiran
   Devi, Sita
TI Yoga for glycemic control in type 2 diabetes: A randomized trial
SO JOURNAL OF EXAMPLES
AB {A_ABS}
PY 2019
DT Article
ER

PT J
AF Singh, A
TI Meditation and blood pressure
SO MEDRXIV
AB {G_ABS}
DI 10.1101/g7pp
PY 2018
DT Article
ER

EF
"""
WOS_RIS = """TY  - JOUR
TI  - Lifestyle interventions in diabetes: a review
AU  - Kumar, P
PY  - 2021
JO  - Review Journal
DO  - 10.1000/b2
AB  - Duplicate of a record in the plain text export.
ER  -
"""
SCOPUS_BIB = """@article{das2017,
  author = {Das, R and {M{\\"u}ller}, K},
  title = {Pranayama and lung function in {diabetics}},
  journal = {Respiratory Notes},
  year = {2017},
  doi = {10.1000/h8},
  abstract = {%s},
  keywords = {pranayama; lung}
}
""" % H_ABS
IEEE_HEAD = ['Document Title', 'Authors', 'Publication Title', 'Publication Year', 'Abstract', 'DOI', 'Author Keywords', 'Document Identifier']
IEEE_ROWS = [
    ['Wearable sensors for glucose monitoring using machine learning', 'Lee, J.', '2020 IEEE International Conference on Health', '2020', C_ABS, '10.1109/c3', 'glucose', 'IEEE Conferences'],
    ['Deep learning for retinal image analysis', 'Chen, L.', 'IEEE Access', '2022', F_ABS, '10.1109/f6', '', 'IEEE Journals & Magazines'],
]


class UP(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        data = {
            '/v2/10.1000/a1': {'is_oa': True, 'best_oa_location': {'url_for_pdf': 'http://open.example/a1.pdf', 'url': 'http://open.example/a1'}},
            '/v2/10.1000/b2': {'is_oa': False, 'best_oa_location': None},
            '/v2/10.1000/h8': {'is_oa': True, 'best_oa_location': {'url_for_pdf': None, 'url': 'http://open.example/h8'}},
            '/v2/10.1000/g7': {'is_oa': False, 'best_oa_location': None},
        }.get(path)
        code = 200 if data is not None else 404
        body = json.dumps(data if data is not None else {'message': 'not found'}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)


def write_csv(path, head, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(head)
        w.writerows(rows)


def sheet(proj):
    with open(proj / '03_screening' / 'screening.csv', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def save_sheet(proj, rows):
    with open(proj / '03_screening' / 'screening.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def make_pdf(path, title, lines):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(path), pagesize=A4)
    y = 800
    c.setFont('Helvetica-Bold', 14)
    c.drawString(50, y, title[:90])
    c.setFont('Helvetica', 10)
    for ln in lines:
        y -= 18
        c.drawString(50, y, ln)
    c.save()


def main():
    srv = HTTPServer(('127.0.0.1', 0), UP)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    env = dict(os.environ, UNPAYWALL_BASE=f'http://127.0.0.1:{srv.server_port}/v2', UNPAYWALL_EMAIL='test@example.org',
               PYTHONIOENCODING='utf-8')
    import contextlib
    keep = os.environ.get('SLR_TEST_KEEP')
    cm = contextlib.nullcontext(keep) if keep else tempfile.TemporaryDirectory()
    with cm as d:
        d = Path(d)
        d.mkdir(parents=True, exist_ok=True)
        proj = d / 'rev'
        # `tabs` writes its links to this file instead of opening a real browser (works on Windows, macOS and Linux)
        opened = d / 'opened.txt'
        env['SLR_TABS_LOG'] = str(opened)

        def run(*args, ok=True):
            r = subprocess.run([sys.executable, '-I', SLR, '-p', str(proj)] + list(args), env=env, capture_output=True, text=True)
            print('$ slr.py', ' '.join(args))
            print(r.stdout + r.stderr)
            if ok:
                assert r.returncode == 0, f'failed: {args}'
            return r

        run('init', str(proj), '--title', 'Yoga and T2D', '--rq', 'Does yoga lower HbA1c?', '--proxy', 'https://proxy.example/login?url=')
        ex = proj / '01_exports'
        (ex / 'pubmed' / 'pubmed-yoga-set.txt').write_text(PUBMED, encoding='utf-8')
        write_csv(ex / 'scopus' / 'scopus.csv', SCOPUS_HEAD, SCOPUS_ROWS)
        (ex / 'scopus' / 'scopus_extra.bib').write_text(SCOPUS_BIB, encoding='utf-8')
        (ex / 'wos' / 'savedrecs.txt').write_text(WOS, encoding='utf-8')
        (ex / 'wos' / 'savedrecs.ris').write_text(WOS_RIS, encoding='utf-8')
        write_csv(ex / 'ieee' / 'export2026.csv', IEEE_HEAD, IEEE_ROWS)

        out = run('import').stdout
        log = json.load(open(proj / '02_records' / 'import_log.json', encoding='utf-8'))
        got = {k: v['records'] for k, v in log['per_db'].items()}
        assert got == {'PubMed': 2, 'Scopus': 6, 'Web of Science': 4, 'IEEE Xplore': 2}, got
        assert log['per_db']['Scopus']['repeats_removed'] == 1 and log['per_db']['Web of Science']['repeats_removed'] == 1, log['per_db']
        recs = list(csv.DictReader(open(proj / '02_records' / 'records_all.csv', encoding='utf-8-sig')))
        by_title = {r['title']: r for r in recs}
        assert 'Breathing exercises and type 2 diabetes: a pilot study' in by_title, 'PubMed [ ] title not cleaned'
        assert by_title['Pranayama and lung function in diabetics']['authors'] == 'Das, R; Müller, K', by_title['Pranayama and lung function in diabetics']['authors']
        assert by_title['Wearable sensors for glucose monitoring using machine learning']['doc_type'] == 'conference'
        assert [r for r in recs if r['db'] == 'pubmed'][0]['doc_type'] == 'journal'

        run('dedupe')
        dl = json.load(open(proj / '02_records' / 'dedupe_log.json', encoding='utf-8'))
        assert dl['unique'] == 8 and dl['duplicates_removed'] == 6, dl
        assert dl['pairs_for_manual_review'] >= 1, dl
        uniq = list(csv.DictReader(open(proj / '02_records' / 'records_unique.csv', encoding='utf-8-sig')))
        a_rec = [u for u in uniq if u['title'].startswith('Yoga for glyc')][0]
        assert a_rec['n_found'] == '4' and set(a_rec['sources'].split('+')) == {'PubMed', 'Scopus', 'Web of Science'}, a_rec
        assert a_rec['doi'] == '10.1000/a1'

        kw = {'fields': ['title', 'abstract', 'keywords'],
              'require_groups': {'population': ['diabet*'], 'intervention': ['yoga', 'pranayam*', 'breathing', 'meditation']},
              'exclude_terms': [], 'year_from': 2015}
        (proj / 'keywords.json').write_text(json.dumps(kw), encoding='utf-8')
        run('screen', '--apply')
        rows = sheet(proj)
        flags = {r['title'][:12]: r['kw_flag'] for r in rows}
        assert flags['Wearable sen'] == 'fail' and flags['Deep learnin'] == 'fail' and flags['Yoga for gly'] == 'pass', flags
        assert sum(1 for r in rows if r['reason'].startswith('automation')) == 2

        for r in rows:
            t = r['title']
            if r['ta_decision']:
                continue
            if t.startswith('Meditation') and r['doi'] == '10.1101/g7pp':
                r['ta_decision'], r['reason'] = 'exclude', 'preprint of an included paper'
            elif t.startswith('Meditation'):
                r['ta_decision'] = 'maybe'
            else:
                r['ta_decision'] = 'include'
        save_sheet(proj, rows)
        run('number')
        rows = sheet(proj)
        pids = {r['title'][:8]: r['pid'] for r in rows if r['pid']}
        assert len(pids) == 5 and all(v.startswith('P') for v in pids.values()), pids
        first = dict(pids)
        run('screen')  # re-run must keep decisions and pids
        assert {r['title'][:8]: r['pid'] for r in sheet(proj) if r['pid']} == first

        run('access')
        acc = {r['title'][:8]: (r['access'], r['oa_url']) for r in sheet(proj) if r['pid']}
        assert acc['Yoga for'] == ('open', 'http://open.example/a1.pdf'), acc
        assert acc['Pranayam'] == ('open', 'http://open.example/h8'), acc
        assert acc['Lifestyl'][0] == 'subscription' and acc['Breathin'][0] == 'unknown', acc
        run('batches', '--size', '2')
        assert (proj / '04_access' / 'open_access_001.html').exists() and (proj / '04_access' / 'subscription_002.html').exists()
        page = (proj / '04_access' / 'subscription_001.html').read_text(encoding='utf-8')
        assert 'https://proxy.example/login?url=https://doi.org/10.1000/b2' in page, 'proxy prefix missing'
        run('tabs', 'open', '1', '--delay', '0.05')
        run('tabs', 'sub', '1', '--delay', '0.05')
        urls = opened.read_text(encoding='utf-8').split()
        assert len(urls) == 4 and 'http://open.example/a1.pdf' in urls, urls

        inbox = proj / '05_pdfs' / 'inbox'
        pid_of = {r['title'][:8]: r['pid'] for r in sheet(proj) if r['pid']}
        make_pdf(inbox / 'download (1).pdf', 'Yoga for glycaemic control in type 2 diabetes: a randomised trial',
                 ['Rao K, Devi S', 'doi: 10.1000/a1'] + ['Participants practised yoga three times per week for twelve weeks.'] * 20)
        make_pdf(inbox / 'second_copy.pdf', 'Yoga for glycaemic control in type 2 diabetes: a randomised trial',
                 ['doi:10.1000/A1'] + ['Same paper downloaded from another site.'] * 5)
        make_pdf(inbox / 'elsevier_xyz.pdf', 'Lifestyle interventions in diabetes: a review',
                 ['Kumar P'] + ['Lifestyle programmes combine diet, walking and yoga.'] * 20 + [''] + ['References'] + ['1. Someone. Another paper. 2010.'] * 5)
        make_pdf(inbox / f"{pid_of['Pranayam']}.pdf", 'Pranayama and lung function in diabetics', ['Das R'] + ['Breathing practice raised FEV1.'] * 15)
        make_pdf(inbox / 'random.pdf', 'An unrelated paper about bridges', ['Concrete and steel.'] * 5)
        run('pdfmatch')
        rows = sheet(proj)
        have = {r['title'][:8]: r['pdf_file'] for r in rows if r['pdf_file']}
        assert len(have) == 3, have
        assert have['Yoga for'].startswith('journal/') and pid_of['Yoga for'] in have['Yoga for'], have
        assert (proj / '05_pdfs' / 'unmatched' / 'random.pdf').exists()
        assert list((proj / '05_pdfs' / 'duplicates').glob('*.pdf')), 'duplicate PDF not set aside'
        missing = list(csv.DictReader(open(proj / '05_pdfs' / 'missing_pdfs.csv', encoding='utf-8-sig')))
        assert len(missing) == 2, missing  # breathing study + meditation

        for r in rows:
            if r['pid']:
                t = r['title']
                r['ft_decision'] = ('include' if t.startswith(('Yoga for', 'Lifestyle', 'Pranayama')) else
                                    'exclude' if t.startswith('Breathing') else 'not_retrieved')
                if r['ft_decision'] == 'exclude':
                    r['reason'] = 'pilot, n<20'
                if t.startswith('Pranayama'):
                    r['role'] = 'supplementary'
        save_sheet(proj, rows)
        run('prisma')
        pr = json.load(open(proj / 'prisma.json', encoding='utf-8'))
        want = {'identified': {'PubMed': 2, 'Scopus': 6, 'Web of Science': 4, 'IEEE Xplore': 2}, 'duplicates': 6,
                'automation_excluded': 2, 'screened': 6, 'excluded_ta': 1, 'sought': 5, 'not_retrieved': 1, 'assessed': 4,
                'excluded_ft': {'pilot, n<20': 1}, 'included': 3}
        assert pr == want, pr

        run('pack', '--words', '120')
        names = sorted(p.name for p in (proj / '06_pack').glob('*.docx'))
        assert any(n.startswith('main_part') for n in names) and 'supplementary_part01.docx' in names, names
        import docx
        txt = '\n'.join(par.text for n in names for par in docx.Document(str(proj / '06_pack' / n)).paragraphs)
        assert f"[{pid_of['Yoga for']}] Yoga for glycaemic control" in txt and 'Participants practised yoga' in txt
        assert '1. Someone. Another paper' not in txt, 'reference list should have been stripped'
        idx = list(csv.DictReader(open(proj / '06_pack' / 'pack_index.csv', encoding='utf-8-sig')))
        assert len(idx) == 3

        # cite: tags split over runs, a list, a range, an unknown tag, author-year leftovers
        pa, pb, ph = pid_of['Yoga for'], pid_of['Lifestyl'], pid_of['Pranayam']
        dr = docx.Document()
        dr.add_heading('Results', 1)
        p1 = dr.add_paragraph('Yoga lowered HbA1c ')
        p1.add_run('[' + pa[:3]).bold = True
        p1.add_run(pa[3:] + '] while diet did too ')
        p1.add_run(f'[{pb}, {pa}].')
        dr.add_paragraph(f'Pranayama helped [{ph}]. Range [{pa}–{ph}]. Odd claim [P099]. Another (Smith et al., 2020).')
        draft = d / 'draft.docx'
        dr.save(str(draft))
        r = run('cite', str(draft), '--out-dir', str(d / 'out'), ok=False)
        assert r.returncode == 1 and 'P099' in r.stdout, 'unknown tag must fail the check'
        nd = docx.Document(str(d / 'out' / 'draft_numbered.docx'))
        body = '\n'.join(par.text for par in nd.paragraphs)
        assert 'Yoga lowered HbA1c [1] while diet did too [1, 2].' in body, body
        assert 'Pranayama helped [3].' in body and 'Range [1\u20135].' in body, body
        assert '?P099' in body
        assert (d / 'out' / 'references.ris').read_text(encoding='utf-8').count('TY  -') == 5
        assert 'Kumar P. Lifestyle interventions' in body or 'Kumar P. Lifestyle' in body
        assert 'Smith et al., 2020' in (d / 'out' / 'cite_report.txt').read_text(encoding='utf-8')

        # a Word file that has no "Heading 1" style (Word keeps only the styles a document uses) must still work
        d2 = docx.Document()
        d2.add_paragraph(f'Plain text [{pa}].')
        d2.styles.element.remove(d2.styles['Heading 1'].element)
        draft2 = d / 'draft_nostyle.docx'
        d2.save(str(draft2))
        r2 = run('cite', str(draft2), '--out-dir', str(d / 'out2'))
        assert 'References' in '\n'.join(par.text for par in docx.Document(str(d / 'out2' / 'draft_nostyle_numbered.docx')).paragraphs)

        # comments: python-docx 1.2 can write Word comments
        cd = docx.Document()
        cd.add_heading('3 Results', 1)
        par = cd.add_paragraph()
        r1 = par.add_run('Yoga is the best exercise for everyone.')
        r2 = par.add_run(' Another sentence stays.')
        cd.add_comment(runs=[r1], text='Too strong - cite evidence or soften.', author='Me', initials='M')
        par2 = cd.add_paragraph()
        r3 = par2.add_run('This claim is unclear.')
        r3.font.highlight_color = 7
        r4 = par2.add_run(' Plain.')
        cdoc = d / 'draft_v1.docx'
        cd.save(str(cdoc))
        run('comments', str(cdoc), '--round', '1', '--out', str(d / 'rev1.md'))
        md = (d / 'rev1.md').read_text(encoding='utf-8')
        assert 'Too strong - cite evidence or soften.' in md and '"Yoga is the best exercise for everyone."' in md, md
        assert 'This claim is unclear.' in md and 'Section: 3 Results' in md, md

        out = run('status').stdout
        assert 'Numbered : 5' in out, out
    # batch page without a proxy: library portal + publisher buttons + direct publisher links
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import slr
    pg = slr.batch_page('sub', 1, 1, [('P001', 'T', 'A B', '2024', 'u1', '10.1145/1'), ('P002', 'U', 'C', '2023', 'u2', '10.1109/2')], False,
                        {'home': 'https://portal.example/home', 'search': 'https://portal.example/s?q={q}'})
    assert 'portal.example/home' in pg and 'IEEE' in pg and 'Mark done' in pg and 'Copy name' in pg
    assert slr.batch_url({'oa_url': '', 'landing_url': 'https://doi.org/10.1002/x', 'title': 't', 'doi': '10.1002/x'}, 'sub', '').startswith('https://onlinelibrary.wiley.com/')
    # a screening sheet saved by Excel as plain CSV (Windows-1252) must still be readable
    import slr as _s
    _f = Path(tempfile.mkdtemp()) / 'cp1252_test.csv'
    _f.write_bytes('pid,title\nP001,Caf\xe9 \xa9 test\n'.encode('cp1252'))
    assert _s.read_csv(_f)[0]['title'] == 'Caf\u00e9 \u00a9 test'
    # control characters from real PDFs must not break the Word files
    import docx as _docx
    _x = _s.xml_clean('a\x00b\x08c\x0cd\ud800e\ufffef ok \u00e9')
    assert _x == 'abcdef ok \u00e9', repr(_x)
    _d = _docx.Document(); _d.add_paragraph(_x)
    print('ALL SLR TESTS PASSED')


if __name__ == '__main__':
    main()
