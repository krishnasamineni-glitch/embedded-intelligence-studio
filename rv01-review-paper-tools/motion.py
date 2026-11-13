#!/usr/bin/env python3
# motion.py - small motion-graphics engine (Pillow + ffmpeg): animated explainer scenes timed to the narration.
# Every element has an "enter" time (seconds) and animates in (fade + slide/pop); the scene is rendered frame by
# frame straight into ffmpeg. No GPU, no extra libraries beyond Pillow and numpy.
import math
import pathlib
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
HERE = pathlib.Path(__file__).resolve().parent
BG, BG2 = (14, 20, 36), (24, 36, 70)
import os
THEME = os.environ.get('MOTION_THEME', 'dark')
if THEME == 'light':
    FG, MUTED, PANEL, PANEL2 = (28, 34, 52), (96, 108, 135), (255, 255, 255), (232, 237, 246)
    ACCENT, TEAL, GREEN, AMBER, RED, BLUE = (235, 160, 0), (0, 150, 135), (40, 165, 90), (240, 170, 40), (220, 70, 70), (40, 110, 220)
else:
    FG, MUTED, PANEL, PANEL2 = (245, 245, 245), (165, 175, 195), (30, 40, 62), (38, 50, 76)
    ACCENT, TEAL, GREEN, AMBER, RED, BLUE = (255, 193, 7), (80, 200, 180), (110, 220, 140), (255, 200, 90), (245, 110, 110), (120, 190, 255)
CODE_BG, CODE_FG, CODE_LINE = (10, 14, 26), (235, 236, 240), (60, 75, 110)   # terminal boxes look the same in both themes
_fonts = {}


def font(size, bold=True):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(str(HERE / 'assets' / ('Inter-Bold.otf' if bold else 'Inter-Regular.otf')), size)
    return _fonts[key]


def mono(size):
    key = ('mono', size)
    if key not in _fonts:
        for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 'C:/Windows/Fonts/consola.ttf'):
            if pathlib.Path(p).exists():
                _fonts[key] = ImageFont.truetype(p, size)
                break
        else:
            _fonts[key] = font(size, False)
    return _fonts[key]


def ease(p):
    """ease-out cubic, clamped 0..1"""
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def pop(p):
    """overshoot: 0 -> 1.08 -> 1"""
    p = max(0.0, min(1.0, p))
    return 1 + 0.08 * math.sin(p * math.pi) if p < 1 else 1.0


STYLES = {
    # name: top colour, bottom colour, pattern, [(blob colour, radius, (x, y, drift)), ...]
    'nebula':   dict(top=(14, 20, 36), bottom=(24, 36, 70), pattern='grid', dots=True,
                     blobs=[((50, 110, 230), 420, (900, -650)), ((255, 160, 20), 320, (-520, 420)), ((40, 190, 170), 280, (1350, 520))]),
    'ocean':    dict(top=(8, 24, 34), bottom=(10, 52, 70), pattern='waves', dots=False,
                     blobs=[((0, 170, 200), 460, (1000, -600)), ((0, 120, 160), 380, (-600, 500)), ((40, 220, 190), 240, (1400, 600))]),
    'midnight': dict(top=(18, 12, 40), bottom=(40, 24, 80), pattern='bokeh', dots=True,
                     blobs=[((120, 70, 230), 440, (-500, -500)), ((230, 60, 160), 320, (1200, 500)), ((60, 120, 255), 300, (1300, -500))]),
    'graphite': dict(top=(22, 24, 28), bottom=(34, 37, 44), pattern='dotgrid', dots=False,
                     blobs=[((90, 100, 120), 520, (700, -700)), ((255, 193, 7), 200, (-350, 800))]),
    'studio':   dict(top=(26, 18, 14), bottom=(44, 30, 22), pattern='none', dots=False,
                     blobs=[((255, 170, 60), 520, (-500, -600)), ((255, 120, 40), 300, (1500, 700))]),
    'paper':    dict(top=(246, 247, 251), bottom=(226, 232, 244), pattern='grid', dots=False, light=True,
                     blobs=[((120, 170, 255), 460, (900, -650)), ((255, 205, 90), 340, (-520, 420)), ((90, 220, 200), 300, (1350, 520))]),
    'forest':   dict(top=(10, 26, 20), bottom=(16, 48, 36), pattern='grid', dots=True,
                     blobs=[((40, 200, 120), 420, (-550, -450)), ((255, 193, 7), 260, (1450, 650)), ((0, 150, 170), 300, (1200, -450))]),
}
STYLE = 'paper' if THEME == 'light' else 'nebula'


