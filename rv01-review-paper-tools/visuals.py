#!/usr/bin/env python3
# visuals.py - make the slide images for a video: tables, timelines, the PRISMA diagram, placeholder clips (Pillow only).
# Languages: en (English) and te (Telugu, the default for older episodes). The language is chosen by
#   1) the --lang en|te option, else 2) {"lang": "en"} in the episode folder's episode.json, else 3) te.
#
# Usage:
#   python visuals.py episode episodes/rv01_en    # builds everything in data/ into img/
#   python visuals.py table  data.csv out.png --title "Title" --note "Source: ..." --lang en
#   python visuals.py timeline milestones.csv img/tl     # one image per "slide" column value: tl_01.png, tl_02.png ...
#   python visuals.py prisma prisma.json img/prisma.png --lang en
#
# CSV rules: the first row is the header. Lines starting with '#' are comments; '# title: ...' and '# note: ...' set the
# slide title and the footnote. A cell that starts with [g] is green, [r] red, [y] amber.
import csv
import json
import pathlib
import re
import subprocess
import sys
import unicodedata
from PIL import Image, ImageDraw, ImageFont, features

W, H = 1920, 1080
BG, FG, MUTED = (18, 24, 38), (245, 245, 245), (165, 175, 195)
ACCENT, TEAL, PANEL, PANEL2 = (255, 193, 7), (80, 200, 180), (30, 40, 62), (38, 50, 76)
GREEN, RED, AMBER = (110, 220, 140), (245, 120, 120), (255, 200, 90)
HERE = pathlib.Path(__file__).resolve().parent
FONTS = {  # language -> (Bold, Regular). English uses Inter (SIL OFL licence, see assets/FONTS-LICENSE.txt).
    'te': (str(HERE / 'assets/NotoSansTelugu-Bold.ttf'), str(HERE / 'assets/NotoSansTelugu-Regular.ttf')),
    'en': (str(HERE / 'assets/Inter-Bold.otf'), str(HERE / 'assets/Inter-Regular.otf')),
}
FONT_B, FONT_R = FONTS['te']
LANG = 'te'
TAGS = {'[g]': GREEN, '[r]': RED, '[y]': AMBER}
HAS_RAQM = features.check('raqm')

# భాష వారీగా చిత్రాల్లో వచ్చే పదాలు
STR = {
    'te': {
        'source': 'మూలం: ',
        'prisma_title': 'PRISMA 2020 ఫ్లో డయాగ్రమ్', 'prisma_example': ' — ఉదాహరణ సంఖ్యలు',
        'ph_ident': 'గుర్తింపు', 'ph_screen': 'స్క్రీనింగ్', 'ph_incl': 'చేర్పు',
        'ident': 'డేటాబేస్‌ల నుంచి వచ్చిన రికార్డులు (n = %s)',
        'removed': 'స్క్రీనింగ్‌కు ముందు తీసేసినవి:', 'dups': 'డూప్లికేట్లు (n = %s)',
        'auto': 'కీవర్డ్ ఆటోమేషన్ తీసేసినవి (n = %s)',
        'screened': 'స్క్రీనింగ్ చేసిన రికార్డులు', 'ex_ta': 'శీర్షిక/సారాంశం చూసి తీసేసినవి',
        'sought': 'పూర్తి పేపర్ కోసం వెతికినవి', 'notret': 'దొరకని పేపర్లు',
        'assessed': 'అర్హత పరిశీలించిన పేపర్లు', 'ex_ft': 'పూర్తి పేపర్ చదివి తీసేసినవి (n = %s)',
        'other_reasons': 'ఇతర కారణాలు: %s', 'included': 'రివ్యూలో చేర్చిన అధ్యయనాలు',
        'foot': 'సంఖ్యలు మీ స్వంత ప్రాజెక్ట్ నుంచి (slr.py prisma) తీసుకోండి.',
        'ph_title': 'ఇక్కడ మీ స్క్రీన్ రికార్డింగ్ వస్తుంది',
        'made': 'తయారైనవి:', 'missing': 'ఇంకా లేని చిత్రాలు:', 'placeholder_note': 'ప్లేస్‌హోల్డర్ — మీ రికార్డింగ్‌తో మార్చండి',
        'font': 'ఫాంట్',
    },
    'en': {
        'source': 'Source: ',
        'prisma_title': 'PRISMA 2020 flow diagram', 'prisma_example': ' — example numbers',
        'ph_ident': 'Identification', 'ph_screen': 'Screening', 'ph_incl': 'Included',
        'ident': 'Records identified from databases (n = %s)',
        'removed': 'Records removed before screening:', 'dups': 'Duplicates (n = %s)',
        'auto': 'Excluded by keyword automation (n = %s)',
        'screened': 'Records screened', 'ex_ta': 'Excluded after title/abstract screening',
        'sought': 'Reports sought for retrieval', 'notret': 'Reports not retrieved',
        'assessed': 'Reports assessed for eligibility', 'ex_ft': 'Excluded after full-text review (n = %s)',
        'other_reasons': 'Other reasons: %s', 'included': 'Studies included in the review',
        'foot': 'Take the real numbers from your own project (slr.py prisma).',
        'ph_title': 'Your screen recording goes here',
        'made': 'Created:', 'missing': 'Images still missing:', 'placeholder_note': 'placeholder: replace with your recording',
        'font': 'font',
    },
}
S = STR['te']


