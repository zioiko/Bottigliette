"""
gopro_webcam_recorder.py
------------------------
Record a GoPro HERO8 Black straight to the PC, controlled from your experiment
script, with a timestamp logged for every frame.

Requires:  pip install opencv-python
Target:    Python 3.14, Windows 11.

Setup before running (once):
  1. Camera firmware v2.50 or later (v2.51 is the last HERO8 release).
  2. On the camera: Preferences > Connections > USB Connection > "GoPro Connect"
     (NOT MTP -- this is the step that trips most people up).
  3. Install the GoPro Webcam Desktop Utility for Windows.
  4. Plug in via USB-C. The camera shows a webcam icon; Windows now has a
     video device called "GoPro Webcam".

Run this file directly once to find your camera's device index:
      python gopro_webcam_recorder.py --list

In webcam mode the camera does NOT write to its SD card. Everything is saved
by this script on the PC.
"""

from __future__ import annotations

import csv
import sys
import time
import queue
import logging
import threading
from pathlib import Path

import cv2

log = logging.getLogger(__name__)


def list_cameras(max_index: int = 6) -> None:
    """Print which device indices are usable. Run this once during setup."""
    print("Probing video devices (this takes a few seconds)...\n")
    for i in range(max_index):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ok, frame = cap.read()
            if ok:
                h, w = frame.shape[:2]
                print(f"  index {i}: OK  -  {w}x{h}")
            else:
                print(f"  index {i}: opened but returned no frame")
            cap.release()
        else:
            print(f"  index {i}: not available")
    print("\nThe GoPro is usually the highest working index (index 0 is "
          "typically your laptop's built-in camera).")