def _base(st):
    img = Image.new('RGB', (W, H), st['top'])
    d = ImageDraw.Draw(img)
    a, b = st['top'], st['bottom']
    for y in range(0, H, 2):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)), width=2)
    line = tuple(max(0, c - 9) for c in a) if st.get('light') else tuple(min(255, c + 7) for c in a)
    if st['pattern'] == 'grid':
        for x in range(0, W, 80):
            d.line([(x, 0), (x, H)], fill=line)
        for y in range(0, H, 80):
            d.line([(0, y), (W, y)], fill=line)
    elif st['pattern'] == 'dotgrid':
        for x in range(40, W, 60):
            for y in range(40, H, 60):
                d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=tuple(min(255, c + 22) for c in a))
    elif st['pattern'] == 'waves':
        for k in range(14):
            pts = [(x, 700 + k * 32 + 26 * math.sin(x / 260 + k * 0.6)) for x in range(0, W + 20, 20)]
            d.line(pts, fill=tuple(min(255, c + 10 + k) for c in a), width=2)
    elif st['pattern'] == 'bokeh':
        rng = np.random.RandomState(3)
        for _ in range(26):
            x, y, r = rng.rand() * W, rng.rand() * H, 30 + rng.rand() * 110
            d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(min(255, c + 9) for c in a))
    return img


def _blob(color, r, alpha=190):
    """soft glowing disc (RGBA sprite), blurred once and reused every frame"""
    s = Image.new('RGBA', (r * 4, r * 4), (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse([r, r, 3 * r, 3 * r], fill=color + (alpha,))
    return s.filter(ImageFilter.GaussianBlur(r * 0.7))


def _vignette():
    v = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(v)
    for i in range(12):
        k = i / 12
        d.rounded_rectangle([int(-W * 0.2 + W * 0.2 * k), int(-H * 0.2 + H * 0.2 * k), int(W * 1.2 - W * 0.2 * k), int(H * 1.2 - H * 0.2 * k)],
                            300, fill=int(70 * (1 - k)))
    return v.filter(ImageFilter.GaussianBlur(90))


_CACHE = {}
_RNG = np.random.RandomState(7)
_DOTS = [(_RNG.rand(), _RNG.rand(), 0.4 + _RNG.rand() * 1.6, _RNG.rand() * 6.28) for _ in range(70)]


def background(t=0.0, style=None):
    """Living background: gradient + pattern, slowly drifting colour glows, floating dots, vignette."""
    name = style or STYLE
    st = STYLES[name]
    if _CACHE.get('name') != name:
        _CACHE.clear()
        _CACHE['name'] = name
        _CACHE['base'] = _base(st)
        _CACHE['blobs'] = [(_blob(c, r, 110 if st.get('light') else 190), pos) for c, r, pos in st['blobs']]
        _CACHE['vig'] = _vignette()
    img = _CACHE['base'].copy()
    for k, (b, (x, y)) in enumerate(_CACHE['blobs']):
        img.paste(b, (int(x + 120 * math.sin(t * 0.17 + k)), int(y + 90 * math.cos(t * 0.21 + k * 2))), b)
    if st['dots']:
        d = ImageDraw.Draw(img, 'RGBA')
        for fx, fy, r, ph in _DOTS:
            x = (fx * W + 12 * math.sin(t * 0.3 + ph)) % W
            y = (fy * H - 6 * t * r) % H
            a = int(70 + 60 * math.sin(t * 0.8 + ph))
            d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 225, 245, a))
    if not st.get('light'):
        img.paste((0, 0, 0), (0, 0), _CACHE['vig'])
    return img


class Scene:
    def __init__(self, duration):
        self.duration = duration
        self.items = []          # (enter, exit, draw_fn)  draw_fn(layer_draw, layer_img, progress, t)

    def add(self, enter, fn, exit=None, dur=0.5):
        self.items.append((enter, exit, dur, fn))

    def frame(self, t):
        img = background(t)
        for enter, exit, dur, fn in self.items:
            if t < enter or (exit is not None and t >= exit + 0.4):
                continue
            p = ease((t - enter) / dur)
            alpha = p
            if exit is not None and t >= exit:
                alpha = 1 - ease((t - exit) / 0.4)
            layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            fn(ImageDraw.Draw(layer), layer, p, t - enter)
            if alpha < 1:
                a = layer.split()[3].point(lambda v: int(v * alpha))
                layer.putalpha(a)
            img.paste(layer, (0, 0), layer)
        return img

    def render(self, out, fps=FPS):
        n = round(self.duration * fps)
        proc = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                                 '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                                 '-pix_fmt', 'yuv420p', str(out)], stdin=subprocess.PIPE)
        for i in range(n):
            proc.stdin.write(self.frame(i / fps).tobytes())
        proc.stdin.close()
        proc.wait()
        if proc.returncode != 0:
            raise SystemExit('ffmpeg failed while writing ' + str(out))
        print(f'Wrote {out} ({self.duration:.1f}s, {n} frames)')


