#!/usr/bin/env bash
# Post + sound + encode the PS1 'Day' short.  Usage: ./assemble_day.sh <width> <out.mp4>
set -euo pipefail
cd "$(dirname "$0")/../.."
W=${1:-540}
OUTF=${2:-out/ps1/day_draft.mp4}
rm -rf out/ps1day/post
python3 blender/ps1/post_day.py out/ps1day out/ps1day/post "$W"
python3 blender/ps1/sound_day.py out/ps1day out/ps1day/sound.wav
ffmpeg -v error -y -framerate 30 -i out/ps1day/post/%04d.png -i out/ps1day/sound.wav \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium -tune animation -c:a aac -b:a 192k -shortest "$OUTF"
echo "$OUTF"
