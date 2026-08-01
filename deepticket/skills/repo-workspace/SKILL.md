---
name: repo-workspace
description: 在 DeepTicket 已同步的 Git 知识库中只读查代码。用户提到具体服务、仓库、源码、配置、接口实现时使用；纯概念问题可跳过。
---

# 只读代码工作区

## 何时需要读代码

- 需要看实现、调用链、配置定义 → 读 `workspace/project/<repo-id>/`
- 闲聊、概念解释、与具体仓库无关 → **不要**打开 workspace

`<repo-id>` 来自 `deepticket.yaml` 的 `knowledge.repos`（例如 `my-service`）。

## 路径说明

| 路径 | 用途 |
|------|------|
| `workspace/project/<repo-id>/` | **Agent 只读分析入口**（读这里） |
| `workspace/knowledge/<repo-id>/` | Git 缓存；DeepTicket 启动或 UI「同步知识库」时更新 |

两者是同一仓库的两个视图，**不是两个项目**。优先读 `workspace/project/`，一般**不要**在对话里手动 `git pull`——需要最新代码时，请用户点「同步知识库」或告知已同步即可。

## 约束

- 只读：不修改、不提交 `workspace/project` 下任何文件
- 不猜测用户本机其他路径（如 `~/Projects/...`），除非用户明确给出
