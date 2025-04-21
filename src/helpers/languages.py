import sys
import os
import importlib
CLASSES_HASH = {}
INSTANCES_HASH = {}

def get_ext(file_path):
    return file_path.lower().split('.')[-1]

def load_plugins():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_dir = os.path.join(base_dir, '..', 'languages', 'classes')

    for filename in os.listdir(plugin_dir):
        if filename.endswith('.py'):
            name = filename[:-3]
            path = os.path.join(plugin_dir, filename)

            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)

            CLASSES_HASH[name] = getattr(module, 'LanguagePlugin')

load_plugins()

ext_lang = {
    "py": "python",
    "js": "javascript",
    "ts": "javascript",
}

def get_instance(ext, file_path):
    if ext not in ext_lang:
        return None
    lang_name = ext_lang[ext]
    if file_path in INSTANCES_HASH:
        return INSTANCES_HASH[file_path]

    if lang_name in CLASSES_HASH:
        inst = CLASSES_HASH[lang_name](file_path)
        INSTANCES_HASH[file_path] = inst
        return inst
    
    return None

def invoke_lang(file_path, method_name):
    ext = get_ext(file_path)
    inst = get_instance(ext, file_path)
    if not inst:
        return None
    method = getattr(inst, method_name)
    return method()