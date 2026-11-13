# anim_scenes.py - animated explainer scenes for rv01_en, timed to the narration (sentence start times in seconds).
# Run:  python motion_build.py episodes/rv01_en   (it imports this file, renders img/anim_NN.mp4 for each scene here)
import math
from motion import *

SCENES = {}


def scene_02(T):
    """The whole journey. T = sentence start times, T[-1] = end."""
    s = Scene(T[-1])
    s.add(0.0, title('The whole journey, in one picture'))
    steps = [('1  Plan', AMBER), ('2  Search', AMBER), ('3  Import + dedupe', GREEN), ('4  Screen', AMBER),
             ('5  PDFs', GREEN), ('6  Pack for the AI', GREEN), ('7  Cite check', GREEN), ('8  Revise', AMBER)]
    when = [T[1], T[2], T[2] + 3.4, T[3], T[3] + 2.6, T[4], T[5], T[5] + 2.8]
    pos = []
    for i in range(8):
        r, c = divmod(i, 4)
        pos.append((200 + c * 400, 360 + r * 260))
    for i, ((txt, col), t0) in enumerate(zip(steps, when)):
        x, y = pos[i]
        s.add(t0, panel((x, y - 70, x + 360, y + 70), fill=PANEL, outline=col, width=4))
        s.add(t0 + 0.15, label(txt, x + 180, y, 36, FG, True, 'mm'))
        if i < 7:
            nx, ny = pos[i + 1]
            if i == 3:
                s.add(t0 + 0.4, arrow((x + 180, y + 72), (pos[4][0] + 180, pos[4][1] - 72), MUTED, 5))
            else:
                s.add(t0 + 0.4, arrow((x + 362, y), (nx - 4, ny), MUTED, 5))
    # AI draft note during sentence 4
    s.add(T[4] + 3.2, label('AI writes the draft, citing papers only by number  [P012]', 200, 800, 32, BLUE))
    # legend (sentence 6)
    s.add(T[6], panel((1360, 860, 1840, 1010), fill=PANEL2))
    s.add(T[6] + 0.2, chip('green = the tool', 1390, 900, GREEN, (14, 20, 36), 28)[0])
    s.add(T[6] + 1.6, chip('amber = I decide', 1390, 965, AMBER, (14, 20, 36), 28)[0])
    s.add(T[7], stamp('DECISIONS STAY WITH ME', 700, 940, ACCENT, 40, -4))
    return s


def scene_03(T):
    s = Scene(T[-1])
    s.add(0.0, title('Step 1: the search'))
    s.add(T[1], magnifier(1700, 110, 44))
    # notepad
    s.add(T[2], panel((90, 190, 1120, 640), fill=(246, 247, 250), outline=(205, 210, 220)))
    s.add(T[2] + 0.3, label('Write the concepts on paper first', 130, 225, 30, (120, 128, 145), False))
    # concept A
    s.add(T[3] + 1.6, chip('stacked patch antenna', 130, 330, (255, 228, 120), (40, 48, 66), 32)[0])
    s.add(T[3] + 5.0, chip('isolation', 130, 500, (170, 230, 255), (40, 48, 66), 32)[0])
    s.add(T[3] + 7.6, chip('decoupling', 480, 500, (170, 230, 255), (40, 48, 66), 32)[0])
    # sentence 4: synonyms + OR / AND
    s.add(T[4] + 0.8, chip('multilayer antenna', 610, 330, (255, 228, 120), (40, 48, 66), 32)[0])
    s.add(T[4] + 1.6, label('OR', 560, 330, 30, (120, 128, 145), True, 'mm'))
    s.add(T[4] + 2.4, label('OR', 410, 500, 30, (120, 128, 145), True, 'mm'))
    s.add(T[4] + 4.0, chip('AND', 130, 415, (40, 48, 66), (255, 255, 255), 30)[0])
    s.add(T[4] + 4.0, highlight((110, 290, 1040, 370), (255, 193, 7), 16, 3, False))
    s.add(T[4] + 4.0, highlight((110, 460, 760, 540), (80, 170, 255), 16, 3, False))
    # sentence 5: AI suggests, you test
    s.add(T[5] + 0.3, sparkle(1270, 330, BLUE))
    s.add(T[5] + 0.6, chip('AI: "dual-layer patch" ?', 1310, 330, PANEL2, BLUE, 28, outline=BLUE)[0])
    s.add(T[5] + 2.6, chip('test it yourself', 1310, 410, PANEL2, AMBER, 28, outline=AMBER)[0])
    s.add(T[5] + 3.2, check(1680, 410, 22))
    # sentence 6/7: database syntax
    s.add(T[6], arrow((600, 650), (600, 720), ACCENT, 6))
    s.add(T[6] + 0.3, panel((90, 740, 1700, 840), fill=CODE_BG, outline=CODE_LINE))
    s.add(T[6] + 0.3, panel((90, 870, 1700, 970), fill=CODE_BG, outline=CODE_LINE))
    s.add(T[6] + 0.5, label('PubMed', 110, 790, 26, (120, 190, 255), True, 'lm'))
    s.add(T[6] + 0.5, label('Scopus', 110, 920, 26, (120, 190, 255), True, 'lm'))
    s.add(T[7], typewriter('("stacked patch"[tiab] OR "multilayer antenna"[tiab]) AND (isolation[tiab] OR decoupling[tiab])', 250, 776, 22, CODE_FG, 45))
    s.add(T[7] + 2.4, typewriter('TITLE-ABS-KEY("stacked patch" OR "multilayer antenna") AND TITLE-ABS-KEY(isolation OR decoupling)', 250, 906, 22, CODE_FG, 45))
    # sentence 8: other databases
    s.add(T[8] + 0.4, chip('IEEE Xplore', 90, 1020, PANEL2, MUTED, 28, outline=MUTED)[0])
    s.add(T[8] + 1.0, chip('Web of Science', 330, 1020, PANEL2, MUTED, 28, outline=MUTED)[0])
    s.add(T[8] + 1.6, chip('... same logic, same tool', 620, 1020, PANEL2, MUTED, 28, outline=MUTED)[0])
    return s


