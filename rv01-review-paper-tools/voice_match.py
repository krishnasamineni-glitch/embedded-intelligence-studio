#!/usr/bin/env python3
# voice_match.py - bring cloned narration closer to YOUR recording, without any credits (pure signal processing).
#
# It measures your own recording (the reference) and each cloned scene, then fixes three things that a clone
# often gets wrong and that CAN be fixed afterwards:
#   1. speed    : clones usually talk faster than you  -> slowed down with the pitch kept (ffmpeg atempo)
#   2. tone (EQ): the clone's sound colour is matched to yours, band by band (limited to +-3 dB, so it stays natural)
#   3. loudness : the clone is brought to the same level as your recording
# It can NOT change the accent or the way words are stressed - that is decided when the audio is generated.
#
# Usage:
#   python voice_match.py profile voice_sample2/new_voice.mp4 episodes/rv01_en/audio    # only measure, write voice/voice_profile.*
#   python voice_match.py apply   voice_sample2/new_voice.mp4 episodes/rv01_en/audio    # measure + write scene_NN.wav (matched)
#   python voice_match.py apply   voice_sample2/new_voice.mp4 episodes/rv01_en/audio --speed 0.9   # your own speed factor
#   python voice_match.py apply   ... --pitch            # ALSO raise/lower the pitch to yours (off by default; listen first)
#   python voice_match.py apply   ... --pitch-hz 135     # bring every scene to exactly this pitch (per-scene ratio)
#   python voice_match.py apply   ... --no-speed | --no-eq | --no-loudness        # switch a step off
#
# The matched files are written as scene_NN.wav next to the scene_NN.mp3 files; tts.py prefers .wav, so the next
# "python tts.py <episode>" uses them automatically. The .mp3 originals are kept. To go back to the originals,
# delete the .wav files.
import json
import pathlib
import subprocess
import sys
import tempfile

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
BANDS = [(0, 300), (300, 600), (600, 1200), (1200, 2500), (2500, 4000), (4000, 6000), (6000, 8000)]
BAND_CENTRES = [150, 450, 900, 1800, 3200, 5000, 7000]
MAX_EQ_DB = 3.0
AUDIO_EXT = ('.wav', '.mp3', '.m4a', '.mp4', '.flac', '.ogg', '.aac')


def die(msg):
    raise SystemExit('ERROR: ' + msg)


def load16k(path):
    """Any audio -> mono float32 at 16 kHz (via ffmpeg)."""
    r = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(path), '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                       capture_output=True)
    if r.returncode != 0 or len(r.stdout) < 64000:
        die(f'ffmpeg could not read {path}')
    return np.frombuffer(r.stdout, dtype=np.float32)


def measure(y, sr=16000):
    """Pitch, pauses, band energies and level of one recording."""
    import librosa
    f0, _, _ = librosa.pyin(y, fmin=70, fmax=350, sr=sr, frame_length=1024)
    f0 = f0[~np.isnan(f0)]
    S = np.abs(librosa.stft(y, n_fft=1024))
    rms = librosa.feature.rms(S=S, frame_length=1024)[0]
    voiced = rms > 0.02
    if voiced.sum() < 10:
        die('the recording is too quiet to measure')
    freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)
    P = (S[:, voiced] ** 2).mean(axis=1)
    bands = [10 * np.log10(P[(freqs >= lo) & (freqs < hi)].sum() / P.sum()) for lo, hi in BANDS]
    iv = librosa.effects.split(y, top_db=35)
    speech = sum(b - a for a, b in iv) / sr
    gaps = [(iv[i + 1][0] - iv[i][1]) / sr for i in range(len(iv) - 1)]
    gaps = [g for g in gaps if g > 0.15]
    dur = len(y) / sr
    syl = syllable_rate(y, sr, iv)
    return {
        'duration_s': round(dur, 2),
        'syllables_per_second': round(syl, 2),
        'speech_fraction': round(speech / dur, 3),
        'pauses_per_minute': round(len(gaps) / (dur / 60), 1),
        'median_pause_s': round(float(np.median(gaps)), 2) if gaps else 0.0,
        'pitch_median_hz': round(float(np.median(f0)), 1),
        'pitch_std_hz': round(float(np.std(f0)), 1),
        'pitch_range_p10_p90_hz': [round(float(np.percentile(f0, 10)), 1), round(float(np.percentile(f0, 90)), 1)],
        'spectral_centroid_hz': round(float(np.mean(librosa.feature.spectral_centroid(S=S, sr=sr)[0][voiced])), 0),
        'band_energy_db': {f'{lo}-{hi}': round(float(b), 2) for (lo, hi), b in zip(BANDS, bands)},
        'level_rms_dbfs': round(float(20 * np.log10(np.sqrt((y ** 2).mean()) + 1e-9)), 2),
        'speech_level_rms_dbfs': round(float(20 * np.log10(np.sqrt(np.mean(np.concatenate([y[a:b] for a, b in iv]) ** 2)) + 1e-9)), 2),
    }


