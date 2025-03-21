import os

class WalkItem:
    def __init__(self, root, dirs, files):
        self.root = root
        self.dirs = dirs
        self.files = files

class Project:
    def __init__(self, project_root):
        self.project_root = project_root
        self.walk_items = []
        for root, dirs, files in os.walk(project_root):
            self.walk_items.append(WalkItem(root, dirs, files))
        
        if os.path.exists(os.path.join(project_root, "README.md")):
            self.doc_path = os.path.join(project_root, "README.md")
        else:
            print("Currently only README.md is supported as documentation, but it was not found in the project")
            exit()