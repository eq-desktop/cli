import sys
import os
import json
import shutil
from ..config import *
from ..utils.system import *
from ..plugins.manager import install_plugin

def versions():
    print("\033[96mInfo\033[0m\n")

    # --- Kavo ---
    print("\033[94mKavo Format\033[0m")
    print(f"  Version : \033[96m{PLUGIN_API_VERSION}\033[0m")
    print()

    # --- CLI ---
    print("\033[94mAureli\033[0m")
    print(f"  CLI Version   : \033[96m0.1.0\033[0m")
    print(f"  Install Path  : \033[96m{os.path.expanduser(aureli_location)}\033[0m")
    print(f"  Runtime Path  : \033[96m{os.path.expanduser(RUNTIME_PATH)}\033[0m")
    print()

    # --- Python ---
    print("\033[94mRuntime\033[0m")
    print(f"  Python        : \033[96m{sys.version.split()[0]}\033[0m")
    print()


def msg_help(cmd: str|None=None):
    print(f"{BOLD}Communicate with Aureli.{RESET}\n")
    if cmd:
        print(f"{BOLD}{UNDERLINE}Usage:{RESET} msg {cmd} <method> [args...]\n")
        print(f"{BOLD}{UNDERLINE}Commands:{RESET}")
        for category, methods in collect_funcs().items():
            if category.lower() == cmd.lower():
                for method in methods:
                    print(f"  {BOLD}{method['name']}{RESET}({', '.join(method['args'])}) -> {method['return']}")
    else:
        print(f"{BOLD}{UNDERLINE}Usage:{RESET} msg <target> <method> [args...]\n")
        print(f"{BOLD}{UNDERLINE}Commands:{RESET}")
        for category, methods in collect_funcs().items():
            print(f"  {BOLD}{category}{RESET}{(20 - len(category)) * ' '}{", ".join([x['name'] for x in methods])}")

def msg_table():
    for category, methods in collect_funcs().items():
        for method in methods:
            print(f"\033[1m{category} | {method['name']}({', '.join([x.split(": ")[0] for x in method['args']])})\033[0m")


def install_wallpapers():
    global aureli_location
    ok("Downloading Wallpapers...")
    try:
        # check exist
        if os.path.exists(os.path.expanduser(aureli_location + "/wallpapers")):
            warn("Wallpapers are already installed")
            if input("Do you want to overwrite them? (y/n) ").lower() == "y":
                shutil.rmtree(os.path.expanduser(aureli_location + "/wallpapers"))
            else:
                exit_because("Download aborted")
        os.system(f"git clone https://github.com/eq-desktop/wallpapers {aureli_location}/wallpapers")
        ok("Wallpapers installed")
    except Exception as e:
        err(f"Failed to install Wallpapers: {e}")

def install_aureli():
    global aureli_location
    ok("Installing Aureli...")
    try:
        # check exist
        if os.path.exists(os.path.expanduser(aureli_location)):
            warn("Aureli is already installed")
            if input("Do you want to overwrite it? (y/n) ").lower() == "y":
                shutil.rmtree(os.path.expanduser(aureli_location))
            else:
                exit_because("Installation aborted")
        # install aureli
        os.mkdir(os.path.expanduser("~/eqsh"))
        # git clone
        os.system("git clone https://github.com/eq-desktop/eqsh ~/eqsh")
        os.system("git submodule update --init --recursive")
        # mv ~/eqsh to ~/.local/share/equora
        if input("Do you want to also install wallpapers (Large files)? (y/n) ").lower() == "y":
            os.system("git clone https://github.com/eq-desktop/wallpapers ~/eqsh/wallpapers")
            print("Wallpapers installed")
        shutil.move(os.path.expanduser("~/eqsh"), os.path.expanduser(aureli_location))
        # mkdir .config/aureli/
        # mkdir .config/aureli/plugins
        os.mkdir(os.path.expanduser("~/.config/aureli"))
        os.mkdir(os.path.expanduser("~/.config/aureli/plugins"))
        # install plugins
        install_plugin("https://github.com/eq-desktop/Aureli-Base-Plugin")
        ok("Aureli installed")
        print("Post-installation steps:")
        print("- Install Quickshell https://quickshell.org")
        print("- Run `au run` to start Aureli")
    except Exception as e:
        err(f"Failed to install Aureli: {e}")

def is_aureli_running() -> bool:
    """Check if Aureli is running or not."""

    # get json of .local/share/equora/eqsh/runtime/runtime
    contents = {}
    # if file doesnt exist
    if not os.path.exists(os.path.expanduser(RUNTIME_PATH + "/runtime")):
        return False
    with open(os.path.expanduser(RUNTIME_PATH + "/runtime"), "r") as f:
        contents = json.load(f)

    proc_id = contents["processId"]

    return process_name_from_pid(proc_id) != None

def kill_aureli():
    # get json of .local/share/equora/eqsh/runtime/runtime
    contents = {}
    # if file doesnt exist
    if not os.path.exists(os.path.expanduser(RUNTIME_PATH + "/runtime")):
        exit_because("Aureli is not running")
    with open(os.path.expanduser(RUNTIME_PATH + "/runtime"), "r") as f:
        contents = json.load(f)

    proc_id = contents["processId"]

    if not is_aureli_running():
        exit_because("Aureli is not running")

    os.kill(int(proc_id), 9)