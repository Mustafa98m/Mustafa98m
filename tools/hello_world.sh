#!/bin/sh
# Builds art/hello-world.webp (animated): the real Hello World globe, recorded from the-thing.dev, turning on the
# console panel that tools/bake_profile.py draws (tools/build/hello-panel.svg).
#
#   tools/hello_world.sh <frames-dir>
#
# <frames-dir> holds f000.png … one PNG per step of one 48 s turn, read straight off the site's
# canvas by tools/record_globe.cjs (Playwright with a frozen clock, so the steps are exact and the
# loop is seamless). Needs ImageMagick, img2webp (libwebp) and Google Chrome. WebP, not GIF: a GIF of
# a few hundred turning words came to 5.5 MB; lossy WebP is under half that.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
FRAMES=$1
WORK=$(mktemp -d)
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
read -r X Y SIZE W H <<EOF2
$(python3 -c "import json;d=json.load(open('$ROOT/tools/build/globe.json'));print(d['x'],d['y'],d['size'],d['w'],d['h'])")
EOF2
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-prefers-reduced-motion \
  --window-size="$W,$H" --screenshot="$WORK/panel.png" "file://$ROOT/tools/build/hello-panel.svg" 2>/dev/null
for f in "$FRAMES"/f*.png; do
  magick "$WORK/panel.png" \( "$f" -resize "${SIZE}x${SIZE}" \) -geometry "+$X+$Y" -composite "$WORK/$(basename "$f")"
done
img2webp -loop 0 -d 120 -lossy -q 70 -m 6 "$WORK"/f*.png -o "$ROOT/art/hello-world.webp" >/dev/null
rm -rf "$WORK"
ls -la "$ROOT/art/hello-world.webp"
