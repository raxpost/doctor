import ast

# Covers python strings comparisons:
# var == "string"
# "string" == var
# ["startswith", "endswith", "find", "index"]

class StringCheckExtractor(ast.NodeVisitor):
    def __init__(self, txt, file_path):
        self.tainted_vars = set()
        self.tree = ast.parse(txt, filename=file_path)
        self.important_constants = set()
        self.visit(self.tree)

    def visit_Compare(self, node):
        left = node.left
        comparators = node.comparators
        if isinstance(left, ast.Name) and left.id in self.tainted_vars:
            for comp in comparators:
                if isinstance(comp, ast.Constant) and isinstance(comp.value, str):
                    self.important_constants.add(comp.value)
        elif any(isinstance(comp, ast.Name) and comp.id in self.tainted_vars for comp in comparators):
            if isinstance(left, ast.Constant) and isinstance(left.value, str):
                self.important_constants.add(left.value)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method in ["startswith", "endswith", "find", "index"]:
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        self.important_constants.add(arg.value)
        self.generic_visit(node)