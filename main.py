from datetime import time
from typing import List, Deque
import serial
import matplotlib.pyplot as plt
from dataclasses import dataclass
from collections import deque
from config import Config, require_env
from calibration import Calibrator, CalibrationState
import cli
from timelength import TimeLength
import time
from recorder import Recorder


# --- Config ---
PORT = require_env('PORT')
BAUDRATE = int(require_env('BAUDRATE'))
config = Config(port=PORT, baudrate=BAUDRATE)

# --- Serial ---
ser = serial.Serial(config.port, config.baudrate)

# --- Calibration ---
calibrator = Calibrator(config)

# --- Plotting buffers ---
@dataclass
class Data:
    raw: Deque[float]
    corrected: Deque[float]
    smoothed: Deque[float]
    samples: int = 0

    @staticmethod
    def create(window_size: int) -> "Data":
        return Data(
            raw=deque([0.0] * window_size, maxlen=window_size),
            corrected=deque([0.0] * window_size, maxlen=window_size),
            smoothed=deque([0.0] * window_size, maxlen=window_size),
        )

data = Data.create(config.plot_window)

plt.ion()
fig, ax = plt.subplots()
fig_manager = plt.get_current_fig_manager()
if fig_manager is not None:
    if config.fullscreen:
        fig_manager.full_screen_toggle()
    fig_manager.set_window_title("nFluora NIR Fluorescence Sensor Visualization")

raw_line, = ax.plot(data.raw, alpha=0.25, label="raw")
corr_line, = ax.plot(data.corrected, alpha=0.25, label="baseline corrected")
smooth_line, = ax.plot(data.smoothed, linewidth=2, label=f"smoothed")
smooth_line.set_visible(False)  # Hidden until calibration is READY

ax.legend(loc='upper right')
ax.set_xlabel("sample")
ax.set_ylabel("Voltage (raw / corrected)")
title = ax.set_title("IDLE - Type 'baseline' to start calibration")


def adc2volts(adc_value: float, vref: float = 5.0, resolution: int = 1024) -> float:
    """Convert ADC counts to voltage."""
    return (adc_value / (resolution - 1)) * vref


recorder = Recorder()

def handle_record(duration: str, filename: str):
    global recorder
    tl = TimeLength(duration).result
    if not tl.success:
        print(f"Invalid duration format: {duration}")
        return
    if not calibrator.state == CalibrationState.READY:
        print("Calibration not ready. Please calibrate before recording.")
        return
    dur = tl.seconds
    recorder.start(dur, filename);
    pass

def handle_exit():
    print("\nByebye!")
    ser.close()
    plt.close()
    exit(0)

def handle_command(cmd: cli.CommandType, args: List[str]) -> None:
    """Handle CLI commands. Add a case when adding new commands to CommandType."""
    match cmd:
        case cli.CommandType.HELP:
            cli.help_message()
        case cli.CommandType.CALIBRATE:
            calibrator.start()
        case cli.CommandType.EXIT:
            handle_exit()
        case cli.CommandType.RECORD:
            duration, filename = args
            handle_record(duration, filename)


cli.welcome_message()
command_handler = cli.CommandHandler(handle_command)
try:
    while True:
        # Check for stdin (non-blocking)
        input = cli.read_input()
        if input :
            cmd, args = input
            command_handler.handle_command(cmd, args)

        # Drain all available data from serial buffer
        lines_read = 0
        while True:
            # Always read at least one line (blocking)
            if lines_read == 0 or ser.in_waiting:
                try:
                    value = adc2volts(float(ser.readline().decode(errors="ignore").strip()))
                    data.raw.append(value)
                    corrected, smoothed, state_changed = calibrator.process(value)
                    data.corrected.append(corrected)
                    data.smoothed.append(smoothed)
                    now = time.time()
                    if recorder.is_recording():
                        print(f"Recording... {recorder.remaining():.1f}s remaining", end="\r")
                        recorder.record(f"{round(recorder.elapsed(), 3)},{value},{corrected},{smoothed}\n")
                    else:
                        recorder.stop()  # Ensure recording is stopped if time has elapsed
                    data.samples += 1
                    lines_read += 1

                    # Update title based on state
                    if calibrator.state == CalibrationState.IDLE:
                        title.set_text("IDLE - Type 'calibrate' to start calibration")
                    elif calibrator.state == CalibrationState.CALIBRATING:
                        current, total = calibrator.calibration_progress
                        title.set_text(f"CALIBRATING BASELINE (DO NOT APPLY SIGNAL) ({current}/{total})")
                    elif state_changed:
                        title.set_text("READY")
                        smooth_line.set_visible(True)
                        ax.legend(loc='upper right')  # Recreate legend to show smooth_line color
                except ValueError:
                    continue
            else:
                break

        # Only update plot every N samples
        if data.samples % config.plot_update_interval == 0:
            x = range(len(data.raw))
            raw_line.set_xdata(x)
            corr_line.set_xdata(x)
            smooth_line.set_xdata(x)

            raw_line.set_ydata(data.raw)
            corr_line.set_ydata(data.corrected)
            smooth_line.set_ydata(data.smoothed)

            ax.relim()
            ax.autoscale_view()
            plt.draw()
            plt.pause(0.001)
except KeyboardInterrupt:
    handle_exit()
