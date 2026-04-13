from pathlib import Path
import os
from ..core.node import KvoNode
from ..core.parser import parse
from ..config import *
import tempfile
import subprocess
import shutil
import json
from ..utils.system import ok

def get_plugins():
    plugins = []
    dirs = os.listdir(os.path.expanduser(RUNTIME_PATH + "/plugins"))
    for directory in dirs:
        # Read plugin.kvo file inside plugins
        content = ""
        with open(os.path.expanduser(RUNTIME_PATH + "/plugins/" + directory + "/plugin.kvo"), "r") as f:
            content = f.read()
        kavo = KvoNode(parse(content))
        kavo.add_property("directory", directory)
        files_of_dir = os.listdir(os.path.expanduser(RUNTIME_PATH + "/plugins/" + directory))
        files = {}
        for file in files_of_dir:
            if file.endswith(".kvo"):
                with open(os.path.expanduser(RUNTIME_PATH + "/plugins/" + directory + "/" + file), "r") as f:
                    files[file] = f.read()
        imports = kavo.nav("plugin").filter_kind("import")
        for import_ in imports:
            import_path = import_.value
            if import_path.startswith("/"): pass
            elif import_path.startswith("./"):
                import_path = import_path[2:]
            else: pass
            import_nav_path = import_.path_parent()
            import_file = files[import_path]
            import_kvo = KvoNode(parse(import_file))
            for child in import_kvo.children:
                kavo.nav(import_nav_path).add_child(child)
            kavo.nav(import_nav_path).remove_child(import_.id)
        plugins.append(kavo)
    return plugins

def get_plugin(id: str):
    plugins = get_plugins()
    for plugin in plugins:
        props = plugin.nav("plugin").properties
        key = next(iter(props))
        if key == id:
            return plugin

def prompt_default(text: str, default: str) -> str:
    """
    Prompt the user with a default value.
    If user presses Enter, default is returned.
    """
    response = input(f"{text} [{default}]: ").strip()
    return response or default    

def install_plugin(url: str):
    # --- Validate URL ---
    if not (url.startswith("https://") or url.startswith("http://") or url.startswith("git@")):
        raise ValueError("Only git/http(s) URLs are allowed")

    plugins_dir = Path(RUNTIME_PATH) / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    # --- Clone to temp dir ---
    with tempfile.TemporaryDirectory(prefix="aureli-plugin-") as tmp:
        tmp_path = Path(tmp)

        result = subprocess.run(
            [
                "git", "clone",
                "--depth", "1",
                "--filter=blob:none",
                url,
                str(tmp_path)
            ],
            capture_output=True,
            text=True,
            timeout=25
        )

        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed:\n{result.stderr}")

        # --- Read metadata ---
        kvo_file = tmp_path / "plugin.kvo"
        if not kvo_file.exists():
            raise FileNotFoundError("plugin.kvo not found in repository")

        content = kvo_file.read_text()
        kavo = KvoNode(parse(content))

        plugin_id = next(iter(kavo.nav("plugin").properties), None)
        if not plugin_id:
            raise ValueError("Plugin ID missing in plugin.kvo")

        # --- Check if already installed ---
        if get_plugin(plugin_id):
            raise FileExistsError(f"Plugin '{plugin_id}' is already installed")

        # --- Final destination uses ID, not repo name ---
        target_dir = plugins_dir / plugin_id

        shutil.move(str(tmp_path), target_dir)

    ok(f"Plugin '{plugin_id}' installed")

def new_plugin():
    print("Creating new Aureli plugin...")

    while True:
        dir_name = input("Enter the plugin folder name (or '.' for current folder): ").strip()
        if not dir_name:
            print("Folder name cannot be empty")
            continue

        if dir_name == ".":
            target_path = Path.cwd()
        else:
            target_path = Path.cwd() / dir_name
            if target_path.exists():
                print(f"Folder '{dir_name}' already exists. Pick another name.")
                continue
            target_path.mkdir(parents=True)

        print(f"Plugin development folder ready at: {target_path}")
        break

    print("\nEnter plugin metadata:")
    plugin_name = prompt_default("Plugin Name", "MyPlugin")
    plugin_id = prompt_default("Plugin Id", plugin_name.lower().replace(" ", "-"))
    plugin_author = prompt_default("Author", "Anonymous")
    plugin_version = prompt_default("Version", "0.1.0")
    plugin_api = prompt_default("API Version", PLUGIN_API_VERSION)
    plugin_description = prompt_default("Description", "A new Aureli plugin")

    kvo_content = f"""plugin "{plugin_id}" {{
  meta {{
    name: "{plugin_name}"
    author: "{plugin_author}"
    version: "{plugin_version}"
    api: "{plugin_api}"
    description: "{plugin_description}"
  }}
}}
"""

    kvo_path = target_path / "plugin.kvo"
    kvo_path.write_text(kvo_content, encoding="utf-8")
    ok(f"plugin.kvo created at {kvo_path}")


