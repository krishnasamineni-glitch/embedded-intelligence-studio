# tts.py - makes narration.wav and timings.json from the script, in your cloned voice.
#
# Usage:
#   python tts.py episodes/rv01_en                 # all scenes (sentences already in the cache are not regenerated)
#   python tts.py episodes/rv01_en --redo 3,7      # regenerate only scenes 3 and 7, with a new random seed
#   python tts.py episodes/rv01_en --check         # check the script and the lexicon without loading any model
#
# Engine (in episode.json, e.g. {"lang":"en","engine":"chatterbox"}; default: en -> chatterbox, te -> indicf5):
#   chatterbox : English, clones the voice in voice/ref.wav          (pip install chatterbox-tts)
#   indicf5    : Telugu / Indian languages (ai4bharat/IndicF5); voice/ref.txt must hold the words spoken in ref.wav
#   files      : audio you made yourself in any other tool (even a web page): one file per scene in <episode>/audio/,
#                named scene_01.wav (or .mp3 .m4a .flac), scene_02.wav ... The text to paste into that tool:
#                python tts.py episodes/rv01_en --export-text      (writes audio/scene_01.txt, scene_02.txt ...)
#   cmd        : your own command, given in the environment variable TTS_CMD, for example
#                TTS_CMD='mytts --text-file {text} --ref {ref} --out {out}'   ({text} {ref} {out} are filled in)
#
# Pronunciation fixes (lexicon): lexicon_en.txt (English) or lexicon.txt (Telugu), plus lexicon.txt inside the episode folder.
#   Format: word in the script = how it should be spoken. The subtitles keep the original word.
import hashlib
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import tempfile
import wave

import numpy as np

PAUSE = 0.35        # pause between scenes (build.py reads the same value from timings.json)
SENT_GAP = 0.18     # pause between sentences inside one scene
HERE = pathlib.Path(__file__).resolve().parent


def die(msg):
    raise SystemExit(msg)


def read_wav(path):
    with wave.open(str(path), 'rb') as w:
        sr, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    if sw != 2:
        die(f'{path}: only 16-bit PCM wav is supported here.')
    a = np.frombuffer(raw, dtype='<i2').astype(np.float32) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    return a, sr


def write_wav(path, wav, sr):
    pcm = (np.clip(wav, -1.0, 1.0) * 32767.0).astype('<i2')
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def load_lexicon(*paths):
    lex = {}
    for path in paths:
        p = pathlib.Path(path)
        if p.exists():
            for line in p.read_text(encoding='utf-8').splitlines():
                if '=' in line and not line.lstrip().startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip():
                        lex[k.strip()] = v.strip()
    return lex


def apply_lexicon(text, lex):
    # longer entries first; English entries match whole words only (so the entry AI never changes MAIN)
    for k in sorted(lex, key=len, reverse=True):
        if re.fullmatch(r'[A-Za-z0-9 .\-]+', k):
            text = re.sub(r'(?<![A-Za-z0-9])' + re.escape(k) + r'(?![A-Za-z0-9])', lex[k], text)
        else:
            text = text.replace(k, lex[k])
    return text


