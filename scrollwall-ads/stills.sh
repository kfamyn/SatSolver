#!/usr/bin/env bash
# Usage: ./stills.sh <CompositionId> frame1 frame2 ...  -> out/<id>-sheet.png
set -e
cd "$(dirname "$0")"
id=$1; shift
B=${BROWSER:-/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell}
mkdir -p out/stills
files=()
for fr in "$@"; do
  npx remotion still "$id" "out/stills/$id-$fr.png" --frame="$fr" --gl=swangle --browser-executable="$B" --log=error >/dev/null
  files+=("out/stills/$id-$fr.png")
done
montage "${files[@]}" -tile ${#files[@]}x1 -geometry 360x640+4+4 -background '#333' "out/$id-sheet.png"
echo "out/$id-sheet.png"