def load_plugin(source_folder: str):
    source_path = Path(source_folder).expanduser().resolve()
    if not source_path.exists() or not source_path.is_dir():
        raise FileNotFoundError(f"Source folder '{source_folder}' does not exist or is not a directory")

    kvo_file = source_path / "plugin.kvo"
    if not kvo_file.exists():
        raise FileNotFoundError(f"No 'plugin.kvo' found in {source_path}")

    # Read metadata
    content = kvo_file.read_text(encoding="utf-8")
    kavo = KvoNode(parse(content))
    meta = kavo.nav("plugin.meta")
    plugin_id = next(iter(kavo.nav("plugin").properties), None)
    if not plugin_id:
        raise ValueError("plugin.kvo is missing the 'id' field")

    # Destination path
    plugins_dir = Path(RUNTIME_PATH) / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    target_path = plugins_dir / plugin_id

    if target_path.exists():
        raise FileExistsError(f"Plugin '{plugin_id}' is already installed")

    # Copy folder
    shutil.copytree(source_path, target_path)
    ok(f"Plugin '{meta.nav('name').value}' loaded into plugins folder as '{plugin_id}'")

def meta_plugin(url: str):
    if not (url.startswith("https://") or url.startswith("http://") or url.startswith("git@")):
        raise ValueError("Only git/http(s) URLs are allowed")

    with tempfile.TemporaryDirectory(prefix="aureliplugin-") as tmp:
        tmp_path = Path(tmp)

        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", url, str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=20
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed:\n{result.stderr}")

        kvo_file = tmp_path / "plugin.kvo"
        if not kvo_file.exists():
            raise FileNotFoundError("plugin.kvo not found in repository")

        content = kvo_file.read_text(encoding="utf-8")
        kavo = KvoNode(parse(content))

        plugin_node = kavo.nav("plugin")
        plugin_id = next(iter(plugin_node.properties), None)

        meta = plugin_node.nav("meta")

        installed = get_plugin(plugin_id) is not None

        print(f"\nInformation for '{meta.nav('name').value}' Plugin")
        print("─" * 40)
        print(f"Name:        {meta.nav('name').value}")
        print(f"ID:          {plugin_id}")
        print(f"Version:     {meta.nav('version').value}")
        print(f"API:         {meta.nav('api').value}")
        print(f"Author:      {meta.nav('author').value}")
        print(f"Description: {meta.nav('description').value}")
        print(f"Installed:   {'Yes' if installed else 'No'}")

def uninstall_plugin(id: str):
    plugin = get_plugin(id)
    if plugin is None:
        raise FileNotFoundError(f"Plugin '{id}' is not installed")

    plugin_dir_name = plugin.prop("directory")
    if not plugin_dir_name:
        raise FileNotFoundError(f"Plugin '{id}' does not have a directory assigned")

    plugin_dir = Path(RUNTIME_PATH) / "plugins" / plugin_dir_name

    if not plugin_dir.exists():
        raise FileNotFoundError(f"Plugin '{id}' directory '{plugin_dir}' not found")

    try:
        shutil.rmtree(plugin_dir)
    except Exception as e:
        raise RuntimeError(f"Failed to remove plugin '{id}': {e}")

    ok(f"Plugin '{id}' uninstalled successfully")

def update_plugin(id: str):
    plugin = get_plugin(id)
    if plugin is None:
        raise FileNotFoundError(f"Plugin '{id}' is not installed")

    plugin_dir_name = plugin.prop("directory")
    if not plugin_dir_name:
        raise FileNotFoundError(f"Plugin '{id}' does not have a directory assigned")

    plugin_dir = Path(RUNTIME_PATH) / "plugins" / plugin_dir_name

    if not plugin_dir.exists():
        raise FileNotFoundError(f"Plugin '{id}' directory '{plugin_dir}' not found")

    if not (plugin_dir / ".git").exists():
        raise RuntimeError(f"Plugin '{id}' is not a git repository, cannot update")

    try:
        result = subprocess.run(
            ["git", "-C", str(plugin_dir), "pull", "--ff-only"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            raise RuntimeError(f"Update failed:\n{result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Update timed out for plugin '{id}'")

    ok(f"Plugin '{id}' updated successfully")

def list_plugins():
    plugins = get_plugins()

    for plugin in plugins:
        try:
            props = plugin.nav("plugin").properties or {}
            key = next(iter(props), "unknown")

            name = plugin.nav("plugin.meta.name").value
            author = plugin.nav("plugin.meta.author").value

            print(" · " + "\033[90m" + f"{name} — {author}" + "\033[0m")
            print(" ├ Id: " + "\033[94m" + key + "\033[0m")
            print(" └ Enabled: " + "\033[92menabled\033[0m")
        except Exception as e:
            print(" · \033[91mBroken plugin\033[0m:", e)

def compile_plugin(id: str, compact: bool):
    plugins = get_plugins()
    # get plugin
    for plugin in plugins:
        props = plugin.nav("plugin").properties
        key = next(iter(props))
        if key == id:
            print(json.dumps(plugin.raw, indent=None if compact else 4))
            return