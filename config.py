from dataclasses import dataclass
import os

@dataclass
class Config:
    port: str
    baudrate: int
    baseline_samples: int = 100
    plot_window: int = 100
    moving_avg_k: int = 30
    use_median_baseline: bool = False
    plot_update_interval: int = 5  # Only update plot every N samples
    fullscreen: bool = False


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"{name} environment variable not set")
    return value

# def g
# PORT = os.getenv('PORT')
# if not PORT:
#     print("PORT environment variable not set")
#     sys.exit(1)
#
# BAUDRATE = os.getenv('BAUDRATE')
# if not BAUDRATE:
#     print("BAUDRATE environment variable not set")
#     sys.exit(1)
#
# BAUDRATE = int(BAUDRATE)
# config = Config(port=PORT, baudrate=BAUDRATE)