def progress_bar(box, t_start, seconds, label_text, result, color=BLUE):
    """A fake 'search running' bar: fills over `seconds`, then shows the result count."""
    def fn(d, img, p, t):
        x0, y0, x1, y1 = box
        d.rounded_rectangle([x0, y0, x1, y1], 14, fill=PANEL2)
        q = ease(min(1.0, t / seconds))
        d.rounded_rectangle([x0, y0, x0 + (x1 - x0) * q, y1], 14, fill=color)
        d.text((x0 + 20, (y0 + y1) / 2), label_text, font=font(28), fill=FG, anchor='lm')
        if q >= 1:
            d.text((x1 - 20, (y0 + y1) / 2), result, font=font(28), fill=(14, 20, 36), anchor='rm')
        else:
            d.text((x1 - 20, (y0 + y1) / 2), f'searching… {int(q * 100)}%', font=font(26, False), fill=FG, anchor='rm')
    return fn


def scene_04(T):
    s = Scene(T[-1])
    s.add(0.0, title('Export the results'))
    # sentence 0: search running
    s.add(0.0, panel((90, 190, 1000, 420), fill=PANEL))
    s.add(0.1, progress_bar((120, 230, 970, 300), 0, 1.6, 'PubMed', '412 results', BLUE))
    s.add(0.6, progress_bar((120, 330, 970, 400), 0, 1.9, 'Scopus', '688 results', TEAL))
    s.add(T[1], label('What next?', 1050, 300, 48, ACCENT, True, 'lm'))
    # sentence 2: export into folders
    s.add(T[2], arrow((545, 430), (545, 500), ACCENT, 6))
    s.add(T[2] + 0.3, icon_folder(300, 540, 150, 110, ACCENT, '01_exports/pubmed'))
    s.add(T[2] + 0.9, icon_folder(640, 540, 150, 110, TEAL, '01_exports/scopus'))
    # sentence 3: PubMed format
    s.add(T[3], chip('format: PubMed (.txt)', 150, 760, (255, 228, 120), (40, 48, 66), 28)[0])
    s.add(T[3] + 0.2, icon_doc(320, 420, 60, 80, (240, 242, 246), 3))
    # sentence 4: Scopus CSV with abstracts
    s.add(T[4], chip('CSV  +  abstracts', 560, 760, (170, 230, 255), (40, 48, 66), 28)[0])
    s.add(T[4] + 2.5, chip('needed for screening', 560, 830, PANEL2, MUTED, 26, outline=MUTED)[0])
    # sentence 5: log card
    s.add(T[5], card((1080, 480, 1840, 860), [('database:  PubMed', (40, 48, 66)), ('date:  2026-11-08', (40, 48, 66)),
                                               ('hits:  412', (40, 48, 66)), ('search string:', (40, 48, 66)),
                                               ('("stacked patch"[tiab] OR ...) AND (...)', (90, 100, 125))], heading='search_log.txt'))
    s.add(T[5] + 0.5, chip('1 minute now', 1100, 920, GREEN, (14, 20, 36), 28)[0])
    # sentence 6: PRISMA + methods
    s.add(T[6] + 1.2, chip('PRISMA diagram', 1400, 920, PANEL2, ACCENT, 28, outline=ACCENT)[0])
    s.add(T[6] + 2.2, chip('Methods section', 1400, 990, PANEL2, ACCENT, 28, outline=ACCENT)[0])
    s.add(T[6] + 1.2, arrow((1330, 920), (1385, 920), MUTED, 5))
    return s


