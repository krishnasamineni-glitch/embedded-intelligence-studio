# selftest.py - tests litsearch.py with a fake (mock) server, without internet.
# Usage: python selftest.py     (no API key needed)
import json, os, subprocess, sys, tempfile, threading, pathlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote

HERE = pathlib.Path(__file__).resolve().parent

OA_W1 = {'id': 'https://openalex.org/W1', 'doi': 'https://doi.org/10.1000/xyz', 'title': 'Yoga for glycaemic control: a randomised trial',
         'publication_year': 2019, 'cited_by_count': 12, 'type': 'article', 'ids': {'pmid': 'https://pubmed.ncbi.nlm.nih.gov/111'},
         'primary_location': {'source': {'display_name': 'Journal of Examples'}},
         'authorships': [{'author': {'display_name': 'Rao K'}}, {'author': {'display_name': 'Devi S'}}],
         'abstract_inverted_index': {'Yoga': [0], 'lowered': [1], 'HbA1c': [2], 'modestly.': [3]}}
OA_W2 = {'id': 'https://openalex.org/W2', 'doi': 'https://doi.org/10.1000/abc', 'title': 'Lifestyle interventions in diabetes: a review',
         'publication_year': 2021, 'cited_by_count': 40, 'type': 'review', 'ids': {},
         'primary_location': {'source': {'display_name': 'Review Journal'}},
         'authorships': [{'author': {'display_name': 'Kumar P'}}], 'abstract_inverted_index': None}
OA_W3 = {'id': 'https://openalex.org/W3', 'doi': None, 'title': 'An older cited paper', 'publication_year': 2010,
         'cited_by_count': 5, 'type': 'article', 'ids': {}, 'primary_location': None, 'authorships': [], 'abstract_inverted_index': {'Old.': [0]}}

PM_XML = '''<?xml version="1.0"?><PubmedArticleSet>
<PubmedArticle><MedlineCitation><PMID>111</PMID><Article><Journal><JournalIssue><PubDate><Year>2019</Year></PubDate></JournalIssue><Title>Journal of Examples</Title></Journal>
<ArticleTitle>Yoga for glycaemic control: a randomised trial</ArticleTitle><Abstract><AbstractText Label="BACKGROUND">Yoga may help.</AbstractText><AbstractText Label="RESULTS">HbA1c fell.</AbstractText></Abstract>
<AuthorList><Author><LastName>Rao</LastName><ForeName>K</ForeName></Author></AuthorList><ELocationID EIdType="doi">10.1000/XYZ</ELocationID>
<PublicationTypeList><PublicationType>Journal Article</PublicationType></PublicationTypeList></Article></MedlineCitation></PubmedArticle>
<PubmedArticle><MedlineCitation><PMID>222</PMID><Article><Journal><JournalIssue><PubDate><MedlineDate>2020 Jan-Feb</MedlineDate></PubDate></JournalIssue><Title>Other Journal</Title></Journal>
<ArticleTitle>Breathing exercises and <i>type 2</i> diabetes</ArticleTitle><Abstract><AbstractText>Small pilot study.</AbstractText></Abstract>
<AuthorList><Author><LastName>Lee</LastName><Initials>J</Initials></Author></AuthorList></Article></MedlineCitation>
<PubmedData><ArticleIdList><ArticleId IdType="doi">10.2000/pilot</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>'''


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, body, ctype='application/json', code=200):
        b = body.encode('utf-8') if isinstance(body, str) else json.dumps(body).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        p = unquote(u.path)
        if p == '/oa/works':
            flt = q.get('filter', '')
            if flt.startswith('openalex:'):
                return self.send({'meta': {'count': 1, 'next_cursor': None}, 'results': [OA_W3]})
            if flt.startswith('cites:'):
                return self.send({'meta': {'count': 1, 'next_cursor': None}, 'results': [OA_W2]})
            assert q.get('search'), 'search parameter missing'
            return self.send({'meta': {'count': 2, 'next_cursor': None}, 'results': [OA_W1, OA_W2]})
        if p == '/oa/works/W1':
            return self.send({'referenced_works': ['https://openalex.org/W3']})
        if p.startswith('/oa/works/https://doi.org/'):
            return self.send({'id': 'https://openalex.org/W1'})
        if p == '/eutils/esearch.fcgi':
            return self.send({'esearchresult': {'count': '2', 'idlist': ['111', '222']}})
        if p == '/eutils/efetch.fcgi':
            return self.send(PM_XML, 'text/xml')
        if p == '/cr/works/10.1000/xyz':
            return self.send({'message': {'title': ['Yoga for glycaemic control: a randomised trial']}})
        if p == '/cr/works/10.1000/abc':
            return self.send({'message': {'title': ['Totally different title about economics'],
                                          'updated-by': [{'type': 'retraction'}]}})
        if p.startswith('/cr/works/10.9999'):
            return self.send({'status': 'not found'}, code=404)
        if p == '/cr/works':
            return self.send({'message': {'items': [{'DOI': '10.1000/xyz', 'title': ['Yoga for glycaemic control: a randomised trial']}]}})
        self.send({'error': p}, code=404)


