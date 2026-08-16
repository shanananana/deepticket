# 5 分钟上手 & ROI 演示

## 路径 A：最快体验（只需 LLM Key）

适合第一次 Star / 试用，**不需要** ad_agent 数据仓库。

**A1 · Docker（推荐，无需 Python）**

```bash
mkdir deepticket && cd deepticket
curl -LO https://raw.githubusercontent.com/shanananana/deepticket/main/docker-compose.image.yml
curl -LO https://raw.githubusercontent.com/shanananana/deepticket/main/.env.docker.example
cp .env.docker.example .env
docker compose -f docker-compose.image.yml up -d
```

详见 [docker.md](docker.md)。LLM Key 可在 `.env` 预填，或登录后在 Web **LLM 配置** 填写。

**A2 · Clone（开发调试）**

```bash
git clone https://github.com/shanananana/deepticket.git
cd deepticket
bash scripts/setup.sh
# 可选：编辑 deepticket.yaml 填写 llm.api_key；也可启动后在 Web LLM 配置 填写
bash scripts/start_all.sh
```

浏览器打开 http://127.0.0.1:8600 ，登录 `admin` / `admin`，新建对话，粘贴 [DEMO_PROMPT.md](DEMO_PROMPT.md) 里的 **Nginx 日志** 示例。

Agent 会走 Thinking 步骤并流式输出 Markdown 结论。

## 路径 B：ROI 归因完整 Demo（读 log + 代码 + 置信度）

演示 **log-query → 读配置/代码 → 分析置信度徽章**，与 README 录屏一致。

1. 完成路径 A（Docker 或 Clone），并确保 LLM 已配置（yaml、`.env` 或 Web **LLM 配置**）
2. 在 `deepticket.yaml` 的 `knowledge.repos` 增加本地 ad-agent 演示仓（`file://` 绝对路径，见 `deepticket.example.yaml` 注释）
3. `bash scripts/start_all.sh` → 工作台 **同步知识库**
4. `bash scripts/refresh_ad_agent_logs.sh` 预生成 `campaign_metrics.log`
5. 复制 [DEMO_PROMPT.md](DEMO_PROMPT.md) 中的 **ROI 提问**

> 垂类业务 Agent 参考实现：[ad_agent](https://github.com/shanananana/ad_agent)（Spring AI 广告投放对话）。DeepTicket 是在 OpenHands 之上的 **SRE/工单编排层**，两者可组合使用。

## 录屏建议

- 设置 → **录屏模式**（Thinking 保持展开）
- 浏览器 125% 缩放，隐藏 yaml 与 API Key
