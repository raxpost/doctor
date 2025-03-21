import os

base = (input("Input the full path to the project: ")).strip()

from src.paralents import report as parallel_entities_report
from src.validation import report as constants_report
from src.common import report as common_finding_report
from src.project import Project

if not os.path.isdir(base):
    print(f"Path {base} doesn't exist")
    exit()

p = Project(base)
common_finding_report(p)
parallel_entities_report(p)
constants_report(p)
