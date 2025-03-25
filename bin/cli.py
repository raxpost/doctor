import os

def start(base):
    from src.paralents import report as parallel_entities_report
    from src.validation import report as constants_report
    from src.common import report as common_finding_report
    from src.project import Project
    if not os.path.isdir(base):
        print(f"Path {base} doesn't exist")
        exit()
    try:
        p = Project(base)
        common_finding_report(p)
        #parallel_entities_report(p)
        #constants_report(p)
    except Exception as e:
        print(e)


MULI_FOLDER = os.getenv("MULI_FOLDER")
if MULI_FOLDER:
    for name in os.listdir(MULI_FOLDER):
        full_path = os.path.join(MULI_FOLDER, name)
        if os.path.isdir(full_path):
            print(f"============ PROJECT {name} ==============")
            start(full_path)
else:
    base = (input("Input the full path to the project: ")).strip()
    start(base)
