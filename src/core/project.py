import os
from src.helpers.exclusions import is_file_to_skip

class WalkItem:
    def __init__(self, root, dirs, files):
        self.root = root
        self.dirs = dirs
        filtered_files = []
        for file in files:
            file_path = os.path.join(root, file)
            if is_file_to_skip(file_path):
                continue
            filtered_files.append(file)
        self.files = filtered_files

class Project:
    def __init__(self, project_root):
        self.project_root = project_root
        self.walk_items = []
        for root, dirs, files in os.walk(project_root):
            if is_file_to_skip(root):
                continue
            self.walk_items.append(WalkItem(root, dirs, files))
        
        readme_path = os.path.join(project_root, "README.md")
        if os.path.exists(readme_path) and os.path.getsize(readme_path) > 0:
            self.doc_path = os.path.join(project_root, "README.md")
        else:
            raise Exception("Currently only README.md is supported as documentation, but it was not found in the project")