import os
from src.files_exclusions import is_file_to_skip
from src.ast.python import StringCheckExtractor as PyStringCheckExtractor
from src.ast.javascript import StringCheckExtractor as JSStringCheckExtractor

exclusions = [
    # Authentication / Authorization
    "bearer", "basic", "token", "jwt", "oauth", "apikey",

    # Data Types / Formats
    "integer", "int", "float", "double", "decimal", "number",
    "string", "boolean", "bool", "null", "undefined", "object",
    "array", "date", "timestamp", "uuid", "json", "xml", "yaml",
    "csv", "binary", "file", "int64", "int32"

    # HTTP Methods
    "get", "post", "put", "delete", "patch", "options", "head",

    # Content Types / MIME Types
    "application/json", "application/xml", "text/html", "text/plain",
    "application/octet-stream", "multipart/form-data", "application/pdf",

    # HTTP Status / Results
    "success", "error", "failed", "ok", "not_found",
    "unauthorized", "forbidden", "timeout", "internal_error", "true", "false"

    # File / Path Checks
    ".jpg", ".png", ".zip", ".tar.gz", "index.html", "README.md",
    "config", "settings",

    # Environment / Deployment
    "development", "staging", "production", "test", "debug",

    # Boolean / Flags
    "true", "false", "yes", "no", "on", "off",

    # Protocols / Schemes
    "http", "https", "ftp", "ssh", "tcp", "udp", "ws", "wss",

    # Security / Roles
    "readonly", "write", "read",
    # Events
    "click", "dblclick", "mousedown", "mouseup", "mousemove",
    "mouseover", "mouseout", "mouseenter", "mouseleave",
    "keydown", "keyup", "keypress",
    "submit", "change", "input", "focus", "blur", "load", "unload",
    "resize", "scroll", "contextmenu", "touchstart", "touchend", "enter"
    # DOM / Elements
    "div", "span", "input", "button", "form", "label", "textarea",
    "select", "option", "table", "thead", "tbody", "tr", "td",
    "ul", "li", "img", "a", "p", "h1", "h2", "h3", "h4", "h5", "h6",

    # Common JS Types / Values
    "undefined", "null", "true", "false", "NaN", "Infinity",
    "object", "function", "number", "string", "boolean", "symbol", "bigint",

    # Network / WebSocket
    "ws", "wss", "http", "https", "open", "close", "message", "error",

    # States / Status
    "loading", "loaded", "error", "success", "fail", "ready", "pending",

    # Misc
    "id", "class", "name", "value", "type", "disabled", "checked", "readonly",
    "visible", "hidden", "selected", "parameter", "parameters", "server", "servers"
]


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
        if "//" in const or const.isdigit() or const.lower().strip() in exclusions:
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