def set_lang(code):
    """Select the language: fonts and the words inside the images change."""
    global LANG, FONT_B, FONT_R, S
    if code not in FONTS:
        raise SystemExit(f'Unknown language "{code}": use te or en.')
    LANG, (FONT_B, FONT_R), S = code, FONTS[code], STR[code]
    for f in (FONT_B, FONT_R):
        if not pathlib.Path(f).exists():
            raise SystemExit(f'Font file not found: {f}\nPut the font files in the assets/ folder (see the setup document).')
    if code == 'te' and not HAS_RAQM:
        print('Warning: this Pillow has no raqm; Telugu conjunct letters may render incorrectly.', file=sys.stderr)


def lang_of(ep_dir):
    p = pathlib.Path(ep_dir) / 'episode.json'
    if p.exists():
        try:
            return json.loads(p.read_text(encoding='utf-8')).get('lang', 'te')
        except ValueError:
            raise SystemExit(f'{p} is not valid JSON.')
    return 'te'


def font(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM if HAS_RAQM else ImageFont.Layout.BASIC)


def split_word(draw, word, f, max_w):
    """Split a very long word into pieces without breaking a conjunct letter (Telugu)."""
    parts, cur = [], ''
    for i, ch in enumerate(word):
        trial = cur + ch
        if draw.textlength(trial, font=f) > max_w and cur:
            nxt_combining = unicodedata.category(ch).startswith('M')
            if nxt_combining or cur.endswith('్'):
                cur = trial
                continue
            parts.append(cur)
            cur = ch
        else:
            cur = trial
    if cur:
        parts.append(cur)
    return parts


def wrap(draw, text, f, max_w):
    lines = []
    for para in str(text).split('\\n'):
        cur = ''
        for word in para.split():
            trial = (cur + ' ' + word).strip()
            if draw.textlength(trial, font=f) <= max_w:
                cur = trial
                continue
            if cur:
                lines.append(cur)
            if draw.textlength(word, font=f) > max_w:
                chunks = split_word(draw, word, f, max_w)
                lines += chunks[:-1]
                cur = chunks[-1]
            else:
                cur = word
        lines.append(cur)
    return lines or ['']


def read_csv_rows(path):
    meta, lines = {}, []
    for line in pathlib.Path(path).read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('#'):
            m = re.match(r'#\s*(title|note)\s*:\s*(.*)', line)
            if m:
                meta[m.group(1)] = m.group(2).strip()
            continue
        if line.strip():
            lines.append(line)
    return list(csv.reader(lines)), meta


def tag_color(text, default=FG):
    for t, c in TAGS.items():
        if text.startswith(t):
            return text[len(t):].strip(), c
    return text, default


