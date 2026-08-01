from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SkillInfo:
    name: str
    path: str
    source: str


class SkillManager:
    """Skill 管理：从项目 skills/ 与用户目录发布到 workspace/.openhands/skills。"""

    def __init__(
        self,
        *,
        skills_dir: Path,
        user_skills_dir: Path | None,
        workspace_skills_dir: Path,
    ) -> None:
        self.skills_dir = skills_dir
        self.user_skills_dir = user_skills_dir
        self.workspace_skills_dir = workspace_skills_dir

    def list_skills(self) -> list[SkillInfo]:
        items: list[SkillInfo] = []
        for source, label in (
            (self.skills_dir, "project"),
            (self.user_skills_dir, "user"),
        ):
            if source is None or not source.is_dir():
                continue
            for child in sorted(source.iterdir()):
                if child.is_dir() and (child / "SKILL.md").is_file():
                    items.append(
                        SkillInfo(name=child.name, path=str(child), source=label)
                    )
        return items

    def publish_to_workspace(self) -> list[str]:
        if self.workspace_skills_dir.exists():
            shutil.rmtree(self.workspace_skills_dir)
        self.workspace_skills_dir.mkdir(parents=True, exist_ok=True)

        published: list[str] = []
        for skill in self.list_skills():
            src = Path(skill.path)
            dest = self.workspace_skills_dir / skill.name
            if dest.exists() or dest.is_symlink():
                if dest.is_symlink():
                    dest.unlink()
                elif dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            dest.symlink_to(src.resolve(), target_is_directory=True)
            published.append(skill.name)
            logger.info("已发布 Skill: %s (%s)", skill.name, skill.source)
        return published
