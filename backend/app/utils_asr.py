from __future__ import annotations
from faster_whisper import WhisperModel
from typing import Tuple, List, Dict, Any
import tempfile
from pydub import AudioSegment
import io

_model = None
_model_size = None

def get_whisper(model_size: str = "tiny") -> WhisperModel:
    global _model, _model_size
    if _model is None or _model_size != model_size:
        _model = WhisperModel(model_size, device="cpu", compute_type="int8")
        _model_size = model_size
    return _model

def transcribe_bytes(file_bytes: bytes, language: str = "en", model_size: str = "tiny"):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        model = get_whisper(model_size=model_size)
        segments, info = model.transcribe(tmp.name, language=language)
        segs = []
        text = ""
        for seg in segments:
            segs.append({"start": seg.start, "end": seg.end, "text": seg.text})
            text += seg.text
        return text.strip(), segs, {"language": info.language, "duration": info.duration}

def convert_audio_to_mono_wav(audio_bytes: bytes) -> bytes:
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    audio = audio.set_channels(1)  # Convert to mono
    
    # Export to WAV format in memory
    mono_wav_bytes = io.BytesIO()
    audio.export(mono_wav_bytes, format="wav")
    return mono_wav_bytes.getvalue()
