#!/usr/bin/env bash
set -euo pipefail
video_dir=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$video_dir"
temp_dir=$(mktemp -d /tmp/jagoncito-video.XXXXXX)
trap 'rm -rf -- "$temp_dir"' EXIT
audio_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 audio.wav)
# 1080p, 24 fps, imagen fija para no distraer. El audio empieza con el vídeo.
# El WAV es el único máster de audio entregado; AAC se utiliza dentro del MP4.
ffmpeg -hide_banner -loglevel warning -nostdin -y \
  -loop 1 -framerate 24 -i imagen.png -i audio.wav \
  -map 0:v:0 -map 1:a:0 \
  -vf 'scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080,setsar=1' \
  -c:v libx264 -threads 3 -preset fast -tune stillimage -crf 22 \
  -pix_fmt yuv420p -profile:v high -level:v 4.1 \
  -c:a aac -b:a 192k -ar 44100 \
  -metadata title='Chopin Prelude Op. 28 No. 4 | Quiet Piano for an Autumn Evening' \
  -metadata artist='Jagoncito' -metadata comment='New digital piano interpretation; three complete performances.' \
  -movflags +faststart -shortest "$temp_dir/encode.mp4"
# Cerrar el contenedor con el final del WAV, sin recodificar vídeo ni audio.
ffmpeg -hide_banner -loglevel warning -nostdin -y \
  -i "$temp_dir/encode.mp4" -map 0 -c copy -t "$audio_duration" \
  -movflags +faststart "$temp_dir/video.mp4"
mv -- "$temp_dir/video.mp4" video.mp4
