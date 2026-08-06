#!/usr/bin/env bash
# 打印 5 分钟上手步骤；若已配置 ad-agent 本地 repo 则尝试预生成 log。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "DeepTicket 快速上手"
echo "==================="
echo ""
echo "1) 若尚未安装：bash scripts/setup.sh"
echo "2) 编辑 deepticket.yaml，填写 llm.api_key"
echo "3) 启动：bash scripts/start_all.sh"
echo "4) 打开 http://127.0.0.1:8600 ，使用 DEMO_PROMPT.md 中的示例提问"
echo ""
echo "详细说明：docs/quickstart-demo.md"
echo ""

if [[ -f "${ROOT}/deepticket.yaml" ]] && [[ -d "${ROOT}/workspace/project/ad-agent" ]]; then
  echo "检测到 workspace/project/ad-agent，尝试预生成演示 log…"
  bash "${ROOT}/scripts/refresh_ad_agent_logs.sh" || true
else
  echo "（可选）配置 ad-agent 演示仓后，运行 bash scripts/refresh_ad_agent_logs.sh"
fi
