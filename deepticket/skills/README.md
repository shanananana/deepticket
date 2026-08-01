# DeepTicket 内置 Skills

本目录是 **一个 Skill 包**，下面每个子文件夹 = 一个 Skill（一份 `SKILL.md`），不是多个 Git 仓库。

| Skill | 状态 | 用途 |
|-------|------|------|
| `repo-workspace/` | 可用 | 只读查已同步的 Git 代码 |
| `config-query/` | 模板 | 接公司内部配置中心（需自行补脚本） |
| `log-query/` | 模板 | 接公司内部日志平台（需自行补脚本） |

可选：在 `deepticket.yaml` 的 `extensions.user_skills_dir` 指定第二个 Skill 目录。
