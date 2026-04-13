from ..runtime.aureli import is_aureli_running
from ..utils.system import *
import json

def ipc(*cmd: str):
    if not is_aureli_running(): exit_because("Aureli is not running")
    cmd_list = [f"\"{x}\"" if isinstance(x, str) else str(x) for x in cmd]
    eqsh_run("ipc " + "call " + " ".join(cmd_list))

def ipc_call(*cmd: str):
    if not is_aureli_running():
        exit_because("Aureli is not running")

    cmd_list = [f"\"{x}\"" if isinstance(x, str) else str(x) for x in cmd]
    full_cmd = eqsh("ipc call " + " ".join(cmd_list))

    output = run_capture(full_cmd)

    try:
        return json.loads(output)
    except:
        return output

def ipc_raw(*cmd: str):
    if not is_aureli_running(): exit_because("Aureli is not running")
    cmd_list = [f"\"{x}\"" if isinstance(x, str) else str(x) for x in cmd]
    eqsh_run_dev("ipc " + " ".join(cmd_list))
