from __future__ import annotations

import logging

from deepticket.layers.storage.base import StorageBackend
from deepticket.projects.models import ProjectMemberRecord, UserProjectMembership
from deepticket.projects.store import ProjectConfigStore

logger = logging.getLogger(__name__)

_NS_MEMBERS = "project_members"
_NS_USER_PROJECTS = "user_projects"


class ProjectPermissionStore:
    """用户 ↔ 项目权限（存 Redis / local storage）。"""

    def __init__(self, storage: StorageBackend) -> None:
        self.storage = storage

    def list_members(self, project_id: str) -> list[ProjectMemberRecord]:
        doc = self.storage.get_json(_NS_MEMBERS, project_id) or {}
        members = doc.get("members") or []
        result: list[ProjectMemberRecord] = []
        for item in members:
            if not isinstance(item, dict):
                continue
            uid = str(item.get("uid") or "").strip()
            username = str(item.get("username") or "").strip()
            if uid and username:
                result.append(ProjectMemberRecord(uid=uid, username=username))
        return result

    def set_members(
        self, project_id: str, members: list[ProjectMemberRecord]
    ) -> list[ProjectMemberRecord]:
        previous = {item.uid for item in self.list_members(project_id)}
        payload = {
            "members": [
                {"uid": item.uid, "username": item.username} for item in members
            ]
        }
        self.storage.set_json(_NS_MEMBERS, project_id, payload)
        next_uids = {item.uid for item in members}
        for member in members:
            self.grant(member.uid, project_id)
        for uid in previous - next_uids:
            self.revoke(uid, project_id)
        return members

    def grant(self, uid: str, project_id: str) -> None:
        doc = self.storage.get_json(_NS_USER_PROJECTS, uid) or {}
        ids = [str(item) for item in doc.get("project_ids") or []]
        if project_id not in ids:
            ids.append(project_id)
            self.storage.set_json(_NS_USER_PROJECTS, uid, {"project_ids": sorted(ids)})

    def revoke(self, uid: str, project_id: str) -> None:
        doc = self.storage.get_json(_NS_USER_PROJECTS, uid) or {}
        ids = [str(item) for item in doc.get("project_ids") or [] if str(item) != project_id]
        self.storage.set_json(_NS_USER_PROJECTS, uid, {"project_ids": sorted(ids)})

    def list_project_ids_for_user(self, uid: str) -> list[str]:
        doc = self.storage.get_json(_NS_USER_PROJECTS, uid) or {}
        return sorted({str(item) for item in doc.get("project_ids") or [] if str(item).strip()})

    def ensure_default_access(self, uid: str, username: str) -> None:
        default_id = ProjectConfigStore.default_project_id()
        members = self.list_members(default_id)
        if not any(item.uid == uid for item in members):
            members.append(ProjectMemberRecord(uid=uid, username=username))
            self.set_members(default_id, members)
        else:
            self.grant(uid, default_id)

    def user_has_access(self, uid: str, project_id: str) -> bool:
        return project_id in self.list_project_ids_for_user(uid)
