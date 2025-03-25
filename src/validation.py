import os
from src.exclusions import is_file_to_skip, is_in_common_tech_terms
from src.ast.python import StringCheckExtractor as PyStringCheckExtractor
from src.ast.javascript import StringCheckExtractor as JSStringCheckExtractor




ast_extractors = {
    "py": PyStringCheckExtractor,
    "js": JSStringCheckExtractor,
    "ts": JSStringCheckExtractor,
    "tsx": JSStringCheckExtractor
}

def extract_external_constants(file_path, ext, constants_dict):
    if ext not in ast_extractors:
        return
    with open(file_path, 'r', encoding='utf-8') as f:
        txt = f.read()
    extractor = ast_extractors[ext]
    ex = extractor(txt, file_path)
    for const in ex.important_constants:
        if "//" in const or const.isdigit() or is_in_common_tech_terms(const):
            continue
        if const in constants_dict:
            constants_dict[const] = [constants_dict[const][0] + 1, file_path]
        else:
            constants_dict[const] = [1, file_path]

def report(p):
    constants_dict = {}
    with open(p.doc_path, 'r', encoding='utf-8') as f:
        doc = str(f.read())

    for witem in p.walk_items:
        for file in witem.files:
            ext = file.lower().split('.')[-1]
            file_path = os.path.join(witem.root, file)
            if is_file_to_skip(file_path):
                continue
            extract_external_constants(file_path, ext, constants_dict)

    sorted_constants = sorted(constants_dict.items(), key=lambda item: item[1][0], reverse=True)
    for const, count_list in sorted_constants:
        if count_list[0] > 0 and const not in doc:
            print(f"It looks like you validate against <{const}>({count_list[0]}) from {count_list[1]}. Potential values could be documented\n")
