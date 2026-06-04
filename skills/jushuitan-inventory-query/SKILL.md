---
name: jushuitan-inventory-query
description: >
  当需要查询聚水潭主库存或虚拟库存时使用。本技能通过 HTTP 调用后端服务完成查询，支持按商品名称、SKU、款式编码进行查询。
---

# 聚水潭库存查询工具 (Jushuitan Skill)

## 简介

本技能用于执行聚水潭库存相关的只读查询，当前仅包含以下两类能力：

- 主库存查询
- 虚拟库存查询

本技能通过 HTTP 调用 `jushuitan-skill-service` 后端服务获取原始数据，由客户端脚本完成 markdown 渲染输出。

**核心调用入口**：

- 技能注册表：`scripts/registry.py`
- 主库存脚本：`scripts/tools/query_inventory.py`
- 虚拟库存脚本：`scripts/tools/query_virtual_stock.py`


## 环境准备

首次使用前需在 `scripts/` 目录下初始化 Python 环境：

```bash
cd scripts
uv sync
```

如未安装 uv，先执行：
- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

初始化完成后，使用 `.venv` 中的 Python 执行工具脚本。

## 使用原则

使用本技能时，应遵循以下原则：

1. 应优先调用固定包装脚本，不应直接手写 API 调用。
2. 应根据查询目标选择对应脚本，不应将主库存和虚拟库存逻辑混用。
3. 应仅使用脚本已封装的查询方式：商品名称、SKU、款式编码。

## 主库存查询

主库存查询脚本为 `scripts/tools/query_inventory.py`。

适用场景：

- 查询指定 SKU 的主库存
- 查询指定款式编码 `i_id` 的主库存
- 查询指定商品名称的主库存
- 查询 `实际库存`、`库存锁定数`、`订单占有数`、`采购在途数`、`剩余可用`

命令示例：

以下命令默认在 `skills/jushuitan-inventory-query/` 目录下执行。

```bash
python scripts/tools/query_inventory.py --sku-ids 6974318532161,6974318532147
python scripts/tools/query_inventory.py --i-ids KQ26043,KQ26044
python scripts/tools/query_inventory.py --names 小森林翻翻帽,甜粉小番茄
```

可选参数：

- `--page-index`
- `--page-size`
- `--timeout`
- `--json`

使用限制：

- 必须且只能提供一种查询条件：`--sku-ids` / `--i-ids` / `--names`
- `page_size` 最大值为 `100`

主库存输出字段：

- `SKU ID`
- `款式ID`
- `颜色/规格`
- `实际库存`
- `库存锁定数`
- `订单占有数`
- `采购在途数`
- `进货仓库存`
- `剩余可用`

## 虚拟库存查询

虚拟库存查询脚本为 `scripts/tools/query_virtual_stock.py`。

适用场景：

- 查询指定 SKU 的虚拟库存
- 查询指定款式编码 `i_id` 对应的虚拟库存
- 查询指定商品名称对应的虚拟库存
- 查询天猫仓可配货数

命令示例：

以下命令默认在 `skills/jushuitan-inventory-query/` 目录下执行。

```bash
python scripts/tools/query_virtual_stock.py --sku-ids 6974318532161,6974318532147
python scripts/tools/query_virtual_stock.py --i-ids KQ26043,KQ26044
python scripts/tools/query_virtual_stock.py --names 小森林翻翻帽,甜粉小番茄
```

可选参数：

- `--wms-co-id`
- `--page-index`
- `--page-size`
- `--timeout`
- `--json`

使用限制：

- 必须且只能提供一种查询条件：`--sku-ids` / `--i-ids` / `--names`
- `page_size` 最大值为 `500`

虚拟库存输出字段：

- `SKU ID`
- `颜色/规格`
- `库存数`
- `仓库待发数`
- `可配货数`

## 输出要求

- 默认输出 markdown（由客户端脚本渲染），传 `--json` 输出原始 JSON 数据
- markdown 输出按商品名称分组，减少商品名称重复
- 当补查失败、接口失败或 `颜色/规格` 缺失时，应在 `异常与补查` 区域体现
- 可适当使用emoji增强可读性

### 示例
**注意不要少数据，所有返回数据都需要**  
可以适当给出一些建议，但不要过多，保持简洁。  
尽量保持 markdown 格式的美观和清晰，方便阅读和理解。  

1. 主库存查询示例：
```markdown
## *数据明细*

### **小森林翻翻帽**

| 🏷️ SKU ID | 🧾 款式ID | 🎨 颜色/规格 | 📦 实际库存 | 🔒 库存锁定数 | 📌 订单占有数 | 🚚 采购在途数 | 📥 进货仓库存 | ✅ 剩余可用 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 6974318532147 | KQ26043 | 山野果语M | 2347 | 0 | 5 | 120 | 2342 |
| 6974318532130 | KQ26043 | 山野果语S | 0 | 0 | 12 | 80 | -12 |

---

## *异常与补查*

---

## *建议*

```

2. 虚拟库存查询示例：
```markdown
## *数据明细*

### **小森林翻翻帽**

| 🏷️ SKU ID | 🧾 款式ID | 🎨 颜色/规格 | 📦 库存数 | 🚚 仓库待发数 | ✅ 虚拟仓可配货数 |
| --- | --- | --- | ---: | ---: | ---: |
| 6974318533328 | KQ26043 | 甜粉小番茄 | 140 | 0 | 140 |
| 6974318533329 | KQ26043 | 甜粉小番茄 | 120 | 5 | 115 |

---

## *异常与补查*

---

## *建议*

```
