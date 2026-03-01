import select
import sys
from enum import Enum
from typing import Callable, Tuple, List

# Type alias for command handler function
Handler = Callable[["CommandType", List[str]], None]


class CommandType(Enum):
    """All available CLI commands. Add new commands here."""
    HELP = "help"
    CALIBRATE = "calibrate"
    RECORD = "record"
    EXIT = "exit"

    @property
    def help_text(self) -> str:
        return {
            CommandType.HELP: "Show this help message",
            CommandType.CALIBRATE: "Start calibration process",
            CommandType.EXIT: "Exit the program",
            CommandType.RECORD: "Record data for a specified duration (e.g. 10s, 1m30s) to a specified file"
        }[self]
    @property
    def args(self) -> List[str]:
        return {
            CommandType.HELP: [],
            CommandType.CALIBRATE: [],
            CommandType.EXIT: [],
            CommandType.RECORD: ["duration", "filename"]
        }[self]


class CommandHandler:
    def __init__(self, handler: Handler):
        self.handler = handler

    def handle_command(self, cmd: str, args: List[str]) -> None:
        try:
            command = CommandType(cmd)
        except ValueError:
            print(f"Unknown command: {cmd}. Type 'help' for options.")
            return
        self.handler(command, args)

def read_input() -> Tuple[str, List[str]] | None:
    """Check stdin for input commands without blocking. Returns command if complete, None otherwise."""
    # Check if stdin has data available (non-blocking)
    while select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline()
        if line:
            cleaned = line.strip().lower()
            cmd_type, *args = cleaned.split(" ");
            return cmd_type, args
    return None

def welcome_message():
    print("Welcome to nFloura NIR Fluorescence Monitor!");
    print("Enter a command to get started ('help' for options).")

def help_message():
    print("Available commands:")
    for cmd in CommandType:
        res = f"  {cmd.value}";
        if cmd.args:
            for arg in cmd.args:
                res += f" <{arg.upper()}>"
        res += f": {cmd.help_text}"
        print(res)

