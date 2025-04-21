import pytest
import shutil
import os
from src.ucases.validation import report
from src.core.project import Project

# Remove test paths from exclusions
@pytest.fixture(autouse=True, scope="session")
def set_env():
    os.environ["ALLOW_TEST_PATHS"] = "yes"
    os.environ["EMBEDDING_MODEL"] = "sentence-transformers/paraphrase-MiniLM-L6-v2"

def create_file(path, fname, content):
    filename = os.path.join(path, fname)
    with open(filename, "w") as f:
        f.write(content)
    return filename

def test_validation_not_documented():
    path_to_project = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases", "validation")
    os.makedirs(path_to_project, exist_ok=True)
    sf = os.path.join(path_to_project, "services")
    os.makedirs(sf, exist_ok=True)
    create_file(path_to_project, "README.md", "# Services\nHello world\n##")
    create_file(sf, "service.py", """
def check_auth(header):
    if header == "top_secret":
        return True
    return False
""")
    p = Project(path_to_project)
    r = report(p)
    assert len(r.advices) == 1
    assert r.advices[0].subs[0] == "top_secret"


def test_validation_already_documented():
    path_to_project = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases", "validation")
    os.makedirs(path_to_project, exist_ok=True)
    sf = os.path.join(path_to_project, "services")
    os.makedirs(sf, exist_ok=True)
    create_file(path_to_project, "README.md", "# Services\nInternal authentication over a header 'top_secret' is available\n##")
    create_file(sf, "service.py", """
def check_auth(header):
    if header == "top_secret":
        return True
    return False
""")
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