# ---------- table ----------
def make_table(rows, out, title='', note=''):
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    x0, x1 = 90, W - 90
    y0 = 90
    if title:
        tf = font(FONT_B, 62)
        for ln in wrap(d, title, tf, W - 180)[:2]:
            d.text((x0, y0), ln, font=tf, fill=ACCENT)
            y0 += 84
        y0 += 20
    y_bottom = H - (130 if note else 70)
    ncol = len(rows[0])
    for i, r in enumerate(rows[1:], 2):
        if len(r) > ncol:
            raise SystemExit(f'CSV row {i}: the header has {ncol} columns but this row has {len(r)}. Put any cell that contains a comma in "double quotes": {r[0]}')
    rows = [r + [''] * (ncol - len(r)) for r in rows]
    weights = []
    for c in range(ncol):
        longest = max(len(tag_color(r[c])[0]) for r in rows)
        weights.append(min(max(longest, 10), 46))
    total_w = x1 - x0
    pad = 22
    chosen = None
    for size in range(46, 23, -2):
        fb, fr = font(FONT_B, size), font(FONT_R, size)
        # minimum column width = longest word in it + padding (so words never break in the middle)
        minw = []
        for c in range(ncol):
            words = [w for r_i, r in enumerate(rows) for w in tag_color(r[c])[0].split()]
            f_c = fb if c == 0 else fr
            minw.append(max([d.textlength(w, font=(fb if r_i == 0 else f_c)) for r_i, r in enumerate(rows)
                             for w in tag_color(r[c])[0].split()] + [0]) + 2 * pad + 6)
        if sum(minw) > total_w:
            continue
        extra = total_w - sum(minw)
        widths = [m + extra * w / sum(weights) for m, w in zip(minw, weights)]
        heights = []
        for ri, r in enumerate(rows):
            lines_n = 0
            for ci, cell in enumerate(r):
                f = fb if (ri == 0 or ci == 0) else fr
                lines_n = max(lines_n, len(wrap(d, tag_color(cell)[0], f, widths[ci] - 2 * pad)))
            heights.append(int(lines_n * size * 1.45 + 2 * 14))
        if y0 + sum(heights) <= y_bottom:
            chosen = (size, fb, fr, heights)
            break
    if chosen is None:
        raise SystemExit('The table does not fit on one slide: use fewer rows or split it into two tables.')
    size, fb, fr, heights = chosen
    y = y0
    for ri, r in enumerate(rows):
        h = heights[ri]
        bg = ACCENT if ri == 0 else (PANEL if ri % 2 else PANEL2)
        d.rectangle([x0, y, x1, y + h], fill=bg)
        x = x0
        for ci, cell in enumerate(r):
            text, color = tag_color(cell, (20, 24, 36) if ri == 0 else (TEAL if ci == 0 else FG))
            f = fb if (ri == 0 or ci == 0) else fr
            ty = y + 14
            for ln in wrap(d, text, f, widths[ci] - 2 * pad):
                d.text((x + pad, ty), ln, font=f, fill=color)
                ty += int(size * 1.45)
            x += widths[ci]
        y += h
    if note:
        nf = font(FONT_R, 28)
        ny = H - 100
        for ln in wrap(d, note, nf, W - 180)[:2]:
            d.text((x0, ny), ln, font=nf, fill=MUTED)
            ny += 40
    img.save(out)
    return size


