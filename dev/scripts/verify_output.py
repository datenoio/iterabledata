import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from iterable import open_iterable

path = "examples/rmsp_data_sample.jsonl.zst"
try:
    with open_iterable(path) as data:
        count = 0
        for row in data:
            count += 1
            if count == 1:
                print("First row:", row)
        print(f"Total read back: {count}")
except Exception as e:
    print(f"Failed to read back: {e}")
