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
            re.compile(r"environ\.get\(['\"]([A-Z0-9_]+)['\"]"),
            re.compile(r"environ\[['\"]([A-Z0-9_]+)['\"]"),
            re.compile(r"getenv\(['\"]([A-Z0-9_]+)['\"]"),
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



class StringCheckExtractor(ast.NodeVisitor):
    def __init__(self, txt, file_path):
        self.tree = ast.parse(txt, filename=file_path)
        self.important_constants = set()
        self.visit(self.tree)

    def visit_Compare(self, node):
        left = node.left
        comparators = node.comparators
        if isinstance(left, ast.Constant) and isinstance(left.value, str):
            self.important_constants.add(left.value)
        for comp in comparators:
            if isinstance(comp, ast.Constant) and isinstance(comp.value, str):
                self.important_constants.add(comp.value)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method in ["startswith", "endswith", "find", "index"]:
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        self.important_constants.add(arg.value)
        self.generic_visit(node)
