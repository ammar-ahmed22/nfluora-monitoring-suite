
PORT := /dev/cu.usbmodem1201
BAUDRATE := 9600

ARDUINO_TARGET := arduino

.PHONY: all compile

all: compile
	@echo "==== UPLOAD ========================================="
	@echo "Uploading sketch"
	@echo "Port   : $(PORT)"
	@echo "====================================================="
	@arduino-cli upload -p $(PORT) --fqbn arduino:avr:uno $(ARDUINO_TARGET)

compile:
	@echo "==== BUILD =========================================="
	@echo "Building sketch"
	@echo "====================================================="
	arduino-cli compile --fqbn arduino:avr:uno $(ARDUINO_TARGET)

monitor:
	@PORT=$(PORT) BAUDRATE=$(BAUDRATE) python3 main.py
