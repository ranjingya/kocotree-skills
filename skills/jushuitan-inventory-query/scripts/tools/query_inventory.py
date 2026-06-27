#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if not (SCRIPTS_DIR / ".venv").exists():
    print(f"错误: 未找到虚拟环境，请先在 scripts/ 目录下执行 uv sync\n  路径: {SCRIPTS_DIR}", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(SCRIPTS_DIR))

from auth.auth_client import with_auth, get_headers

import requests


JUSHUITAN_SERVICE_URL = os.environ.get("JUSHUITAN_SERVICE_URL", "https://jushuitan.skills.kktree.cn")


def render_inventory_markdown(rows: list[dict], failures: list[dict]) -> str:
    lines = ["## 数据明细"]

    if rows:
        grouped: OrderedDict[str, list[dict]] = OrderedDict()
        for row in rows:
            grouped.setdefault(row["name"], []).append(row)

        for item_name, group_rows in grouped.items():
            lines.extend(
                [
                    "",
                    f"### {item_name}",
                    "| SKU ID | 款式ID | 颜色/规格 | 实际库存 | 库存锁定数 | 订单占有数 | 采购在途数 | 进货仓库存 | 剩余可用 |",
                    "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
                ]
            )
            for row in group_rows:
                lines.append(
                    f"| {row['sku_id']} | {row['i_id']} | {row['color_spec']} | {row['qty']} | {row['lock_qty']} | {row['order_lock']} | {row['purchase_qty']} | {row['in_qty']} | {row['available_qty']} |"
                )
    else:
        lines.extend(
            [
                "",
                "| SKU ID | 款式ID | 颜色/规格 | 实际库存 | 库存锁定数 | 订单占有数 | 采购在途数 | 进货仓库存 | 剩余可用 |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
                "| - | - | - | - | - | - | - | - | - |",
            ]
        )

    if failures:
        lines.extend(
            [
                "",
                "## 异常与补查",
                "| 来源 | 批次 | 页码 | 错误码 | 错误信息 | 查询对象 |",
                "| --- | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for item in failures:
            batch_preview = ",".join(item.get("batch", [])[:5])
            lines.append(
                f"| {item.get('source')} | {item.get('batch_index', '')} | {item.get('page', '')} | {item.get('code', '')} | {item.get('msg', '')} | {batch_preview} |"
            )

    return "\n".join(lines)


def parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]

@with_auth
def _request(payload: dict, timeout: int) -> requests.Response:
    return requests.post(
        headers=get_headers(),
        url=f"{JUSHUITAN_SERVICE_URL}/api/inventory/query",
        json=payload,
        timeout=timeout,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="查询聚水潭库存")
    parser.add_argument("--sku-ids", default="", help="逗号分隔的 sku_id 列表")
    parser.add_argument("--i-ids", default="", help="逗号分隔的 i_id 列表")
    parser.add_argument("--names", default="", help="逗号分隔的商品名称列表")
    parser.add_argument("--page-index", type=int, default=1, help="起始页码，默认 1")
    parser.add_argument("--page-size", type=int, default=100, help="每页数量，默认 100，最大 100")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    query_candidates = []
    if args.sku_ids.strip():
        query_candidates.append(("sku_ids", parse_list(args.sku_ids)))
    if args.i_ids.strip():
        query_candidates.append(("i_ids", parse_list(args.i_ids)))
    if args.names.strip():
        query_candidates.append(("names", parse_list(args.names)))

    if len(query_candidates) > 1:
        print("只能提供一种查询条件：--sku-ids / --i-ids / --names", file=sys.stderr)
        return 1

    if not query_candidates:
        print("必须提供一种查询条件：--sku-ids / --i-ids / --names", file=sys.stderr)
        return 1

    query_type, query_values = query_candidates[0]

    payload = {
        "query_type": query_type,
        "query_values": query_values,
        "page_index": args.page_index,
        "page_size": args.page_size,
        "timeout": args.timeout,
    }

    try:
        resp = _request(payload, args.timeout + 10)
        body = resp.json()
    except requests.RequestException as e:
        print(f"请求服务失败: {e}", file=sys.stderr)
        return 1

    if body.get("code") != 0:
        print(f"服务返回错误: {body.get('msg', '未知错误')}", file=sys.stderr)
        return 1

    result = body["data"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_inventory_markdown(result["rows"], result.get("failures", [])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
