from .llm import chat, analyze_image
from .inventory import (
    load_inventory, add_item, remove_item,
    use_item, get_expiring_soon,
)

def suggest_recipes(access_token: str) -> str:
    """根据当前库存推荐菜谱"""
    inventory = load_inventory(access_token)
    if not inventory:
        return "冰箱是空的，请先添加食材！"

    expiring = get_expiring_soon(access_token)
    expiring_names = [e["name"] for e in expiring]
    items = [f"{i['name']} {i['quantity']}{i['unit']}" for i in inventory]

    system = """你是一个专业厨师助手，根据用户现有食材推荐菜谱。
回答格式：
1. 菜名
   食材：...
   做法：简单3步
"""
    expiring_note = (
        f"\n特别注意，这些食材快过期了，优先用：{', '.join(expiring_names)}"
        if expiring_names else ""
    )
    user = f"我冰箱里有：{', '.join(items)}{expiring_note}\n请推荐3个菜谱"
    return chat(system=system, user=user)


def analyze_nutrition(access_token: str) -> str:
    """分析当前库存的营养状况"""
    inventory = load_inventory(access_token)
    if not inventory:
        return "冰箱是空的！"

    items = [f"{i['name']} {i['quantity']}{i['unit']}" for i in inventory]
    system = "你是营养师助手，分析食材的营养均衡情况，给出简短建议。"
    user = f"我冰箱里有：{', '.join(items)}\n请分析营养是否均衡，缺什么？"
    return chat(system=system, user=user)


def generate_shopping_list(access_token: str) -> str:
    """生成购物清单建议"""
    inventory = load_inventory(access_token)
    items = (
        [f"{i['name']} {i['quantity']}{i['unit']}" for i in inventory]
        if inventory else ["冰箱是空的"]
    )
    system = "你是生活助手，根据现有食材推荐需要补充的食材，给出购物清单。"
    user = f"我冰箱里现有：{', '.join(items)}\n请推荐我下次购物应该买什么，给出购物清单"
    return chat(system=system, user=user)


def scan_receipt(access_token: str, user_id: str, image_path: str) -> None:
    """扫描小票自动入库（CLI 用）"""
    from .llm import analyze_image as _analyze
    print("📸 正在分析小票...")
    result = _analyze(image_path)
    print(f"识别结果：\n{result}")
    print("\n请确认以上食材是否正确？(y/n)")
    if input().strip().lower() == "y":
        for line in result.strip().split("\n"):
            parts = line.strip().split()
            if len(parts) >= 2:
                name = parts[0]
                try:
                    quantity = float(parts[1])
                    unit = parts[2] if len(parts) > 2 else "个"
                    expiry = input(f"  {name} 过期日期：").strip()
                    add_item(access_token, user_id, name, quantity, unit, expiry or None)
                except ValueError:
                    pass


def parse_voice_text(text: str) -> list[dict]:
    """用 Claude 把语音文字解析成结构化食材列表"""
    system = """你是一个食材解析助手。用户会说一段话描述买了什么食材。
请把这段话解析成结构化的食材列表，用JSON格式返回。

格式：
[
  {"name": "鸡蛋", "quantity": 6, "unit": "个", "expiry": "2026-05-15"},
  {"name": "牛奶", "quantity": 2, "unit": "盒", "expiry": null}
]

规则：
- 没有提到过期日期就填 null
- 数量用数字
- 只返回JSON，不要其他文字"""

    result = chat(system=system, user=text)
    import json
    try:
        clean = result.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        return json.loads(clean.strip())
    except Exception:
        return []
