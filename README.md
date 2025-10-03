# Equora CLI

<p align="center">
  <i>“Your desktop, your rules. Full control at your fingertips.”</i>
</p>

---

## 📌 Overview

**Equora CLI** is the command-line interface for **Equora** — the next-generation Linux desktop shell and environment.  
It allows you to **launch, control, and configure** every aspect of Equora, from panels and launchers to dialogs, notifications, and Notch apps.

With Equora CLI, you can:  

- Start, restart, or quit the Equora shell.  
- Lock your screen or open the notification center.  
- Configure settings dynamically via JSON-backed configuration.  
- Create and manage Notch apps (dynamic popups and mini-apps).  
- Launch dialogs with fully customizable content and behavior.  

---

## ⚡ Installation

Make sure you have **Python 3** installed. Install it using pip:

```bash
git clone https://github.com/eq-desktop/cli.git
cd cli/
./install.sh
````

---

## 🚀 Usage

```bash
equora <command> [arguments]
```

### Available Commands

| Command                                                                                                               | Description                                 |
| --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `run`                                                                                                                 | Start Equora                                |
| `lock`                                                                                                                | Lock the screen                             |
| `settings`                                                                                                            | Open settings panel                         |
| `update`                                                                                                              | Check for updates (not yet implemented)     |
| `launchpad`                                                                                                           | Open the Launchpad                          |
| `new_notch_app <file> <title>`                                                                | Create a new Notch app                      |
| `destroy_notch_app`                                                                                                   | Forcefully quit a Notch app                 |
| `dialog <appName> <iconPath> <title> <description> <accept> <decline> <commandAccept> <commandDecline> <customStyle>` | Open a customizable dialog                  |
| `notification_center`                                                                                                 | Open the notification center                |
| `quit`                                                                                                                | Quit Equora                                 |
| `restart`                                                                                                             | Restart Equora                              |
| `set <setting> <value>`                                                                                               | Set a specific setting (e.g., `bar.height`) |
| `get <setting>`                                                                                                       | Get the value of a setting                  |
| `reset <setting> [--all]`                                                                                             | Reset a setting or all settings             |

---

## 🛠 Configuration

Equora CLI reads and writes settings directly to Equora Shell:

* **Set values dynamically**:

  ```bash
  equora set bar.height 22
  ```
* **Get current values**:

  ```bash
  equora get bar.height
  ```
* **Reset a specific setting or all settings**:

  ```bash
  equora reset bar.height
  equora reset --all
  ```

---

## 🔧 Development

Equora CLI is built in **Python 3** and designed to integrate seamlessly with the Equora shell.
Feel free to fork, contribute, or extend the CLI to suit your needs.

---

## ⚖️ License

Released under the **MIT License**.
You are free to use, modify, and distribute this software as you wish.