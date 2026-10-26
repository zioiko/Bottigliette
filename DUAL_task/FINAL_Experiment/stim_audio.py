"""
stim_audio.py — low-latency stimulus playback with onset-locked triggering.

All WAVs are loaded into RAM once, and a single audio stream stays open for the
whole session (playing silence between trials). Starting a sound is just a
pointer swap inside the audio callback, so there is no file loading and no
device wake-up at trial time.

    pip install sounddevice soundfile numpy
"""
import threading
import time

import numpy as np
import sounddevice as sd
import soundfile as sf


class StimPlayer:
    def __init__(self, wav_paths, device=None, blocksize=256,
                 latency="low", wasapi_exclusive=False):
        # ---- preload every stimulus into memory ----
        self.sounds = {}
        rates, chans = set(), set()
        for p in set(wav_paths):
            data, sr = sf.read(p, dtype="float32", always_2d=True)
            self.sounds[p] = data
            rates.add(sr)
            chans.add(data.shape[1])
        if len(rates) != 1:
            raise ValueError(f"All WAVs must share one sample rate, found {rates}")
        self.sr = rates.pop()
        self.channels = max(chans)
        # mono -> stereo (or N channels) so every buffer matches the stream
        for p, d in self.sounds.items():
            if d.shape[1] == 1 and self.channels > 1:
                self.sounds[p] = np.repeat(d, self.channels, axis=1)

        self._lock = threading.Lock()
        self._current = None
        self._pos = 0
        self._started = threading.Event()
        self._onset_dac_time = None

        extra = sd.WasapiSettings(exclusive=True) if wasapi_exclusive else None
        self.stream = sd.OutputStream(
            samplerate=self.sr, channels=self.channels, dtype="float32",
            blocksize=blocksize, latency=latency, device=device,
            extra_settings=extra, callback=self._callback,
        )
        self.stream.start()  # stays open (outputs silence) until close()

    # runs in PortAudio's real-time thread
    def _callback(self, outdata, frames, time_info, status):
        outdata.fill(0)
        with self._lock:
            if self._current is None:
                return
            chunk = self._current[self._pos:self._pos + frames]
            outdata[:len(chunk)] = chunk
            if self._pos == 0:
                # stream-clock time at which this buffer's first sample hits the DAC
                self._onset_dac_time = time_info.outputBufferDacTime
                self._started.set()
            self._pos += len(chunk)
            if self._pos >= len(self._current):
                self._current = None

    def play(self, path):
        """Queue a preloaded sound; it starts in the next audio buffer (~ms)."""
        self._started.clear()
        with self._lock:
            self._current = self.sounds[path]
            self._pos = 0

    def wait_onset(self, timeout=1.0):
        """Block until the first sample is actually leaving the sound card.
        Returns the residual wait (s) that was spent spinning."""
        if not self._started.wait(timeout):
            raise RuntimeError("Audio callback never started the sound")
        remaining = self._onset_dac_time - self.stream.time
        if remaining > 0:
            t_end = time.perf_counter() + remaining
            while time.perf_counter() < t_end:  # busy-wait: sub-ms precision
                pass
        return remaining

    def is_playing(self):
        return self._current is not None

    def stop(self):
        with self._lock:
            self._current = None

    def close(self):
        self.stream.stop()
        self.stream.close()


if __name__ == "__main__":
    # Quick diagnostics: list devices, and check WAVs for leading silence.
    import sys
    print(sd.query_devices())
    for p in sys.argv[1:]:
        d, sr = sf.read(p, always_2d=True)
        thr = 0.01 * np.abs(d).max()
        first = np.argmax(np.abs(d).max(axis=1) > thr)
        print(f"{p}: first audible sample at {1000 * first / sr:.1f} ms")
