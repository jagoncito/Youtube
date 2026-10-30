#!/usr/bin/env python3
"""Fully decode the 007 cycle and measure its seam and actual local motion.

These are technical/visual measurements, not an audio audition. Animal and
architecture masks are separately checked to remain essentially unchanged.
"""
from pathlib import Path
import argparse
import json
import subprocess

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video', type=Path)
    ap.add_argument('--config', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    config = json.loads(args.config.read_text())
    metadata = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(args.video)
    ]))
    video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
    subprocess.run([
        'ffmpeg', '-v', 'error', '-xerror', '-nostdin', '-i', str(args.video),
        '-map', '0:v:0', '-f', 'null', '-'
    ], check=True)
    selection = "select='lt(n,8)+eq(n,360)+eq(n,384)+eq(n,720)+eq(n,1200)+gte(n,1432)',scale=960:540:flags=area,format=gray"
    raw = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-nostdin', '-i', str(args.video), '-vf', selection,
        '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'
    ])
    frames = np.frombuffer(raw, np.uint8).reshape(-1, 540, 960).astype(np.float32)
    assert len(frames) == 20, len(frames)
    differences = np.r_[
        abs(np.diff(frames[:8], axis=0)).mean(axis=(1, 2)),
        abs(np.diff(frames[-8:], axis=0)).mean(axis=(1, 2)),
    ]
    ordinary = float(np.median(differences))
    seam = float(abs(frames[-1] - frames[0]).mean())

    def region(array, rect):
        x, y, width, height = rect
        return array[y // 2:(y + height) // 2, x // 2:(x + width) // 2]

    change_15s = abs(frames[8] - frames[0])
    foliage = {
        p['name']: float(region(change_15s, p['rectangle']).mean())
        for p in config['foliage_patches']
    }
    protected = {
        name: float(region(change_15s, rect).mean())
        for name, rect in config['protected_regions_1920x1080'].items()
    }
    # This open-air rectangle is clear of both canopy-motion patches and animals.
    # 15s and16s contain the first drifting leaf in different positions.
    leaf_change = region(abs(frames[9] - frames[8]), [1160, 210, 330, 300])
    leaf_pixels = int((leaf_change > 2).sum())
    report = {
        'file': args.video.name,
        'full_decode': 'passed',
        'frames': int(video['nb_frames']),
        'width': video['width'], 'height': video['height'],
        'duration_seconds': float(metadata['format']['duration']),
        'codec': video['codec_name'], 'profile': video['profile'],
        'pixel_format': video['pix_fmt'], 'fps': video['avg_frame_rate'],
        'audio_streams': sum(s['codec_type'] == 'audio' for s in metadata['streams']),
        'loop_boundary_gray_mae': seam,
        'adjacent_gray_mae_median': ordinary,
        'boundary_criterion': 'boundary <= max(0.15, 4 * ordinary adjacent MAE)',
        'loop_boundary_passed': seam <= max(.15, 4 * ordinary),
        'foliage_change_15s_gray_mae': foliage,
        'protected_regions_change_15s_gray_mae': protected,
        'drifting_leaf_pixels_changed_gt2_15s_to16s_half_resolution': leaf_pixels,
        'environment_motion_present': all(value > .05 for value in foliage.values()) and leaf_pixels >= 12,
        'characters_animated': False, 'architecture_animated': False,
        'existing_near_dragon_leaf_animated': False,
        'subjective_audition_performed': False,
    }
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    assert report['loop_boundary_passed'], 'Visual loop seam exceeds fixed criterion'
    assert report['environment_motion_present'], 'Required vine/leaf motion is not measured'
    assert all(value < .2 for value in protected.values()), 'A protected region changes significantly'
    assert (report['width'], report['height'], report['frames']) == (1920, 1080, 1440)
    assert report['fps'] == '24/1' and report['audio_streams'] == 0


if __name__ == '__main__':
    main()
