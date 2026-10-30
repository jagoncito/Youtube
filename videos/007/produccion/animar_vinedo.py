#!/usr/bin/env python3
"""Create the new 007 vineyard's 60-second environmental video loop.

FFmpeg video effects only. No image is retouched by this script. The camera,
landscape, architecture, dragon and mouse remain still. Only the explicitly
masked vine foliage moves; three newly drawn autumn leaves drift past.
"""
from pathlib import Path
import argparse
import json
import math
import os
import subprocess

W, H, FPS, PERIOD = 1920, 1080, 24, 60


def stamp(seconds):
    n = round(seconds * 100)
    return f'{n // 360000}:{n // 6000 % 60:02d}:{n % 6000 // 100:02d}.{n % 100:02d}'


def falling_leaves():
    """Original vector leaf drawings, with continuous position/rotation paths.

    Each leaf is invisible well before the cycle boundary. The image's existing
    leaf near the dragon is not animated or replaced. No animal motion is added.
    """
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Leaf,DejaVu Sans,12,&H006398BB,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    # A small irregular autumn leaf and a narrow stem, drawn for this video.
    leaf = ('m -10 0 b -7 -1 -10 -4 -5 -4 l -6 -7 -2 -6 '
            'b 0 -6 0 -10 2 -10 l 3 -6 7 -7 6 -3 '
            'b 12 -4 9 -1 12 0 b 8 0 9 4 5 3 l 4 7 1 5 '
            'b -2 7 -3 4 -4 3 l -8 3 -7 1 -10 0 '
            'm 1 1 l -2 8 -3 8 0 0')
    events = []
    # Deliberately quiet intervals; none crosses a character or basket.
    paths = [
        dict(start=10., length=10., x=1190., y=240., dx=116., dy=132., phase=.2, scale=66, color='537FA6'),
        dict(start=30., length=12., x=1490., y=180., dx=-86., dy=170., phase=1.0, scale=78, color='4C86AF'),
        dict(start=47., length=10., x=1310., y=360., dx=105., dy=120., phase=2.1, scale=61, color='4E80A6'),
    ]
    for p in paths:
        steps = round(p['length'] * 4)  # 250 ms path intervals, interpolated by ASS.

        def point(f):
            x = p['x'] + p['dx'] * f + 14 * math.sin(2 * math.pi * f + p['phase'])
            y = p['y'] + p['dy'] * f + 3 * math.sin(4 * math.pi * f)
            angle = 18 * math.sin(2 * math.pi * f + p['phase']) + 85 * f
            alpha = round(255 - 186 * math.sin(math.pi * f) ** .8)
            width = 75 + 25 * math.cos(2 * math.pi * f + p['phase']) ** 2
            return x, y, angle, alpha, width

        for k in range(steps):
            f0, f1 = k / steps, (k + 1) / steps
            t0, t1 = p['start'] + f0 * p['length'], p['start'] + f1 * p['length']
            x0, y0, r0, a0, w0 = point(f0)
            x1, y1, r1, a1, w1 = point(f1)
            ms = round((t1 - t0) * 1000)
            tag = (
                f'{{\\an7\\p1\\bord0\\shad0\\blur0.45\\1c&H{p["color"]}&'
                f'\\fscx{p["scale"] * w0 / 100:.3f}\\fscy{p["scale"]}'
                f'\\frz{r0:.3f}\\1a&H{a0:02X}&'
                f'\\t(0,{ms},\\frz{r1:.3f}\\1a&H{a1:02X}&\\fscx{p["scale"] * w1 / 100:.3f})'
                f'\\move({x0:.3f},{y0:.3f},{x1:.3f},{y1:.3f})}}'
            )
            events.append(f'Dialogue: 1,{stamp(t0)},{stamp(t1)},Leaf,,0,0,0,,{tag}{leaf}')
    return header + '\n'.join(events) + '\n'


def make_filters(ass, patches):
    n = len(patches)
    split = ''.join(f'[p{k}]' for k in range(n))
    fs = [
        '[0:v]scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,'
        f'crop=1920:1080,setsar=1,format=yuv420p,split={n + 1}[bg]{split}'
    ]
    previous = 'bg'
    for k, p in enumerate(patches):
        x, y, w, h = p['rectangle']
        cx, cy, rx, ry = p['mask_center_radii']
        opacity = p.get('alpha', 180)
        fs.extend([
            f'[p{k}]crop={w}:{h}:{x}:{y}[leaf{k}]',
            f"nullsrc=s={w // 4}x{h // 4}:r=24:d=60,format=gray,"
            f"geq=lum='128+1.8*sin(2*PI*T/20+{k * .7})+0.6*sin(2*PI*(Y/43+T/30))',"
            f'scale={w}:{h}:flags=bilinear[xmap{k}]',
            f"nullsrc=s={w // 4}x{h // 4}:r=24:d=60,format=gray,"
            f"geq=lum='128+1.3*sin(2*PI*T/30+{.6 + k * .7})+0.4*cos(2*PI*(X/51+T/20))',"
            f'scale={w}:{h}:flags=bilinear[ymap{k}]',
            f'[leaf{k}][xmap{k}][ymap{k}]displace=edge=smear,format=yuva420p,'
            f"geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':"
            f"a='{opacity}*exp(-pow((X-{cx})/{rx},4)-pow((Y-{cy})/{ry},4))'[fx{k}]",
            f'[{previous}][fx{k}]overlay={x}:{y}[stage{k}]',
        ])
        previous = f'stage{k}'
    fs.append(f"[{previous}]ass=filename='{ass.as_posix()}',format=yuv420p[out]")
    return ';'.join(fs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image', type=Path, required=True)
    ap.add_argument('--config', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--seconds', type=float, default=PERIOD)
    ap.add_argument('--qp', type=int, default=1)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    config = json.loads(args.config.read_text())
    ass = args.output.parent / 'hojas-otono.ass'
    ass.write_text(falling_leaves())
    cmd = [
        'ffmpeg', '-hide_banner', '-loglevel', 'warning', '-nostdin', '-y',
        '-filter_complex_threads', '2', '-loop', '1', '-framerate', str(FPS),
        '-i', str(args.image), '-filter_complex', make_filters(ass, config['foliage_patches']),
        '-map', '[out]', '-an', '-t', str(args.seconds), '-c:v', 'libx264',
        '-threads', '3', '-preset', 'fast', '-qp', str(args.qp), '-profile:v', 'high',
        '-g', str(10 * FPS), '-keyint_min', str(10 * FPS), '-sc_threshold', '0',
        '-flags', '+cgop', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(args.output),
    ]
    cache = args.output.parent / 'font-cache'
    cache.mkdir(exist_ok=True)
    subprocess.run(cmd, check=True, env=dict(os.environ, XDG_CACHE_HOME=str(cache)))
    config.update({
        'period_seconds': PERIOD, 'fps': FPS, 'width': W, 'height': H,
        'source_artwork': args.image.name, 'qp': args.qp,
        'effects': ['local periodic vine-foliage displacement', 'three new drifting vector autumn leaves'],
        'characters_animated': False, 'camera_animated': False,
        'architecture_animated': False, 'existing_near_dragon_leaf_animated': False,
        'ambient_audio': False,
    })
    (args.output.parent / 'escena-config.json').write_text(json.dumps(config, indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
