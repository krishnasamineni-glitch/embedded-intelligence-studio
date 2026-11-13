#!/usr/bin/env python3
# voice_api.py - make the narration in YOUR cloned voice with the ElevenLabs API (no GPU needed, no new recording).
#
# Your API key is never written into any file. Put it in the terminal for this session only (PowerShell):
#   $env:ELEVENLABS_API_KEY="paste-your-key-here"
#
# Usage:
#   python voice_api.py clone episodes/rv01_en/audio_old     # once: upload about 3 minutes of your own recordings,
#                                                            # saves the new voice id in voice/voice_id.txt
#   python voice_api.py speak episodes/rv01_en --check       # count the characters (= credits) without calling the API
#   python voice_api.py speak episodes/rv01_en               # writes audio/scene_01.mp3 ... (existing files are kept)
#   python voice_api.py speak episodes/rv01_en --only 16     # make ONLY scene 16 (a cheap test before the full run)
#   python voice_api.py speak episodes/rv01_en --redo 3,7    # make scenes 3 and 7 again (plus any scene still missing)
# Then, as usual:
#   python tts.py episodes/rv01_en        (engine "files": joins the scene files and writes the timings)
#   python build.py episodes/rv01_en
#
# Optional settings in episode.json: "api_model" (default eleven_multilingual_v2),
#   "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.0}
# Pronunciation fixes from lexicon_api.txt and the episode's lexicon.txt are applied (subtitles keep the original words).
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid

from tts import apply_lexicon, load_lexicon, parse_script

HERE = pathlib.Path(__file__).resolve().parent
BASE = os.environ.get('ELEVENLABS_BASE_URL', 'https://api.elevenlabs.io').rstrip('/')
VOICE_FILE = HERE / 'voice' / 'voice_id.txt'
AUDIO_EXT = ('.wav', '.mp3', '.m4a', '.mp4', '.flac', '.ogg', '.aac', '.opus', '.webm', '.wma')
MAX_SAMPLE_SECONDS = 180


def die(msg):
    raise SystemExit('ERROR: ' + msg)


def api_key():
    k = os.environ.get('ELEVENLABS_API_KEY', '').strip()
    if not k:
        die('no API key. In PowerShell type:  $env:ELEVENLABS_API_KEY="your-key"  (with the quotes), then run again.')
    return k


def request(method, path, key, body=None, headers=None):
    req = urllib.request.Request(BASE + path, data=body, method=method, headers={'xi-api-key': key, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:600]
        hint = {401: 'the API key is wrong or expired.',
                402: 'your plan has no credits left, or does not include this feature (voice cloning needs a paid plan).',
                403: 'this feature is not allowed on your plan.',
                422: 'the service did not accept the request (see the details).',
                429: 'too many requests or out of quota: wait a minute and run again (finished scenes are kept).'}
        die(f'the voice service answered {e.code}: {hint.get(e.code, "")}\n{detail}')
    except urllib.error.URLError as e:
        die(f'could not reach the voice service ({e.reason}). Check the internet connection.')


def multipart(fields, files):
    b = uuid.uuid4().hex
    out = bytearray()
    for name, value in fields.items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
    for name, (fname, data, ctype) in files:
        out += (f'--{b}\r\nContent-Disposition: form-data; name="{name}"; filename="{fname}"\r\n'
                f'Content-Type: {ctype}\r\n\r\n').encode() + data + b'\r\n'
    out += f'--{b}--\r\n'.encode()
    return bytes(out), f'multipart/form-data; boundary={b}'


def cmd_clone(argv):
    if not argv:
        die('give the folder with your own recordings, e.g.  python voice_api.py clone episodes/rv01_en/audio_old')
    folder = pathlib.Path(argv[0])
    if not folder.is_dir():
        die(f'folder not found: {folder}')
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in AUDIO_EXT)
    if not files:
        die(f'no audio files in {folder}')
    name = argv[argv.index('--name') + 1] if '--name' in argv else 'My narration voice'
    key = api_key()
    with tempfile.TemporaryDirectory() as td:
        lst = pathlib.Path(td) / 'list.txt'
        lst.write_text(''.join(f"file '{p.resolve().as_posix()}'\n" for p in files), encoding='utf-8')
        sample = pathlib.Path(td) / 'sample.mp3'
        r = subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst),
                            '-t', str(MAX_SAMPLE_SECONDS), '-ac', '1', '-ar', '44100', '-b:a', '128k', str(sample)],
                           capture_output=True, text=True)
        if r.returncode != 0 or not sample.exists():
            die('ffmpeg could not join your recordings:\n' + r.stderr[-500:])
        body, ctype = multipart({'name': name, 'remove_background_noise': 'true',
                                 'description': 'My own voice, recorded by me, for my own videos.'},
                                [('files', ('sample.mp3', sample.read_bytes(), 'audio/mpeg'))])
    print(f'Uploading about {MAX_SAMPLE_SECONDS // 60} minutes from {len(files)} files in {folder} ...')
    res = json.loads(request('POST', '/v1/voices/add', key, body, {'Content-Type': ctype}))
    vid = res.get('voice_id')
    if not vid:
        die(f'no voice id in the answer: {res}')
    VOICE_FILE.parent.mkdir(exist_ok=True)
    VOICE_FILE.write_text(vid + '\n', encoding='utf-8')
    print(f'Done. Voice id {vid} saved in {VOICE_FILE}')
    if res.get('requires_verification'):
        print('NOTE: the service asks you to verify this voice on its website before you can use it.')


