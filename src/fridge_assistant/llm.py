import time
import hashlib
import anthropic
import base64
import structlog
from .config import settings

def redact_prompt(_, __, event):
    if "prompt" in event:
        p = event.pop("prompt")
        event["prompt_sha"] = hashlib.sha256(p.encode()).hexdigest()[:8]
        event["prompt_len"] = len(p)
    return event

structlog.configure(processors=[
    redact_prompt,
    structlog.dev.ConsoleRenderer(),
])

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
log = structlog.get_logger()

def chat(system: str, user: str) -> str:
    """文字对话"""
    full_prompt = system + user
    log.info("llm_call_start",
        func="chat",
        prompt=full_prompt,        # 会被 redact_prompt 自动处理掉
        model=settings.model,
    )
    t0 = time.time()
    msg = client.messages.create(
        model=settings.model,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    log.info("llm_call_done",
        func="chat",
        latency_ms=int((time.time() - t0) * 1000),
        input_tokens=msg.usage.input_tokens,
        output_tokens=msg.usage.output_tokens,
    )
    return msg.content[0].text

def analyze_image(image_path: str) -> str:
    """分析图片里的食材"""
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    log.info("llm_call_start", func="analyze_image", model=settings.model)

    t0 = time.time()
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
    log.info("llm_call_done",
        func="analyze_image",
        latency_ms=int((time.time() - t0) * 1000),
        input_tokens=msg.usage.input_tokens,
        output_tokens=msg.usage.output_tokens,
    )
    return msg.content[0].text