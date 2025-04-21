# Parallel entities different kinds of entities (see function collect_code_items)
# which appear at the same level. We assume they belong to one class of entities and should be
# documented
import os
import json
import yaml
from concurrent.futures import ThreadPoolExecutor
from src.helpers.languages import invoke_lang
from itertools import product
from tqdm import tqdm
from src.core.report import Report
from collections import defaultdict
from string import punctuation
import re
from multiprocessing import Value
from src.helpers.comparison import hybrid_strings_lists_comparison

import time
import sys

start = time.time()

class Parallents:
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

        return "ParEnt (" + self.type + ", " + str(self.parallents) + "):\n" + txt + "\n"

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


def should_skip_root(root, base_path):
    rel = os.path.relpath(root, base_path)
    parts = rel.split(os.sep)
    return any(p.startswith('.') for p in parts if p != '.')

# Collects:
# - files/folders in a folder
# - yaml, json sections of the same level
# - env vars from one file
# there should be more than 1 item
def collect_code_items(project):
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
            if ext == "json" and "package" not in file:
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except Exception as e:
                        print(e)
                        data = {}
                    if isinstance(data, dict):
                        collect_yaml_keys(data, root, parent_instances, "JSON")
            else:
                envvars = invoke_lang(file_path, "fetch_env_vars")
                if envvars:
                    parent_instances.append(Parallents(type="file", parent=file_path, items=envvars))
            
            file_list.append(file.replace("." + ext, ""))

        if file_list and project.project_root != root: # in root the context is getting blurred, skip it
            parent_instances.append(Parallents(type="file", parent=root, items=file_list))

        parent_instances.append(Parallents(type="folder", parent=root, items=[d for d in dirs]))
    res = [p for p in parent_instances if len(p.items) > 1]

    return res

def collect_yaml_keys(data, parent_key, parent_instances, type):
    if isinstance(data, dict):
        keys = list(data.keys())
        if keys:
            parent_instances.append(Parallents(type=type, parent=parent_key, items=keys))
        for key, value in data.items():
            collect_yaml_keys(value, key, parent_instances, type)

def extract_env_vars(file_path, ext, parent_instances):
    with open(file_path, 'r', encoding='utf-8') as f:
        txt = f.read()
        if ext not in patterns:
            return
        matches_for_all_patterns = []
        for p in patterns[ext]:
            matches = p.findall(txt)
            if matches:
                matches_for_all_patterns += matches
        parent_instances.append(Parallents(type="EnvVar", parent=file_path, items=list(set(matches_for_all_patterns))))


# Collects documentation parallel entities:
# 1. sections on the same level
# 2. lists started with *, - or digit
def collects_doc_parents(doc_path):
    readme_content = ""
    with open(doc_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()
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
                res.append(Parallents(type="doc_" + key, parent="README " + key, items=item))

    return res

def compare_par_ents(par_ent1, par_ent2):
    total_scores = []

    items1 = par_ent1.items
    items2 = par_ent2.items

    k = 1
    if len(items1) > len(items2):
        k = len(items1) / len(items2)
    else:
        k = len(items2) / len(items1)
    if k > 3: # some sequence is bigger than anothe more than 3x
        return 0, [], {}

    # matched_rights has items2(docs) indecies
    total_scores, matched_rights = hybrid_strings_lists_comparison(items1, items2)
    #total_scores = compare_fuzz(items1, items2)

    if len([s for s in total_scores if s !=0]) == 1: # if only one items matched, skip it, garbage
        return 0, [], {}
    # here no weighted sum, because multiple good matches are better than one or two perfect ones
    res = sum(total_scores) if total_scores else 0
    return res, total_scores, matched_rights


# list1 - list of code Parallents instances. list2 - list of doc Parallents instances
def sort_parent_pairs(list1, list2):
    pairs = []
    #for p1, p2 in product(list1, list2):
    total = len(list1)*len(list2)
    if total > 50000:
        print(f"Too many items to compare ({total} operations). Skipping due to potentially too long execution")
        return pairs
    for p1, p2 in tqdm(product(list1, list2), total=total, desc="Analyzing.."):
        # matched_rights has items2(docs) indecies
        score, total_scores, matched_rights = compare_par_ents(p1, p2)
        #print(score, p1.items, p2.items, matched_rights)
        if score > 0:
            p1.total_scores = total_scores
            #p2.matched_rights = matched_rights
            pairs.append((p1, p2, score, matched_rights))
    
    pairs.sort(key=lambda x: x[2], reverse=True)
    return pairs

def report(project):
    r = Report("Parallel entities")
    parent_instances =  collect_code_items(project)
    doc_parents = collects_doc_parents(project.doc_path)
    r.debug_add("Found {} code items and {} doc items", (str(len(parent_instances)), str(len(doc_parents))))
    pairs = sort_parent_pairs(parent_instances, doc_parents)
    for st in pairs:
        if st[2] > 0:
            doc = st[1]
            code = st[0]
            matched_rights = st[3]
            n=0
            documented = []
            explanation_items = []
            for i, item in enumerate(doc.items):
                if i in matched_rights:
                    n+=1
                    corresponded_code_index = matched_rights[i]["with"]
                    score = matched_rights[i]["score"]
                    if corresponded_code_index >= len(code.items):
                        print(f"WARNING. corresponded_code_index {corresponded_code_index} not found in code.items", code.items)
                        continue
                    documented.append(corresponded_code_index)
                    explanation_items.append(["Found item in documentation '{}' (from {}) matched with item in code '{}' ({}) {}", (item, doc.parent, code.items[corresponded_code_index], code.parent, score)])
            # @TODO CHECK FOR EXTRA NON EXISTING ITEM
            if n < len(code.items): # report only something is missing
                for exp in explanation_items:
                    r.meta_add(exp[0], exp[1])
                items_to_document = [item for i, item in enumerate(code.items) if i not in documented]
                r.advice_add("You probably want to document other items from {}: {}", (code.parent, items_to_document))

    end = time.time()
    r.execution_time = end - start
    return r