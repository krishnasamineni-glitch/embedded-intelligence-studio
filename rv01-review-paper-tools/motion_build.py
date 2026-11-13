#!/usr/bin/env python3
# motion_build.py - render the animated scenes of an episode (episodes/<ep>/anim_scenes.py) to img/anim_NN.mp4,
# timed to the narration: the start time of every sentence is measured from audio/scene_NN.* (needs librosa).
#
# Usage:  python motion_build.py episodes/rv01_en            # all scenes defined in anim_scenes.py
#         python motion_build.py episodes/rv01_en 2,6        # only scenes 2 and 6
# Then put  clip: anim_02.mp4  in script.txt for that scene and run  python tts.py <ep>  and  python build.py <ep>.
import importlib.util
import pathlib
import re
import subprocess
import sys
import tempfile

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tts import parse_script, find_scene_audio   # noqa: E402


def sentence_times(audio, text):
    """Start time of each sentence, measured from the narration audio (pauses) with a character-count prior."""
    import librosa
    sents = [s for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s]
    with tempfile.TemporaryDirectory() as td:
        wav = pathlib.Path(td) / 'a.wav'
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(audio), '-ac', '1', '-ar', '16000', str(wav)], check=True)
        y, sr = librosa.load(str(wav), sr=16000)
    dur = len(y) / sr
    iv = librosa.effects.split(y, top_db=38)
    s0, s1 = iv[0][0] / sr, iv[-1][1] / sr
    gaps = [((iv[i][1] + iv[i + 1][0]) / 2 / sr, (iv[i + 1][0] - iv[i][1]) / sr) for i in range(len(iv) - 1)]
    gaps = [g for g in gaps if g[1] > 0.10]
    chars = np.cumsum([len(s) + 1 for s in sents])
    T = [round(float(s0), 2)]
    for c in chars[:-1]:
        t = s0 + (s1 - s0) * c / chars[-1]
        near = [g for g in gaps if abs(g[0] - t) < 0.9]
        if near:
            t = max(near, key=lambda g: g[1])[0]
        T.append(round(float(max(t, T[-1] + 0.4)), 2))
    T.append(round(dur, 2))
    return T, sents


def main(argv):
    ep = pathlib.Path(argv[0])
    only = {int(x) for x in argv[1].split(',')} if len(argv) > 1 else None
    spec = importlib.util.spec_from_file_location('anim_scenes', ep / 'anim_scenes.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    scenes = parse_script(ep / 'script.txt')
    (ep / 'img').mkdir(exist_ok=True)
    for n, fn in sorted(mod.SCENES.items()):
        if only and n not in only:
            continue
        audio = find_scene_audio(ep, n)
        if not audio:
            raise SystemExit(f'scene {n}: no audio/scene_{n:02d}.* file; make the narration first.')
        T, sents = sentence_times(audio, scenes[n - 1]['text'])
        print(f'scene {n}: {len(sents)} sentences, starts at {T[:-1]}, length {T[-1]}s')
        fn(T).render(ep / 'img' / f'anim_{n:02d}.mp4')


if __name__ == '__main__':
    main(sys.argv[1:])