# ---------- timeline ----------
def make_timeline_slide(items, out, title=''):
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    if title:
        d.text((90, 70), title, font=font(FONT_B, 58), fill=ACCENT)
    n = len(items)
    cy = H // 2 + 70
    d.line([(70, cy), (W - 70, cy)], fill=MUTED, width=6)
    step = (W - 240) / n
    fd, ft, fx, fs = font(FONT_B, 72), font(FONT_B, 54), font(FONT_R, 42), font(FONT_R, 30)
    box_w = min(int(step * 1.85), 760)
    for i, it in enumerate(items):
        cx = int(120 + step * (i + 0.5))
        up = (i % 2 == 0)
        d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=ACCENT)
        lines = [(it['date'], fd, ACCENT)]
        lines += [(ln, ft, FG) for ln in wrap(d, it['title'], ft, box_w)]
        lines += [(ln, fx, (210, 215, 225)) for ln in wrap(d, it['detail'], fx, box_w)]
        if it.get('source'):
            lines += [(S['source'] + it['source'], fs, MUTED)]
        total = sum(int(f.size * 1.35) for _, f, _ in lines)
        if up:
            top = cy - 60 - total
            d.line([(cx, cy - 16), (cx, cy - 50)], fill=ACCENT, width=4)
        else:
            top = cy + 60
            d.line([(cx, cy + 16), (cx, cy + 50)], fill=ACCENT, width=4)
        left = min(max(cx - box_w // 2, 60), W - 60 - box_w)
        y = top
        for text, f, color in lines:
            d.text((left, y), text, font=f, fill=color)
            y += int(f.size * 1.35)
    img.save(out)


def make_timelines(csv_path, prefix):
    rows, meta = read_csv_rows(csv_path)
    head = [h.strip() for h in rows[0]]
    for i, r in enumerate(rows[1:], 2):
        if len(r) != len(head):
            raise SystemExit(f'milestones row {i}: expected {len(head)} columns, found {len(r)}. Put any cell that contains a comma in "double quotes": {r[0] if r else ""}')
    recs = [dict(zip(head, r + [''] * (len(head) - len(r)))) for r in rows[1:]]
    slides = {}
    for r in recs:
        slides.setdefault(int(r['slide']), []).append(r)
    outs = []
    for k in sorted(slides):
        out = f'{prefix}_{k:02}.png'
        make_timeline_slide(slides[k], out, meta.get('title', ''))
        outs.append(out)
    return outs


# ---------- PRISMA ----------
def n(v):
    return f'{int(v):,}'


def box(d, xy, lines, size=31, bold=False, fill=PANEL, outline=TEAL, color=FG):
    """Lines inside a box: wrapped to the width; the font shrinks until the text fits."""
    x, y, w, h = xy
    d.rectangle([x, y, x + w, y + h], fill=fill, outline=outline, width=3)
    path = FONT_B if bold else FONT_R
    for sz in range(size, 17, -1):
        f = font(path, sz)
        wrapped = []
        for ln in lines:
            wrapped += wrap(d, ln, f, w - 36)
        total = len(wrapped) * int(sz * 1.35)
        if total <= h - 14:
            break
    ty = y + (h - total) // 2
    for ln in wrapped:
        tw = d.textlength(ln, font=f)
        d.text((x + (w - tw) / 2, ty), ln, font=f, fill=color)
        ty += int(sz * 1.35)


def phase_label(d, text, y0, y1):
    d.rectangle([50, y0, 240, y1], fill=TEAL)
    for sz in range(34, 15, -1):
        f = font(FONT_B, sz)
        if d.textlength(text, font=f) <= 170:
            break
    tw = d.textlength(text, font=f)
    d.text((50 + (190 - tw) / 2, (y0 + y1) / 2 - sz * 0.7), text, font=f, fill=(15, 20, 30))


def make_prisma(data, out):
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    mx, mw, sx, sw, bh = 300, 760, 1200, 650, 108
    ys = [150, 305, 460, 615, 800]
    d.text((90, 50), S['prisma_title'] + (S['prisma_example'] if data.get('example') else ''),
           font=font(FONT_B, 54), fill=ACCENT)
    phase_label(d, S['ph_ident'], ys[0] - 20, ys[0] + bh + 20)
    phase_label(d, S['ph_screen'], ys[1], ys[3] + bh + 80)
    phase_label(d, S['ph_incl'], ys[4], ys[4] + bh)
    ident = data.get('identified', {})
    items = [f'{k}: {n(v)}' for k, v in ident.items()]
    id_lines = [S['ident'] % n(sum(ident.values()))]
    id_lines += ['  |  '.join(items[i:i + 2]) for i in range(0, len(items), 2)]
    box(d, (mx, ys[0] - 20, mw, bh + 40), id_lines, size=30)
    rem = [S['removed'], S['dups'] % n(data.get('duplicates', 0))]
    if 'automation_excluded' in data:
        rem.append(S['auto'] % n(data['automation_excluded']))
    box(d, (sx, ys[0] - 20, sw, bh + 40), rem, size=30, outline=MUTED)
    box(d, (mx, ys[1], mw, bh), [S['screened'], '(n = %s)' % n(data.get('screened', 0))])
    box(d, (sx, ys[1], sw, bh), [S['ex_ta'], '(n = %s)' % n(data.get('excluded_ta', 0))], outline=MUTED)
    box(d, (mx, ys[2], mw, bh), [S['sought'], '(n = %s)' % n(data.get('sought', 0))])
    box(d, (sx, ys[2], sw, bh), [S['notret'], '(n = %s)' % n(data.get('not_retrieved', 0))], outline=MUTED)
    box(d, (mx, ys[3], mw, bh), [S['assessed'], '(n = %s)' % n(data.get('assessed', 0))])
    ex = data.get('excluded_ft', {})
    pairs = sorted(ex.items(), key=lambda kv: -kv[1])
    shown = pairs if len(pairs) <= 3 else pairs[:2]
    ex_lines = [S['ex_ft'] % n(sum(ex.values()))] + [f'{k}: {n(v)}' for k, v in shown]
    if len(pairs) > 3:
        ex_lines.append(S['other_reasons'] % n(sum(v for _, v in pairs[2:])))
    box(d, (sx, ys[3] - 10, sw, bh + 90), ex_lines, size=28, outline=MUTED)
    box(d, (mx, ys[4], mw, bh), [S['included'], '(n = %s)' % n(data.get('included', 0))], bold=True, outline=ACCENT, fill=PANEL2)
    for i in range(4):
        x = mx + mw // 2
        ya, yb = ys[i] + bh + (20 if i == 0 else 0), ys[i + 1] - 6
        d.line([(x, ya), (x, yb)], fill=FG, width=4)
        d.polygon([(x - 12, yb - 14), (x + 12, yb - 14), (x, yb + 4)], fill=FG)
    for i in range(4):
        y = ys[i] + bh // 2
        d.line([(mx + mw, y), (sx, y)], fill=MUTED, width=3)
    d.text((90, H - 70), S['foot'], font=font(FONT_R, 28), fill=MUTED)
    img.save(out)


# ---------- placeholder clips ----------
def make_placeholder(name, path):
    png = pathlib.Path(str(path) + '.png')
    img = Image.new('RGB', (W, H), (60, 36, 36))
    d = ImageDraw.Draw(img)
    f1, f2 = font(FONT_B, 64), font(FONT_R, 44)
    t1 = S['ph_title']
    d.text(((W - d.textlength(t1, font=f1)) / 2, 400), t1, font=f1, fill=ACCENT)
    d.text(((W - d.textlength(name, font=f2)) / 2, 520), name, font=f2, fill=FG)
    img.save(png)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-loop', '1', '-t', '4', '-i', str(png), '-vf', 'format=yuv420p',
                    '-r', '30', '-c:v', 'libx264', '-preset', 'veryfast', str(path)], check=True)
    png.unlink()