def scene_06(T):
    s = Scene(T[-1])
    s.add(0.0, title('How duplicates are found'))
    A = card((120, 200, 740, 470), ['Title: A Decoupling Structure for ...', 'Year: 2022', 'First author: Fang Y.',
                                    ('DOI: 10.1109/lawp.2022.3158420', (40, 48, 66))], heading='Record from PubMed')
    B = card((1180, 200, 1800, 470), ['Title: A Decoupling Structure for ...', 'Year: 2022', 'First author: Fang Y.',
                                      ('DOI: 10.1109/lawp.2022.3158420', (40, 48, 66))], heading='Record from Scopus')
    s.add(0.3, A, exit=T[4])
    s.add(0.8, B, exit=T[4])
    s.add(1.4, label('same paper?', 960, 335, 40, ACCENT, True, 'mm'), exit=T[3])
    # rules
    s.add(T[1], chip('1  DOI', 120, 560, ACCENT, (14, 20, 36), 32)[0], exit=T[4])
    s.add(T[1] + 0.3, highlight((140, 383, 720, 423), ACCENT, 10, 4), exit=T[3])
    s.add(T[1] + 0.3, highlight((1200, 383, 1780, 423), ACCENT, 10, 4), exit=T[3])
    s.add(T[2], chip('2  title + year', 120, 640, (255, 228, 120), (14, 20, 36), 32)[0], exit=T[4])
    s.add(T[2] + 3.8, chip('3  very close title + same first author', 120, 720, (255, 228, 120), (14, 20, 36), 32)[0], exit=T[4])
    # merge
    s.add(T[3], arrow((745, 335), (1175, 335), GREEN, 8), exit=T[4])
    s.add(T[3] + 0.6, stamp('MERGED', 960, 440, GREEN, 36, -6), exit=T[4])
    s.add(T[3] + 1.2, label('keeps the most complete record', 960, 540, 30, MUTED, False, 'mm'), exit=T[4])
    # sentence 4..: the exception
    s.add(T[4] + 0.2, label('… except one case', 960, 330, 48, ACCENT, True, 'mm'), exit=T[5] + 0.3)
    P = card((120, 200, 740, 470), ['Title: A Decoupling Structure for ...', 'Year: 2022', ('DOI: 10.48550/arXiv.2201.01234', RED)], heading='Preprint')
    Q = card((1180, 200, 1800, 470), ['Title: A Decoupling Structure for ...', 'Year: 2022', ('DOI: 10.1109/lawp.2022.3158420', RED)], heading='Published paper')
    s.add(T[5] + 0.3, P)
    s.add(T[5] + 0.8, Q)
    s.add(T[5] + 2.2, label('different DOIs', 960, 335, 36, RED, True, 'mm'))
    s.add(T[6], stamp('NOT MERGED', 960, 440, RED, 36, -6))
    s.add(T[6] + 2.2, label('a wrong merge would silently delete a paper', 960, 560, 30, MUTED, False, 'mm'))
    s.add(T[7], panel((560, 640, 1360, 760), fill=PANEL2, outline=AMBER, width=4))
    s.add(T[7] + 0.2, label('dedupe_review.csv  →  you decide', 960, 700, 34, AMBER, True, 'mm'))
    return s


SCENES = {2: scene_02, 3: scene_03, 4: scene_04, 6: scene_06}


