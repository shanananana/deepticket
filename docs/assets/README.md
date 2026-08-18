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
| `演示视频.mp4` | 仓库内源文件（~55s, 1280×642）；README 用 GitHub 图床播放 |
| `demo-poster.jpg` | 可选封面帧（更新图床视频后可用 ffmpeg 重导） |
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

README embed — 使用 GitHub Issue 上传后的 **user-attachments** URL（与 MoneyPrinterTurbo 相同做法）：

```html
<p align="center">
  <video src="https://github.com/user-attachments/assets/d5f5f2bf-1d78-44c2-b6db-35f31ac007ae" width="720" controls autoplay muted loop playsinline></video>
</p>
```

换视频：在 Issue/PR 拖入新 MP4 → 替换 URL。源文件仍保存在 `docs/assets/演示视频.mp4`。

**Do not commit** real API keys, internal URLs, or production ticket content in recordings.
