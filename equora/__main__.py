#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import shlex
import json
import shutil

CONFIG_PATH = os.path.expanduser("~/.local/share/equora/eqsh/runtime/config.json")

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
    print(f"Set {key_path} = {val}")

def get_setting(key_path: str):
    cfg = load_config()
    keys = key_path.split(".")
    ref = cfg
    for k in keys:
        if k not in ref:
            print(f"Setting {key_path} not found")
            return
        ref = ref[k]
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


def eqsh(cmd: str):
    return ("qs -p ~/.local/share/equora/eqsh" + " " + cmd)

def eqsh_run(cmd: str):
    run_detached(eqsh(cmd))

def eqsh_run_dev(cmd: str):
    run(eqsh(cmd))

def ipc(*cmd: str):
    if not is_equora_running(): exit_because("Equora is not running")
    cmd = [f"\"{x}\"" if isinstance(x, str) else str(x) for x in cmd]
    eqsh_run("ipc " + "call " + " ".join(cmd))

def ipc_raw(*cmd: str):
    if not is_equora_running(): exit_because("Equora is not running")
    cmd = [f"\"{x}\"" if isinstance(x, str) else str(x) for x in cmd]
    eqsh_run_dev("ipc " + " ".join(cmd))

def ok(msg: str):
    print("\033[92m\033[38;5;46mOK: \033[0m" + msg)

def warn(msg: str):
    print("\033[93m\033[38;5;208mWARNING: \033[0m" + msg)

def err(msg: str):
    print("\033[91m\033[38;5;196mERROR: \033[0m" + msg)

def install_equora():
    ok("Installing Equora...")
    try:
        # check if ~/eqSh or ~/.config/quickshell/eqsh exists
        if os.path.exists(os.path.expanduser("~/.local/share/equora")):
            warn("Equora is already installed")
            if input("Do you want to overwrite it? (y/n) ").lower() == "y":
                shutil.rmtree(os.path.expanduser("~/.local/share/equora"))
            else:
                exit_because("Installation aborted")
        # install equora
        os.mkdir(os.path.expanduser("~/eqSh"))
        # git clone
        os.system("git clone https://github.com/eq-desktop/eqSh ~/eqSh")
        os.system("git submodule update --init --recursive")
        # mv ~/eqSh to ~/.local/share/equora
        if input("Do you want to also install wallpapers? (y/n) ").lower() == "y":
            os.system("git clone https://github.com/eq-desktop/wallpapers ~/eqSh/wallpapers")
            print("Wallpapers installed")
        shutil.move(os.path.expanduser("~/eqSh"), os.path.expanduser("~/.local/share/equora/"))
        ok("Equora installed")
        print("Post-installation steps:")
        print("- Install Quickshell https://quickshell.org")
        print("- Run `equora run` to start Equora")
    except Exception as e:
        err(f"Failed to install Equora: {e}")

