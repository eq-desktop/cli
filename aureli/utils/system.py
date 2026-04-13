import subprocess
import sys
from ..config import location

def eqsh(cmd: str):
    global location
    return ("qs -p " + location + " " + cmd)

def eqsh_run(cmd: str):
    run_detached(eqsh(cmd))

def eqsh_run_dev(cmd: str):
    global location
    run(eqsh(cmd))

def collect_funcs() -> dict[str, dict]:
    """Collect all available message functions."""
    res = run_capture("qs -p " + location + " ipc show").splitlines()
    categories = {}
    for line in res:
        if line.startswith("  "):
            # This is a method
            method = line.strip()
            # remove function prefix
            method = method[9:]
            # get name before (
            method_name = method.split("(")[0].strip()
            # get arguments name: type, ...
            method_args = [x.strip() for x in method.split("(")[1].split(")")[0].split(",")]
            # get return type
            method_return = method.split(")")[1].strip().split(":")[-1].strip()
            categories[category].append({
                "name": method_name,
                "args": method_args,
                "return": method_return
            })
        elif line.startswith("target"):
            # This is a category
            category = line[6:].strip()
            categories[category] = []
    return categories

def ok(msg: str):
    print("\033[92m\033[38;5;46mOK: \033[0m" + msg)

def warn(msg: str):
    print("\033[93m\033[38;5;208mWARNING: \033[0m" + msg)

def err(msg: str):
    print("\033[91m\033[38;5;196mERROR: \033[0m" + msg)

def run_detached(cmd: str):
    """Run a command detached from this process."""
    subprocess.Popen(
        args=cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

def run_capture(cmd: str, cwd: str | None = None) -> str:
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout.strip()

def run(cmd: str, cwd: str|None=None):
    subprocess.run(
        args=cmd,
        shell=True,
        cwd=cwd
    )

def log():
    print("\033[92mVersion: \033[0m")
    run("qs --version")
    print("\033[91mLog:\033[0m")
    run(eqsh("log"))

def exit_because(msg: str, code: int=0):
    print(msg)
    sys.exit(code)

def process_name_from_pid(pid: int) -> str | None:
    try:
        with open(f"/proc/{pid}/comm", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None  # process does not exist
