import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

# 测试用临时文件，不污染真实库存
@pytest.fixture
def temp_inventory(tmp_path):
    temp_file = tmp_path / "inventory.json"
    temp_file.write_text("{}")
    with patch("fridge_assistant.inventory.INVENTORY_FILE", temp_file):
        yield temp_file

# ─── 添加食材测试 ───

def test_add_basic(temp_inventory):
    """基本添加"""
    from fridge_assistant.inventory import add_item, load_inventory
    add_item("鸡蛋", 6, "个", "2026-05-20")
    inventory = load_inventory()
    assert "鸡蛋" in inventory
    assert inventory["鸡蛋"]["数量"] == 6
    assert inventory["鸡蛋"]["单位"] == "个"
    assert inventory["鸡蛋"]["过期日期"] == "2026-05-20"

def test_add_without_expiry(temp_inventory):
    """不填过期日期"""
    from fridge_assistant.inventory import add_item, load_inventory
    add_item("苹果", 3, "个")
    inventory = load_inventory()
    assert inventory["苹果"]["过期日期"] == "未知"

def test_add_multiple_items(temp_inventory):
    """添加多个食材"""
    from fridge_assistant.inventory import add_item, load_inventory
    add_item("鸡蛋", 6, "个")
    add_item("牛奶", 1, "盒")
    add_item("西红柿", 3, "个")
    inventory = load_inventory()
    assert len(inventory) == 3

def test_add_decimal_quantity(temp_inventory):
    """小数数量"""
    from fridge_assistant.inventory import add_item, load_inventory
    add_item("猪肉", 0.5, "斤")
    inventory = load_inventory()
    assert inventory["猪肉"]["数量"] == 0.5

def test_add_overwrites_existing(temp_inventory):
    """重复添加同一食材会覆盖"""
    from fridge_assistant.inventory import add_item, load_inventory
    add_item("鸡蛋", 6, "个")
    add_item("鸡蛋", 12, "个")  # 覆盖
    inventory = load_inventory()
    assert inventory["鸡蛋"]["数量"] == 12

# ─── 删除食材测试 ───

def test_remove_existing(temp_inventory):
    """删除存在的食材"""
    from fridge_assistant.inventory import add_item, remove_item, load_inventory
    add_item("鸡蛋", 6, "个")
    remove_item("鸡蛋")
    inventory = load_inventory()
    assert "鸡蛋" not in inventory

def test_remove_nonexistent(temp_inventory, capsys):
    """删除不存在的食材"""
    from fridge_assistant.inventory import remove_item
    remove_item("不存在的食材")
    captured = capsys.readouterr()
    assert "找不到" in captured.out

# ─── 使用食材测试 ───

def test_use_item_partial(temp_inventory):
    """部分使用"""
    from fridge_assistant.inventory import add_item, use_item, load_inventory
    add_item("鸡蛋", 6, "个")
    use_item("鸡蛋", 2)
    inventory = load_inventory()
    assert inventory["鸡蛋"]["数量"] == 4

def test_use_item_all(temp_inventory):
    """用完自动删除"""
    from fridge_assistant.inventory import add_item, use_item, load_inventory
    add_item("鸡蛋", 6, "个")
    use_item("鸡蛋", 6)
    inventory = load_inventory()
    assert "鸡蛋" not in inventory

def test_use_item_nonexistent(temp_inventory, capsys):
    """使用不存在的食材"""
    from fridge_assistant.inventory import use_item
    use_item("不存在", 1)
    captured = capsys.readouterr()
    assert "找不到" in captured.out

# ─── 过期提醒测试 ───

def test_expiring_soon(temp_inventory):
    """3天内过期"""
    from fridge_assistant.inventory import add_item, get_expiring_soon
    from datetime import date, timedelta
    soon = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
    add_item("牛奶", 1, "盒", soon)
    expiring = get_expiring_soon()
    assert len(expiring) == 1
    assert expiring[0][0] == "牛奶"

def test_not_expiring_soon(temp_inventory):
    """30天后才过期"""
    from fridge_assistant.inventory import add_item, get_expiring_soon
    from datetime import date, timedelta
    later = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    add_item("鸡蛋", 6, "个", later)
    expiring = get_expiring_soon()
    assert len(expiring) == 0

def test_unknown_expiry_ignored(temp_inventory):
    """过期日期未知不计入过期提醒"""
    from fridge_assistant.inventory import add_item, get_expiring_soon
    add_item("苹果", 3, "个")  # 没有过期日期
    expiring = get_expiring_soon()
    assert len(expiring) == 0