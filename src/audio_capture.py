"""
Live Microphone Capture and Audio Buffering module.
Implements a thread-safe ring/linear buffer for continuous live call recording,
supporting 'Mark Question Start' and 'Get Answer Now' slice extraction.
"""

import threading
import time
from pathlib import Path
from typing import Optional, Tuple, List
import numpy as np
from scipy.io import wavfile

SAMPLE_RATE = 16000  # 16kHz standard for Whisper speech models
CHANNELS = 1         # Mono audio


class LiveCallAudioBuffer:
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.is_recording = False
        self.call_start_time: Optional[float] = None
        self.question_start_sample: Optional[int] = None
        self.question_start_time: Optional[float] = None
        
        self._chunks: List[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream = None

    def start_call(self) -> Tuple[bool, str]:
        """
        Start capturing continuous microphone audio into memory buffer.
        """
        import sounddevice as sd

        if self.is_recording:
            return True, "Call recording is already in progress."

        with self._lock:
            self._chunks = []
            self.question_start_sample = None
            self.question_start_time = None
            self.call_start_time = time.time()
            self.is_recording = True

        def audio_callback(indata, frames, time_info, status):
            if status:
                # Driver overflow/underflow notice (non-fatal)
                pass
            if self.is_recording:
                # Copy float32 mono data into chunks
                with self._lock:
                    self._chunks.append(indata.copy())

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=CHANNELS,
                dtype="float32",
                callback=audio_callback
            )
            self._stream.start()
            return True, "Microphone capture started successfully."
        except Exception as e:
            self.is_recording = False
            return False, f"Failed to initialize microphone: {str(e)}. Please check microphone permissions."

    def mark_question_start(self) -> Tuple[bool, float, str]:
        """
        Record the current audio position as the beginning of the customer question.
        Returns: (success, timestamp_offset_seconds, status_message)
        """
        if not self.is_recording:
            return False, 0.0, "Cannot mark question start: Call is not currently active."

        with self._lock:
            current_samples = sum(len(c) for c in self._chunks)
            self.question_start_sample = current_samples
            self.question_start_time = time.time()
            offset_sec = round(current_samples / self.sample_rate, 2)

        return True, offset_sec, f"Question start marked at {offset_sec:.1f}s into the call."

    def get_elapsed_call_time(self) -> float:
        """Return total elapsed call time in seconds."""
        if not self.call_start_time:
            return 0.0
        return round(time.time() - self.call_start_time, 1)

    def extract_question_segment(self) -> Tuple[Optional[np.ndarray], float, Optional[str]]:
        """
        Extract the audio segment from marked question start to current moment.
        If question start was not marked, extracts from call beginning or last 15 seconds.
        Returns: (audio_array, duration_seconds, error_message)
        """
        with self._lock:
            if not self._chunks:
                return None, 0.0, "Audio buffer is empty. No voice data recorded yet."

            full_audio = np.concatenate(self._chunks, axis=0).flatten()

            start_idx = self.question_start_sample if self.question_start_sample is not None else 0
            end_idx = len(full_audio)

            if start_idx >= end_idx:
                return None, 0.0, "Marked segment is empty (marked point is at current end)."

            segment = full_audio[start_idx:end_idx]
            duration = len(segment) / self.sample_rate

            if duration < 0.4:
                return None, duration, f"Extracted audio segment is too short ({duration:.2f}s). Please speak a complete question."

            return segment, duration, None

    def stop_call(self) -> None:
        """Stop microphone stream and audio capture."""
        self.is_recording = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def save_segment_to_wav(self, segment: np.ndarray, destination_path: Path) -> Path:
        """
        Save a numpy float32 audio segment as a 16-bit PCM WAV file.
        """
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        # Convert float32 [-1.0, 1.0] to int16 [-32768, 32767]
        clipped = np.clip(segment, -1.0, 1.0)
        pcm16 = (clipped * 32767).astype(np.int16)
        wavfile.write(str(destination_path), self.sample_rate, pcm16)
        return destination_path
