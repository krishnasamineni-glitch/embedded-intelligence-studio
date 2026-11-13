# build.py - usage: python build.py episodes/rv01_en   (language: {"lang":"en"} in the episode folder's episode.json)
import json, re, sys, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageOps, features

W, H, FPS = 1920, 1080, 30
HERE = pathlib.Path(__file__).resolve().parent
FONTS = {'te': str(HERE / 'assets/NotoSansTelugu-Bold.ttf'), 'en': str(HERE / 'assets/Inter-Bold.otf')}
FONT = FONTS['te']
SUB_CHARS = {'te': 80, 'en': 72}   # maximum characters in one subtitle piece
LANG = 'te'
BG, FG = (18, 24, 38), (245, 245, 245)
HAS_RAQM = features.check('raqm')

def run(cmd):
    subprocess.run(cmd, check=True)

def wrap(draw, text, font, max_w):
    lines, cur = [], ''
    for word in text.split():
        trial = (cur + ' ' + word).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

def wrap_balanced(draw, text, font, max_w):
    """Wrap with the same number of lines but evenly filled lines (no lonely last word)."""
    lines = wrap(draw, text, font, max_w)
    if len(lines) < 2:
        return lines
    for w in range(int(max_w) - 20, 300, -20):
        trial = wrap(draw, text, font, w)
        if len(trial) > len(lines) or any(draw.textlength(x, font=font) > w for x in trial):
            break
        lines = trial
    return lines

def load_font(size):
    return ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM if HAS_RAQM else ImageFont.Layout.BASIC)

def make_card(text, out):
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    font = load_font(96)
    lines = wrap_balanced(d, text, font, W - 240)
    y = (H - 140 * len(lines)) // 2
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((W - w) / 2, y), ln, font=font, fill=FG)
        y += 140
    img.save(out)

def make_image(path, out):
    ImageOps.fit(Image.open(path).convert('RGB'), (W, H)).save(out)

FADE = 0.3        # seconds: every scene fades in from black and out to black, so cuts never feel abrupt
KEN = 0.05        # slow zoom on still slides (1.0 -> 1.05 over the scene); 0 switches it off

def fades(dur):
    return f'fade=t=in:st=0:d={FADE},fade=t=out:st={max(0.0, dur - FADE):.3f}:d={FADE}'

def seg_from_png(png, dur, out, motion=True):
    n = max(1, round(dur * FPS))
    vf = (f"zoompan=z='1+{KEN}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},"
          if motion and KEN > 0 else '') + 'format=yuv420p,' + fades(dur)
    run(['ffmpeg', '-y', '-loop', '1', '-i', str(png), '-vf', vf, '-frames:v', str(n), '-r', str(FPS),
         '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', str(out)])

def make_caption_png(text, out):
    """Caption drawn over a clip: a transparent PNG with a semi-transparent dark panel behind the text."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = load_font(84)
    lines = wrap_balanced(d, text, font, W - 360)
    lh = 124
    box_h = lh * len(lines) + 70
    box_w = int(max(d.textlength(x, font=font) for x in lines)) + 140
    x0, y0 = (W - box_w) // 2, (H - box_h) // 2
    d.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], radius=28, fill=(10, 14, 24, 175))
    y = y0 + 35
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((W - w) / 2, y), ln, font=font, fill=FG)
        y += lh
    img.save(out)

def seg_from_clips(clips, dur, out, tmp, caption=None):
    """One or several clips (a.mp4+b.mp4): convert to 1920x1080 at 30 fps, join them, loop or trim to the scene
    length, drop their audio, and (optionally) put a caption on top."""
    vf = f'scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,format=yuv420p'  # whole recording stays visible (no cropped text)
    for c in clips:
        if not pathlib.Path(c).exists():
            raise SystemExit(f'Clip not found: {c}  (put the video file in the episode img/ folder)')
    norm = []
    for k, c in enumerate(clips):
        n = tmp / f'{out.stem}_n{k}.mp4'
        run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(c), '-vf', vf, '-r', str(FPS), '-an',
             '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', str(n)])
        norm.append(n)
    if len(norm) == 1:
        joined = norm[0]
    else:
        lst = tmp / f'{out.stem}_list.txt'
        lst.write_text(''.join(f'file {n.name}\n' for n in norm), encoding='utf-8')
        joined = tmp / f'{out.stem}_joined.mp4'
        run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(joined)])
    # Fit the clip to the scene: a clip a bit longer than the scene is sped up (up to 1.6x), a much longer one is
    # trimmed, and a shorter one holds its last frame (so the result of a command stays on screen while you talk).
    pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(joined)],
                        capture_output=True, text=True)
    try:
        cd = float(pr.stdout.strip())
    except ValueError:
        cd = dur
    chain = 'null'
    if cd > dur * 1.02:
        if cd / dur <= 1.6:
            chain = f'setpts=PTS*{dur / cd:.5f}'
    elif cd < dur:
        chain = f'tpad=stop_mode=clone:stop_duration={dur - cd + 0.5:.3f}'
    cmd = ['ffmpeg', '-loglevel', 'error', '-y', '-i', str(joined)]
    if caption:
        cap = tmp / f'{out.stem}_cap.png'
        make_caption_png(caption, cap)
        cmd += ['-i', str(cap), '-filter_complex', f'[0:v]{chain}[v0];[v0][1:v]overlay=0:0,format=yuv420p,{fades(dur)}']
    else:
        cmd += ['-vf', f'{chain},format=yuv420p,{fades(dur)}']
    cmd += ['-t', f'{dur:.3f}', '-r', str(FPS), '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', str(out)]
    run(cmd)

def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def split_cues(text, start, end, max_chars=80):
    """Split a scene's narration into sentences (and shorter pieces if needed) and share the scene time by character count."""
    pieces = []
    for sent in re.split(r'(?<=[.!?])\s+', text.strip()):
        while len(sent) > max_chars:
            cut = sent.rfind(', ', 0, max_chars)
            cut = cut + 1 if cut > 20 else sent.rfind(' ', 0, max_chars)
            if cut <= 0:
                cut = max_chars
            pieces.append(sent[:cut].strip())
            sent = sent[cut:].strip()
        if sent:
            pieces.append(sent)
    merged = []
    for x in pieces:  # very short pieces are merged into the previous piece
        if merged and len(merged[-1]) < 16:
            merged[-1] += ' ' + x
        else:
            merged.append(x)
    pieces = merged
    total = sum(len(x) for x in pieces) or 1
    cues, t0 = [], start
    for x in pieces:
        t1 = t0 + (end - start) * len(x) / total
        cues.append((t0, t1, x))
        t0 = t1
    return cues

