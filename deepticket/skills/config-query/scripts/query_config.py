#!/usr/bin/env python3
"""占位：对接 Apollo / Nacos 等配置中心。请按 SKILL.md 替换为真实 API 调用。"""
from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="Query config (template stub)")
    parser.add_argument("--key", default="", help="Config key")
    parser.add_argument("--app", default="", help="Application id")
    args = parser.parse_args()
    payload = {
        "status": "template",
        "message": "Configure config center API in deepticket.yaml and replace this script.",
        "app": args.app,
        "key": args.key,
        "value": None,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