def parse_script(path):
    scenes = []
    for n, line in enumerate(pathlib.Path(path).read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '||' not in line:
            die(f'script line {n}: format must be  visual || narration')
        visual, text = [s.strip() for s in line.split('||', 1)]
        scenes.append({'visual': visual, 'text': text})
    return scenes


def split_sentences(text, lang):
    parts = [x.strip() for x in re.split(r'(?<=[.!?])\s+', text.strip()) if x.strip()]
    out = []
    for s in parts:       # split very long sentences at a comma (never give the model more than about 300 characters)
        while len(s) > 300:
            cut = s.rfind(', ', 0, 300)
            if cut < 40:
                cut = s.rfind(' ', 0, 300)
            out.append(s[:cut + 1].strip())
            s = s[cut + 1:].strip()
        out.append(s)
    return out


# ------------------------------------------------------------------ engines
class Chatterbox:
    name = 'chatterbox'

    def __init__(self, cfg):
        try:
            import torch
            from chatterbox.tts import ChatterboxTTS
        except ImportError:
            die('chatterbox is not installed. In the venv:  pip install chatterbox-tts   (Python 3.10 or 3.11; see setup document)')
        self.torch = torch
        dev = os.environ.get('TTS_DEVICE') or ('cuda' if torch.cuda.is_available() else
                                               'mps' if getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available() else 'cpu')
        print(f'Chatterbox device: {dev}' + ('  (CPU is slow: expect minutes per sentence)' if dev == 'cpu' else ''))
        self.model = ChatterboxTTS.from_pretrained(device=dev)
        self.sr = self.model.sr
        self.ref = cfg['ref_audio']
        self.exaggeration = float(cfg.get('exaggeration', 0.5))
        self.cfg_weight = float(cfg.get('cfg_weight', 0.5))
        self.temperature = float(cfg.get('temperature', 0.8))

    def params(self):
        return f'{self.exaggeration}/{self.cfg_weight}/{self.temperature}'

    def synth(self, text, seed):
        self.torch.manual_seed(seed)
        if self.torch.cuda.is_available():
            self.torch.cuda.manual_seed_all(seed)
        wav = self.model.generate(text, audio_prompt_path=self.ref, exaggeration=self.exaggeration,
                                  cfg_weight=self.cfg_weight, temperature=self.temperature)
        return wav.squeeze().cpu().numpy().astype(np.float32)


class IndicF5:
    name = 'indicf5'

    def __init__(self, cfg):
        try:
            from transformers import AutoModel
        except ImportError:
            die('transformers is not installed (see the Telugu setup document).')
        ref_txt = pathlib.Path(cfg['ref_text_file'])
        if not ref_txt.exists():
            die(f'{ref_txt} not found: write the exact words spoken in voice/ref.wav into it.')
        self.ref, self.ref_text = cfg['ref_audio'], ref_txt.read_text(encoding='utf-8').strip()
        self.model = AutoModel.from_pretrained('ai4bharat/IndicF5', trust_remote_code=True)
        self.sr = 24000

    def params(self):
        return 'indicf5'

    def synth(self, text, seed):
        audio = self.model(text, ref_audio_path=self.ref, ref_text=self.ref_text)
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        return np.asarray(audio, dtype=np.float32)


class Cmd:
    name = 'cmd'

    def __init__(self, cfg):
        self.tmpl = os.environ.get('TTS_CMD', '')
        if not self.tmpl or '{text}' not in self.tmpl or '{out}' not in self.tmpl:
            die('engine "cmd" needs the environment variable TTS_CMD containing {text} and {out}, '
                'e.g.  TTS_CMD="mytts --text-file {text} --ref {ref} --out {out}"')
        self.ref = cfg['ref_audio']
        self.sr = None

    def params(self):
        return self.tmpl

    def synth(self, text, seed):
        with tempfile.TemporaryDirectory() as td:
            tp, op = pathlib.Path(td) / 'in.txt', pathlib.Path(td) / 'out.wav'
            tp.write_text(text, encoding='utf-8')
            args = [a.replace('{text}', str(tp)).replace('{out}', str(op)).replace('{ref}', str(self.ref))
                    for a in shlex.split(self.tmpl)]
            r = subprocess.run(args, capture_output=True, text=True)
            if r.returncode != 0 or not op.exists():
                die(f'TTS_CMD failed (exit {r.returncode}):\n{r.stderr[-800:]}')
            wav, sr = read_wav(op)
        self.sr = sr
        return wav


ENGINES = {'chatterbox': Chatterbox, 'indicf5': IndicF5, 'cmd': Cmd, 'files': None}


def find_scene_audio(ep, n):
    for ext in ('wav', 'mp3', 'm4a', 'mp4', 'flac', 'ogg', 'aac', 'opus', 'webm', 'wma'):
        f = ep / 'audio' / f'scene_{n:02d}.{ext}'
        if f.exists():
            return f
    return None


def load_scene_audio(f, sr=24000):
    """Any audio file -> mono 16-bit wav at 24 kHz (needs ffmpeg), returned as a float array."""
    with tempfile.TemporaryDirectory() as td:
        out = pathlib.Path(td) / 'x.wav'
        r = subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(f), '-ac', '1', '-ar', str(sr), str(out)],
                           capture_output=True, text=True)
        if r.returncode != 0 or not out.exists():
            die(f'ffmpeg could not read {f}:\n{r.stderr[-500:]}')
        wav, _ = read_wav(out)
    return wav, sr


