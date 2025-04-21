import ast
import re
from src.languages.abstract import Language

class LanguagePlugin(Language):
    def __init__(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            txt = f.read()
        self.content = txt
        self.file_path = file_path

    # consider using ast
    def fetch_env_vars(self):
        patterns = [
            re.compile(r"process\.env\.([A-Z0-9_]+)"),
            re.compile(r"process\.env\[['\"]([A-Z0-9_]+)['\"]\]"),
        ]
        matches_for_all_patterns = []
        for p in patterns:
            matches = p.findall(self.content)
            if matches:
                matches_for_all_patterns += matches
        return list(set(matches_for_all_patterns))
    

    def fetch_comparisons(self):
        comp = StringCheckExtractor(self.content, self.file_path)
        return comp.important_constants

# tree-sitter-languages is pain, just regexps here
# Covers python strings comparisons:
# var == "string"
# "string" == var
# ["startswith", "endswith", "find", "index"]

regex_patterns = [
    (re.compile(r'\b[a-zA-Z0-9_$]+\s*={2,3}\s*["\']([^"\']+)["\']'), 1),  # var == "string"
    (re.compile(r'["\']([^"\']+)["\']\s*={2,3}\s*\b[a-zA-Z0-9_$]+'), 1),  # "string" == var
    (re.compile(r'(startsWith|endsWith|find|indexOf)\s*\(\s*["\']([^"\']+)["\']\s*\)'), 2) # method("string")
]

class StringCheckExtractor:
    def __init__(self, txt, file_path):
        self.important_constants = set()
        self.collect_matched_strings(txt)


    def collect_matched_strings(self, content):
        for pattern, group_idx in regex_patterns:
            for match in pattern.finditer(content):
                val = match.group(group_idx)
                self.important_constants.add(val)
