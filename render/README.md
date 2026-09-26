# physical-ai.webp build

The header animation is a real WebGL render (Three.js: PBR materials, an
env-mapped glass shell over a glowing wireframe core, bloom post-processing),
not a hand-drawn SVG or a stock GIF — rendered offline in headless Chrome
and exported as a looping animated WebP, since GitHub READMEs can't host a
live WebGL canvas.

This folder is only needed to *regenerate* `physical-ai.webp` — the profile
README just references the committed file directly.

## Regenerating

```bash
cd render
npm install
node capture.js       # renders 60 deterministic frames to frames/*.png
python3 assemble.py   # combines them into ../physical-ai.webp
```

`scene.html` exposes `window.renderFrame(t)` for `t` in `[0, 1)` — one full
loop — so frames are captured at exact animation positions rather than
real wall-clock time, guaranteeing a seamless loop regardless of how long
each frame takes to render.
