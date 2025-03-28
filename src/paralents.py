import os
import json
import yaml
from concurrent.futures import ThreadPoolExecutor
from itertools import product
from tqdm import tqdm
from collections import defaultdict
from string import punctuation
import re
from multiprocessing import Value
from src.embeddings import map_texts_cosine_with_cache
from src.comparison import hybrid_score
from src.exclusions import is_file_to_skip
import time
import sys

start = time.time()

class Parent:
    def __init__(self, type, parent, items):
        self.type = type
        self.parent = parent
        self.items = items
        self.hash = str(hash(",".join([str(item) for item in items])))
        self.total_scores = []
        self.matched_rights = {}


    def __str__(self):
        txt = ""
        for i, item in enumerate(self.items):
            if i in self.matched_rights:
                txt += item + f" ({self.matched_rights[i]})\n"
            if self.total_scores and i < len(self.total_scores):
                txt += item + f" ({self.total_scores[i]})\n"
            else:
                txt += item + "\n"

        return "ParEnt (" + self.type + ", " + str(self.parent) + "):\n" + txt + "\n"

class IgnoreUnknownTagsLoader(yaml.SafeLoader):
    """
    Custom loader that ignores unknown YAML tags instead of throwing an error.
    """

def unknown_tag_handler(loader, tag_suffix, node):
    return 'unknownyamltag'

IgnoreUnknownTagsLoader.add_multi_constructor('', unknown_tag_handler)

patterns = {
    "py": [
        re.compile(r"environ\.get\(['\"]([A-Z0-9_]+)['\"]"),
        re.compile(r"environ\[['\"]([A-Z0-9_]+)['\"]"),
        re.compile(r"getenv\(['\"]([A-Z0-9_]+)['\"]"),
    ],
    "js": [
        re.compile(r"process\.env\.([A-Z0-9_]+)"),
        re.compile(r"process\.env\[['\"]([A-Z0-9_]+)['\"]\]"),
    ],
    "ts": [
        re.compile(r"process\.env\.([A-Z0-9_]+)"),
        re.compile(r"process\.env\[['\"]([A-Z0-9_]+)['\"]\]"),
    ]
}

str_patterns = [
    re.compile(r"[\'\"]{1}([A-Z_\-0-9a-zäßöü@\.:/ %]+)[\'\"]{1}"),
]

def should_skip_root(root, base_path):
    rel = os.path.relpath(root, base_path)
    parts = rel.split(os.sep)
    return any(p.startswith('.') for p in parts if p != '.')

