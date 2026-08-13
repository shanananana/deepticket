# DeepTicket README assets

## Files

| File | Purpose |
|------|---------|
| `logo.png` | Square logo / app icon |
| `logo.svg` | Vector logo (legacy) |
| `banner.png` | README header banner |
| `banner.svg` | Vector banner (legacy) |
| `architecture.svg` | Architecture diagram (vector source, five-layer scheme A) |
| `architecture.png` | README preview image (click-through to SVG) |
| `demo-flow.svg` | Static demo flow (fallback diagram) |
| `demo.mp4` | Full demo screen recording (~67s, 1280×682, 15fps) |
| `demo.gif` | README autoplay preview (720px, links to MP4) |

## Re-compress a new recording

Source is often high-DPI screen capture (120fps HEVC). Example:

```bash
ffmpeg -y -hwaccel videotoolbox -i /path/to/recording.mp4 \
  -an \
  -vf "fps=15,scale=1280:-2:flags=lanczos,format=yuv420p" \
  -c:v libx264 -profile:v main -pix_fmt yuv420p -crf 27 -preset medium \
  -movflags +faststart -tag:v avc1 \
  docs/assets/demo.mp4
```

README embed (root `README.md` / `README.en.md`):

```html
<a href="docs/assets/demo.mp4">
  <img src="docs/assets/demo.gif" width="720" alt="DeepTicket demo">
</a>
```

GitHub does not reliably play `<video>` in README; use GIF + MP4 link instead.

**Do not commit** real API keys, internal URLs, or production ticket content in recordings.
