import pytest
from unittest.mock import patch, MagicMock

# ─── 图片识别测试 ───

def test_analyze_receipt_mode(tmp_path):
    """小票模式调用正确的 prompt"""
    fake_image = tmp_path / "receipt.jpg"
    fake_image.write_bytes(b"fake")

    with patch("fridge_assistant.vision.client") as mock_client:
        mock_msg = MagicMock()
        mock_msg.content[0].text = "鸡蛋 6 个\n牛奶 1 盒"
        mock_client.messages.create.return_value = mock_msg

        from fridge_assistant.vision import analyze_image
        result = analyze_image(str(fake_image), mode="receipt")
        
        call_args = mock_client.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"][1]["text"]
        assert "小票" in prompt
        assert "鸡蛋" in result

def test_analyze_fridge_mode(tmp_path):
    """冰箱模式调用正确的 prompt"""
    fake_image = tmp_path / "fridge.jpg"
    fake_image.write_bytes(b"fake")

    with patch("fridge_assistant.vision.client") as mock_client:
        mock_msg = MagicMock()
        mock_msg.content[0].text = "西红柿 3 个\n排骨 500 克"
        mock_client.messages.create.return_value = mock_msg

        from fridge_assistant.vision import analyze_image
        result = analyze_image(str(fake_image), mode="fridge")

        call_args = mock_client.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"][1]["text"]
        assert "冰箱" in prompt
        assert "西红柿" in result

def test_analyze_returns_string(tmp_path):
    """识别结果是字符串"""
    fake_image = tmp_path / "test.jpg"
    fake_image.write_bytes(b"fake")

    with patch("fridge_assistant.vision.client") as mock_client:
        mock_msg = MagicMock()
        mock_msg.content[0].text = "鸡蛋 6 个"
        mock_client.messages.create.return_value = mock_msg

        from fridge_assistant.vision import analyze_image
        result = analyze_image(str(fake_image))
        assert isinstance(result, str)

# ─── 解析测试 ───

def test_parse_basic():
    """基本解析"""
    from fridge_assistant.vision import parse_items
    result = parse_items("鸡蛋 6 个\n牛奶 1 盒")
    assert len(result) == 2
    assert result[0]["name"] == "鸡蛋"
    assert result[0]["quantity"] == 6.0
    assert result[0]["unit"] == "个"

def test_parse_without_unit():
    """没有单位默认用'个'"""
    from fridge_assistant.vision import parse_items
    result = parse_items("苹果 3")
    assert result[0]["unit"] == "个"

def test_parse_decimal():
    """小数数量"""
    from fridge_assistant.vision import parse_items
    result = parse_items("猪肉 0.5 斤")
    assert result[0]["quantity"] == 0.5

def test_parse_empty():
    """空字符串返回空列表"""
    from fridge_assistant.vision import parse_items
    result = parse_items("")
    assert result == []

def test_parse_invalid_lines():
    """忽略无效行"""
    from fridge_assistant.vision import parse_items
    result = parse_items("鸡蛋 6 个\n这不是食材\n牛奶 1 盒")
    assert len(result) == 2