def collect_files_recursive(project):
    parent_instances = []
    for witem in project.walk_items:
        root = witem.root
        files = witem.files
        dirs = witem.dirs
        # skip hidden folders and all its content
        # if should_skip_root(root, project.project_root):
        #     continue
        file_list = []
        for file in files:
            file_path = os.path.join(root, file)
            if is_file_to_skip(file_path):
                continue
            ext = file.lower().split('.')[-1]

            if ext in ("yaml", "yml"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = yaml.load(f, Loader=IgnoreUnknownTagsLoader)
                    except Exception as e:
                        print(e)
                        data = {}
                    if isinstance(data, dict):
                        collect_yaml_keys(data, root, parent_instances, "YAML")
            if ext == "json":
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except Exception as e:
                        print(e)
                        data = {}
                    if isinstance(data, dict):
                        collect_yaml_keys(data, root, parent_instances, "JSON")
            
            elif ext in ["py", "js", "ts"]:
                extract_env_vars(file_path, ext, parent_instances)

            elif ext in ["py", "js", "ts", ".java", ".go", ".php", ".swift", ".c", ".cpp", ".rb", ".sh", ".scala", ".rs", ".kt", ".cs", ".r", ".pl"]:
                extract_constant_values(file_path, parent_instances)
            
            file_list.append(file.replace("." + ext, ""))

        if file_list:
            parent_instances.append(Parent(type="file", parent=root, items=file_list))

        #for name in dirs:
        parent_instances.append(Parent(type="folder", parent=root, items=[d for d in dirs if not d.startswith(".")]))

    res = [p for p in parent_instances if len(p.items) > 1]

    return res

def collect_yaml_keys(data, parent_key, parent_instances, type):
    if isinstance(data, dict):
        keys = list(data.keys())
        if keys:
            parent_instances.append(Parent(type=type, parent=parent_key, items=keys))
        for key, value in data.items():
            collect_yaml_keys(value, key, parent_instances, type)

def extract_env_vars(file_path, ext, parent_instances):
    with open(file_path, 'r', encoding='utf-8') as f:
        txt = f.read()
        if ext not in patterns:
            return
        for p in patterns[ext]:
            matches = p.findall(txt)
            if matches:
                parent_instances.append(Parent(type="EnvVar", parent=file_path, items=list(set(matches))))

def extract_constant_values(file_path, parent_instances):
    with open(file_path, 'r', encoding='utf-8') as f:
        txt = f.read()
        for p in str_patterns:
            matches = p.findall(txt)
            if matches:
                parent_instances.append(Parent(type="EnvVar", parent=file_path, items=list(set(matches))))

def collects_doc_parents(doc_path):
    readme_content = ""
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except Exception as e:
        print(f"{doc_path} doesn't exist. There should be a README file to continue", e)
        exit()
    lines = readme_content.splitlines()
    parallel_entities = {"h1": [], "h2": [], "h3": [], "lists": []}
    
    current_h1, current_h2, current_h3 = [], [], []
    current_list = []
    all_lists = []
    
    for line in lines:
        if line.startswith("# "):
            if current_h2:
                parallel_entities["h2"].append(current_h2)
                current_h2 = []
            if current_h3:
                parallel_entities["h3"].append(current_h3)
                current_h3 = []
            if current_list:
                all_lists.append(current_list)
                current_list = []
            current_h1 = [line.strip().replace("# ", "")]
            parallel_entities["h1"].append(current_h1)
        elif line.startswith("## "):
            if current_h3:
                parallel_entities["h3"].append(current_h3)
                current_h3 = []
            if current_list:
                all_lists.append(current_list)
                current_list = []
            current_h2.append(line.strip().replace("## ", ""))
        elif line.startswith("### "):
            if current_list:
                all_lists.append(current_list)
                current_list = []
            current_h3.append(line.strip().replace("### ", ""))
        elif line.startswith("- ") or line.startswith("* ") or re.match(r'\d+\. ', line):
            current_list.append(line.strip().replace("* ", ""))
        else:
            if current_list:
                all_lists.append(current_list)
                current_list = []
    
    if current_h2:
        parallel_entities["h2"].append(current_h2)
    if current_h3:
        parallel_entities["h3"].append(current_h3)
    if current_list:
        all_lists.append(current_list)
    
    parallel_entities["lists"] = all_lists
    res = []
    for key, items in parallel_entities.items():
        for item in items:
            if len(item) > 1:
                res.append(Parent(type="doc_" + key, parent="README " + key, items=item))

    return res


def compare_cosine(items1, items2):
    total_scores = []
    items1 = [str(item) for item in items1 if str(item).strip() != ""]
    items2 = [str(item) for item in items2 if str(item).strip() != ""]
    
    matrix = map_texts_cosine_with_cache(items1, items2)
    i2s_already_matched_with_i1s = []
    matched_rights = {}
    for i1, items in enumerate(matrix):
        scores = []
        mx = 0
        mx_right_i = -1
        for i2, cosine in enumerate(items):
            # avoid duplicates in the left column
            if i2 in i2s_already_matched_with_i1s:
                continue
            rat = hybrid_score(items1[i1], items2[i2], cosine)
            if rat > 0.6 and rat > mx:
                mx = rat
                mx_right_i = i2
                scores.append(rat)
                i2s_already_matched_with_i1s.append(i2)
        max_score = mx
        # avoid duplicates in the right column
        total_scores.append(max_score)
        if mx_right_i != -1:
            matched_rights[mx_right_i] = {"score": max_score, "with": i1}
    return total_scores, matched_rights

def similarity_score(par_ent1, par_ent2):
    total_scores = []

    items1 = par_ent1.items
    items2 = par_ent2.items

    k = 1
    if len(items1) > len(items2):
        k = len(items1) / len(items2)
    else:
        k = len(items2) / len(items1)
    if k > 3: # some sequence is bigger than anothe rmore than 3x
        return 0, [], {}

    total_scores, matched_rights = compare_cosine(items1, items2)
    #total_scores = compare_fuzz(items1, items2)

    if len([s for s in total_scores if s !=0]) == 1: # if only one items matched, skip it, garbage
        return 0, [], {}
    # here no weighted sum, because multiple good matches are better than one or two perfect ones
    res = sum(total_scores) if total_scores else 0
    return res, total_scores, matched_rights


def sort_parent_pairs(list1, list2):
    pairs = []
    #for p1, p2 in product(list1, list2):
    total = len(list1)*len(list2)
    if total > 50000:
        print(f"Too many items to compare ({total} operations). Skipping due to potentially too long execution")
        return pairs

    for p1, p2 in tqdm(product(list1, list2), total=total, desc="Analyzing.."):
        score, total_scores, matched_rights = similarity_score(p1, p2)
        if score > 0:
            p1.total_scores = total_scores
            p2.matched_rights = matched_rights
            pairs.append((p1, p2, score))
    
    pairs.sort(key=lambda x: x[2], reverse=True)
    return pairs

def report(project):
    parent_instances = collect_files_recursive(project)
    doc_parents = collects_doc_parents(project.doc_path)
    print(f"Found {str(len(parent_instances))} code items and {str(len(doc_parents))} doc items")
    pairs = sort_parent_pairs(parent_instances, doc_parents)

    print("REPORT:")
    for st in pairs:
        if st[2] > 0:
            doc = st[1]
            code = st[0]
            n=0
            documented = []
            explanation_items = []
            for i, item in enumerate(doc.items):
                if i in doc.matched_rights:
                    n+=1
                    corresponded_code_index = doc.matched_rights[i]["with"]
                    if corresponded_code_index >= len(code.items):
                        print(f"WARNING. corresponded_code_index {corresponded_code_index} not found in code.items", code.items)
                        continue
                    documented.append(corresponded_code_index)
                    explanation_items.append(f"Found item in documentation '{item}' (from {doc.parent}) matched with item in code '{code.items[corresponded_code_index]}' ({code.parent})")
            if n < len(doc.items):
                print("\n".join(explanation_items))
                print(f"==> RECOMMENDATION: You probably want to document other items from {code.parent}:")
                for i, item in enumerate(code.items):
                    if i not in documented:
                        print("* " + item)
            print("\n=====================================\n")

            #print("CODE: \n" + str(code) + "\nDOC: " + str(doc) + "\nSCORE:: " + str(st[2]) + "\n\n")

    end = time.time()

    print(f"Execution time: {end - start:.4f} seconds")