import json
from datetime import datetime, date
from pathlib import Path

INVENTORY_FILE = Path("inventory.json")

def load_inventory() -> dict:
    """读取库存文件"""
    if not INVENTORY_FILE.exists():
        return {}
    with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_inventory(inventory: dict) -> None:
    """保存库存文件"""
    with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)

def add_item(name: str, quantity: float, unit: str, expiry_date: str = None) -> None:
    """添加或更新食材"""
    inventory = load_inventory()
    name = name.strip()
    inventory[name] = {
        "数量": quantity,
        "单位": unit,
        "过期日期": expiry_date or "未知"
    }
    save_inventory(inventory)
    print(f"✅ 已添加：{name} {quantity}{unit}")

def remove_item(name: str) -> None:
    """删除食材"""
    inventory = load_inventory()
    name = name.strip()
    if name in inventory:
        del inventory[name]
        save_inventory(inventory)
        print(f"✅ 已删除：{name}")
    else:
        print(f"❌ 找不到：{name}")

def use_item(name: str, quantity: float) -> None:
    """使用食材，扣减库存"""
    inventory = load_inventory()
    name = name.strip()
    if name not in inventory:
        print(f"❌ 找不到：{name}")
        return
    inventory[name]["数量"] -= quantity
    if inventory[name]["数量"] <= 0:
        del inventory[name]
        save_inventory(inventory)
        print(f"✅ {name} 已用完，从库存移除")
    else:
        save_inventory(inventory)
        print(f"✅ 已使用 {name} {quantity}{inventory[name]['单位']}，剩余 {inventory[name]['数量']}{inventory[name]['单位']}")

def get_expiring_soon(days: int = 3) -> list:
    """获取即将过期的食材"""
    inventory = load_inventory()
    expiring = []
    today = date.today()
    for name, info in inventory.items():
        if info["过期日期"] == "未知":
            continue
        expiry = datetime.strptime(info["过期日期"], "%Y-%m-%d").date()
        days_left = (expiry - today).days
        if days_left <= days:
            expiring.append((name, info, days_left))
    return expiring

def show_inventory() -> None:
    """显示当前库存"""
    inventory = load_inventory()
    if not inventory:
        print("冰箱是空的！")
        return
    print("\n📦 当前库存：")
    print("─" * 40)
    expiring = get_expiring_soon()
    expiring_names = [e[0] for e in expiring]
    for name, info in inventory.items():
        warning = " ⚠️ 快过期！" if name in expiring_names else ""
        print(f"  {name}: {info['数量']}{info['单位']} （过期：{info['过期日期']}）{warning}")
    print("─" * 40)