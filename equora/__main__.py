#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import shlex
import json
import shutil

CONFIG_PATH = os.path.expanduser("~/.config/quickshell/eqsh/Runtime/config.json")

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
    return ("qs -c eqsh" + " " + cmd)

def eqsh_run(cmd: str):
    run_detached(eqsh(cmd))

def ipc(*cmd: str):
    if not is_equora_running(): exit_because("Equora is not running")
    cmd = [f"\"{x}\"" if isinstance(x, str) else str(x) for x in cmd]
    eqsh_run("ipc " + "call " + " ".join(cmd))

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
        exists = [os.path.exists(os.path.expanduser("~/eqSh")), os.path.exists(os.path.expanduser("~/.config/quickshell/eqsh"))]
        if exists[0] or exists[1]:
            warn("Equora is already installed")
            if input("Do you want to overwrite it? (y/n) ").lower() == "y":
                if exists[0]:
                    shutil.rmtree(os.path.expanduser("~/eqSh"))
                if exists[1]:
                    shutil.rmtree(os.path.expanduser("~/.config/quickshell/eqsh"))
            else:
                exit_because("Installation aborted")
        # install equora
        os.mkdir(os.path.expanduser("~/eqSh"))
        os.mkdir(os.path.expanduser("~/.config/quickshell/"), exist_ok=True)
        # git clone
        os.system("git clone https://github.com/eq-desktop/eqSh ~/eqSh")
        # mv ~/eqSh/eqsh ~/.config/quickshell/
        shutil.move(os.path.expanduser("~/eqSh/eqsh"), os.path.expanduser("~/.config/quickshell/"))
        ok("Equora installed")
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

    # get json of .config/quickshell/eqsh/Runtime/runtime
    contents = {}
    with open(os.path.expanduser("~/.config/quickshell/eqsh/Runtime/runtime"), "r") as f:
        contents = json.load(f)

    proc_id = contents["processId"]

    return process_name_from_pid(proc_id) != None

def kill_equora():
    # get json of .config/quickshell/eqsh/Runtime/runtime
    contents = {}
    with open(os.path.expanduser("~/.config/quickshell/eqsh/Runtime/runtime"), "r") as f:
        contents = json.load(f)

    proc_id = contents["processId"]

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

def exit_because(msg: str, code: int=0):
    print(msg)
    sys.exit(code)

def main():
    parser = argparse.ArgumentParser(prog="equora", description="Equora Command Line Interface")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Run Equora")

    sub.add_parser("lock", help="Lock the screen")
    sub.add_parser("update", help="Look for updates")
    sub.add_parser("install", help="Install Equora")
    sub.add_parser("settings", help="Open settings")
    sub.add_parser("launchpad", help="Open launchpad")
    notch = sub.add_parser("new_notch_app", help="Create a new notch app")
    sub.add_parser("destroy_notch_app", help="Forcefully quits any running notch app")
    notch.add_argument("file", help="The QML file to open")
    notch.add_argument("title", help="The title of the app")
    notch.add_argument("timeout", help="The timeout in ms to destroy the app", type=int)
    notch.add_argument("start_delay", help="The start delay in ms", type=int)
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

    reset_cmd = sub.add_parser("reset", help="Reset (delete) a setting")
    reset_cmd.add_argument("setting", help="The setting to reset")
    reset_cmd.add_argument("--all", action="store_true", help="Reset all settings")

    args = parser.parse_args()

    if args.command == "run":
        if is_equora_running(): exit_because("Equora is already running", 0)
        eqsh_run("")
    elif args.command == "lock":
        ipc("eqlock", "lock")
    elif args.command == "install":
        install_equora()
    elif args.command == "settings":
        ipc("settings", "toggle")
    elif args.command == "update":
        exit_because("Not implemented yet")
    elif args.command == "launchpad":
        ipc("launchpad", "toggle")
    elif args.command == "new_notch_app":
        # code: string, timeout: int, start_delay: int
        file_contents = ""
        with open(args.file, "r") as f:
            file_contents = f.read()
        safe_contents = shlex.quote(file_contents)
        ipc("notch", "instance", safe_contents, str(args.timeout), str(args.start_delay))
    elif args.command == "destroy_notch_app":
        ipc("notch", "instanceHide")
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