class GoProRecorder:
    """
    Keeps the camera stream open continuously in a background thread, and
    writes frames to a file only between start_recording() and stop_recording().

    Because the stream is already warm, start_recording() returns in a few
    milliseconds rather than the ~1 s a GoPro Wi-Fi shutter command takes.

    Usage:

        rec = GoProRecorder(device_index=1, out_dir="data/sub01")
        rec.open()

        rec.start_recording("trial_01")
        rec.mark("stimulus_on")          # optional event marker
        ... your trial code ...
        rec.stop_recording()

        rec.close()
    """

    def __init__(
        self,
        device_index: int = 1,
        out_dir: str | Path = ".",
        width: int = 1280,
        height: int = 720,
        fps: float = 30.0,
        fourcc: str = "mp4v",
        ext: str = ".mp4",
    ) -> None:
        self.device_index = device_index
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.width = width
        self.height = height
        self.fps = fps
        self.fourcc = fourcc
        self.ext = ext

        self._cap: cv2.VideoCapture | None = None
        self._writer: cv2.VideoWriter | None = None
        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self._recording = threading.Event()
        self._lock = threading.Lock()

        # Frames are handed to a writer thread through this queue so that a slow
        # disk write can never block frame capture.
        self._write_q: queue.Queue = queue.Queue(maxsize=120)
        self._writer_thread: threading.Thread | None = None

        self.frame_index = 0
        self.frames_dropped = 0
        self._ts_rows: list[tuple] = []
        self._marks: list[tuple] = []
        self._current_name = ""
        self.latest_frame = None   # for optional live preview

    # -- lifecycle ------------------------------------------------------------

    def open(self) -> None:
        """Open the camera and start the capture thread."""
        cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            raise RuntimeError(
                f"Could not open video device {self.device_index}. "
                f"Run 'python {Path(__file__).name} --list' to find the right index."
            )
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # keep latency low

        ok, frame = cap.read()
        if not ok:
            cap.release()
            raise RuntimeError("Camera opened but delivered no frames. "
                               "Is the GoPro in webcam mode?")

        actual_h, actual_w = frame.shape[:2]
        if (actual_w, actual_h) != (self.width, self.height):
            log.warning("Requested %dx%d but got %dx%d; using the actual size.",
                        self.width, self.height, actual_w, actual_h)
            self.width, self.height = actual_w, actual_h

        self._cap = cap
        self._stop_flag.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        self._writer_thread = threading.Thread(target=self._write_loop, daemon=True)
        self._writer_thread.start()
        log.info("Camera open at %dx%d.", self.width, self.height)

    def close(self) -> None:
        if self._recording.is_set():
            self.stop_recording()
        self._stop_flag.set()
        if self._thread:
            self._thread.join(timeout=3)
        if self._writer_thread:
            self._writer_thread.join(timeout=5)
        if self._cap:
            self._cap.release()
            self._cap = None
        log.info("Camera closed.")

    def __enter__(self) -> "GoProRecorder":
        self.open()
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    # -- threads --------------------------------------------------------------

    def _capture_loop(self) -> None:
        while not self._stop_flag.is_set():
            ok, frame = self._cap.read()
            if not ok:
                log.warning("Dropped read from camera.")
                time.sleep(0.005)
                continue
            t_cap = time.perf_counter()
            t_wall = time.time()
            self.latest_frame = frame

            if self._recording.is_set():
                try:
                    self._write_q.put_nowait((frame, self.frame_index, t_cap, t_wall))
                    self._ts_rows.append((self.frame_index, t_cap, t_wall))
                    self.frame_index += 1
                except queue.Full:
                    self.frames_dropped += 1
                    log.warning("Write queue full; frame dropped (%d total).",
                                self.frames_dropped)

    def _write_loop(self) -> None:
        while not (self._stop_flag.is_set() and self._write_q.empty()):
            try:
                frame, *_ = self._write_q.get(timeout=0.2)
            except queue.Empty:
                continue
            with self._lock:
                if self._writer is not None:
                    self._writer.write(frame)

    # -- the calls you put in your experiment ---------------------------------

    def start_recording(self, name: str | None = None) -> float:
        """Begin writing frames. Returns the perf_counter timestamp of the call."""
        if self._recording.is_set():
            log.warning("start_recording() called while already recording.")
            return time.perf_counter()

        name = name or f"rec_{time.strftime('%Y%m%d_%H%M%S')}"
        self._current_name = name
        video_path = self.out_dir / f"{name}{self.ext}"

        writer = cv2.VideoWriter(
            str(video_path),
            cv2.VideoWriter_fourcc(*self.fourcc),
            self.fps,
            (self.width, self.height),
        )
        if not writer.isOpened():
            raise RuntimeError(f"Could not open VideoWriter for {video_path}. "
                               f"Try fourcc='MJPG' with ext='.avi'.")

        self.frame_index = 0
        self.frames_dropped = 0
        self._ts_rows = []
        self._marks = []

        with self._lock:
            self._writer = writer
        t0 = time.perf_counter()
        self._recording.set()
        log.info("Recording -> %s", video_path)
        return t0

    def stop_recording(self) -> Path | None:
        """Stop writing, flush, and save the frame-timestamp CSV."""
        if not self._recording.is_set():
            return None
        self._recording.clear()
        time.sleep(0.1)                      # let the queue drain
        self._write_q.join() if False else None
        while not self._write_q.empty():
            time.sleep(0.02)

        with self._lock:
            if self._writer:
                self._writer.release()
                self._writer = None

        csv_path = self.out_dir / f"{self._current_name}_frametimes.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["frame_index", "t_perf_counter_s", "t_unix_s"])
            w.writerows(self._ts_rows)

        if self._marks:
            mark_path = self.out_dir / f"{self._current_name}_events.csv"
            with open(mark_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["label", "frame_index", "t_perf_counter_s", "t_unix_s"])
                w.writerows(self._marks)

        n = len(self._ts_rows)
        if n > 1:
            dur = self._ts_rows[-1][1] - self._ts_rows[0][1]
            log.info("Saved %d frames over %.2f s (effective %.2f fps, "
                     "%d dropped).", n, dur, (n - 1) / dur if dur else 0,
                     self.frames_dropped)
        return self.out_dir / f"{self._current_name}{self.ext}"

    def mark(self, label: str) -> None:
        """
        Log an experiment event against the current frame. This is what lets you
        say "the stimulus appeared at frame 412" when you analyse the video.
        """
        self._marks.append((label, self.frame_index,
                            time.perf_counter(), time.time()))
        log.info("Event '%s' at frame %d", label, self.frame_index)


class Recording:
    """Context manager so a recording is always closed, even if a trial raises."""

    def __init__(self, rec: GoProRecorder, name: str | None = None) -> None:
        self.rec = rec
        self.name = name

    def __enter__(self) -> GoProRecorder:
        self.rec.start_recording(self.name)
        return self.rec

    def __exit__(self, *exc_info) -> None:
        self.rec.stop_recording()


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s  %(levelname)s  %(message)s")

    if "--list" in sys.argv:
        list_cameras()
        raise SystemExit(0)

    # Change device_index to whatever --list reported for the GoPro.
    rec = GoProRecorder(device_index=1, out_dir="recordings",
                        width=1280, height=720, fps=30)
    rec.open()

    # --- your experiment setup ---

    with Recording(rec, name="trial_01"):
        time.sleep(2)
        rec.mark("stimulus_on")      # <- call this at your event points
        time.sleep(3)
        rec.mark("response")
        time.sleep(1)

    rec.close()
