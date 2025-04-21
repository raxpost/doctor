import os
import traceback

def start(base):
    from src.ucases.parallents import report as parallel_entities_report
    from src.ucases.validation import report as constants_report
    from src.ucases.common import report as common_finding_report
    from src.ucases.endpoints import report as endpoints_report
    from src.core.project import Project

    if not os.path.isdir(base):
        print(f"Path {base} doesn't exist")
        exit()
    try:
        ucases_to_run = [
            #common_finding_report,
            #parallel_entities_report,
            #constants_report,
            endpoints_report
        ]
        p = Project(base)
        for uc in ucases_to_run:
            r = uc(p)
            r.print()
    except Exception as e:
        print(e)
        traceback.print_exc()


MULTI_FOLDER = os.getenv("MULTI_FOLDER")
PROJECT_PATH = os.getenv("PROJECT_PATH")
if MULTI_FOLDER:
    for name in os.listdir(MULTI_FOLDER):
        full_path = os.path.join(MULTI_FOLDER, name)
        if os.path.isdir(full_path):
            print(f"============ PROJECT {name} ==============")
            start(full_path)
else:
    base = PROJECT_PATH if PROJECT_PATH else (input("Input the full path to the project: ")).strip()
    start(base)
