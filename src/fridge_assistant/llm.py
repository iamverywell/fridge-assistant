import anthropic
import base64
from .config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

def chat(system: str, user: str) -> str:
    """文字对话"""
    msg = client.messages.create(
        model=settings.model,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text

def analyze_image(image_path: str) -> str:
    """分析图片里的食材"""
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    
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
                    "text": "请列出这张图片里所有的食材，格式：食材名称 数量 单位，每行一个"
                }
            ],
        }],
    )
    return msg.content[0].text