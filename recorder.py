import time
import threading
import queue

class Recorder:
    def __init__(self):
        self.recording = False
        self.start_time = 0.0
        self.end_time = 0.0
        self.filename = ""
        self.queue = queue.Queue()

    def _reset(self):
        self.recording = False
        self.start_time = 0.0
        self.end_time = 0.0
        self.filename = ""

    def _worker(self, path: str, flush_every=200, flush_interval=0.25):
        buf = []
        last_flush = time.time()
        with open(path, "w") as f:
            while True:
                item = self.queue.get()
                if item is None:
                    self.queue = queue.Queue()  # Reset queue for next recording session
                    break
                buf.append(item)
                now = time.time()
                if len(buf) >= flush_every or now - last_flush >= flush_interval:
                    f.writelines(buf)
                    buf.clear()
                    last_flush = now
            if buf:
                f.writelines(buf)

    def start(self, duration: float, filename: str):
        self.recording = True
        self.start_time = time.time()
        self.end_time = self.start_time + duration
        self.filename = filename
        t = threading.Thread(target=self._worker, args=(filename,), daemon=True)
        t.start()

    def stop(self):
        if self.recording:
            print(f"Recording stopped. Data saved to {self.filename}")
            self.queue.put(None)
            self._reset()

    def remaining(self) -> float:
        if not self.recording:
            return 0.0
        return max(0.0, self.end_time - time.time())
    def elapsed(self) -> float:
        if not self.recording:
            return 0.0
        return time.time() - self.start_time

    def record(self, item: str):
        if self.recording:
            self.queue.put(item)

    def is_recording(self) -> bool:
        return self.recording and time.time() < self.end_time
