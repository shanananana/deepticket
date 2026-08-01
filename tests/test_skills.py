from __future__ import annotations

from deepticket.layers.knowledge.skill_manager import SkillManager


def _make_skill(root, name, content="---\nname: test\ndescription: t\n---\n"):
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return d


def _manager(skills, user, ws):
    return SkillManager(skills_dir=skills, user_skills_dir=user, workspace_skills_dir=ws)


def test_list_skills_discovers(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    _make_skill(skills, "beta")
    (skills / "not-a-skill").mkdir()  # 无 SKILL.md，应被忽略

    manager = _manager(skills, None, tmp_path / "ws")
    listed = manager.list_skills()
    assert [s.name for s in listed] == ["alpha", "beta"]
    assert all(s.source == "project" for s in listed)


def test_list_skills_with_user_dir(tmp_path):
    proj = tmp_path / "proj"
    user = tmp_path / "user"
    _make_skill(proj, "proj-skill")
    _make_skill(user, "user-skill")

    manager = _manager(proj, user, tmp_path / "ws")
    by_source = {s.name: s.source for s in manager.list_skills()}
    assert by_source["proj-skill"] == "project"
    assert by_source["user-skill"] == "user"


def test_publish_creates_symlinks(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "demo")
    ws = tmp_path / "ws" / ".openhands" / "skills"

    manager = SkillManager(skills_dir=skills, user_skills_dir=None, workspace_skills_dir=ws)
    published = manager.publish_to_workspace()
    assert published == ["demo"]
    assert (ws / "demo").is_symlink()
    assert (ws / "demo" / "SKILL.md").is_file()


def test_publish_is_idempotent(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "demo")
    ws = tmp_path / "ws"

    manager = SkillManager(skills_dir=skills, user_skills_dir=None, workspace_skills_dir=ws)
    first = manager.publish_to_workspace()
    second = manager.publish_to_workspace()
    assert first == second == ["demo"]