# ---------- widgets: each returns a draw function for Scene.add ----------
def slide(p, dist=40):
    return int((1 - p) * dist)


def title(text, x=90, y=70, size=64, color=FG, anchor='la'):
    def fn(d, img, p, t):
        d.text((x, y + slide(p)), text, font=font(size), fill=color, anchor=anchor)
    return fn


def label(text, x, y, size=34, color=MUTED, bold=False, anchor='la', maxw=None):
    def fn(d, img, p, t):
        f = font(size, bold)
        txt = text
        if maxw:
            txt = wrap(text, f, maxw, d)
        d.multiline_text((x, y + slide(p, 20)), txt, font=f, fill=color, anchor=anchor if '\n' not in txt else 'la', spacing=8)
    return fn


def wrap(text, f, maxw, d):
    words, lines, cur = text.split(), [], ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if d.textlength(trial, font=f) <= maxw:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return '\n'.join(lines)


def panel(box, fill=PANEL, outline=None, radius=22, width=3):
    def fn(d, img, p, t):
        x0, y0, x1, y1 = box
        s = pop(p)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hw, hh = (x1 - x0) / 2 * s, (y1 - y0) / 2 * s
        d.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh], radius, fill=fill, outline=outline, width=width)
    return fn


def chip(text, x, y, color=ACCENT, fg=(14, 20, 36), size=34, pad=22, h=None, bold=True, outline=None):
    """Rounded pill with text; anchored at left-centre (x, y). Returns (fn, width)."""
    f = font(size, bold)
    tw = int(ImageDraw.Draw(Image.new('RGB', (1, 1))).textlength(text, font=f))
    hh = h or size + 28

    def fn(d, img, p, t):
        s = pop(p)
        w = (tw + 2 * pad) * s
        d.rounded_rectangle([x, y - hh / 2 * s, x + w, y + hh / 2 * s], hh // 2, fill=color, outline=outline, width=3)
        if p > 0.5:
            d.text((x + pad, y), text, font=f, fill=fg, anchor='lm')
    return fn, tw + 2 * pad


def arrow(p0, p1, color=MUTED, width=6, head=18):
    def fn(d, img, p, t):
        x0, y0 = p0
        x1 = x0 + (p1[0] - x0) * p
        y1 = y0 + (p1[1] - y0) * p
        d.line([(x0, y0), (x1, y1)], fill=color, width=width)
        if p > 0.6:
            ang = math.atan2(y1 - y0, x1 - x0)
            pts = [(x1, y1), (x1 - head * math.cos(ang - 0.5), y1 - head * math.sin(ang - 0.5)),
                   (x1 - head * math.cos(ang + 0.5), y1 - head * math.sin(ang + 0.5))]
            d.polygon(pts, fill=color)
    return fn


def card(box, lines, heading=None, fill=(246, 247, 250), outline=(205, 210, 220), text_color=(40, 48, 66), size=26):
    """A 'record' card: white panel with a heading and small text lines."""
    def fn(d, img, p, t):
        x0, y0, x1, y1 = box
        s = pop(p)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hw, hh = (x1 - x0) / 2 * s, (y1 - y0) / 2 * s
        d.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh], 18, fill=fill, outline=outline, width=3)
        if p > 0.5:
            y = y0 + 22
            if heading:
                d.text((x0 + 26, y), heading, font=font(size + 4), fill=text_color)
                y += size + 22
            for ln in lines:
                col = text_color
                if isinstance(ln, tuple):
                    ln, col = ln
                d.text((x0 + 26, y), ln, font=font(size, False), fill=col)
                y += size + 12
    return fn


def highlight(box, color=ACCENT, radius=12, width=5, pulse=True):
    def fn(d, img, p, t):
        g = 1.0 if not pulse else 0.75 + 0.25 * math.sin(t * 4)
        col = tuple(int(c * g) for c in color)
        d.rounded_rectangle(box, radius, outline=col, width=width)
        d.rounded_rectangle(box, radius, fill=color + (22,))
    return fn


