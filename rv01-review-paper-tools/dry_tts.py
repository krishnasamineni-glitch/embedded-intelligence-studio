# dry_tts.py - test the layout and the length WITHOUT any voice model.
# Usage: python dry_tts.py episodes/rv01_en [words per second]   (default: 2.5 for English, 2.2 for Telugu)
# It writes a silent narration.wav and timings.json (the same output format as tts.py), so you can run build.py
# straight away and see how long the video will be and how every scene looks.
import sys, json, pathlib, wave

SR = 24000
PAUSE = 0.35


def parse_script(path):
    scenes = []
    for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '||' not in line:
            raise SystemExit(f'script line {n}: the format must be  visual || narration')
        visual, text = [s.strip() for s in line.split('||', 1)]
        scenes.append({'visual': visual, 'text': text})
    return scenes


def main(ep_dir, wps=None):
    ep = pathlib.Path(ep_dir)
    cfg = json.loads((ep / 'episode.json').read_text(encoding='utf-8')) if (ep / 'episode.json').exists() else {}
    if wps is None:
        wps = 2.5 if cfg.get('lang') == 'en' else 2.2
    scenes = parse_script(ep / 'script.txt')
    t, total_words = 0.0, 0
    for sc in scenes:
        words = len(sc['text'].split())
        total_words += words
        dur = max(2.0, words / wps)
        sc['start'], sc['end'] = round(t, 3), round(t + dur, 3)
        t += dur + PAUSE
    with wave.open(str(ep / 'narration.wav'), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b'\x00\x00' * int(SR * t))
    out = {'pause': PAUSE, 'scenes': scenes}
    (ep / 'timings.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(scenes)} scenes, {total_words} words, estimated length {t / 60:.1f} minutes (at {wps} words per second)')


if __name__ == '__main__':
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else None)
