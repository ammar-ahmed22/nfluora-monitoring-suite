from enum import Enum, auto

from config import Config
from stats import RunningAverage, median


class CalibrationState(Enum):
    IDLE = auto()        # Waiting for user to trigger calibration
    CALIBRATING = auto() # Collecting baseline samples
    READY = auto()       # Baseline acquired, normal operation


class Calibrator:
    """Encapsulates calibration state and signal processing."""

    def __init__(self, config: Config):
        self.config = config
        self.state = CalibrationState.IDLE
        self.baseline: float | None = None
        self._baseline_buf: list[float] = []
        self._running_avg = RunningAverage(config.moving_avg_k)

    def start(self) -> None:
        """Reset state for a new calibration."""
        self._baseline_buf.clear()
        self._running_avg.reset()
        self.baseline = None
        self.state = CalibrationState.CALIBRATING
        print("Starting baseline calibration...")

    def process(self, value: float) -> tuple[float, float, bool]:
        """
        Process a single value. Returns (corrected, smoothed, state_changed).
        
        - corrected: baseline-corrected value (0 if not ready)
        - smoothed: smoothed corrected value (0 if not ready)
        - state_changed: True if calibration just completed
        """
        if self.state == CalibrationState.IDLE:
            return 0.0, 0.0, False

        elif self.state == CalibrationState.CALIBRATING:
            self._baseline_buf.append(value)
            curr, total = self.calibration_progress
            if curr % 10 == 0 or curr == total:  # Print progress every 10 samples and at the end
                print(f"Calibration progress: {round(curr/total*100)}%", end='\r')
            if len(self._baseline_buf) >= self.config.baseline_samples:
                if self.config.use_median_baseline:
                    self.baseline = median(self._baseline_buf)
                else:
                    self.baseline = sum(self._baseline_buf) / len(self._baseline_buf)
                print(f"Baseline acquired: {self.baseline:.2f}")
                self.state = CalibrationState.READY
                return 0.0, 0.0, True
            return 0.0, 0.0, False

        else:  # CalibrationState.READY
            corrected = value - self.baseline  # type: ignore (baseline is set when READY)
            self._running_avg.add(corrected)
            smoothed = self._running_avg.get()
            return corrected, smoothed, False

    @property
    def calibration_progress(self) -> tuple[int, int]:
        """Returns (current_samples, total_samples) for calibration progress."""
        return len(self._baseline_buf), self.config.baseline_samples
