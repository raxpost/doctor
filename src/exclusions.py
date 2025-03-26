import os

def is_file_to_skip(file_path):
    file = os.path.basename(file_path)
    paths_exclusions = ["node_modules", "test", "documentation", ".venv", "venv", "virtualenv", ".git", "schema", "build", "static", "CHANGELOG", "CREDITS", "LEGAL", "LICENSE", "MANIFEST", "dist/"]
    exclusions = ["README.md", "package.json", "package-lock.json", "pyproject.toml", "pdm.lock", "__init__"]
    return any(pe in file_path for pe in paths_exclusions) or file in exclusions


file_extensions = [
    ".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".csv", ".json", ".xml", ".html", ".htm", ".jpg", ".jpeg", ".png",
    ".gif", ".bmp", ".svg", ".mp3", ".wav", ".mp4", ".mov", ".avi",
    ".mkv", ".zip", ".rar", ".7z", ".tar", ".gz", ".exe", ".msi",
    ".apk", ".iso", ".dll", ".py", ".java", ".c", ".cpp", ".js",
    ".ts", ".php", ".rb", ".go", ".sh", ".bat", ".log"
]

data_types = ["int", "integer", "float", "bool", "str", "list", "dict", "set", "tuple", "bytes", "complex", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "uintptr", "byte", "rune", "float32", "float64", "complex64", "complex128", "string", "bool", "error", "interface", "map", "slice", "chan", "byte", "short", "int", "long", "float", "double", "boolean", "char", "object", "list", "map", "set", "void", "int", "float", "double", "bool", "character", "dictionary", "set", "optional", "any", "anyobject", "never", "tuple", "int", "float", "bool", "array", "object", "callable", "iterable", "null", "resource", "mixed", "void", "function", "class", "interface", "enum", "struct", "pointer", "reference", "tuple"]


common_terms = ["type", "name", "and", "number", "false", "description", "text", "string", "for", "true", "function", "work", "https", "http", "with", "image", "index", "lib", "filename", "that", "home", "currency", "colno", "you", "input", "value", "percent", "output", "this", "from", "are", "symbol", "source", "object", "data", "target", "properties", "title", "path", "rgba", "api", "code", "width", "height", "file", "content", "other", "default", "get", "url", "video", "page", "image", "list", "entry", "entries", "item", "items", "left", "right", "format", "children", "search", "user", "schema", "message", "service", "class", "global", "private", "some", "any",
"token", "id", "key", "secret", "hash", "auth", "login", "logout", "session", "request",
"response", "client", "server", "host", "port", "domain", "protocol", "status", "error",
"exception", "debug", "log", "trace", "cache", "config", "setting", "options", "option", "params",
"version", "build", "release", "update", "upgrade", "install", "run", "execute", "thread",
"process", "memory", "storage", "disk", "cpu", "load", "limit", "timeout", "retry", "queue",
"event", "listener", "handler", "callback", "stream", "buffer", "packet",
"binary", "hex", "base64", "encode", "decode", "serialize", "deserialize", "parse", "compile",
"render", "view", "model", "controller", "route", "test", "status", "quota", "date", "self", "this", "warning", "info", "debug", "main", "method", "mode", 'undefined', 'production', "development", "prd", "prod", "dev", "stage", "yes", "no", "NaN", "bearer"
]

def is_http_content_or_header(s):
    s_lower = s.lower()
    return (
        s_lower.startswith("content-") or
        s_lower in {
            "accept", "authorization", "user-agent", "host", "connection", "cache-control",
            "cookie", "set-cookie", "upgrade", "pragma", "referer", "origin", "accept-encoding",
            "accept-language", "etag", "expires", "last-modified", "location", "server", "date",
            "transfer-encoding", "content-type", "content-length", "content-encoding", "content-disposition"
        } or
        "/" in s_lower and s_lower.split("/")[0] in {
            "text", "image", "application", "audio", "video", "multipart", "message", "font"
        }
    )

def is_in_common_tech_terms(word):
    word = word.lower().strip()
    if word in file_extensions:
        return True
    if "." + word in file_extensions:
        return True
    if word in data_types:
        return True
    if word in common_terms:
        return True
    if is_http_content_or_header(word):
        return True
    return False
    