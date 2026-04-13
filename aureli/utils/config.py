import json
from ..config import *

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def set_setting(key_path: str, value: str):
    cfg = load_config()
    keys = key_path.split(".")
    ref = cfg
    for k in keys[:-1]:
        if k not in ref or not isinstance(ref[k], dict):
            ref[k] = {}
        ref = ref[k]

    # Try to cast value into int/float/bool if possible
    if value.isdigit():
        val: object = int(value)
    else:
        try:
            val = float(value)
        except ValueError:
            if value.lower() in ("true", "false"):
                val = value.lower() == "true"
            else:
                val = value

    ref[keys[-1]] = val
    save_config(cfg)
    if val == True: val = "true"
    if val == False: val = "false"
    if isinstance(val, list): val = ", ".join(val)
    print(f"\033[92mSet {key_path} = {val}\033[0m")

def get_setting(key_path: str):
    cfg = load_config()
    if key_path == "all":
        print("\033[All Sections:\033[0m")
        for k in cfg:
            print(f"\033[94m- {k}\033[0m")
        return
    keys = key_path.split(".")
    ref = cfg
    for k in keys:
        if k not in ref:
            print(f"Setting {key_path} not found")
            return
        ref = ref[k]
    # style ref
    if ref == True: ref = "\033[92mtrue\033[0m"
    if ref == False: ref = "\033[91mfalse\033[0m"
    if isinstance(ref, list): ref = ", ".join(ref)
    if isinstance(ref, dict):
        final_string = ""
        def recurse(ref):
            nonlocal final_string
            for k in ref:
                if isinstance(ref[k], dict):
                    final_string += f"\033[94m{k}\033[0m\n"
                    recurse(ref[k])
                else:
                    val = ref[k]
                    if val == True: val = "true"
                    if val == False: val = "false"
                    if isinstance(val, list): val = ", ".join(val)
                    if val == "true":
                        final_string += f"\033[94m{k}\033[0m = \033[92m{val}\033[0m\n"
                    elif val == "false":
                        final_string += f"\033[94m{k}\033[0m = \033[91m{val}\033[0m\n"
                    else:
                        final_string += f"\033[94m{k}\033[0m = \033[90m{val}\033[0m\n"
        recurse(ref)
        print(final_string)
        return
    print(ref)

def reset_setting(setting: str):
    cfg = load_config()
    keys = setting.split(".")
    d = cfg
    for k in keys[:-1]:
        if k not in d:
            return  # nothing to reset
        d = d[k]
    d.pop(keys[-1], None)
    save_config(cfg)

def reset_config():
    save_config({})
