"""
Speech-to-Text module using local Faster-Whisper.
Provides reliable transcription of WAV/MP3 files or in-memory audio numpy arrays.
Bypasses PyAV container incompatibilities by decoding audio into float32 waveforms.
Measures actual latency and handles inaudible/silent speech gracefully.
"""

import os
import time
from pathlib import Path
from typing import Tuple, Optional, Union
import numpy as np
from scipy.io import wavfile

# Global whisper model cache to avoid re-loading weights on every query
_WHISPER_MODEL = None
_CURRENT_MODEL_SIZE = None


def get_whisper_model(
    model_size: Optional[str] = None,
    device: Optional[str] = None,
    compute_type: Optional[str] = None
):
    """
    Load or retrieve cached Faster-Whisper model.
    Defaults to CPU with int8 quantization for lightweight, reliable execution.
    """
    global _WHISPER_MODEL, _CURRENT_MODEL_SIZE
    from faster_whisper import WhisperModel

    model_size = model_size or os.getenv("WHISPER_MODEL_SIZE", "tiny.en")
    device = device or os.getenv("WHISPER_DEVICE", "cpu")
    compute_type = compute_type or os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    if _WHISPER_MODEL is None or _CURRENT_MODEL_SIZE != model_size:
        _WHISPER_MODEL = WhisperModel(
            model_size_or_path=model_size,
            device=device,
            compute_type=compute_type
        )
        _CURRENT_MODEL_SIZE = model_size

    return _WHISPER_MODEL


def load_audio_waveform(audio_path: Union[str, Path]) -> Tuple[Optional[np.ndarray], int]:
    """
    Load audio from file into a 16kHz float32 mono numpy array.
    """
    path_obj = Path(audio_path)
    if not path_obj.exists() or path_obj.stat().st_size == 0:
        return None, 0

    try:
        # First attempt: standard WAV reader
        rate, data = wavfile.read(str(path_obj))
        # Convert stereo to mono if needed
        if data.ndim > 1:
            data = data.mean(axis=1)

        # Convert to float32 normalized between -1.0 and 1.0
        if data.dtype == np.int16:
            audio = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            audio = data.astype(np.float32) / 2147483648.0
        elif data.dtype == np.uint8:
            audio = (data.astype(np.float32) - 128.0) / 128.0
        else:
            audio = data.astype(np.float32)

        # Simple resample to 16000Hz if needed
        if rate != 16000 and len(audio) > 0:
            target_len = int(len(audio) * 16000 / rate)
            indices = np.linspace(0, len(audio) - 1, target_len)
            audio = np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)
            rate = 16000

        return audio, rate
    except Exception:
        # Fallback for MP3 or non-standard WAV
        try:
            import soundfile as sf
            data, rate = sf.read(str(path_obj), dtype="float32")
            if data.ndim > 1:
                data = data.mean(axis=1)
            if rate != 16000 and len(data) > 0:
                target_len = int(len(data) * 16000 / rate)
                indices = np.linspace(0, len(data) - 1, target_len)
                data = np.interp(indices, np.arange(len(data)), data).astype(np.float32)
            return data, 16000
        except Exception:
            return None, 0


def transcribe_audio_file(
    audio_source: Union[str, Path, np.ndarray],
    model_size: Optional[str] = None
) -> Tuple[str, float, Optional[str]]:
    """
    Transcribe a local audio file (WAV/MP3) or in-memory numpy float32 array.
    
    Returns:
        transcribed_text (str): Extracted spoken query.
        latency_seconds (float): Measured wall-clock time in seconds.
        error (Optional[str]): Error message if transcription failed.
    """
    start_time = time.time()

    if isinstance(audio_source, (str, Path)):
        audio_array, _ = load_audio_waveform(audio_source)
        if audio_array is None or len(audio_array) == 0:
            return "", 0.0, f"Unable to decode audio or audio is empty: {audio_source}"
    elif isinstance(audio_source, np.ndarray):
        audio_array = audio_source.astype(np.float32)
        if len(audio_array) == 0:
            return "", 0.0, "Provided audio buffer is empty."
    else:
        return "", 0.0, f"Unsupported audio source type: {type(audio_source)}"

    try:
        model = get_whisper_model(model_size=model_size)
        segments, info = model.transcribe(
            audio_array,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        text_pieces = [s.text.strip() for s in segments if s.text.strip()]
        full_transcription = " ".join(text_pieces).strip()
        latency = round(time.time() - start_time, 3)

        if not full_transcription:
            return "", latency, "No audible speech detected in the provided audio."

        return full_transcription, latency, None

    except Exception as e:
        latency = round(time.time() - start_time, 3)
        return "", latency, f"Transcription error: {str(e)}"