def typewriter(text, x, y, size=30, color=FG, cps=30, f=None):
    """Monospace text typed at cps characters per second."""
    def fn(d, img, p, t):
        n = int(t * cps)
        d.text((x, y), text[:n] + ('|' if int(t * 3) % 2 == 0 and n < len(text) else ''), font=f or mono(size), fill=color)
    return fn


def counter(x, y, start, end, seconds, size=72, color=FG, suffix='', anchor='la'):
    def fn(d, img, p, t):
        v = start + (end - start) * ease(t / seconds)
        d.text((x, y), f'{int(round(v)):,}{suffix}', font=font(size), fill=color, anchor=anchor)
    return fn


def icon_doc(x, y, w=70, h=90, color=(240, 242, 246), lines=4):
    def fn(d, img, p, t):
        s = pop(p)
        ww, hh = w * s, h * s
        d.rounded_rectangle([x, y, x + ww, y + hh], 8, fill=color, outline=(180, 186, 200), width=3)
        for i in range(lines):
            d.line([(x + 12, y + 22 + i * 16 * s), (x + ww - 12 - (i % 2) * 14, y + 22 + i * 16 * s)], fill=(160, 168, 185), width=4)
    return fn


def icon_folder(x, y, w=120, h=90, color=ACCENT, text=None):
    def fn(d, img, p, t):
        s = pop(p)
        ww, hh = w * s, h * s
        d.rounded_rectangle([x, y + 14, x + ww, y + hh], 10, fill=color)
        d.rounded_rectangle([x, y, x + ww * 0.45, y + 30], 8, fill=color)
        d.rounded_rectangle([x, y + 26, x + ww, y + hh], 10, fill=tuple(min(255, c + 25) for c in color))
        if text and p > 0.5:
            d.text((x + ww / 2, y + hh + 14), text, font=font(24, False), fill=MUTED, anchor='ma')
    return fn


def stamp(text, x, y, color=GREEN, size=40, angle=-8):
    def fn(d, img, p, t):
        f = font(size)
        tw = int(d.textlength(text, font=f))
        lay = Image.new('RGBA', (tw + 60, size + 40), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle([0, 0, tw + 59, size + 39], 14, outline=color, width=6)
        ld.text((30, 20), text, font=f, fill=color)
        lay = lay.rotate(angle, expand=True, resample=Image.BICUBIC)
        s = 1.6 - 0.6 * p
        lay = lay.resize((int(lay.width * s), int(lay.height * s)))
        img.paste(lay, (int(x - lay.width / 2), int(y - lay.height / 2)), lay)
    return fn


def check(x, y, r=26, color=GREEN):
    def fn(d, img, p, t):
        s = pop(p)
        d.ellipse([x - r * s, y - r * s, x + r * s, y + r * s], fill=color)
        if p > 0.4:
            d.line([(x - r * 0.45, y), (x - r * 0.1, y + r * 0.4), (x + r * 0.5, y - r * 0.35)], fill=(14, 20, 36), width=6)
    return fn


def cross(x, y, r=26, color=RED):
    def fn(d, img, p, t):
        s = pop(p)
        d.ellipse([x - r * s, y - r * s, x + r * s, y + r * s], fill=color)
        if p > 0.4:
            d.line([(x - r * 0.4, y - r * 0.4), (x + r * 0.4, y + r * 0.4)], fill=(14, 20, 36), width=6)
            d.line([(x - r * 0.4, y + r * 0.4), (x + r * 0.4, y - r * 0.4)], fill=(14, 20, 36), width=6)
    return fn


def magnifier(x, y, r=50, color=ACCENT):
    def fn(d, img, p, t):
        s = pop(p)
        rr = r * s
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=color, width=10)
        d.line([(x + rr * 0.7, y + rr * 0.7), (x + rr * 1.5, y + rr * 1.5)], fill=color, width=14)
    return fn


def sparkle(x, y, color=BLUE, n=6, r=36):
    """small 'AI' burst"""
    def fn(d, img, p, t):
        for k in range(n):
            a = k * 2 * math.pi / n + t * 0.8
            d.line([(x + math.cos(a) * r * 0.35, y + math.sin(a) * r * 0.35), (x + math.cos(a) * r * p, y + math.sin(a) * r * p)], fill=color, width=5)
        d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=color)
    return fn
