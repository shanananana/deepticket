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
| `演示视频.mp4` | README demo screen recording (~55s, 1280×642, 30fps) |
| `demo-poster.jpg` | README 封面图（点击跳转 MP4；GitHub 不支持内嵌 `<video>`） |
| `mascot/` | ComfyUI 生成的看板娘 icon / banner（见 `comfyui/README.md`） |
| `comfyui/` | ComfyUI 提示词与生成说明 |

## 看板娘 / Banner（ComfyUI）

```bash
# 1. 启动 ComfyUI Desktop（8188）
# 2. 安装动漫 checkpoint 到 models/checkpoints/
python scripts/comfyui/generate_brand_assets.py --checkpoint YOUR.safetensors
```

详见 [comfyui/README.md](comfyui/README.md)。

## Re-compress a new recording

Source is often high-DPI screen capture (120fps HEVC). Example:

```bash
ffmpeg -y -hwaccel videotoolbox -i /path/to/recording.mp4 \
  -an \
  -vf "fps=15,scale=1280:-2:flags=lanczos,format=yuv420p" \
  -c:v libx264 -profile:v main -pix_fmt yuv420p -crf 27 -preset medium \
  -movflags +faststart -tag:v avc1 \
  docs/assets/演示视频.mp4
```

README embed (root `README.md` / `README.en.md`) — GitHub **不会播放** 相对路径的 `<video>`，用封面图 + raw MP4 链接：

```html
<p align="center">
  <a href="https://github.com/shanananana/deepticket/raw/main/docs/assets/%E6%BC%94%E7%A4%BA%E8%A7%86%E9%A2%91.mp4">
    <img src="docs/assets/demo-poster.jpg" width="720" alt="DeepTicket demo">
  </a>
</p>
```

更新封面：`ffmpeg -ss 8 -i docs/assets/演示视频.mp4 -frames:v 1 -q:v 2 docs/assets/demo-poster.jpg`

**Do not commit** real API keys, internal URLs, or production ticket content in recordings.
