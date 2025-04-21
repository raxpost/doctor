class Item:
    def __init__(self, template, subs, compiled):
        self.template = template
        self.subs = subs
        self.compiled = compiled

    def __str__(self):
        return self.compiled

    def __repr__(self):
        return self.compiled


class Report:
    def __init__(self, usecase):
        self.usecase  = usecase
        self.lines = []
        self.meta = []
        self.debug = []
        self.advices = []
        self.execution_time = None

    def format(self, template, subs):
        new_t = tuple(", ".join(map(str, x)) if isinstance(x, list) else x for x in subs)
        return template.format(*new_t)

    def advice_add(self, template, subs):
        compiled = self.format(template, subs)
        item = Item(template, subs, compiled)
        self.advices.append(item)
        return compiled

    def meta_add(self, template, subs):
        compiled = self.format(template, subs)
        item = Item(template, subs, compiled)
        self.meta.append(item)
        return compiled
    
    def debug_add(self, template, subs):
        compiled = self.format(template, subs)
        item = Item(template, subs, compiled)
        self.debug.append(item)
        return compiled


    def print(self):
        print("# " + self.usecase + "\n")
        print("\n".join([item.compiled for item in self.meta]))
        print("\n".join([item.compiled for item in self.advices]))
        print("=========================================")