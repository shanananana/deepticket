from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from deepticket.api.deps import get_service
from deepticket.api.schemas import LoginRequest, OkResponse, RegisterRequest, UserResponse
from deepticket.auth.dependencies import get_current_user
from deepticket.auth.user_store import AuthUser

router = APIRouter(prefix="/api/auth", tags=["Auth"])
_bearer = HTTPBearer(auto_error=False)


@router.post("/register")
async def register(body: RegisterRequest, request: Request) -> dict:
    service = get_service(request)
    if not service.config.auth.register_enabled:
        raise HTTPException(status_code=403, detail="注册已关闭，请联系管理员")
    try:
        user = service.users.register(body.username, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    service.grant_default_project(user)
    return {"user": UserResponse(uid=user.uid, username=user.username).model_dump()}


@router.post("/login")
async def login(body: LoginRequest, request: Request) -> dict:
    try:
        user, token = get_service(request).users.login(body.username, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {
        "token": token,
        "user": UserResponse(uid=user.uid, username=user.username).model_dump(),
    }


@router.get("/me")
async def me(request: Request, user: AuthUser = Depends(get_current_user)) -> dict:
    service = get_service(request)
    return {
        "user": UserResponse(
            uid=user.uid,
            username=user.username,
            is_admin=service.is_admin(user),
        ).model_dump()
    }


@router.post("/logout", response_model=OkResponse)
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> OkResponse:
    if credentials:
        get_service(request).users.logout(credentials.credentials)
    return OkResponse()
