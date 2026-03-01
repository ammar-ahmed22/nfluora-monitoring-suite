from collections import deque

class RunningAverage:
    """Efficient moving average using running sum."""
    def __init__(self, k):
        self.k = k
        self.buffer = deque(maxlen=k)
        self.running_sum = 0.0

    def add(self, value):
        if len(self.buffer) == self.k:
            self.running_sum -= self.buffer[0]
        self.buffer.append(value)
        self.running_sum += value

    def get(self):
        if not self.buffer:
            return 0.0
        return self.running_sum / len(self.buffer)

    def reset(self):
        self.buffer.clear()
        self.running_sum = 0.0

def median(values):
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return 0.5 * (s[mid - 1] + s[mid])
