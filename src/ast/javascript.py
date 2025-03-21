import re

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
