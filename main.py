from typing import List
import serial
# import sys
# import select
from enum import Enum, auto
import matplotlib.pyplot as plt
from collections import deque
from stats import RunningAverage, median
from config import Config, require_env
import cli
# from cli import read_command, print_welcome_message


class CalibrationState(Enum):
    IDLE = auto()        # Waiting for user to trigger calibration
    CALIBRATING = auto() # Collecting baseline samples
    READY = auto()       # Baseline acquired, normal operation


# --- Non-blocking input ---
# input_buffer = ""

# def check_for_command():
#     """Check stdin for input commands without blocking. Returns command if complete, None otherwise."""
#     # Check if stdin has data available (non-blocking)
#     while select.select([sys.stdin], [], [], 0)[0]:
#         line = sys.stdin.readline()
#         if line:
#             return line.strip().lower()
#     return None


# --- Config ---
PORT = require_env('PORT')
BAUDRATE = int(require_env('BAUDRATE'))
config = Config(port=PORT, baudrate=BAUDRATE)


# --- Serial ---
ser = serial.Serial(config.port, config.baudrate)

# baseline collection buffer
baseline_buf = []

# plotting buffers
raw_window = deque([0.0] * config.plot_window, maxlen=config.plot_window)
corr_window = deque([0.0] * config.plot_window, maxlen=config.plot_window)
smooth_window = deque([0.0] * config.plot_window, maxlen=config.plot_window)

baseline: float | None = None
running_avg = RunningAverage(config.moving_avg_k)
sample_count = 0
state = CalibrationState.IDLE

plt.ion()
fig, ax = plt.subplots()
fig_manager = plt.get_current_fig_manager()
if fig_manager is not None:
    if config.fullscreen:
        fig_manager.full_screen_toggle()
    fig_manager.set_window_title("nFluora NIR Fluorescence Sensor Visualization")

raw_line, = ax.plot(raw_window, alpha=0.25, label="raw")
corr_line, = ax.plot(corr_window, alpha=0.25, label="baseline corrected")
smooth_line, = ax.plot(smooth_window, linewidth=2, label=f"smoothed ({config.moving_avg_k} sample moving avg)")

ax.legend(loc='upper right')
ax.set_xlabel("sample")
ax.set_ylabel("Voltage (raw / corrected)")
title = ax.set_title("IDLE - Type 'baseline' to start calibration")


def process_value(value):
    """Process a single value from serial. Returns True if state changed."""
    global baseline, state
    raw_window.append(value)

    if state == CalibrationState.IDLE:
        # Just show raw data, no correction
        corr_window.append(0)
        smooth_window.append(0)
        return False

    elif state == CalibrationState.CALIBRATING:
        # Collect baseline samples
        baseline_buf.append(value)
        if len(baseline_buf) >= config.baseline_samples:
            if config.use_median_baseline:
                baseline = median(baseline_buf)
            else:
                baseline = sum(baseline_buf) / len(baseline_buf)
            print(f"Baseline acquired: {baseline:.2f}")
            state = CalibrationState.READY
            return True
        corr_window.append(0)
        smooth_window.append(0)
        return False

    else:  # CalibrationState.READY
        corrected = value - baseline
        corr_window.append(corrected)
        running_avg.add(corrected)
        smooth_window.append(running_avg.get())
        return False

def adc2volts(adc_value, vref=5.0, resolution=1024):
    """Convert ADC counts to voltage."""
    return (adc_value / (resolution - 1)) * vref

def start_calibration():
    """Reset state for a new calibration."""
    global state, baseline
    baseline_buf.clear()
    running_avg.reset()
    baseline = None
    state = CalibrationState.CALIBRATING
    print("Starting baseline calibration...")

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
            start_calibration()
        case cli.CommandType.EXIT:
            handle_exit()
        case cli.CommandType.RECORD:
            print(f"record data for {args[0]} to file {args[1]} (not implemented yet)")
        case _:
            print(f"Unhandled command: {cmd}")


cli.welcome_message()
command_handler = cli.CommandHandler(handle_command)
try:
    while True:
        # Check for calibration trigger (non-blocking)
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
                    state_changed = process_value(value)
                    sample_count += 1
                    lines_read += 1

                    # Update title based on state
                    if state == CalibrationState.IDLE:
                        title.set_text("IDLE - Type 'calibrate' to start calibration")
                    elif state == CalibrationState.CALIBRATING:
                        title.set_text(f"CALIBRATING BASELINE (DO NOT APPLY SIGNAL) ({len(baseline_buf)}/{config.baseline_samples})")
                    elif state_changed:
                        title.set_text("READY")
                except ValueError:
                    continue
            else:
                break

        # Only update plot every N samples
        if sample_count % config.plot_update_interval == 0:
            x = range(len(raw_window))
            raw_line.set_xdata(x)
            corr_line.set_xdata(x)
            smooth_line.set_xdata(x)

            raw_line.set_ydata(raw_window)
            corr_line.set_ydata(corr_window)
            smooth_line.set_ydata(smooth_window)

            ax.relim()
            ax.autoscale_view()
            plt.draw()
            plt.pause(0.001)
except KeyboardInterrupt:
    handle_exit()
