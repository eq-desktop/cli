#!/usr/bin/env python3
import argparse
import os
from .config import *
from .plugins.manager import *
from .utils.system import *
from .utils.config import *
from .runtime.aureli import *
from .runtime.ipc import *

if os.environ.get("QT_LOGGING_RULES", False):
    os.environ["QT_LOGGING_RULES"] += ";qml.debug=true"
else:
    os.environ["QT_LOGGING_RULES"] = "qml.debug=true"


command_map = {
    "v": "version",
    "q": "quit",
    "p": "plugin",
    "i": "ipc",
    "m": "msg",
    "s": "set",
    "g": "get",
    "r": "run",
}

class CustomHelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Bold section headers
        if heading.lower().startswith("positional"):
            heading = "Commands"
        heading = f"{BOLD}{UNDERLINE}{heading.capitalize()}{RESET}"
        super().start_section(heading)

    def add_usage(self, usage, actions, groups, prefix=None):
        # Custom "Usage" header
        if prefix is None:
            prefix = f"{BOLD}{UNDERLINE}Usage:{RESET} "
        return super().add_usage(usage, actions, groups, prefix)

    def add_arguments(self, actions):
        seen = set()
        lines = []

        max_len = 0

        # build unique action list
        for action in actions:
            name = self._format_action_invocation(action)

            # skip duplicates
            key = tuple(action.option_strings)
            if key in seen:
                continue
            seen.add(key)

            max_len = max(max_len, len(name))

        for action in actions:
            key = tuple(action.option_strings)
            if key not in seen:
                continue
            seen.remove(key)

            name = self._format_action_invocation(action)
            help_text = action.help or ""

            padding = " " * (max_len - len(name) + 2)
            lines = f"  {name}{padding}{help_text}\n"

            self._add_item(lambda l=lines: l, [])
    
    def _format_action(self, action):
        # skip duplicate help entries or empty ones
        if not action.option_strings and not action.metavar:
            return ""

        action_header = self._format_action_invocation(action)
        help_text = action.help or ""

        pad = 30
        spacing = " " * max(2, pad - len(action_header))

        return f"  {action_header}{spacing}{help_text}\n"

    def _format_actions_usage(self, actions, groups):
        for a in actions:
            if isinstance(a, argparse._SubParsersAction):
                return "<command>"

        return super()._format_actions_usage(actions, groups)

    def _format_action_invocation(self, action):
        if isinstance(action, argparse._SubParsersAction):
            # collect subcommands properly
            entries = []

            for choice_action in action._choices_actions:
                name = choice_action.dest
                help_text = choice_action.help or ""
                
                # skip short aliases like "r", "p", etc.
                if len(name) == 1:
                    continue

                entries.append((name, help_text))

            # alignment
            max_len = max(len(name) for name, _ in entries)

            result = [
                f"{BOLD}{name}{RESET}{' ' * (max_len - len(name) + 2)}{help_text}"
                for name, help_text in entries
            ]

            return "\n  ".join(result)

        return super()._format_action_invocation(action)

class AureliArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter_class", CustomHelpFormatter)
        super().__init__(*args, **kwargs)

