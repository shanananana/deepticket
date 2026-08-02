#!/usr/bin/env bash
# 本地预生成 ad_agent 投放 log（不提交 Git）。Agent 对话中应只 query，不跑本脚本。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT_DIR="${ROOT}/workspace/project/ad-agent"

if [[ ! -d "${AGENT_DIR}" ]]; then
  echo "workspace ad-agent 不存在: ${AGENT_DIR}" >&2
  echo "请先在 deepticket.yaml 配置 knowledge.repos 并同步知识库。" >&2
  exit 1
fi

cd "${AGENT_DIR}"
python3 scripts/generate_campaign_data.py --start 2026-07-24 --end 2026-08-01

echo "OK: ${AGENT_DIR}/data/campaign_metrics.log"
echo "OK: ${AGENT_DIR}/data/budget_audit.log"