def scene_01(T):
    s = Scene(T[-1])
    s.add(0.0, title('Review paper: from search to final draft', 90, 90, 72))
    s.add(0.0, label('with a small Python tool, and AI as a helper', 90, 190, 36, MUTED, False))
    # confession
    s.add(T[1], chip('a confession', 90, 320, PANEL2, ACCENT, 30, outline=ACCENT)[0], exit=T[5])
    s.add(T[2] + 0.5, label('writing', 90, 450, 56, MUTED, True, 'lm'), exit=T[5])
    s.add(T[2] + 0.5, label('= not the hardest part', 330, 450, 36, MUTED, False, 'lm'), exit=T[5])
    s.add(T[3] + 0.3, label('bookkeeping', 90, 560, 64, ACCENT, True, 'lm'), exit=T[5])
    s.add(T[3] + 0.3, label('= the hardest part', 500, 560, 36, FG, False, 'lm'), exit=T[5])
    # the mess (sentence 4): papers piling up
    for k, (x, y, r) in enumerate([(1180, 300, -12), (1290, 340, 8), (1220, 420, -4), (1360, 400, 15), (1300, 500, -9), (1440, 480, 5)]):
        s.add(T[4] + 0.3 + k * 0.35, icon_doc(x, y, 150, 190, (240, 242, 246), 6), exit=T[5] + 0.3)
    s.add(T[4] + 2.6, chip('same paper x3', 1180, 760, RED, (14, 20, 36), 28)[0], exit=T[5] + 0.3)
    s.add(T[4] + 4.4, chip('paper(3)_final_v2.pdf', 1180, 830, RED, (14, 20, 36), 28)[0], exit=T[5] + 0.3)
    s.add(T[4] + 6.2, chip('reference 17 ≠ [17]', 1180, 900, RED, (14, 20, 36), 28)[0], exit=T[5] + 0.3)
    # computer does it (sentence 5)
    s.add(T[5] + 0.4, panel((90, 300, 900, 560), fill=CODE_BG, outline=CODE_LINE))
    s.add(T[5] + 0.6, typewriter('$ python slr.py import', 130, 340, 30, (120, 190, 255), 28))
    s.add(T[5] + 1.6, typewriter('$ python slr.py dedupe', 130, 400, 30, (120, 190, 255), 28))
    s.add(T[5] + 2.4, typewriter('$ python slr.py cite draft.docx', 130, 460, 30, (120, 190, 255), 28))
    s.add(T[5] + 3.0, check(840, 520, 24))
    # journey (sentence 6)
    for k, (txt, col) in enumerate([('search', AMBER), ('table', GREEN), ('PDFs', GREEN), ('AI draft', BLUE), ('final draft', ACCENT)]):
        s.add(T[6] + 0.4 + k * 0.9, chip(txt, 1180 + 0, 330 + k * 95, col, (14, 20, 36), 30)[0])
        if k < 4:
            s.add(T[6] + 0.8 + k * 0.9, arrow((1215, 360 + k * 95), (1215, 385 + k * 95), MUTED, 4, 10))
    # antenna example (sentence 7)
    s.add(T[7], chip('example: antenna research (stacked patch, decoupling)', 90, 900, PANEL2, TEAL, 30, outline=TEAL)[0])
    return s


def scene_07(T):
    s = Scene(T[-1])
    s.add(0.0, title('Screening: the tool flags, you decide'))
    # three record cards
    recs = [('P?  Record 1', ['Title: Decoupling of stacked patch ...', 'Year: 2023', 'Abstract: yes']),
            ('P?  Record 2', ['Title: Sleep EEG oscillations ...', 'Year: 2021', 'Abstract: yes']),
            ('P?  Record 3', ['Title: Mutual coupling in MIMO ...', 'Year: 2024', ('Abstract: missing', RED)])]
    for k, (hd, ls) in enumerate(recs):
        s.add(0.3 + k * 0.3, card((120 + k * 600, 200, 660 + k * 600, 420), ls, heading=hd))
    # sentence 1: flags
    s.add(T[1] + 0.5, chip('flag: no abstract', 1320, 470, RED, (14, 20, 36), 26)[0])
    s.add(T[1] + 2.2, chip('flag: keywords missing', 720, 470, RED, (14, 20, 36), 26)[0])
    s.add(T[1] + 4.0, label('flags only. No decision yet.', 960, 560, 30, MUTED, False, 'mm'))
    # sentence 2: the decision is yours
    s.add(T[2], stamp('YOUR DECISION', 960, 640, AMBER, 40, -4))
    # sentence 3: include / exclude / maybe
    s.add(T[3] + 1.5, stamp('INCLUDE', 390, 330, GREEN, 34, -10))
    s.add(T[3] + 3.0, stamp('EXCLUDE', 990, 330, RED, 34, 8))
    s.add(T[3] + 4.2, stamp('MAYBE', 1590, 330, AMBER, 34, -6))
    s.add(T[3] + 5.5, label('reason: "not an antenna paper"', 960, 730, 26, MUTED, False, 'mm'))
    # sentence 4: permanent number
    s.add(T[4] + 0.8, chip('P001', 150, 830, ACCENT, (14, 20, 36), 44)[0])
    s.add(T[4] + 1.6, label('permanent number, never changes', 330, 830, 30, FG, False, 'lm'))
    # sentence 5: AI uses it
    s.add(T[5] + 0.5, sparkle(170, 940, BLUE))
    s.add(T[5] + 0.8, label('the AI will call this paper  [P001]  and nothing else', 220, 940, 30, BLUE, True, 'lm'))
    return s


