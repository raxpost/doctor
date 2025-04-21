# Looks for validation of variables against some strings, assuming such cases should be documented

import os
from src.helpers.exclusions import is_file_to_skip, is_in_common_tech_terms
from src.languages.classes.python import StringCheckExtractor as PyStringCheckExtractor
from src.languages.classes.javascript import StringCheckExtractor as JSStringCheckExtractor
from src.core.report import Report
from src.helpers.languages import invoke_lang


def extract_external_constants(file_path, constants_dict):
    important_constants = invoke_lang(file_path, "fetch_comparisons")
    if not important_constants:
        return
    for const in important_constants:
        if "//" in const or const.isdigit() or is_in_common_tech_terms(const):
            continue
        if const in constants_dict:
            constants_dict[const] = [constants_dict[const][0] + 1, file_path]
        else:
            constants_dict[const] = [1, file_path]

def report(p):
    r = Report("Variables validation")
    constants_dict = {}
    with open(p.doc_path, 'r', encoding='utf-8') as f:
        doc = str(f.read())

    for witem in p.walk_items:
        for file in witem.files:
            file_path = os.path.join(witem.root, file)
            extract_external_constants(file_path, constants_dict)

    sorted_constants = sorted(constants_dict.items(), key=lambda item: item[1][0], reverse=True)
    for const, count_list in sorted_constants:
        if count_list[0] > 0 and const not in doc:
            r.advice_add("It looks like you validate against <{}>({}) from {}. Potential values could be documented", (const, count_list[0], count_list[1]))

    return r
