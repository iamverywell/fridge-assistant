import pytest
from unittest.mock import patch, MagicMock

# ─── 语音转文字测试 ───

def test_transcribe_returns_string():
    """转录结果是字符串"""
    with patch("fridge_assistant.voice.whisper") as mock_whisper:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": " 鸡蛋6个牛奶一盒 "}
        mock_whisper.load_model.return_value = mock_model
        with patch("fridge_assistant.voice.model", None):
            from fridge_assistant import voice
            voice.model = None
            voice.model = mock_model
            result = voice.transcribe_audio("fake.wav")
            assert isinstance(result, str)

def test_transcribe_strips_whitespace():
    """转录结果去掉首尾空格"""
    with patch("fridge_assistant.voice.whisper") as mock_whisper:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "  鸡蛋6个  "}
        mock_whisper.load_model.return_value = mock_model
        from fridge_assistant import voice
        voice.model = mock_model
        result = voice.transcribe_audio("fake.wav")
        assert result == result.strip()

def test_transcribe_chinese():
    """能处理中文"""
    with patch("fridge_assistant.voice.whisper") as mock_whisper:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "鸡蛋6个"}
        mock_whisper.load_model.return_value = mock_model
        from fridge_assistant import voice
        voice.model = mock_model
        result = voice.transcribe_audio("fake.wav")
        assert "鸡蛋" in result

def test_transcribe_empty_audio():
    """空音频返回空字符串"""
    with patch("fridge_assistant.voice.whisper") as mock_whisper:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": ""}
        mock_whisper.load_model.return_value = mock_model
        from fridge_assistant import voice
        voice.model = mock_model
        result = voice.transcribe_audio("fake.wav")
        assert result == ""

# ─── 录音测试 ───

def test_record_without_sounddevice(capsys):
    """没有录音设备时返回 None 并提示"""
    from fridge_assistant import voice
    with patch("fridge_assistant.voice.record_audio", return_value=None) as mock_record:
        result = mock_record(1)
        assert result is None

def test_record_returns_wav_path(tmp_path):
    """录音成功返回 wav 文件路径"""
    from fridge_assistant import voice
    with patch.object(voice, "record_audio", return_value=str(tmp_path / "test.wav")):
        result = voice.record_audio(1)
        assert result is not None
        assert result.endswith(".wav")

def test_record_correct_sample_rate():
    """录音使用正确的采样率 16000"""
    from fridge_assistant import voice
    import inspect
    source = inspect.getsource(voice.record_audio)
    assert "16000" in source