def prisma_box(box, text, n, t_count, fill=PANEL, outline=TEAL):
    def fn(d, img, p, t):
        x0, y0, x1, y1 = box
        d.rounded_rectangle([x0, y0, x1, y1], 12, fill=fill, outline=outline, width=3)
        d.text(((x0 + x1) / 2, y0 + 30), text, font=font(26, False), fill=FG, anchor='mm')
        v = int(round(n * ease(t / max(0.1, t_count))))
        d.text(((x0 + x1) / 2, y1 - 34), f'n = {v:,}', font=font(32), fill=ACCENT, anchor='mm')
    return fn


def scene_08(T):
    s = Scene(T[-1])
    s.add(0.0, title('PRISMA numbers, straight from the project'))
    s.add(T[0] + 0.5, chip('a reward for all that logging', 1000, 760, PANEL2, GREEN, 28, outline=GREEN)[0])
    boxes = [((260, 200, 900, 320), 'Records identified (PubMed 412 + Scopus 688)', 1100),
             ((260, 380, 900, 500), 'Records screened', 850),
             ((260, 560, 900, 680), 'Full texts assessed', 108),
             ((260, 740, 900, 860), 'Studies included', 26)]
    side = [((1000, 200, 1640, 320), 'Duplicates removed', 160), ((1000, 380, 1640, 500), 'Excluded at title/abstract', 735),
            ((1000, 560, 1640, 680), 'Excluded at full text (with reasons)', 82)]
    t0 = T[1] + 0.3
    for k, (b, txt, n) in enumerate(boxes):
        s.add(t0 + k * 2.2, prisma_box(b, txt, n, 1.4, PANEL, TEAL if k < 3 else ACCENT))
        if k < 3:
            s.add(t0 + k * 2.2 + 1.2, arrow((580, b[3]), (580, b[3] + 56), MUTED, 5))
            sb, st, sn = side[k]
            s.add(t0 + k * 2.2 + 1.0, prisma_box(sb, st, sn, 1.2, PANEL2, MUTED))
            s.add(t0 + k * 2.2 + 0.8, arrow((902, (b[1] + b[3]) / 2), (996, (b[1] + b[3]) / 2), MUTED, 4))
    s.add(T[2], chip('example numbers', 1000, 840, PANEL2, AMBER, 30, outline=AMBER)[0])
    s.add(T[3] + 0.5, label('yours:  python slr.py prisma', 1000, 910, 30, BLUE, True, 'lm'))
    s.add(T[3] + 2.0, label('no counting by hand', 1000, 965, 30, MUTED, False, 'lm'))
    return s


