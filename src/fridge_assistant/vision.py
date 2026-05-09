import base64
import anthropic
from .config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

def analyze_image(image_path: str, mode: str = "receipt") -> str:
    """
    分析图片
    mode: "receipt" = 小票模式，"fridge" = 冰箱实物模式
    """
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    if mode == "receipt":
        prompt = """这是一张购物小票，请列出所有食材类商品。
格式：每行一个，食材名称 数量 单位
例如：
鸡蛋 6 个
牛奶 1 盒
只列食材，不要列非食品类商品。"""
    else:
        prompt = """这是一张冰箱照片，请识别里面所有可见的食材。
格式：每行一个，食材名称 数量 单位（数量不确定写1）
例如：
鸡蛋 6 个
牛奶 1 盒
西红柿 3 个
尽量识别所有可见食材。"""

    msg = client.messages.create(
        model=settings.model,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ],
        }],
    )
    return msg.content[0].text

def parse_items(text: str) -> list[dict]:
    """把识别结果解析成结构化数据"""
    items = []
    for line in text.strip().split("\n"):
        parts = line.strip().split()
        if len(parts) >= 2:
            try:
                name = parts[0]
                quantity = float(parts[1])
                unit = parts[2] if len(parts) > 2 else "个"
                items.append({
                    "name": name,
                    "quantity": quantity,
                    "unit": unit
                })
            except ValueError:
                continue
    return items