def run(args, env, cwd):
    r = subprocess.run([sys.executable, '-I', str(HERE / 'litsearch.py')] + args, env=env, cwd=cwd,
                       capture_output=True, text=True)
    print('$ litsearch', ' '.join(args))
    print(r.stdout + r.stderr)
    assert r.returncode == 0, f'failed: {args}'
    return r.stdout


def main():
    srv = HTTPServer(('127.0.0.1', 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{srv.server_port}'
    env = dict(os.environ, OPENALEX_BASE=base + '/oa', EUTILS_BASE=base + '/eutils', CROSSREF_BASE=base + '/cr',
               OPENALEX_API_KEY='test-key')
    import csv
    with tempfile.TemporaryDirectory() as d:
        run(['search', '--q', 'yoga AND diabetes', '--from', '2015', '--max', '50'], env, d)
        rows = list(csv.DictReader(open(pathlib.Path(d) / 'results.csv', encoding='utf-8-sig')))
        assert len(rows) == 3, rows            # W1 (merged with PubMed), W2, PMID222
        assert 'openalex+pubmed' in [r['source'] for r in rows], 'dedupe did not merge the records'
        assert rows[0]['abstract'].startswith('Yoga lowered HbA1c'), 'abstract was rebuilt incorrectly'
        assert json.load(open(pathlib.Path(d) / 'search_log.json'))['duplicates_removed'] == 1
        run(['chase', '--ids', '10.1000/xyz', '--dir', 'both'], env, d)
        rows = list(csv.DictReader(open(pathlib.Path(d) / 'results.csv', encoding='utf-8-sig')))
        assert len(rows) == 4 and any(r['title'] == 'An older cited paper' for r in rows), rows
        # screening decisions
        for r in rows:
            r['ta_decision'] = 'exclude' if r['id'] == 'PMID222' else 'include'
            r['ft_decision'] = {'W1': 'include', 'W2': 'exclude', 'W3': 'not_retrieved'}.get(r['id'], '')
            r['reason'] = 'wrong population' if r['id'] == 'W2' else ''
        with open(pathlib.Path(d) / 'results.csv', 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        run(['prisma', 'results.csv'], env, d)
        pr = json.load(open(pathlib.Path(d) / 'prisma.json', encoding='utf-8'))
        assert pr['screened'] == 4 and pr['excluded_ta'] == 1 and pr['sought'] == 3 and pr['not_retrieved'] == 1
        assert pr['assessed'] == 2 and pr['included'] == 1 and pr['excluded_ft'] == {'wrong population': 1}, pr
        run(['export', 'results.csv', '--format', 'ris', '--only', 'include'], env, d)
        run(['export', 'results.csv', '--format', 'bibtex', '--only', 'include', '--out', 'refs.bib'], env, d)
        assert 'TY  - JOUR' in open(pathlib.Path(d) / 'refs.ris', encoding='utf-8').read()
        (pathlib.Path(d) / 'refs.txt').write_text(
            'Rao K, Devi S. Yoga for glycaemic control: a randomised trial. J Examples 2019. doi:10.1000/xyz\n'
            'Made Up A. A paper that does not exist. 2022. https://doi.org/10.9999/fake\n'
            'Kumar P. Lifestyle interventions in diabetes. 2021. doi:10.1000/abc\n'
            'Rao K. Yoga for glycaemic control, randomised trial, 2019\n', encoding='utf-8')
        out = run(['verify', 'refs.txt'], env, d)
        assert '[matched]' in out and '[DOI not found]' in out and '[retracted]' in out and '[possible match (no DOI)]' in out, out
    print('ALL LITSEARCH TESTS PASSED')


if __name__ == '__main__':
    main()
