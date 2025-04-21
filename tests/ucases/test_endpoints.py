import pytest
import shutil
import os
from src.ucases.endpoints import report
from src.core.project import Project

# Remove test paths from exclusions
@pytest.fixture(autouse=True, scope="session")
def set_env():
    os.environ["ALLOW_TEST_PATHS"] = "yes"

def create_file(path, fname, content):
    filename = os.path.join(path, fname)
    with open(filename, "w") as f:
        f.write(content)
    return filename

# 2 modules and one is not imported from others. it should be considered as endpoint, not documented and should be recommended
def test_endpoints_uc_not_documented():
    path_to_project = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases", "endpoints")
    os.makedirs(path_to_project, exist_ok=True)
    create_file(path_to_project, "README.md", "Hello")
    create_file(path_to_project, "module1.py", "import module2\nprint(2)")
    create_file(path_to_project, "module2.py", "print(2)")
    p = Project(path_to_project)
    r = report(p)
    for ad in r.advices:
        assert '/module1.py' == ad.subs[0]


# 2 modules and one is not imported from others. it should be considered as endpoint, documented and should not be recommended
def test_endpoints_uc_documented():
    path_to_project = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases", "endpoints")
    os.makedirs(path_to_project, exist_ok=True)
    create_file(path_to_project, "README.md", "Hello\nModule1 is an entry point")
    create_file(path_to_project, "module1.py", "import module2\nprint(2)")
    create_file(path_to_project, "module2.py", "print(2)")
    p = Project(path_to_project)
    r = report(p)
    assert len(r.advices) == 0


def clean_folder(path):
    for item in os.listdir(path):
        full_path = os.path.join(path, item)
        if os.path.isfile(full_path) or os.path.islink(full_path):
            os.remove(full_path)
        elif os.path.isdir(full_path):
            shutil.rmtree(full_path)


@pytest.fixture(scope="function", autouse=True)
def session_cleanup():
    yield
    clean_folder(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases"))