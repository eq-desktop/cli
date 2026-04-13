import os

RUNTIME_PATH = os.path.expanduser("~/.config/aureli")
CONFIG_PATH = os.path.expanduser(RUNTIME_PATH + "/config.json")
PLUGIN_API_VERSION = "Elephant-1"
global location
global aureli_location
aureli_location = os.path.expanduser("~/.local/share/equora")
location = os.path.expanduser(aureli_location + "/eqsh")

BOLD = "\033[1m"
RESET = "\033[0m"
UNDERLINE = "\033[4m"