def syllable_rate(y, sr, iv):
    """Rough syllables per second of speech (energy peaks in the 300-2500 Hz band); no transcript needed."""
    import librosa
    from scipy.signal import butter, sosfiltfilt, find_peaks
    sos = butter(4, [300, 2500], btype='band', fs=sr, output='sos')
    env = librosa.feature.rms(y=sosfiltfilt(sos, y).astype(np.float32), frame_length=400, hop_length=160)[0]  # 10 ms hops
    env = np.convolve(env, np.ones(5) / 5, mode='same')
    peaks, _ = find_peaks(env, distance=10, prominence=np.max(env) * 0.08)   # at least 100 ms apart
    speech = sum(b - a for a, b in iv) / sr
    return len(peaks) / speech if speech > 0 else 0.0


def scene_files(folder):
    out = []
    for p in sorted(pathlib.Path(folder).iterdir()):
        if p.suffix.lower() == '.mp3' and p.stem.startswith('scene_') and p.stem[6:].isdigit():
            out.append(p)
    return out


def main(argv):
    if len(argv) < 3 or argv[0] not in ('profile', 'apply'):
        die('usage:  python voice_match.py profile|apply <your recording> <folder with scene_NN.mp3> [--speed 0.85]')
    mode, ref_path, folder = argv[0], pathlib.Path(argv[1]), pathlib.Path(argv[2])
    if not ref_path.exists():
        die(f'reference recording not found: {ref_path}')
    scenes = scene_files(folder)
    if not scenes:
        die(f'no scene_NN.mp3 files in {folder}')
    speed = None
    if '--speed' in argv:
        try:
            speed = float(argv[argv.index('--speed') + 1])
        except (IndexError, ValueError):
            die('--speed needs a number, e.g. --speed 0.85')
        if not 0.5 <= speed <= 1.5:
            die('--speed must be between 0.5 and 1.5')

    print(f'Measuring your recording {ref_path} ...')
    ref = measure(load16k(ref_path))
    print('Measuring the cloned scenes ...')
    clones = {p.name: measure(load16k(p)) for p in scenes}
    allc = np.array([[c['band_energy_db'][k] for k in c['band_energy_db']] for c in clones.values()])
    clone_bands = allc.mean(axis=0)
    ref_bands = np.array(list(ref['band_energy_db'].values()))
    eq = np.clip(ref_bands - clone_bands, -MAX_EQ_DB, MAX_EQ_DB)
    clone_pitch = float(np.mean([c['pitch_median_hz'] for c in clones.values()]))
    clone_speech = float(np.mean([c['speech_fraction'] for c in clones.values()]))
    clone_level = float(np.mean([c['speech_level_rms_dbfs'] for c in clones.values()]))
    gain_db = ref['speech_level_rms_dbfs'] - clone_level
    # speed: compare syllables per second (yours vs the clone's); never slow down below 0.75 or speed up
    clone_syl = float(np.mean([c['syllables_per_second'] for c in clones.values()]))
    auto_speed = round(max(0.75, min(1.0, ref['syllables_per_second'] / clone_syl)), 2)
    use_speed = speed if speed is not None else auto_speed

    profile = {
        'note': 'Measured from your own recording (reference) and the cloned scenes. Pitch in Hz, levels in dBFS. '
                'Use the reference recording itself as the voice sample for any other TTS / cloning tool.',
        'reference_recording': str(ref_path),
        'reference': ref,
        'clone_average': {'pitch_median_hz': round(clone_pitch, 1), 'syllables_per_second': round(clone_syl, 2), 'speech_fraction': round(clone_speech, 3),
                          'speech_level_rms_dbfs': round(clone_level, 2),
                          'band_energy_db': {k: round(float(v), 2) for k, v in zip(ref['band_energy_db'], clone_bands)}},
        'clone_scenes': clones,
        'correction': {'eq_db_per_band': {f'{c} Hz': round(float(g), 2) for c, g in zip(BAND_CENTRES, eq)},
                       'gain_db': round(gain_db, 2), 'speed_factor': use_speed,
                       'pitch_ratio_ref_over_clone': round(ref['pitch_median_hz'] / clone_pitch, 3)},
    }
    ep_json = folder.parent / 'episode.json'
    if ep_json.exists():
        try:
            cfg = json.loads(ep_json.read_text(encoding='utf-8-sig'))
            profile['generation_settings'] = {k: cfg[k] for k in ('api_model', 'voice_settings') if k in cfg}
        except ValueError:
            pass
    vid = HERE / 'voice' / 'voice_id.txt'
    if vid.exists():
        profile['elevenlabs_voice_id'] = vid.read_text(encoding='utf-8').strip()
    out_dir = HERE / 'voice'
    out_dir.mkdir(exist_ok=True)
    (out_dir / 'voice_profile.json').write_text(json.dumps(profile, indent=2), encoding='utf-8')
    lines = ['VOICE PROFILE (measured)', '',
             f'Reference recording: {ref_path}', '',
             'YOUR VOICE (reference)                      CLONE (average)',
             f'  pitch median      {ref["pitch_median_hz"]:6.1f} Hz                  {clone_pitch:6.1f} Hz',
             f'  pitch spread (sd) {ref["pitch_std_hz"]:6.1f} Hz',
             f'  pitch range p10-p90 {ref["pitch_range_p10_p90_hz"][0]:.0f}-{ref["pitch_range_p10_p90_hz"][1]:.0f} Hz',
             f'  speech fraction   {ref["speech_fraction"]:6.2f}                     {clone_speech:6.2f}',
             f'  pauses per minute {ref["pauses_per_minute"]:6.1f}',
             f'  syllables / second {ref["syllables_per_second"]:5.2f}                     {clone_syl:5.2f}',
             f'  spectral centroid {ref["spectral_centroid_hz"]:6.0f} Hz',
             f'  speech level      {ref["speech_level_rms_dbfs"]:6.1f} dBFS              {clone_level:6.1f} dBFS', '',
             'Band energy (dB, relative):   ' + '  '.join(f'{lo}-{hi}' for lo, hi in BANDS),
             '  you   ' + '  '.join(f'{v:6.1f}' for v in ref_bands),
             '  clone ' + '  '.join(f'{v:6.1f}' for v in clone_bands), '',
             'Correction that "apply" uses:',
             '  EQ (dB): ' + ', '.join(f'{c} Hz {g:+.1f}' for c, g in zip(BAND_CENTRES, eq)),
             f'  gain {gain_db:+.1f} dB, speed factor {use_speed}',
             '', 'For a free TTS / voice-cloning tool: give it the reference recording above as the voice sample,',
             'and aim for these numbers (pitch, pauses, level). The ElevenLabs clone itself cannot be exported.']
    (out_dir / 'voice_profile.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines[4:12]))
    print(f'\nWrote {out_dir / "voice_profile.json"} and voice_profile.txt')
    if mode == 'profile':
        return

    target_hz = None
    if '--pitch-hz' in argv:
        try:
            target_hz = float(argv[argv.index('--pitch-hz') + 1])
        except (IndexError, ValueError):
            die('--pitch-hz needs a number, e.g. --pitch-hz 135')
    pitch_ratio = max(0.85, min(1.18, (target_hz or ref['pitch_median_hz']) / clone_pitch))
    do_pitch = ('--pitch' in argv or target_hz is not None) and (target_hz is not None or abs(pitch_ratio - 1.0) > 0.01)
    do_speed = '--no-speed' not in argv and abs(use_speed - 1.0) > 0.01
    do_eq = '--no-eq' not in argv
    do_loud = '--no-loudness' not in argv
    filters = []
    if do_pitch:   # pitch and tempo together, keeping the vocal-tract colour (formants) so it still sounds like the same person
        filters.append(f'rubberband=pitch={pitch_ratio:.4f}:tempo={use_speed if do_speed else 1.0}:formant=preserved:pitchq=quality')
    elif do_speed:
        filters.append(f'atempo={use_speed}')
    if do_eq:
        entries = ';'.join(f'entry({c},{g:.2f})' for c, g in zip(BAND_CENTRES, eq))
        filters.append(f"firequalizer=gain_entry='{entries}'")
    if do_loud:
        filters.append(f'volume={gain_db:.2f}dB')
    filters.append('alimiter=limit=0.95')
    chain = ','.join(filters)
    print(f'\nApplying: {chain}')
    for p in scenes:
        out = p.with_suffix('.wav')
        fchain = chain
        if do_pitch and target_hz is not None:   # each scene gets its own ratio, so all scenes land on the same pitch
            pr = max(0.85, min(1.18, target_hz / clones[p.name]['pitch_median_hz']))
            fchain = chain.replace(f'pitch={pitch_ratio:.4f}', f'pitch={pr:.4f}')
        r = subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(p), '-af', fchain, '-ac', '1', '-ar', '44100',
                            str(out)], capture_output=True, text=True)
        if r.returncode != 0:
            die(f'ffmpeg failed on {p.name}:\n{r.stderr[-500:]}')
        print(f'  {out.name}')
    print(f'Done. {len(scenes)} matched files written as .wav in {folder}. Next:  python tts.py {folder.parent}')


if __name__ == '__main__':
    main(sys.argv[1:])
