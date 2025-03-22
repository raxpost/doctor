import os

def is_file_to_skip(file_path):
    file = os.path.basename(file_path)
    paths_exclusions = ["node_modules", "test", "documentation", ".venv", "venv", "virtualenv", ".git", "schema", "build", "static"]
    exclusions = ["README.md", "package.json", "package-lock.json", "pyproject.toml", "pdm.lock", "__init__"]
    return any(pe in file_path for pe in paths_exclusions) or file in exclusions