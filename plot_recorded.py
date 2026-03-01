import matplotlib.pyplot as plt
import pandas as pd
import sys

if __name__ == "__main__":
    print("Usage: python plot_recorded.py <data_file>")
    if len(sys.argv) != 2:
        print("Error: Missing data file argument")
        sys.exit(1)

    filename = sys.argv[1]
    df = pd.read_csv(filename)

    plt.plot(df["timestamp"], df['smoothed'])
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.title("Recorded Smoothed Signal Over Time")
    plt.grid()
    plt.show()


