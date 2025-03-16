import os

base = (input("Input the full path to the project: ")).strip()
from src.paralents import report
if not os.path.isdir(base):
    print(f"Path {base} doesn't exist")
    exit()
report(base)
