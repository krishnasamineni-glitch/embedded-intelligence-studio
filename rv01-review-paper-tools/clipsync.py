#!/usr/bin/env python3
# clipsync.py - re-cut a screen recording so that what is on screen follows the narration, sentence by sentence.
#
# A storyboard (JSON) lists segments in narration order. Each segment is one of:
#   {"play": "src.mp4", "from": 1.0, "to": 5.8, "dur": 4.81}         # play part of the recording (sped up/slowed to fit "dur")
#   {"hold": "src.mp4", "at": 6.0, "dur": 4.6,                        # freeze one frame for "dur" seconds, and optionally
#        "zoom": [1.0, 1.6], "focus": [0.15, 0.33],                   #   zoom from 1.0x to 1.6x towards a point (fractions of the frame)
#        "box": [0, 195, 280, 275]}                                   #   highlight a region (pixel box in the recording's own size)
# Output: 1920x1080, 30 fps, no audio. The total length equals the sum of "dur" (= the narration length of that scene).
#
# Usage:  python clipsync.py storyboard.json out.mp4
import json
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

W, H, FPS = 1920, 1080, 30
PAD = 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('ffmpeg failed:\n' + ' '.join(cmd) + '\n' + r.stderr[-800:])


def frame_at(src, t, png):
    run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{t:.3f}', '-i', src, '-frames:v', '1', str(png)])


def fit_1920(img):
    """Scale a frame to fit 1920x1080 and pad with black (same geometry as build.py), return (image, scale, dx, dy)."""
    s = min(W / img.width, H / img.height)
    nw, nh = round(img.width * s), round(img.height * s)
    out = Image.new('RGB', (W, H), (0, 0, 0))
    dx, dy = (W - nw) // 2, (H - nh) // 2
    out.paste(img.resize((nw, nh), Image.LANCZOS), (dx, dy))
    return out, s, dx, dy


def render_hold(seg, tmp, idx):
    src = seg['hold']
    png = tmp / f'h{idx}.png'
    frame_at(src, seg['at'], png)
    img, s, dx, dy = fit_1920(Image.open(png).convert('RGB'))
    if seg.get('box'):
        x0, y0, x1, y1 = seg['box']
        d = ImageDraw.Draw(img, 'RGBA')
        b = [dx + x0 * s - 10, dy + y0 * s - 8, dx + x1 * s + 10, dy + y1 * s + 8]
        d.rounded_rectangle(b, 10, outline=(255, 193, 7, 255), width=6)
        d.rounded_rectangle(b, 10, fill=(255, 193, 7, 28))
    big = tmp / f'h{idx}_1920.png'
    img.save(big)
    n = max(1, round(seg['dur'] * FPS))
    zf, zt = seg.get('zoom', [1.0, 1.0])
    fx, fy = seg.get('focus', [0.5, 0.5])
    # zoompan: zoom from zf to zt over n frames, keeping the focus point in view
    vf = (f"zoompan=z='{zf}+({zt}-{zf})*on/{n}':x='iw*{fx}-(iw/zoom)*{fx}':y='ih*{fy}-(ih/zoom)*{fy}':d={n}:s={W}x{H}:fps={FPS}")
    out = tmp / f'seg{idx:02d}.mp4'
    run(['ffmpeg', '-loglevel', 'error', '-y', '-loop', '1', '-i', str(big), '-vf', vf + ',format=yuv420p', '-frames:v', str(n),
         '-r', str(FPS), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', str(out)])
    return out


def render_play(seg, tmp, idx):
    src, t0, t1, dur = seg['play'], seg['from'], seg['to'], seg['dur']
    speed = (t1 - t0) / dur                       # >1 = faster than real time
    vf = f'setpts=PTS/{speed:.5f},{PAD},fps={FPS},format=yuv420p'
    out = tmp / f'seg{idx:02d}.mp4'
    run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{t0:.3f}', '-t', f'{t1 - t0:.3f}', '-i', src, '-vf', vf, '-an',
         '-t', f'{dur:.3f}', '-r', str(FPS), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', str(out)])
    return out


def main(argv):
    if len(argv) != 2:
        raise SystemExit('usage: python clipsync.py storyboard.json out.mp4')
    board = json.loads(pathlib.Path(argv[0]).read_text(encoding='utf-8'))
    out = pathlib.Path(argv[1])
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        parts = []
        for i, seg in enumerate(board['segments']):
            parts.append(render_hold(seg, tmp, i) if 'hold' in seg else render_play(seg, tmp, i))
            print(f'  segment {i + 1}/{len(board["segments"])}: {seg["dur"]:.2f}s')
        lst = tmp / 'list.txt'
        lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts), encoding='utf-8')
        run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(out)])
    total = sum(s['dur'] for s in board['segments'])
    print(f'Wrote {out} ({total:.1f} s)')


if __name__ == '__main__':
    main(sys.argv[1:])
