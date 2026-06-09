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


JUSHUITAN_SERVICE_URL = os.environ.get("JUSHUITAN_SERVICE_URL", "http://121.40.167.37:5011")


def render_virtual_stock_markdown(rows: list[dict], failures: list[dict]) -> str:
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
                    "| SKU ID | 颜色/规格 | 库存数 | 仓库待发数 | 虚拟仓可配货数 |",
                    "| --- | --- | ---: | ---: | ---: |",
                ]
            )
            for row in group_rows:
                lines.append(
                    f"| {row['sku_id']} | {row['color_spec']} | {row['qty']} | {row['pick_lock']} | {row['order_able_qty']} |"
                )
    else:
        lines.extend(
            [
                "",
                "| SKU ID | 颜色/规格 | 库存数 | 仓库待发数 | 虚拟仓可配货数 |",
                "| --- | --- | ---: | ---: | ---: |",
                "| - | - | - | - | - |",
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
    else:
        lines.extend(["", "## 异常与补查", "无"])

    return "\n".join(lines)


def parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@with_auth
def _request(payload: dict, timeout: int) -> requests.Response:
    return requests.post(
        headers=get_headers(),
        url=f"{JUSHUITAN_SERVICE_URL}/api/inventory/virtual-stock",
        json=payload,
        timeout=timeout,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="查询聚水潭虚拟库存")
    parser.add_argument("--sku-ids", default="", help="逗号分隔的 sku_id 列表")
    parser.add_argument("--i-ids", default="", help="逗号分隔的 i_id 列表，会先转换为 sku_id")
    parser.add_argument("--names", default="", help="逗号分隔的商品名称列表，会先转换为 sku_id")
    parser.add_argument("--wms-co-id", default="", help="分仓编码，默认不传")
    parser.add_argument("--page-index", type=int, default=1, help="起始页码，默认 1")
    parser.add_argument("--page-size", type=int, default=500, help="每页数量，默认 500，最大 500")
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

    if len(query_candidates) != 1:
        print("必须且只能提供一种查询条件：--sku-ids / --i-ids / --names", file=sys.stderr)
        return 1

    query_type, query_values = query_candidates[0]

    payload = {
        "query_type": query_type,
        "query_values": query_values,
        "page_index": args.page_index,
        "page_size": args.page_size,
        "timeout": args.timeout,
    }
    if args.wms_co_id.strip():
        payload["wms_co_id"] = args.wms_co_id.strip()

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
        print(render_virtual_stock_markdown(result["rows"], result.get("failures", [])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