def cmd_speak(argv):
    if not argv:
        die('give the episode folder, e.g.  python voice_api.py speak episodes/rv01_en')
    ep = pathlib.Path(argv[0])
    cfg = json.loads((ep / 'episode.json').read_text(encoding='utf-8-sig')) if (ep / 'episode.json').exists() else {}
    scenes = parse_script(ep / 'script.txt')
    lex = load_lexicon(HERE / 'lexicon_api.txt', ep / 'lexicon.txt')
    texts = [apply_lexicon(s['text'], lex) for s in scenes]
    redo = set()
    if '--redo' in argv:
        try:
            redo = {int(x) for x in argv[argv.index('--redo') + 1].split(',') if x}
        except (IndexError, ValueError):
            die('--redo needs scene numbers, e.g.  --redo 3,7')
    out_dir = ep / 'audio'
    todo = [i for i in range(1, len(scenes) + 1) if i in redo or not (out_dir / f'scene_{i:02d}.mp3').exists()]
    if '--only' in argv:
        try:
            only = {int(x) for x in argv[argv.index('--only') + 1].split(',') if x}
        except (IndexError, ValueError):
            die('--only needs scene numbers, e.g.  --only 16')
        bad = [n for n in only if not 1 <= n <= len(scenes)]
        if bad:
            die(f'--only {bad}: this script has {len(scenes)} scenes.')
        todo = sorted(only)
    chars = sum(len(texts[i - 1]) for i in todo)
    print(f'{len(scenes)} scenes in the script; to make now: {len(todo)} scenes, {chars} characters (about {chars} credits).')
    if '--check' in argv or not todo:
        return
    key = api_key()
    vid = argv[argv.index('--voice') + 1] if '--voice' in argv else (
        VOICE_FILE.read_text(encoding='utf-8').strip() if VOICE_FILE.exists() else '')
    if not vid:
        die('no voice id yet: run  python voice_api.py clone <folder with your recordings>  first.')
    model = cfg.get('api_model', 'eleven_multilingual_v2')
    out_dir.mkdir(exist_ok=True)
    for i in todo:
        body = {'text': texts[i - 1], 'model_id': model}
        if i > 1:
            body['previous_text'] = texts[i - 2]
        if i < len(texts):
            body['next_text'] = texts[i]
        if cfg.get('voice_settings'):
            body['voice_settings'] = cfg['voice_settings']
        audio = request('POST', f'/v1/text-to-speech/{vid}?output_format=mp3_44100_128', key,
                        json.dumps(body).encode('utf-8'), {'Content-Type': 'application/json', 'Accept': 'audio/mpeg'})
        if len(audio) < 1000:
            die(f'scene {i}: the answer is too small to be audio: {audio[:200]!r}')
        for old in out_dir.glob(f'scene_{i:02d}.*'):
            if old.suffix.lower() in AUDIO_EXT and old.suffix.lower() != '.mp3':
                old.rename(old.with_name(old.name + '.old'))   # an older recording must not be picked instead
        (out_dir / f'scene_{i:02d}.mp3').write_bytes(audio)
        print(f'  scene {i:02d}: {len(audio) // 1024} KB')
    cfg['engine'] = 'files'
    (ep / 'episode.json').write_text(json.dumps(cfg), encoding='utf-8')
    missing = [i for i in range(1, len(scenes) + 1) if not (out_dir / f'scene_{i:02d}.mp3').exists()]
    if missing:
        print(f'Made {len(todo)} scene(s). Still missing: {missing}. Run without --only to make the rest.')
        return
    print(f'Done. Next:  python tts.py {ep}   then   python build.py {ep}')


def main(argv):
    if not argv or argv[0] not in ('clone', 'speak'):
        die('use  python voice_api.py clone <folder>   or   python voice_api.py speak <episode folder>')
    (cmd_clone if argv[0] == 'clone' else cmd_speak)(argv[1:])


if __name__ == '__main__':
    main(sys.argv[1:])
