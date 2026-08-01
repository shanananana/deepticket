from __future__ import annotations

from urllib.parse import urlparse


def normalize_image_urls(*groups: list[str] | None) -> list[str]:
    """保留 http/https 图片 URL，去重并保持顺序。"""
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        if not group:
            continue
        for raw in group:
            url = str(raw).strip()
            if not url or url in seen:
                continue
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                continue
            seen.add(url)
            out.append(url)
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