# ---------- whole episode ----------
def script_names(script, kind):
    names = []
    if script.exists():
        for line in script.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line.startswith(kind + ':'):
                name = line.split('||')[0].split(':', 1)[1].strip()
                if kind == 'clip':      # clip: a.mp4+b.mp4 | caption
                    names += [x.strip() for x in name.partition(' | ')[0].split('+') if x.strip()]
                else:
                    names.append(name)
    return names


def build_episode(ep_dir, lang=None):
    ep = pathlib.Path(ep_dir)
    set_lang(lang or lang_of(ep))
    img_dir, data_dir = ep / 'img', ep / 'data'
    img_dir.mkdir(exist_ok=True)
    made = []
    for p in sorted(data_dir.glob('*.csv')):
        if p.stem == 'milestones':
            made += make_timelines(p, str(img_dir / 'tl'))
            continue
        rows, meta = read_csv_rows(p)
        size = make_table(rows, img_dir / (p.stem + '.png'), meta.get('title', ''), meta.get('note', ''))
        made.append(f"{p.stem}.png ({S['font']} {size})")
    pr = data_dir / 'prisma.json'
    if pr.exists():
        make_prisma(json.loads(pr.read_text(encoding='utf-8')), img_dir / 'prisma.png')
        made.append('prisma.png')
    script = ep / 'script.txt'
    for name in script_names(script, 'clip'):
        if not (img_dir / name).exists():
            make_placeholder(name, img_dir / name)
            made.append(f"{name} ({S['placeholder_note']})")
    missing = [name for name in script_names(script, 'img') if not (img_dir / name).exists()]
    print(S['made'] + '\n  ' + '\n  '.join(made))
    if missing:
        print(S['missing'], ', '.join(sorted(set(missing))))


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__ if __doc__ else 'usage: see the comments at the top of this file')
    cmd = a[0]

    def opt(name):
        return a[a.index(name) + 1] if name in a else ''
    lang = opt('--lang')
    if cmd == 'episode':
        build_episode(a[1], lang or None)
        return
    set_lang(lang or 'te')
    if cmd == 'table':
        rows, meta = read_csv_rows(a[1])
        make_table(rows, a[2], opt('--title') or meta.get('title', ''), opt('--note') or meta.get('note', ''))
    elif cmd == 'timeline':
        print(make_timelines(a[1], a[2]))
    elif cmd == 'prisma':
        make_prisma(json.loads(pathlib.Path(a[1]).read_text(encoding='utf-8')), a[2])
    else:
        raise SystemExit('Unknown command: ' + cmd)


if __name__ == '__main__':
    main()
