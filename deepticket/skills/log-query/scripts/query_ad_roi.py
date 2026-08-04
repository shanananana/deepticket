#!/usr/bin/env python3
"""ad_agent ROI 演示查询占位（需 workspace 内真实数据）。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--album-id", default="")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4] / "workspace" / "project" / "ad-agent"
    metrics = root / "data" / "campaign_metrics.log"
    if not metrics.is_file():
        print(
            json.dumps(
                {
                    "error": "campaign_metrics.log not found; run scripts/refresh_ad_agent_logs.sh",
                    "workspace": str(root),
                }
            )
        )
        return 1
    print("--- key finding ---")
    print(f"album={args.album_id or 'all'} range={args.start}..{args.end}")
    print("daily_budget changed 5000 -> 15000 on 2026-07-28 (demo stub)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
