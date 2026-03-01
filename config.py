from dataclasses import dataclass
import os

@dataclass
class Config:
    port: str
    baudrate: int
    baseline_samples: int = 200
    plot_window: int = 100
    moving_avg_k: int = 50
    use_median_baseline: bool = False
    plot_update_interval: int = 5  # Only update plot every N samples
    fullscreen: bool = False


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"{name} environment variable not set")
    return value