def main():
    global location
    global aureli_location
    parser = AureliArgumentParser(prog="aureli")
    sub = parser.add_subparsers(dest="command", required=True)
    parser.add_argument("-l", "--location", default=location, help="Location of Aureli")
    parser.add_argument("-L", "--location-aureli", default=aureli_location, help="Location to install Aureli to")

    run_cmd = sub.add_parser("run", aliases=["r"], help="Run Aureli")
    run_cmd.add_argument("--dev", action="store_true", help="Run Aureli in development mode")

    plugin = sub.add_parser("plugin", aliases=["p"], help="Manage plugins")
    plugin_sub = plugin.add_subparsers(dest="plugin_command", required=True)

    plugin_install = plugin_sub.add_parser("install", aliases=["i"], help="Install a plugin")
    plugin_install.add_argument("url", help="The URL of the plugin")

    plugin_uninstall = plugin_sub.add_parser("uninstall", aliases=["rm"], help="Uninstall a plugin")
    plugin_uninstall.add_argument("id", help="The name of the plugin")

    plugin_list = plugin_sub.add_parser("list", aliases=["l"], help="List installed plugins")

    plugin_meta = plugin_sub.add_parser("meta", aliases=["m"], help="Get plugin meta")
    plugin_meta.add_argument("url", help="The URL of the plugin")

    plugin_update = plugin_sub.add_parser("update", aliases=["u"], help="Update a plugin")
    plugin_update.add_argument("id", help="The name of the plugin")

    plugin_new = plugin_sub.add_parser("new", aliases=["n"], help="Create a new plugin")

    plugin_load = plugin_sub.add_parser("load", help="Load a plugin from a directory")
    plugin_load.add_argument("dir", help="The directory of the plugin")

    sub.add_parser("log", help="Shows the log of the current running instance")

    plugin_compile = plugin_sub.add_parser("compile", aliases=["c"], help="Compile a plugin")
    plugin_compile.add_argument("id", help="The name of the plugin")
    plugin_compile.add_argument("--compact", action="store_true", help="Don't Indent the plugin")

    sub.add_parser("lock", help="Lock the screen")
    sub.add_parser("update", help="Look for updates")
    sub.add_parser("version", aliases=["v"], help="Show Aureli version")
    sub.add_parser("install", help="Install Aureli")
    sub.add_parser("install-wallpapers", help="Install Aureli's default wallpapers")
    sub.add_parser("settings", help="Open settings")
    sub.add_parser("launchpad", help="Open launchpad")
    sub.add_parser("destroy-notch-app", help="Forcefully quits any running notch app")
    notch = sub.add_parser("new-notch-app", help="Create a new notch app")
    notch.add_argument("file", help="The QML file to open")
    notch.add_argument("title", help="The title of the app")
    sub.add_parser("notification-center", help="Open notification center")
    dialog = sub.add_parser("dialog", help="Open a dialog")
    dialog.add_argument("appName", help="The name of the app")
    dialog.add_argument("iconPath", help="The path to the icon")
    dialog.add_argument("title", help="The title of the dialog")
    dialog.add_argument("description", help="The description of the dialog")
    dialog.add_argument("accept", help="The text of the accept button")
    dialog.add_argument("decline", help="The text of the decline button")
    dialog.add_argument("command-accept", help="The command to run when the accept button is clicked")
    dialog.add_argument("command-decline", help="The command to run when the decline button is clicked")
    dialog.add_argument("custom-style", help="The custom style of the dialog")
    sub.add_parser("quit", aliases=["q"], help="Quit Aureli")
    sub.add_parser("restart", help="Restart Aureli")
    set_cmd = sub.add_parser("set", aliases=["s"], help="Set a setting")
    set_cmd.add_argument("setting", help="The setting to set (e.g. bar.height)")
    set_cmd.add_argument("value", help="The value to set the setting to")

    get_cmd = sub.add_parser("get", aliases=["g"], help="Get a setting")
    get_cmd.add_argument("setting", help="The setting to get (e.g. bar.height)")

    ipc_cmd = sub.add_parser("ipc", aliases=["i"], help="Call an IPC method")
    ipc_cmd.add_argument("method", help="The method to call")
    ipc_cmd.add_argument("args", nargs=argparse.REMAINDER, help="The arguments to pass to the method")

    msg_cmd = sub.add_parser("msg", aliases=["m"], help="Communicate with Aureli")
    msg_cmd.add_argument("method", nargs=argparse.REMAINDER, default=None, help="The method to send")
    sub.add_parser("msg-table", help="Table of msg commands")

    sub.add_parser("funcs", help="Show all available IPC methods")

    reset_cmd = sub.add_parser("reset", help="Reset (delete) a setting")
    reset_cmd.add_argument("setting", help="The setting to reset")
    reset_cmd.add_argument("--all", action="store_true", help="Reset all settings")

    args = parser.parse_args()

    location = args.location
    aureli_location = args.location_aureli

    if args.command in command_map:
        args.command = command_map[args.command]

    if args.command == "plugin":
        if args.plugin_command == "install":
            install_plugin(args.url)
        elif args.plugin_command == "uninstall":
            uninstall_plugin(args.id)
        elif args.plugin_command == "update":
            update_plugin(args.id)
        elif args.plugin_command == "new":
            new_plugin()
        elif args.plugin_command == "load":
            load_plugin(args.dir)
        elif args.plugin_command == "meta":
            meta_plugin(args.url)
        elif args.plugin_command == "list":
            list_plugins()
        elif args.plugin_command == "compile":
            compile_plugin(args.id, args.compact)
    elif args.command == "version":
        versions()
    elif args.command == "run":
        if is_aureli_running(): exit_because("Aureli is already running", 0)
        if args.dev:
            eqsh_run_dev("")
        else:
            eqsh_run("")
    elif args.command == "lock":
        ipc("lock", "lock")
    elif args.command == "install":
        install_aureli()
    elif args.command == "install-wallpapers":
        install_wallpapers()
    elif args.command == "settings":
        ipc("settings", "toggle")
    elif args.command == "log":
        log()
    elif args.command == "update":
        run("git pull ", cwd=os.path.expanduser(aureli_location))
    elif args.command == "launchpad":
        ipc("launchpad", "toggle")
    elif args.command == "ipc":
        answ = ipc_call(args.method, *args.args)
        if answ != "": print("Returned:", answ)
    elif args.command == "msg":
        if args.method == []:
            msg_help()
        elif len(args.method) == 1:
            msg_help(args.method[0])
        else:
            print(args.method[0], *args.method[1:])
            ipc(args.method[0], *args.method[1:])
    elif args.command == "msg-table":
        msg_table()
    elif args.command == "funcs":
        ipc_raw("show")
    elif args.command == "new-notch-app":
        # code: string, timeout: int, start_delay: int
        file_contents = ""
        with open(args.file, "r") as f:
            file_contents = f.read()
        safe_contents = file_contents.replace("\\", "\\\\").replace('"', '\\"')
        ipc("notch", "instance", safe_contents)
    elif args.command == "destroy-notch-app":
        ipc("notch", "closeInstance")
    elif args.command == "dialog":
        # appName: string, icon_path: string, title: string, description: string, accept: string, decline: string, commandAccept: string, commandDecline: string, customStyle: string
        ipc("systemDialogs", "newDialog", args.appName, args.iconPath, args.title, args.description, args.accept, args.decline, args.command_accept, args.command_decline, args.custom_style)
    elif args.command == "notification-center":
        ipc("notificationCenter", "toggle")
    elif args.command == "quit":
        kill_aureli()
    elif args.command == "restart":
        kill_aureli()
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
