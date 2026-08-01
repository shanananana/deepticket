from __future__ import annotations

import argparse
import asyncio

from deepticket.verify.checks import (
    CheckResult,
    check_auth_and_chat_storage,
    check_config_load,
    check_mcp_agent_sync,
    check_mcp_config_file,
    check_package_layout,
    check_skills_publish,
    check_web_health,
)


def _print_result(result: CheckResult) -> None:
    tag = "PASS" if result.ok else ("SKIP" if result.optional else "FAIL")
    opt = " (optional)" if result.optional else ""
    print(f"[{tag}] {result.name}{opt}: {result.message}")


async def run_all(*, include_online: bool) -> int:
    sync_checks = [
        check_package_layout,
        check_config_load,
        check_skills_publish,
        check_mcp_config_file,
        check_auth_and_chat_storage,
    ]

    results: list[CheckResult] = []
    for check in sync_checks:
        results.append(check())

    if include_online:
        results.append(await check_mcp_agent_sync())
        results.append(await check_web_health())

    for item in results:
        _print_result(item)

    required_failures = [r for r in results if not r.ok and not r.optional]
    optional_failures = [r for r in results if not r.ok and r.optional]

    print("")
    if required_failures:
        print(f"验证失败: {len(required_failures)} 项必需检查未通过")
        return 1
    if optional_failures:
        print("必需检查已通过（部分可选在线检查跳过或失败）")
    else:
        print("全部检查通过")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="DeepTicket 功能验证")
    parser.add_argument(
        "--online",
        action="store_true",
        help="包含 Agent Server / Web 在线检查（含 MCP 同步验证）",
    )
    args = parser.parse_args()
    code = asyncio.run(run_all(include_online=args.online))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
