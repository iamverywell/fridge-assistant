from .llm import chat, analyze_image
from .inventory import (
    load_inventory, add_item, remove_item,
    use_item, show_inventory, get_expiring_soon
)

def suggest_recipes() -> str:
    """根据当前库存推荐菜谱"""
    inventory = load_inventory()
    if not inventory:
        return "冰箱是空的，请先添加食材！"
    
    # 优先用快过期的食材
    expiring = get_expiring_soon()
    expiring_names = [e[0] for e in expiring]
    
    items = []
    for name, info in inventory.items():
        items.append(f"{name} {info['数量']}{info['单位']}")
    
    system = """你是一个专业厨师助手，根据用户现有食材推荐菜谱。
回答格式：
1. 菜名
   食材：...
   做法：简单3步
"""
    
    expiring_note = f"\n特别注意，这些食材快过期了，优先用：{', '.join(expiring_names)}" if expiring_names else ""
    user = f"我冰箱里有：{', '.join(items)}{expiring_note}\n请推荐3个菜谱"
    
    return chat(system=system, user=user)

def analyze_nutrition() -> str:
    """分析当前库存的营养状况"""
    inventory = load_inventory()
    if not inventory:
        return "冰箱是空的！"
    
    items = [f"{name} {info['数量']}{info['单位']}" 
             for name, info in inventory.items()]
    
    system = "你是营养师助手，分析食材的营养均衡情况，给出简短建议。"
    user = f"我冰箱里有：{', '.join(items)}\n请分析营养是否均衡，缺什么？"
    
    return chat(system=system, user=user)

def generate_shopping_list() -> str:
    """生成购物清单建议"""
    inventory = load_inventory()
    items = [f"{name} {info['数量']}{info['单位']}" 
             for name, info in inventory.items()] if inventory else ["冰箱是空的"]
    
    system = "你是生活助手，根据现有食材推荐需要补充的食材，给出购物清单。"
    user = f"我冰箱里现有：{', '.join(items)}\n请推荐我下次购物应该买什么，给出购物清单"
    
    return chat(system=system, user=user)

def scan_receipt(image_path: str) -> None:
    """扫描小票自动入库"""
    print("📸 正在分析小票...")
    result = analyze_image(image_path)
    print(f"识别结果：\n{result}")
    print("\n请确认以上食材是否正确？(y/n)")
    if input().strip().lower() == "y":
        print("请为每个食材输入过期日期（格式 2026-05-15，不知道直接回车）：")
        for line in result.strip().split("\n"):
            parts = line.strip().split()
            if len(parts) >= 2:
                name = parts[0]
                try:
                    quantity = float(parts[1])
                    unit = parts[2] if len(parts) > 2 else "个"
                    expiry = input(f"  {name} 过期日期：").strip()
                    add_item(name, quantity, unit, expiry or None)
                except ValueError:
                    pass




                