def scene_10(T):
    s = Scene(T[-1])
    s.add(0.0, title('Where the PDFs go'))
    s.add(0.3, icon_folder(150, 260, 220, 160, ACCENT, '05_pdfs/inbox'))
    names = ['download (3).pdf', 'tap2022.pdf', 'P004.pdf', 'Fang_decoupling.pdf', 'untitled.pdf']
    for k, nm in enumerate(names):
        s.add(0.8 + k * 0.5, chip(nm, 420, 250 + k * 56, (240, 242, 246), (40, 48, 66), 24)[0], exit=T[1] + 1.5 + k * 0.4)
    s.add(T[0] + 3.5, label('any file name is fine', 420, 560, 28, MUTED, False, 'lm'), exit=T[1] + 1.0)
    # sentence 1: matching
    s.add(T[1] + 0.3, panel((420, 230, 1000, 560), fill=PANEL2, outline=BLUE, width=3))
    s.add(T[1] + 0.5, label('match by:', 450, 270, 28, BLUE, True, 'lm'))
    s.add(T[1] + 1.0, chip('paper number', 450, 340, BLUE, (14, 20, 36), 26)[0])
    s.add(T[1] + 1.8, chip('DOI inside the PDF', 450, 410, BLUE, (14, 20, 36), 26)[0])
    s.add(T[1] + 2.6, chip('title', 450, 480, BLUE, (14, 20, 36), 26)[0])
    s.add(T[1] + 3.6, arrow((1010, 400), (1120, 400), GREEN, 6))
    s.add(T[1] + 4.0, icon_folder(1140, 230, 200, 140, GREEN, '05_pdfs/journal'))
    s.add(T[1] + 4.6, icon_folder(1480, 230, 200, 140, TEAL, '05_pdfs/conference'))
    s.add(T[1] + 5.6, chip('P004_Xing_2026.pdf', 1140, 460, (240, 242, 246), (40, 48, 66), 24)[0])
    s.add(T[1] + 6.4, chip('P011_Li_2023.pdf', 1480, 460, (240, 242, 246), (40, 48, 66), 24)[0])
    s.add(T[1] + 7.2, label('renamed, sorted', 1300, 540, 28, MUTED, False, 'lm'))
    # sentence 2: unmatched + missing
    s.add(T[2] + 0.3, icon_folder(150, 680, 200, 140, MUTED, '05_pdfs/unmatched'))
    s.add(T[2] + 1.0, chip('untitled.pdf', 170, 905, (240, 242, 246), (40, 48, 66), 24)[0])
    s.add(T[2] + 3.5, card((700, 660, 1300, 960), [('P002  not downloaded yet', RED), ('P007  not downloaded yet', RED), ('P009  not downloaded yet', RED)], heading='missing_papers.csv'))
    s.add(T[2] + 6.0, label('exactly what to download next', 1340, 820, 28, MUTED, False, 'lm'))
    return s


def scene_12(T):
    s = Scene(T[-1])
    s.add(0.0, title('The brief file: tell the AI what you want'))
    s.add(0.3, sparkle(170, 260, BLUE))
    s.add(0.5, label('AI has the papers ...', 220, 260, 36, FG, True, 'lm'))
    s.add(T[0] + 2.0, label('... but not your goal', 220, 320, 36, ACCENT, True, 'lm'))
    s.add(T[1] + 0.3, chip('07_draft/review_brief.md', 90, 420, PANEL2, BLUE, 30, outline=BLUE)[0])
    rows = ['Review type:  narrative review for an IEEE journal', 'Research questions:  RQ1 ... RQ2 ...',
            'Sections:  Intro, Methods, Results, Discussion, Future', 'Word counts:  6000 total, abstract 250',
            'Analysis rules:  only what the paper says; cite [P0xx]', 'Our contribution:  a comparison framework ...']
    s.add(T[2], panel((90, 470, 1300, 920), fill=(246, 247, 250), outline=(205, 210, 220)))
    for k, r in enumerate(rows):
        s.add(T[2] + 0.6 + k * 1.9, typewriter(r, 130, 500 + k * 68, 28, (40, 48, 66), 40, font(28, False)))
    s.add(T[3] + 0.3, chip('10 minutes here', 1380, 520, GREEN, (14, 20, 36), 30)[0])
    s.add(T[3] + 2.2, chip('saves many rounds later', 1380, 600, GREEN, (14, 20, 36), 30)[0])
    s.add(T[3] + 4.5, chip('vague brief = vague draft', 1380, 700, RED, (14, 20, 36), 30)[0])
    return s


def loop_ring(cx, cy, r, items, t_items):
    def fn(d, img, p, t):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=PANEL2, width=16)
        n = len(items)
        for k, (txt, col) in enumerate(items):
            if t < t_items[k]:
                continue
            a = -math.pi / 2 + 2 * math.pi * k / n
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            q = ease((t - t_items[k]) / 0.5)
            rr = 70 * pop(q)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col)
            if q > 0.5:
                d.text((x, y), txt, font=font(24), fill=(14, 20, 36), anchor='mm')
        # moving dot around the ring
        a = -math.pi / 2 + (t * 0.9) % (2 * math.pi)
        d.ellipse([cx + r * math.cos(a) - 14, cy + r * math.sin(a) - 14, cx + r * math.cos(a) + 14, cy + r * math.sin(a) + 14], fill=FG)
    return fn


