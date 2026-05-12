import whisper
import tempfile

model = None

def load_model():
    global model
    if model is None:
        print("正在加载语音模型...")
        model = whisper.load_model("tiny")
    return model

def transcribe_audio(audio_path: str) -> str:
    m = load_model()
    result = m.transcribe(audio_path, language="zh")
    return result["text"].strip()

def record_audio(seconds: int = 5) -> str:
    try:
        import sounddevice as sd
        import numpy as np
        import scipy.io.wavfile as wav

        print(f"🎤 开始录音 {seconds} 秒...")
        sample_rate = 16000
        recording = sd.rec(
            int(seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )
        sd.wait()
        print("✅ 录音完成！")

        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wav.write(temp_file.name, sample_rate, recording)
        return temp_file.name

    except ImportError:
        print("❌ 需要安装录音库：uv add sounddevice scipy")
        return None