def main(ep_dir):
    global FONT, LANG
    ep = pathlib.Path(ep_dir)
    cfg = ep / 'episode.json'
    LANG = json.loads(cfg.read_text(encoding='utf-8')).get('lang', 'te') if cfg.exists() else 'te'
    if LANG not in FONTS:
        raise SystemExit(f'Unknown language {LANG}: use te or en.')
    FONT = FONTS[LANG]
    if not pathlib.Path(FONT).exists():
        raise SystemExit(f'Font file not found: {FONT} (put the fonts in the assets/ folder)')
    if LANG == 'te' and not HAS_RAQM:
        print('Warning: raqm is missing; Telugu conjunct letters may render incorrectly')
    data = json.loads((ep / 'timings.json').read_text(encoding='utf-8'))
    pause, scenes = data['pause'], data['scenes']
    tmp = ep / 'tmp'
    tmp.mkdir(exist_ok=True)
    segs, srt = [], []
    for i, sc in enumerate(scenes):
        dur = sc['end'] - sc['start'] + pause
        kind, _, arg = sc['visual'].partition(':')
        kind, arg = kind.strip(), arg.strip()
        seg = tmp / f'seg_{i:03}.mp4'
        png = tmp / f's_{i:03}.png'
        if kind == 'card':
            make_card(arg, png)
            seg_from_png(png, dur, seg, motion=False)
        elif kind == 'img':
            make_image(ep / 'img' / arg, png)
            seg_from_png(png, dur, seg)
        elif kind == 'clip':
            # clip: a.mp4            one clip (a short clip is looped)
            # clip: a.mp4+b.mp4      several clips, one after another
            # clip: a.mp4 | Title    a caption drawn over the clip
            names, _, caption = arg.partition(' | ')
            clips = [ep / 'img' / x.strip() for x in names.split('+') if x.strip()]
            seg_from_clips(clips, dur, seg, tmp, caption.strip() or None)
        else:
            raise SystemExit(f'Scene {i + 1}: unknown visual type {kind} (use card:, img: or clip:)')
        segs.append(seg)
        for c0, c1, txt in split_cues(sc['text'], sc['start'], sc['end'], SUB_CHARS[LANG]):
            srt.append(f'{len(srt) + 1}\n{srt_time(c0)} --> {srt_time(c1)}\n{txt}\n')
    (ep / 'subtitles.srt').write_text('\n'.join(srt), encoding='utf-8')
    lst = tmp / 'list.txt'
    lst.write_text(''.join(f'file {s.name}\n' for s in segs), encoding='utf-8')
    silent, final = tmp / 'silent.mp4', ep / 'final.mp4'
    run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(silent)])
    run(['ffmpeg', '-y', '-i', str(silent), '-i', str(ep / 'narration.wav'),
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', str(final)])
    print('Done:', final)

if __name__ == '__main__':
    main(sys.argv[1])
