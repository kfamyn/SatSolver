#!/usr/bin/env bash
# Post-FX + sound + encode for THE FEED.  Usage: ./assemble.sh <width> <out.mp4>
set -euo pipefail
cd "$(dirname "$0")/.."
W=${1:-540}
OUTF=${2:-out/drafts/thefeed_draft.mp4}
rm -rf out/thefeed/post
python3 blender/post.py out/thefeed out/thefeed/post "$W"
python3 blender/sound.py out/thefeed out/thefeed/sound.wav
ffmpeg -v error -y -framerate 30 -i out/thefeed/post/%04d.png -i out/thefeed/sound.wav \
  -c:v libx264 -pix_fmt yuv420p -crf 20 -preset medium -c:a aac -b:a 192k -shortest "$OUTF"
echo "$OUTF"
