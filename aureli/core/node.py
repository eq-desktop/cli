class KvoNode:
    def __init__(self, obj: dict):
        self._obj = obj

    # ---------- Basic access ---------- #

    @property
    def raw(self):
        return self._obj

    @property
    def children(self):
        return [KvoNode(c) for c in self._obj.get("children", [])]

    @children.setter
    def children(self, children):
        self._obj["children"] = [
            c.raw if isinstance(c, KvoNode) else c for c in children
        ]

    @property
    def id(self):
        return self._obj.get("id")

    @id.setter
    def id(self, value):
        self._obj["id"] = value

    @property
    def path(self):
        return self._obj.get("path")

    @path.setter
    def path(self, value):
        self._obj["path"] = value

    @property
    def name(self):
        return self._obj.get("name")

    @name.setter
    def name(self, value):
        self._obj["name"] = value

    @property
    def kind(self):
        return self._obj.get("kind")

    @kind.setter
    def kind(self, value):
        self._obj["kind"] = value

    @property
    def type(self):
        return self._obj.get("type")

    @type.setter
    def type(self, value):
        self._obj["type"] = value

    @property
    def args(self):
        return self._obj.get("args")

    @args.setter
    def args(self, value):
        self._obj["args"] = value

    @property
    def value(self):
        return self._obj.get("value")

    @value.setter
    def value(self, value):
        self._obj["value"] = value

    @property
    def properties(self):
        return self._obj.get("properties", {})

    @properties.setter
    def properties(self, value):
        self._obj["properties"] = value
    
    def add_property(self, key, value):
        self._obj["properties"][key] = value
    
    def remove_property(self, key):
        del self._obj["properties"][key]

    # ---------- Path helpers ---------- #

    def path_trimmed(self):
        return ".".join(self.path.split(".")[1:])

    def path_last(self):
        return self.path.split(".")[-1]

    def path_parent(self):
        return ".".join(self.path.split(".")[1:-1])

    def path_children(self):
        return self.path.split(".")[1:]

    def paths(self):
        return self.path.split(".")

    # ---------- Find ---------- #

    def find(self, name):
        return next((c for c in self.children if c.name == name), None)

    f = find

    def find_all(self, name):
        return [c for c in self.children if c.name == name]

    fA = find_all

    # ---------- Properties ---------- #

    def prop(self, key):
        return self.properties.get(key)

    p = prop

    # ---------- Filters ---------- #

    def filter_kind(self, kind):
        return [c for c in self.children if c.kind == kind]

    fK = filter_kind

    # ---------- Recursive search ---------- #

    def search(self, name):
        if self.name == name:
            return self
        for child in self.children:
            found = child.search(name)
            if found:
                return found
        return None

    s = search

    # ---------- Debug print ---------- #

    def print(self, indent=0):
        pad = " " * (indent * 2)
        out = f"{pad}{self.kind}: {self.name}\n"
        if self.kind == "function":
            return out
        for child in self.children:
            out += child.print(indent + 1)
        return out

    pr = print

    def print_now(self, indent=0):
        pad = " " * (indent * 2)
        print(f"{pad}{self.kind}: {self.name}")
        if self.kind == "function":
            return
        for child in self.children:
            child.print_now(indent + 1)

    prNow = print_now

    # ---------- Child operations ---------- #

    def map_children(self, fn):
        return [fn(c) for c in self.children]

    mC = map_children

    def has_child(self, name):
        return any(c.name == name for c in self.children)

    hC = has_child

    def add_child(self, child):
        if "children" not in self._obj:
            self._obj["children"] = []
        self._obj["children"].append(child.raw if isinstance(child, KvoNode) else child)

    def remove_child(self, id):
        self._obj["children"] = [c for c in self._obj.get("children", []) if c.get("id") != id]

    # ---------- Navigation ---------- #

    def navigate(self, path):
        if not path:
            return self

        parts = path.split(".")
        current = self

        for i, part in enumerate(parts):
            # last part → property check
            if i == len(parts) - 1 and current.prop(part) is not None:
                return current.prop(part)

            nxt = current.find(part)
            if not nxt:
                return None
            current = nxt

        return current

    n = navigate
    nav = navigate