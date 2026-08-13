from __future__ import annotations

import base64
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

_UPLOAD_PATH_PREFIX = "/api/uploads/images/"
_UPLOAD_FILENAME_RE = re.compile(
    r"^[a-f0-9]{32}\.(png|jpe?g|gif|webp)$",
    re.IGNORECASE,
)
_EXT_TO_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def _is_upload_path(url: str) -> bool:
    return url.startswith(_UPLOAD_PATH_PREFIX) and ".." not in url


def _upload_filename(url: str) -> str | None:
    path = url
    if not _is_upload_path(url):
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.path.startswith(
            _UPLOAD_PATH_PREFIX
        ):
            path = parsed.path
        else:
            return None
    name = path.rsplit("/", 1)[-1]
    if not _UPLOAD_FILENAME_RE.fullmatch(name):
        return None
    return name


def normalize_image_urls(*groups: list[str] | None) -> list[str]:
    """保留 http/https 或本地上传路径，去重并保持顺序。"""
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        if not group:
            continue
        for raw in group:
            url = str(raw).strip()
            if not url or url in seen:
                continue
            if _is_upload_path(url):
                seen.add(url)
                out.append(url)
                continue
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                continue
            if parsed.path.startswith(_UPLOAD_PATH_PREFIX):
                relative = parsed.path
                if relative not in seen:
                    seen.add(relative)
                    out.append(relative)
                continue
            seen.add(url)
            out.append(url)
    return out


def resolve_image_urls_for_agent(
    urls: list[str] | None,
    *,
    public_base_url: str,
) -> list[str]:
    """把相对上传路径解析成 Agent Server 可拉取的绝对 URL。"""
    base = public_base_url.rstrip("/") + "/"
    seen: set[str] = set()
    out: list[str] = []
    for raw in urls or []:
        url = str(raw).strip()
        if not url or url in seen:
            continue
        if _is_upload_path(url):
            absolute = urljoin(base, url.lstrip("/"))
        else:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                continue
            if parsed.path.startswith(_UPLOAD_PATH_PREFIX):
                absolute = urljoin(base, parsed.path.lstrip("/"))
            else:
                absolute = url
        if absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out


def inline_local_upload_images(
    urls: list[str] | None,
    *,
    uploads_dir: Path,
) -> list[str]:
    """把本地上传图转成 data URL，避免 Agent 去拉 127.0.0.1 被 SSRF 拦截。"""
    seen: set[str] = set()
    out: list[str] = []
    for raw in urls or []:
        url = str(raw).strip()
        if not url or url in seen:
            continue
        if url.startswith("data:image/"):
            seen.add(url)
            out.append(url)
            continue
        filename = _upload_filename(url)
        if filename is None:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                continue
            seen.add(url)
            out.append(url)
            continue
        path = uploads_dir / filename
        if not path.is_file():
            raise RuntimeError(f"本地截图不存在: {filename}")
        mime = _EXT_TO_MIME.get(path.suffix.lower())
        if mime is None:
            raise RuntimeError(f"不支持的截图格式: {filename}")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        data_url = f"data:{mime};base64,{encoded}"
        if data_url not in seen:
            seen.add(data_url)
            out.append(data_url)
    return out


def image_urls_from_metadata(metadata: dict) -> list[str]:
    """兼容 metadata.image_urls / metadata.images。"""
    raw = metadata.get("image_urls")
    if raw is None:
        raw = metadata.get("images")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(item) for item in raw if item]
    return []