def scene_14(T):
    s = Scene(T[-1])
    s.add(0.0, title('The revision loop'))
    items = [('read', AMBER), ('comment', AMBER), ('collect', GREEN), ('prompt', GREEN), ('new draft', BLUE)]
    s.add(0.3, loop_ring(560, 600, 300, items, [T[1] - 0.3, T[1] + 2.5, T[3] - 0.3, T[3] + 2.0, T[4] - 0.3]))
    s.add(T[1] + 0.3, card((1100, 220, 1840, 520), ['The proposed structure improves isolation', 'by 15 dB [P004].',
                                                     ('▌ too strong: P004 reports 12 dB', RED), 'Decoupling networks add losses [P007] [P011].',
                                                     ('▌ add the comparison table here', AMBER)], heading='draft_v03.docx  (Word comments)', size=24))
    s.add(T[2] + 0.5, chip('draft_v04.docx', 1100, 580, PANEL2, FG, 28, outline=MUTED)[0])
    s.add(T[2] + 2.0, typewriter('$ python slr.py comments draft_v04.docx', 1100, 630, 26, BLUE, 40))
    s.add(T[3] + 1.0, card((1100, 690, 1840, 900), ['Fix 1: P004 reports 12 dB, correct the claim.', 'Fix 2: add a comparison table of ...'], heading='next_prompt.txt'))
    s.add(T[5] + 0.3, counter(560, 600, 1, 20, 4.0, 96, ACCENT, '', 'mm'))
    s.add(T[5] + 0.3, label('rounds', 560, 680, 30, MUTED, False, 'mm'))
    s.add(T[6] + 1.5, chip('each round is quick: the tool copies and pastes', 1100, 960, GREEN, (14, 20, 36), 28)[0])
    return s


def scene_15(T):
    s = Scene(T[-1])
    s.add(0.0, title('Rules I keep'))
    rules = [('AI is a helper, not an author', 'decisions and responsibility stay with you', AMBER),
             ('Verify every fact and reference', 'AI can invent both', RED),
             ('Redraw the figures yourself', 'first-draft figures are rarely clear (next video)', TEAL),
             ('Follow your journal\'s AI rules', 'and say clearly how you used AI', GREEN)]
    for k, (a, b, col) in enumerate(rules):
        y = 230 + k * 190
        s.add(T[1 + k], panel((90, y, 1830, y + 150), fill=PANEL, outline=col, width=4))
        s.add(T[1 + k] + 0.1, chip(str(k + 1), 130, y + 75, col, (14, 20, 36), 36, h=70)[0])
        s.add(T[1 + k] + 0.2, label(a, 230, y + 48, 40, FG, True, 'lm'))
        s.add(T[1 + k] + 0.9, label(b, 230, y + 108, 30, MUTED, False, 'lm'))
    return s


def scene_16(T):
    s = Scene(T[-1])
    s.add(0.0, title('Thank you for watching', 960, 300, 84, FG, 'mm'))
    for k, (txt, col) in enumerate([('search', AMBER), ('table', GREEN), ('PDFs', GREEN), ('AI draft', BLUE), ('final draft', ACCENT)]):
        s.add(0.4 + k * 0.5, chip(txt, 330 + k * 270, 470, col, (14, 20, 36), 30)[0])
        if k < 4:
            s.add(0.6 + k * 0.5, arrow((330 + k * 270 + 170, 470), (330 + (k + 1) * 270 - 10, 470), MUTED, 4, 10))
    s.add(T[1], chip('tool + guides: link in the description', 560, 620, PANEL2, FG, 30, outline=MUTED)[0])
    s.add(T[2], chip('Subscribe', 700, 740, RED, FG, 36)[0])
    s.add(T[2] + 2.5, label('which step should I explain in more detail?  → comments', 960, 840, 30, MUTED, False, 'mm'))
    return s


SCENES.update({1: scene_01, 7: scene_07, 8: scene_08, 10: scene_10, 12: scene_12, 14: scene_14, 15: scene_15, 16: scene_16})