def main(argv):
    if not argv or argv[0].startswith('-'):
        die(__doc__)
    ep = pathlib.Path(argv[0])
    redo = []
    if '--redo' in argv:
        try:
            redo = [int(x) for x in argv[argv.index('--redo') + 1].split(',') if x]
        except (IndexError, ValueError):
            die('--redo needs scene numbers, e.g.  --redo 3,7')
    check_only = '--check' in argv
    cfg = {}
    if (ep / 'episode.json').exists():
        cfg = json.loads((ep / 'episode.json').read_text(encoding='utf-8'))
    lang = cfg.get('lang', 'te')
    engine = cfg.get('engine') or ('chatterbox' if lang == 'en' else 'indicf5')
    if engine not in ENGINES:
        die(f'unknown engine {engine}: choose from {", ".join(ENGINES)}')
    cfg['ref_audio'] = str(cfg.get('ref_audio', 'voice/ref.wav'))
    cfg['ref_text_file'] = str(cfg.get('ref_text_file', 'voice/ref.txt'))
    if engine != 'files' and not pathlib.Path(cfg['ref_audio']).exists() and not check_only and '--export-text' not in argv:
        die(f'{cfg["ref_audio"]} not found: record your reference voice first (see the setup document).')

    scenes = parse_script(ep / 'script.txt')
    lex_global = 'lexicon_en.txt' if lang == 'en' else 'lexicon.txt'
    lex = load_lexicon(HERE / lex_global, ep / 'lexicon.txt')
    seeds_path = ep / 'seeds.json'
    seeds = json.loads(seeds_path.read_text(encoding='utf-8')) if seeds_path.exists() else {}
    for n in redo:
        if not 1 <= n <= len(scenes):
            die(f'--redo {n}: this script has {len(scenes)} scenes.')
        seeds[str(n)] = int(seeds.get(str(n), 0)) + 1
    if redo:
        seeds_path.write_text(json.dumps(seeds, indent=2), encoding='utf-8')

    if '--export-text' in argv:
        (ep / 'audio').mkdir(exist_ok=True)
        for i, sc in enumerate(scenes, 1):
            (ep / 'audio' / f'scene_{i:02d}.txt').write_text(apply_lexicon(sc['text'], lex) + '\n', encoding='utf-8')
        print(f'Wrote {len(scenes)} text files to {ep / "audio"}. Make one audio file per scene (scene_01.wav, scene_02.wav ...) in the same folder, then run:  python tts.py {ep}')
        return

    if engine == 'files':
        parts, t, sr = [], 0.0, 24000
        silence = np.zeros(int(sr * PAUSE), dtype=np.float32)
        missing = [i for i in range(1, len(scenes) + 1) if not find_scene_audio(ep, i)]
        if missing:
            die(f'engine "files": no audio file for scene(s) {missing}. Put scene_NN.wav (or .mp3/.m4a/.flac) in {ep / "audio"}.')
        for i, sc in enumerate(scenes, 1):
            wav, _ = load_scene_audio(find_scene_audio(ep, i), sr)
            dur = len(wav) / sr
            sc['start'], sc['end'] = round(t, 3), round(t + dur, 3)
            parts += [wav, silence]
            t += dur + PAUSE
        write_wav(ep / 'narration.wav', np.concatenate(parts), sr)
        (ep / 'timings.json').write_text(json.dumps({'pause': PAUSE, 'scenes': scenes}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Done: {t / 60:.1f} minutes of narration from your audio files -> {ep / "narration.wav"}')
        return

    if check_only:
        words = sum(len(s['text'].split()) for s in scenes)
        print(f'{len(scenes)} scenes, {words} words, engine={engine}, lexicon entries={len(lex)}')
        for i, sc in enumerate(scenes, 1):
            sp = apply_lexicon(sc['text'], lex)
            if sp != sc['text']:
                print(f'  scene {i} spoken as: {sp[:150]}')
        return

    ref_hash = hashlib.md5(pathlib.Path(cfg['ref_audio']).read_bytes()).hexdigest()[:8]
    cache = ep / 'cache'
    cache.mkdir(exist_ok=True)
    eng = ENGINES[engine](cfg)
    gap_pause = None
    parts, t = [], 0.0
    for i, sc in enumerate(scenes, 1):
        seed = int(seeds.get(str(i), 0))
        sent_wavs = []
        for sent in split_sentences(apply_lexicon(sc['text'], lex), lang):
            key = hashlib.md5(f'{engine}|{eng.params()}|{ref_hash}|{seed}|{sent}'.encode('utf-8')).hexdigest()[:16]
            wp = cache / f'{key}.wav'
            if wp.exists():
                wav, sr = read_wav(wp)
            else:
                print(f'  scene {i}: {sent[:60]}...')
                wav = eng.synth(sent, seed)
                sr = eng.sr
                write_wav(wp, wav, sr)
            sent_wavs.append((wav, sr))
        sr = sent_wavs[0][1]
        if any(s != sr for _, s in sent_wavs):
            die('the engine returned different sample rates; clear episodes/<name>/cache and retry.')
        if gap_pause is None or gap_pause[0] != sr:
            gap_pause = (sr, np.zeros(int(sr * SENT_GAP), dtype=np.float32), np.zeros(int(sr * PAUSE), dtype=np.float32))
        chunks = []
        for k, (w, _) in enumerate(sent_wavs):
            chunks.append(w)
            if k < len(sent_wavs) - 1:
                chunks.append(gap_pause[1])
        scene_wav = np.concatenate(chunks)
        dur = len(scene_wav) / sr
        sc['start'], sc['end'] = round(t, 3), round(t + dur, 3)
        parts += [scene_wav, gap_pause[2]]
        t += dur + PAUSE
    write_wav(ep / 'narration.wav', np.concatenate(parts), gap_pause[0])
    (ep / 'timings.json').write_text(json.dumps({'pause': PAUSE, 'scenes': scenes}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Done: {t / 60:.1f} minutes of narration -> {ep / "narration.wav"}')


if __name__ == '__main__':
    main(sys.argv[1:])
