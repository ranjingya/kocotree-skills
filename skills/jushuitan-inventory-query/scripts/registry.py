TOOLS = {
    "inventory_query": {
        "script": "skills/jushuitan-inventory-query/scripts/tools/query_inventory.py",
        "description": "查询聚水潭库存，支持按 sku_ids、i_ids、names 查询。",
        "required_one_of": ["sku_ids", "i_ids", "names"],
        "optional_args": ["page_index", "page_size"],
        "output": "markdown_table",
    },
    "virtual_stock_query": {
        "script": "skills/jushuitan-inventory-query/scripts/tools/query_virtual_stock.py",
        "description": "查询聚水潭虚拟库存，支持按 sku_ids、i_ids、names 查询，默认只返回天猫仓数据。",
        "required_one_of": ["sku_ids", "i_ids", "names"],
        "optional_args": ["wms_co_id", "page_index", "page_size"],
        "output": "markdown_table",
    }
}
