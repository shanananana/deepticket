from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from deepticket.auth.dependencies import get_current_user
from deepticket.auth.user_store import AuthUser
from deepticket.paths import PROJECT_ROOT

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])

_ALLOWED_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
_MAX_BYTES = 8 * 1024 * 1024
_FILENAME_RE = re.compile(r"^[a-f0-9]{32}\.(png|jpe?g|gif|webp)$", re.IGNORECASE)


def _uploads_dir() -> Path:
    path = PROJECT_ROOT / "data" / "uploads" / "images"
    path.mkdir(parents=True, exist_ok=True)
    return path


@router.post("/images")
async def upload_image(
    file: UploadFile = File(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, str]:
    del user
    content_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    ext = _ALLOWED_TYPES.get(content_type)
    if ext is None:
        raise HTTPException(status_code=400, detail="仅支持 PNG / JPEG / GIF / WebP")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="空文件")
    if len(data) > _MAX_BYTES:
        raise HTTPException(status_code=400, detail="图片不能超过 8MB")

    filename = f"{uuid.uuid4().hex}{ext}"
    (_uploads_dir() / filename).write_bytes(data)
    return {
        "url": f"/api/uploads/images/{filename}",
        "name": file.filename or filename,
    }


@router.get("/images/{filename}")
async def get_image(filename: str) -> FileResponse:
    if not _FILENAME_RE.fullmatch(filename):
        raise HTTPException(status_code=404, detail="图片不存在")
    path = _uploads_dir() / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="图片不存在")
    return FileResponse(path)
