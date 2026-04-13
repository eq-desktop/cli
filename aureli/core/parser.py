import re

UUID = 0

def new_part(
    name="",
    kind="object",
    type="KavoObject",
    children=None,
    path="",
    id=None,
    args=None,
    value=None,
    properties=None,
):
    global UUID
    if children is None:
        children = []
    if args is None:
        args = []
    if properties is None:
        properties = {}
    if id is None:
        id = UUID
        UUID += 1

    return {
        "name": name,
        "kind": kind,
        "type": type,
        "id": id,
        "arguments": args,
        "path": path,
        "value": value,
        "properties": properties,
        "children": children,
    }


# ---------------- Utility ---------------- #

def strip_comments(src: str) -> str:
    src = re.sub(r"//.*$", "", src, flags=re.MULTILINE)
    src = re.sub(r"/\*[\s\S]*?\*/", "", src)
    return src


def normalize_indent(block: str) -> str:
    lines = block.split("\n")

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    min_indent = float("inf")
    for line in lines:
        if not line.strip():
            continue
        match = re.match(r"^(\s+)", line)
        if match:
            min_indent = min(min_indent, len(match.group(1)))
        else:
            min_indent = 0
            break

    if not min_indent or min_indent == float("inf"):
        min_indent = 0

    return "\n".join(
        line[min_indent:] if line.startswith(" " * min_indent) else line
        for line in lines
    )


def scan_block(lines, start_index):
    state = {"in_string": False, "escape": False, "depth": 1}
    body = []
    i = start_index

    while i < len(lines):
        line = lines[i]
        for c in line:
            if state["escape"]:
                state["escape"] = False
                continue
            if c == "\\":
                state["escape"] = True
                continue
            if c == '"':
                state["in_string"] = not state["in_string"]
                continue
            if not state["in_string"]:
                if c == "{":
                    state["depth"] += 1
                if c == "}":
                    state["depth"] -= 1

        if state["depth"] == 0:
            break
        body.append(line)
        i += 1

    return {"body": "\n".join(body), "endIndex": i}


def parse_value(raw: str):
    raw = raw.strip()
    if re.match(r'^".*"$', raw):
        return {"type": "string", "value": raw[1:-1]}
    if re.match(r"^-?\d+(\.\d+)?$", raw):
        return {"type": "number", "value": float(raw) if "." in raw else int(raw)}
    if raw in ("true", "false"):
        return {"type": "boolean", "value": raw == "true"}
    return {"type": "string", "value": raw}


# ---------------- Inline Property Parser ---------------- #

def parse_inline_props(s: str):
    props = {}
    i = 0

    def skip_spaces():
        nonlocal i
        while i < len(s) and s[i].isspace():
            i += 1

    def read_key_or_flag():
        nonlocal i
        skip_spaces()
        if i < len(s) and s[i] == '"':
            i += 1
            start = i
            while i < len(s) and s[i] != '"':
                i += 1
            val = s[start:i]
            i += 1
            return val

        start = i
        while i < len(s) and not re.match(r"[\s:]", s[i]):
            i += 1
        return s[start:i]

    def read_value():
        nonlocal i
        skip_spaces()
        if i < len(s) and s[i] == '"':
            i += 1
            start = i
            while i < len(s) and s[i] != '"':
                i += 1
            val = s[start:i]
            i += 1
            return val

        start = i
        while i < len(s) and not s[i].isspace():
            i += 1
        return s[start:i]

    while i < len(s):
        skip_spaces()
        if i >= len(s):
            break

        key = read_key_or_flag()
        skip_spaces()

        if i < len(s) and s[i] == ":":
            i += 1
            raw = read_value()
            if re.match(r"^-?\d+(\.\d+)?$", raw):
                props[key] = float(raw) if "." in raw else int(raw)
            elif raw in ("true", "false"):
                props[key] = raw == "true"
            else:
                props[key] = raw
        else:
            props[key] = True

    return props


# ---------------- Parser ---------------- #

def parse(data: str, parent=None):
    data = strip_comments(data)
    lines = data.split("\n")
    root = parent or new_part(name="root", path="root")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # IMPORT
        if line.startswith("@import "):
            file_path = re.split(r'import(?: nonfinal)?\s+', line)[1].replace('"', '').replace("'", "").strip()

            new_node = new_part(
                name="import:Unknown",
                kind="import",
                path=f"{root['path']}.import:Unknown",
                type="KavoImport",
                value=file_path,
            )
            new_node["name"] = f"import:{new_node['id']}"
            new_node["path"] = f"{root['path']}.{new_node['name']}"
            root["children"].append(new_node)
            i += 1
            continue

        # FUNCTION
        if re.match(r'^[\w]+\(.*\)\s*\{?$', line):
            name = line.split("(")[0].strip()
            args = [a.strip() for a in re.search(r'\((.*?)\)', line).group(1).split(",") if a.strip()]

            node = new_part(
                name=name,
                kind="function",
                path=f"{root['path']}.{name}",
                type="KavoFunction",
                args=args,
            )

            if "{" not in line:
                i += 1

            result = scan_block(lines, i + 1)
            node["children"].append(normalize_indent(result["body"]))
            root["children"].append(node)
            i = result["endIndex"] + 1
            continue

        # SECTION
        if "{" in line:
            name = line.split(" ")[0]
            prop_string = re.sub(r"[{}]", "", line[len(name):]).strip()
            node = new_part(name=name, kind="section", path=f"{root['path']}.{name}", type="KavoSection")

            if prop_string:
                node["properties"] = parse_inline_props(prop_string)

            result = scan_block(lines, i + 1)
            parse(result["body"], node)
            root["children"].append(node)
            i = result["endIndex"] + 1
            continue

        # PROPERTY
        if ":" in line:
            k, v = re.split(r":(.+)", line, maxsplit=1)[:-1]
            parsed = parse_value(v)
            root["children"].append(new_part(
                name=k.strip(),
                kind="property",
                path=f"{root['path']}.{k.strip()}",
                type=parsed["type"],
                value=parsed["value"],
            ))
            i += 1
            continue

        raise ValueError(f"Unknown syntax: {line}")

    return root