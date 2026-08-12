# 贡献指南 / Contributing

感谢考虑为 DeepTicket 贡献！项目处于 **Alpha（0.2.x）**，欢迎文档、Skill 模板、集成示例和小功能改进。

Thank you for contributing! DeepTicket is in **alpha**; we welcome docs, Skill templates, integration examples, and focused code changes.

---

## 快速开始

```bash
git clone https://github.com/shanananana/deepticket.git
cd deepticket
bash scripts/setup.sh
pip install -e ".[dev]"
pytest -q
ruff check deepticket tests
```

编辑本地 `deepticket.yaml`（已 gitignore），**勿提交密钥**。

---

## 适合第一次贡献（Good First Issue）

在 GitHub Issues 中查找标签 **`good first issue`**（可参考 [.github/GOOD_FIRST_ISSUES.md](.github/GOOD_FIRST_ISSUES.md) 创建首批 issue）。

| 类型 | 示例 |
|------|------|
| **文档** | README 错别字、部署说明、Ingress 对接示例 |
| **Skill 模板** | 改进 `log-query` / `config-query` 占位说明；新增 Loki / ELK 示例脚本（不含真实密钥） |
| **测试** | 补充 classifier、ingress、config loader 边界用例 |
| **小功能** | 健康检查字段、verify 脚本检查项（需附测试） |

**暂不建议**首 PR 就改：OpenHands 引擎集成方式、存储 schema 大改、未讨论的架构重构。

---

## 提 PR 前 checklist

- [ ] `pytest -q` 通过
- [ ] `ruff check deepticket tests` 无新增问题
- [ ] 未提交 `deepticket.yaml`、`.env`、`workspace/`、`data/` 等 gitignore 内容
- [ ] 文档改动同步 **中文 README.md** 与 **README.en.md**（若面向用户）
- [ ] PR 描述说明 **为什么改**（业务场景），而非只列文件

---

## 代码原则

1. **安全优先** — 不削弱 Ingress / 登录鉴权；不记录明文密钥到日志  
2. **可维护** — 匹配现有分层（input / knowledge / engine / output / storage）  
3. **最小 diff** — 一个 PR 解决一类问题  

---

## 发版流程 / Releases

**推荐：打 tag 即自动发 Release**（推送 `v*` tag 后 GitHub Actions 从 `CHANGELOG.md` 生成 Release 说明）。

维护者 checklist：

1. 在 **`CHANGELOG.md`** / **`CHANGELOG.en.md`** 写好 `## [x.y.z]` 条目  
2. 提交并合并到 `main`  
3. 打 tag 并推送（会触发 [`.github/workflows/release.yml`](.github/workflows/release.yml)）：

```bash
git tag -a v0.1.3 -m "v0.1.3"
git push origin v0.1.3
```

本地预览 Release 标题/正文：

```bash
bash scripts/extract_changelog_release.sh v0.1.3
```

**不要**只 push tag 不写 CHANGELOG；workflow 找不到对应章节会失败。

---

## 报告 Bug

请包含：

- DeepTicket 版本 / commit
- `deepticket.yaml` 相关片段（**打码密钥**）
- 复现步骤与期望行为
- 相关日志（脱敏）

---

## 功能建议

欢迎用 Issue 描述：

- 场景（谁、在什么系统、要解决什么）
- 是否愿意自行提 PR

---

## 行为准则

保持友善、就事论事。骚扰、歧视、泄露他人或公司敏感数据的内容将被关闭。

---

## License

贡献即表示同意以 [MIT](LICENSE) 协议发布。
