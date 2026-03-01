import matplotlib.pyplot as plt
import sys

if __name__ == "__main__":
    print("Usage: python plot_recorded.py <data_file>")
    if len(sys.argv) != 2:
        print("Error: Missing data file argument")
        sys.exit(1)

    filename = sys.argv[1]
    print(f"Loading data from {filename}...")
    times = []
    smoothed_values = []
    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            time, raw, corrected, smoothed = line.strip().split(",")
            times.append(float(time))
            smoothed_values.append(float(smoothed))

    plt.plot(times, smoothed_values, linewidth=2)
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.title("Recorded Smoothed Signal Over Time")
    plt.grid()
    plt.show()


