import pytest
import shutil
import os
from src.ucases.common import report
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

# there is a pyproject.toml but no installation instructions
# should be one recommendation
def test_common_uc_no_install():
    path_to_project = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases", "common")
    os.makedirs(path_to_project, exist_ok=True)
    create_file(path_to_project, "README.md", "Hello")
    toml_path = create_file(path_to_project, "pyproject.toml", "")
    p = Project(path_to_project)
    r = report(p)
    #print(r.debug)
    for ad in r.advices:
        assert ad.subs[0] == toml_path # specific file found
        assert ad.subs[1] == "INSTALLATION PROCESS" # category


# there is a pyproject.toml and there are installation instructions in readme
# no recommendations
def test_common_uc_with_install():
    path_to_project = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases", "common")
    os.makedirs(path_to_project, exist_ok=True)
    instr = """
# Doctor

## Install

### Mac 

```
brew install python
pip install pdm
pdm install
```
### Windows

Install Python https://www.python.org/downloads/windows/

```
pip install pdm
pdm install
```
"""
    create_file(path_to_project, "README.md", instr)
    create_file(path_to_project, "pyproject.toml", "")
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