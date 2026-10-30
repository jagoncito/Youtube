#!/usr/bin/env python3
"""Verify the pinned piano cache and exercise the actual synthesis engine.

This is a technical sample/engine check, not a subjective listening review.
Requires NumPy, SoundFile and the sfizz shared library used by production.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re

import numpy as np
import soundfile as sf


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cache', required=True, type=Path)
    p.add_argument('--manifest', required=True, type=Path)
    p.add_argument('--library', required=True, type=Path)
    p.add_argument('--renderer', required=True, type=Path)
    p.add_argument('--out-dir', required=True, type=Path)
    a = p.parse_args()
    a.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(a.manifest.read_text())
    sample_info = []
    total_bytes = 0
    checked = []
    for entry in manifest['files']:
        source = a.cache / entry['path']
        data = source.read_bytes()
        assert len(data) == entry['bytes'], source
        assert hashlib.sha256(data).hexdigest() == entry['sha256'], source
        blob = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
        assert blob == entry['git_blob_sha1'], source
        total_bytes += len(data)
        checked.append(entry['path'])
        if source.suffix == '.flac':
            info = sf.info(source)
            assert (info.samplerate, info.channels, info.subtype) == (48000, 2, 'PCM_24'), source
            sample_info.append((entry['path'], info.frames / info.samplerate))
    assert len(checked) == 668 and len(sample_info) == 641
    assert total_bytes == 748451483
    cache_report = {
        'schema': 'jagoncito-piano-source-verification/1',
        'instrument': manifest['instrument'], 'commit': manifest['commit'],
        'source_files_verified': len(checked), 'sample_files_verified': len(sample_info),
        'source_bytes': total_bytes, 'all_sha256_match': True,
        'all_git_blob_sha1_match': True,
        'license': manifest['license'], 'license_url': manifest['license_url'],
        'subjective_listening': False,
    }
    (a.out_dir / 'cache-verification-007.json').write_text(json.dumps(cache_report, indent=2) + '\n')
    # The attack names are A0/C1/D#1/F#1 etc.; the basename distinguishes
    # attack layers from pedal, hammer and string-release sample names.
    attacks = [(name, seconds) for name, seconds in sample_info
               if re.fullmatch(r'[A-G]#?\d+v\d+\.flac', Path(name).name)]
    assert len(attacks) == 480
    layers = sorted({int(re.search(r'v(\d+)\.flac$', name).group(1)) for name, _ in attacks})
    assert layers == list(range(1, 17))
    ranges = [(int(low), int(high)) for low, high in re.findall(
        r'lokey=(\d+) hikey=(\d+)', (a.cache / 'Data/region.txt').read_text())]
    covered = [key for low, high in ranges for key in range(low, high + 1)]
    assert covered == list(range(21, 109))
    format_report = {
        'all_samples_native_rate': 48000, 'all_samples_channels': 2,
        'all_samples_subtype': 'PCM_24', 'sample_count': len(sample_info),
        'attack_sample_count': len(attacks), 'velocity_layers': layers,
        'mapped_midi_keys': [21, 108], 'mapped_key_count': len(covered),
        'mapping_has_gaps_or_overlaps': False,
        'shortest_attack_seconds': min((seconds, Path(name).name) for name, seconds in attacks),
        'longest_attack_seconds': max((seconds, Path(name).name) for name, seconds in attacks),
        'subjective_listening': False,
    }
    (a.out_dir / 'sample-format-validation.json').write_text(json.dumps(format_report, indent=2) + '\n')

    module_spec = importlib.util.spec_from_file_location('piano_renderer', a.renderer)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    engine = module.PianoEngine(a.library)
    velocity_reports = []
    for velocity in [35, 60, 82, 108]:
        notes = [{'start': .25, 'duration': .6, 'pitch': pitch, 'velocity': velocity}
                 for pitch in [60, 64, 67, 72]]
        audio, report = engine.render(a.cache / manifest['original_sfz'],
                                      {'sample_rate': 48000, 'duration': 3., 'events': notes})
        attack = audio[round(.27 * 48000):round(.42 * 48000)].astype(np.float64)
        rms = float(np.sqrt(np.mean(attack ** 2)))
        assert np.isfinite(audio).all() and rms > 0
        velocity_reports.append({'velocity': velocity, 'attack_rms': rms,
                                 'peak': report['peak'], 'regions': report['regions'],
                                 'sample_files': report['sample_files']})
    assert all(x['attack_rms'] < y['attack_rms'] for x, y in zip(velocity_reports, velocity_reports[1:]))
    assert all(x['regions'] == 1121 and x['sample_files'] == 641 for x in velocity_reports)
    velocity_report = {
        'velocities': velocity_reports, 'attack_window_seconds': [.27, .42],
        'shared_piano_per_chord': True, 'original_sfz_unmodified': True,
        'finite': True, 'monotonic_attack_rms': True, 'subjective_listening': False,
    }
    (a.out_dir / 'velocity-response-007.json').write_text(json.dumps(velocity_report, indent=2) + '\n')
    print(json.dumps({'sources': cache_report, 'format': format_report,
                      'velocity': velocity_report}, indent=2))


if __name__ == '__main__':
    main()
