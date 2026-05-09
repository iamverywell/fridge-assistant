import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# ─── 推荐菜谱测试 ───

@pytest.fixture
def temp_inventory(tmp_path):
    import json
    temp_file = tmp_path / "inventory.json"
    temp_file.write_text(json.dumps({
        "鸡蛋": {"数量": 6, "单位": "个", "过期日期": "未知"},
        "西红柿": {"数量": 3, "单位": "个", "过期日期": "未知"},
    }, ensure_ascii=False))
    with patch("fridge_assistant.inventory.INVENTORY_FILE", temp_file):
        yield temp_file

def test_suggest_recipes_returns_string(temp_inventory):
    """推荐菜谱返回字符串"""
    with patch("fridge_assistant.app.chat") as mock_chat:
        mock_chat.return_value = "1. 番茄炒蛋\n食材：西红柿、鸡蛋"
        from fridge_assistant.app import suggest_recipes
        result = suggest_recipes()
        assert isinstance(result, str)
        assert len(result) > 0

def test_suggest_recipes_uses_inventory(temp_inventory):
    """推荐菜谱用到了库存食材"""
    with patch("fridge_assistant.app.chat") as mock_chat:
        mock_chat.return_value = "番茄炒蛋"
        from fridge_assistant.app import suggest_recipes
        suggest_recipes()
        call_args = mock_chat.call_args
        assert "鸡蛋" in call_args.kwargs["user"]
        assert "西红柿" in call_args.kwargs["user"]

def test_suggest_recipes_empty_inventory():
    """空库存时提示"""
    with patch("fridge_assistant.inventory.INVENTORY_FILE") as mock_file:
        with patch("fridge_assistant.app.load_inventory") as mock_load:
            mock_load.return_value = {}
            from fridge_assistant.app import suggest_recipes
            result = suggest_recipes()
            assert "空" in result

# ─── 营养分析测试 ───

def test_analyze_nutrition_returns_string(temp_inventory):
    """营养分析返回字符串"""
    with patch("fridge_assistant.app.chat") as mock_chat:
        mock_chat.return_value = "蛋白质充足，缺少蔬菜"
        from fridge_assistant.app import analyze_nutrition
        result = analyze_nutrition()
        assert isinstance(result, str)

def test_analyze_nutrition_empty_inventory():
    """空库存时提示"""
    with patch("fridge_assistant.app.load_inventory") as mock_load:
        mock_load.return_value = {}
        from fridge_assistant.app import analyze_nutrition
        result = analyze_nutrition()
        assert "空" in result

# ─── 购物清单测试 ───

def test_generate_shopping_list_returns_string(temp_inventory):
    """购物清单返回字符串"""
    with patch("fridge_assistant.app.chat") as mock_chat:
        mock_chat.return_value = "建议购买：牛奶、面包"
        from fridge_assistant.app import generate_shopping_list
        result = generate_shopping_list()
        assert isinstance(result, str)

def test_generate_shopping_list_empty_inventory():
    """空库存也能生成购物清单"""
    with patch("fridge_assistant.app.load_inventory") as mock_load:
        mock_load.return_value = {}
        with patch("fridge_assistant.app.chat") as mock_chat:
            mock_chat.return_value = "建议购买基本食材"
            from fridge_assistant.app import generate_shopping_list
            result = generate_shopping_list()
            assert isinstance(result, str)

# ─── 图片识别测试 ───

def test_scan_receipt_calls_analyze_image(tmp_path):
    """扫描小票调用了图片识别"""
    fake_image = tmp_path / "receipt.jpg"
    fake_image.write_bytes(b"fake image data")
    
    with patch("fridge_assistant.app.analyze_image") as mock_analyze:
        mock_analyze.return_value = "鸡蛋 6 个\n牛奶 1 盒"
        with patch("builtins.input", return_value="n"):
            from fridge_assistant.app import scan_receipt
            scan_receipt(str(fake_image))
            mock_analyze.assert_called_once_with(str(fake_image))

def test_scan_receipt_parses_items(tmp_path, capsys):
    """扫描结果正确解析食材"""
    fake_image = tmp_path / "receipt.jpg"
    fake_image.write_bytes(b"fake image data")
    
    with patch("fridge_assistant.app.analyze_image") as mock_analyze:
        mock_analyze.return_value = "鸡蛋 6 个\n牛奶 1 盒"
        with patch("builtins.input", side_effect=["y", "", ""]):
            with patch("fridge_assistant.app.add_item") as mock_add:
                from fridge_assistant.app import scan_receipt
                scan_receipt(str(fake_image))
                assert mock_add.call_count == 2
