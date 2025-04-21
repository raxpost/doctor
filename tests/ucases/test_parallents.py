import pytest
import shutil
import os
from src.ucases.parallents import report
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

# 3 files in a folder, 2 subtitles in README, 2 intersections =>
# should be notified about the third mising one. There should be at least 2 intersections
def test_paralents_uc_files_subtitles_not_documented():
    path_to_project = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases", "paralents")
    os.makedirs(path_to_project, exist_ok=True)
    sf = os.path.join(path_to_project, "services")
    os.makedirs(sf, exist_ok=True)
    create_file(path_to_project, "README.md", "# Services\nHello world\n## Authentication service\nGood afternon\n##  Users service\nLets talk about module 2")
    create_file(sf, "auth.py", "")
    create_file(sf, "user.py", "")
    create_file(sf, "goods.py", "")
    p = Project(path_to_project)
    r = report(p)
    assert len(r.advices) == 1
    assert r.advices[0].subs[0] == sf
    assert r.advices[0].subs[1] == ["goods"] # existing not documented service


# 3 files in a folder, 2 list items in README, 2 intersections =>
# should be notified about the third mising one. There should be at least 2 intersections
def test_paralents_uc_files_list_not_documented():
    path_to_project = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases", "paralents")
    os.makedirs(path_to_project, exist_ok=True)
    sf = os.path.join(path_to_project, "services")
    os.makedirs(sf, exist_ok=True)
    create_file(path_to_project, "README.md", "# Services\nHello world\n\n* Authentication service\n* Users service\n")
    create_file(sf, "auth.py", "")
    create_file(sf, "user.py", "")
    create_file(sf, "goods.py", "")
    p = Project(path_to_project)
    r = report(p)
    assert len(r.advices) == 1
    assert r.advices[0].subs[0] == sf
    assert r.advices[0].subs[1] == ["goods"] # existing not documented service


# 3 yaml code sections, 2 list items in README, 2 intersections =>
# should be notified about the third mising one. There should be at least 2 intersections
def test_paralents_uc_files_yaml_not_documented():
    path_to_project = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases", "paralents")
    os.makedirs(path_to_project, exist_ok=True)
    sf = os.path.join(path_to_project, "services")
    os.makedirs(sf, exist_ok=True)
    create_file(path_to_project, "README.md", "# Services\nHello world\n\n* Authentication service\n* Users service\n")
    create_file(sf, "services.yaml", """
services:
    auth:
        index: 1
    users:
        index: 2
    goods:
        index: 3
    """)
    p = Project(path_to_project)
    r = report(p)
    assert len(r.advices) == 1
    assert r.advices[0].subs[0] == "services"
    assert r.advices[0].subs[1] == ["goods"] # existing not documented service


# 3 env vars in a file, 2 list items in README, 2 intersections =>
# should be notified about the third mising one. There should be at least 2 intersections
def test_paralents_uc_files_envvars_not_documented():
    path_to_project = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases", "paralents")
    os.makedirs(path_to_project, exist_ok=True)
    sf = os.path.join(path_to_project, "services")
    os.makedirs(sf, exist_ok=True)
    create_file(path_to_project, "README.md", "# Services\nHello world\n\n* Authentication service\n* Users service\n")
    create_file(sf, "services.py", """"
s1 = os.getenv("AUTH")
s2 = os.environ["USERS"]
s3 = os.getenv("GOODS", None)
    """)
    p = Project(path_to_project)
    r = report(p)
    assert len(r.advices) == 1
    assert ("services.py" in r.advices[0].subs[0]) is True
    assert r.advices[0].subs[1] == ["GOODS"] # existing not documented service



# 3 files in a folder, 3 list items in README, 3 intersections =>
# nothing to document
def test_paralents_uc_files_all_documented():
    path_to_project = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases", "paralents")
    os.makedirs(path_to_project, exist_ok=True)
    sf = os.path.join(path_to_project, "services")
    os.makedirs(sf, exist_ok=True)
    create_file(path_to_project, "README.md", "# Services\nHello world\n\n* Authentication service\n* Users service\n* Goods service")
    create_file(sf, "auth.py", "")
    create_file(sf, "user.py", "")
    create_file(sf, "goods.py", "")
    p = Project(path_to_project)
    r = report(p)
    assert len(r.advices) == 0


# 3 files in the ROOT folder, 2 list items in README, 2 intersections =>
# ROOT items must be skipped
def test_paralents_root_files_not_documented():
    path_to_project = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mocks", "ucases", "paralents")
    os.makedirs(path_to_project, exist_ok=True)
    sf = path_to_project
    os.makedirs(sf, exist_ok=True)
    create_file(path_to_project, "README.md", "# Services\nHello world\n\n* Authentication service\n* Users service")
    create_file(sf, "auth.py", "")
    create_file(sf, "user.py", "")
    create_file(sf, "goods.py", "")
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