def process_name_from_pid(pid: int) -> str | None:
    try:
        with open(f"/proc/{pid}/comm", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None  # process does not exist

def is_equora_running() -> bool:
    """Check if Equora is running or not."""

    # get json of .local/share/equora/eqsh/runtime/runtime
    contents = {}
    # if file doesnt exist
    if not os.path.exists(os.path.expanduser("~/.local/share/equora/eqsh/runtime/runtime")):
        return False
    with open(os.path.expanduser("~/.local/share/equora/eqsh/runtime/runtime"), "r") as f:
        contents = json.load(f)

    proc_id = contents["processId"]

    return process_name_from_pid(proc_id) != None

def kill_equora():
    # get json of .local/share/equora/eqsh/runtime/runtime
    contents = {}
    # if file doesnt exist
    if not os.path.exists(os.path.expanduser("~/.local/share/equora/eqsh/runtime/runtime")):
        exit_because("Equora is not running")
    with open(os.path.expanduser("~/.local/share/equora/eqsh/runtime/runtime"), "r") as f:
        contents = json.load(f)

    proc_id = contents["processId"]

    if not is_equora_running():
        exit_because("Equora is not running")

    os.kill(int(proc_id), 9)

def run_detached(cmd: str):
    """Run a command detached from this process."""
    subprocess.Popen(
        args=cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

def run(cmd: str, cwd: str=None):
    subprocess.run(
        args=cmd,
        shell=True,
        cwd=cwd
    )

def exit_because(msg: str, code: int=0):
    print(msg)
    sys.exit(code)

def main():
    parser = argparse.ArgumentParser(prog="equora", description="Equora Command Line Interface")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Run Equora")
    run_cmd.add_argument("--dev", action="store_true", help="Run Equora in development mode")

    sub.add_parser("lock", help="Lock the screen")
    sub.add_parser("update", help="Look for updates")
    sub.add_parser("install", help="Install Equora")
    sub.add_parser("settings", help="Open settings")
    sub.add_parser("launchpad", help="Open launchpad")
    notch = sub.add_parser("new_notch_app", help="Create a new notch app")
    sub.add_parser("destroy_notch_app", help="Forcefully quits any running notch app")
    notch.add_argument("file", help="The QML file to open")
    notch.add_argument("title", help="The title of the app")
    sub.add_parser("notification_center", help="Open notification center")
    dialog = sub.add_parser("dialog", help="Open a dialog")
    dialog.add_argument("appName", help="The name of the app")
    dialog.add_argument("iconPath", help="The path to the icon")
    dialog.add_argument("title", help="The title of the dialog")
    dialog.add_argument("description", help="The description of the dialog")
    dialog.add_argument("accept", help="The text of the accept button")
    dialog.add_argument("decline", help="The text of the decline button")
    dialog.add_argument("commandAccept", help="The command to run when the accept button is clicked")
    dialog.add_argument("commandDecline", help="The command to run when the decline button is clicked")
    dialog.add_argument("customStyle", help="The custom style of the dialog")
    sub.add_parser("quit", help="Quit Equora")
    sub.add_parser("restart", help="Restart Equora")
    set_cmd = sub.add_parser("set", help="Set a setting")
    set_cmd.add_argument("setting", help="The setting to set (e.g. bar.height)")
    set_cmd.add_argument("value", help="The value to set the setting to")

    get_cmd = sub.add_parser("get", help="Get a setting")
    get_cmd.add_argument("setting", help="The setting to get (e.g. bar.height)")

    ipc_cmd = sub.add_parser("ipc", help="Call an IPC method")
    ipc_cmd.add_argument("method", help="The method to call")
    ipc_cmd.add_argument("args", nargs=argparse.REMAINDER, help="The arguments to pass to the method")

    sub.add_parser("funcs", help="Show all available IPC methods")

    reset_cmd = sub.add_parser("reset", help="Reset (delete) a setting")
    reset_cmd.add_argument("setting", help="The setting to reset")
    reset_cmd.add_argument("--all", action="store_true", help="Reset all settings")

    args = parser.parse_args()

    if args.command == "run":
        if is_equora_running(): exit_because("Equora is already running", 0)
        if args.dev:
            eqsh_run_dev("")
        else:
            eqsh_run("")
    elif args.command == "lock":
        ipc("eqlock", "lock")
    elif args.command == "install":
        install_equora()
    elif args.command == "settings":
        ipc("settings", "toggle")
    elif args.command == "update":
        run("pip install --upgrade git+https://github.com/eq-desktop/cli.git")
        run("git pull ", cwd=os.path.expanduser("~/.local/share/equora"))
    elif args.command == "launchpad":
        ipc("launchpad", "toggle")
    elif args.command == "ipc":
        ipc(args.method, *args.args)
    elif args.command == "funcs":
        ipc_raw("show")
    elif args.command == "new_notch_app":
        # code: string, timeout: int, start_delay: int
        file_contents = ""
        with open(args.file, "r") as f:
            file_contents = f.read()
        safe_contents = file_contents.replace("\\", "\\\\").replace('"', '\\"')
        ipc("notch", "instance", safe_contents)
    elif args.command == "destroy_notch_app":
        ipc("notch", "closeInstance")
    elif args.command == "dialog":
        # appName: string, icon_path: string, title: string, description: string, accept: string, decline: string, commandAccept: string, commandDecline: string, customStyle: string
        ipc("systemDialogs", "newDialog", args.appName, args.iconPath, args.title, args.description, args.accept, args.decline, args.commandAccept, args.commandDecline, args.customStyle)
    elif args.command == "notification_center":
        ipc("notificationCenter", "toggle")
    elif args.command == "quit":
        kill_equora()
    elif args.command == "restart":
        kill_equora()
        eqsh_run("")
    elif args.command == "set":
        set_setting(args.setting, args.value)
    elif args.command == "get":
        get_setting(args.setting)
    elif args.command == "reset":
        if args.all:
            reset_config()
            print("Reset all settings (restart required)")
        else:
            reset_setting(args.setting)
            print(f"Reset {args.setting} (restart required)")
if __name__ == "__main__":
    main()
