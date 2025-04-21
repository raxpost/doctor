# Endpoints are modules which are not imported by any other module
# Assuming that such files are entry points of services, or scripts, which should be documented
# Only Python supported
# If they are not yet, to recommend
import os
import re
from pathlib import Path
from collections import defaultdict
from src.core.project import Project
from src.core.report import Report
from src.helpers.readme import split_readme_to_chunks
from src.helpers.comparison import fuzzy_score_lists
from src.helpers.comparison import hybrid_strings_lists_comparison

def find_python_files(base, root, files):
    py_files = []
    for f in files:
        if f.endswith(".py"):
            full_path = os.path.join(root, f)
            module = os.path.relpath(full_path, base).replace(os.sep, ".")[:-3]
            if module.endswith("__init__"):
                module = module.rsplit(".", 1)[0]
            py_files.append((module, full_path))
    return py_files

# @TODO implement for all languages over Language class
def extract_imports(file_content):
    imports = set()
    import_pattern = re.compile(
        r'^\s*import\s+([a-zA-Z0-9_. ,]+)',
        re.MULTILINE
    )

    from_import_pattern = re.compile(
        r'^\s*from\s+([a-zA-Z0-9_.]+)\s+import\s+',
        re.MULTILINE
    )

    for match in import_pattern.findall(file_content):
        parts = match.split(",")
        for part in parts:
            name = part.strip().split()[0]
            if name:
                imports.add(name)

    for match in from_import_pattern.findall(file_content):
        name = match.strip()
        if name:
            imports.add(name)

    return imports

def conv_to_path(imp):
    return imp.replace(".", os.sep)

def grouped(base, file_paths):
    root = Path(base)
    grouped = defaultdict(list)

    depth = 2 # take only folders, not files
    for abs_path in file_paths:
            rel = Path(abs_path).relative_to(root)
            parts = rel.parts

            if len(parts) <= depth:
                continue

            key = "/" + "/".join(parts[:depth])
            value = str(Path(*parts[depth:]))
            grouped[key].append(value)

    return dict(grouped)

def get_eindpoints(directory):
    project = Project(directory)
    not_imported = []
    imports = []
    all_py_files = []
    for witem in project.walk_items:
        root = witem.root
        files = witem.files
        for file in files:
            full_path = os.path.join(root, file)
            if file.endswith(".py") and "__init__" not in file:
                all_py_files.append(full_path)
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                imports += extract_imports(content)
        #pyfiles += find_python_files(directory, root, files)
    #print(all_py_files)
    for full_path in all_py_files:
        found = False
        for im in imports:
            if conv_to_path(im) in full_path:
                found = True
                break
        if not found:
            not_imported.append(full_path)
    
    return not_imported

def norm(txt):
    return txt.replace(".py", "").replace("_", " ").replace("/", " ") # / is not from os here

def normalize_group(gr, groups):
    kws = []
    key = norm(gr)
    for item in groups[gr]:
        kws.append(key + " " + norm(item))
    return kws


def report(p):
    r = Report("Endpoints")
    endpoints = get_eindpoints(p.project_root) # flat list of abs paths
    endpoints = [e.replace(p.project_root, "") for e in endpoints]
    #groups = grouped(p.project_root, endpoints)
    readme_chunks = split_readme_to_chunks(p.doc_path, 150, 50)
    #print([norm(e) for e in endpoints], readme_chunks)
    total_scores, matched_rights = hybrid_strings_lists_comparison([norm(e) for e in endpoints], readme_chunks, 0.5)
    #print(endpoints, readme_chunks, total_scores, matched_rights)
    for i, score in enumerate(total_scores):
        if score == 0: # no readme chunks matched with this endpoint
            r.advice_add("\"{}\" seems to be an endpoint or script. But it's not documented. It can be also obsolete", (endpoints[i],))

    return r
    