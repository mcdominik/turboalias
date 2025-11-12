[![PyPI version](https://badge.fury.io/py/turboalias.svg)](https://badge.fury.io/py/turboalias)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20WSL-lightgrey.svg)](https://github.com/mcdominik/turboalias)

# 🚀 Turboalias

**Cross-workstation alias manager for bash and zsh**

Turboalias is a simple, powerful tool to manage your shell aliases across multiple workstations. Store your aliases in a clean JSON config, organize them by category, and sync them easily.

---

## ✨ Features

- 🐚 **Multi-shell** - Works with both bash and zsh
- ⚡ **Auto-Reload** - Changes apply instantly without manual shell reload
- 🔄 **Auto-Sync** - Sync aliases across machines using Git (optional)
- 🎯 **Simple CLI** - Easy commands to add, remove, and list aliases
- 📁 **Category Support** - Organize aliases by category (git, docker, navigation, etc.)
- 📥 **Quick Migration** - Import your current shell aliases
- 📝 **JSON Config** - Clean, editable configuration file
- 🎨 **Clean Output** - Aliases organized by category in your shell

---

## 🖥️ Supported Platforms

| Platform    | Shells          | Status             |
| ----------- | --------------- | ------------------ |
| **macOS**   | bash, zsh       | ✅ Fully supported |
| **Linux**   | bash, zsh       | ✅ Fully supported |
| **Windows** | WSL (bash, zsh) | ✅ Via WSL         |

---

## 📦 Installation

### macOS (recommended)

Using Homebrew:

```bash
brew tap mcdominik/turboalias
brew install turboalias
```

### Linux, macOS & Windows (WSL)

Using pipx (recommended for Python CLI tools):

```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

pipx install turboalias
```

### Alternative 

If you prefer using pip:

```bash
pip install turboalias
```

> **Note:** Modern Linux distributions discourage system-wide `pip install` without virtual environments (PEP 668). `pipx` is the recommended way to install Python CLI applications as it automatically manages isolated environments.

### From source

```bash
git clone https://github.com/mcdominik/turboalias.git
cd turboalias
pip install -e .
```

---

## 🚀 Quick Start

**1. Initialize turboalias**

```bash
turboalias init
```

**2. Add some aliases**

```bash
turboalias add dps 'docker ps' --category docker
```

⚡ **Changes apply instantly!** No need to reload your shell after adding aliases.

**3. Use your aliases!**

```bash
dps
```

---

## 📖 Usage

### Add an alias

```bash
turboalias add <name> '<command>' [-c <category>]
```

**Examples:**

```bash
turboalias add ll 'ls -lah'
turboalias add gst 'git status' -c git
```

### Remove an alias

```bash
turboalias remove <name>
```

**Example:**

```bash
turboalias remove dps
```

⚡ **Changes apply instantly!** No need to reload your shell after removing aliases.

### List aliases

```bash
# List all aliases
turboalias list

# List aliases in a category
turboalias list --category git
```

### List categories

```bash
turboalias categories
```

### Import existing aliases

```bash
turboalias import
```

Scans your current shell for aliases and imports them into turboalias

### Edit config directly

```bash
turboalias edit
```

Opens the config file in your `$EDITOR` (defaults to nano)

### Clear all aliases

```bash
turboalias clear
```

Removes all turboalias-managed aliases (with confirmation)

### Remove entire config

```bash
turboalias nuke
```

Removes turboalias<->shell bridge, config, and all turboalias-managed aliases (with confirmation)

---

## 🔄 Git Sync

Sync your aliases across multiple workstations using Git.

### Setup sync on your first machine

```bash
# Initialize git sync with a remote repository
turboalias sync init --remote https://github.com/<username>/my-turboalias-config.git

⚡ **Share your setup!** You can also use one shared by the community..

# Check sync status
turboalias sync status

# Push your aliases to the remote
turboalias sync push
```

### Restore aliases on a new machine

```bash
# Clone your aliases configuration
turboalias sync clone https://github.com/yourusername/my-aliases.git

# That's it! All your aliases are now available
# Reload your shell to use them
```

### Sync commands

```bash
# Initialize git sync
turboalias sync init [--remote <url>] [--branch <name>]

# Clone existing config
turboalias sync clone <url> [--branch <name>]

# Push local changes
turboalias sync push

# Pull remote changes
turboalias sync pull

# Check sync status
turboalias sync status

# Enable auto-sync (commits & pushes after every change)
turboalias sync auto on

# Disable auto-sync
turboalias sync auto off
```

### How it works

- Git repository is created in `~/.config/turboalias/`
- Only `aliases.json` is synced (your aliases data)
- `aliases.sh` (shell script) is generated locally on each machine
- `sync_config.json` (git settings) stays local
- Auto-sync runs in background without blocking your commands
- All operations work offline-first, sync is completely optional

### Example workflow

```bash
# Machine 1: Set up and push
turboalias init
turboalias add ll 'ls -lah'
turboalias add gst 'git status' -c git
turboalias sync init --remote https://github.com/mcdominik/my-turboalias-config.git
turboalias sync push

# Machine 2: Clone and use
turboalias sync clone https://github.com/mcdominik/my-turboalias-config.git
# All aliases restored automatically!

# Optional: Enable auto-sync for convenience
turboalias sync auto on
# Now every add/remove/clear will auto-sync in background
```

---

## ⚙️ Configuration

Turboalias stores its configuration in `~/.config/turboalias/`:

| File           | Purpose                                        |
| -------------- | ---------------------------------------------- |
| `aliases.json` | Your aliases and categories                    |
| `aliases.sh`   | Generated shell script (sourced by your shell) |

### Config file format

```json
{
  "aliases": {
    "ll": {
      "command": "ls -lah",
      "category": null
    },
    "gst": {
      "command": "git status",
      "category": "git"
    }
  },
  "categories": {
    "git": ["gst", "gco", "glog"]
  }
}
```

You can edit this file directly with `turboalias edit` or manually.

---

## 💡 Why Turboalias?

| Benefit                    | Description                                                   |
| -------------------------- | ------------------------------------------------------------- |
| **Instant Updates**        | Changes apply immediately without manual shell reload         |
| **Centralized Management** | All your aliases in one place                                 |
| **Organized**              | Categories keep things tidy                                   |
| **Portable**               | Sync via Git across all your machines                         |
| **Safe**                   | Doesn't modify your existing aliases, creates a separate file |
| **Transparent**            | Generated `aliases.sh` is human-readable                      |
| **Cross-platform**         | Works seamlessly on macOS and Linux                           |
| **Fast**                   | Auto-sync runs in background, never blocks your workflow      |

---

## 🗺️ Roadmap

- [x] Git sync support for automatic syncing across machines
- [ ] Shell completion support
- [ ] Export/import to different formats
- [ ] Alias templates and snippets

---

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

---

## 📄 License

MIT License - see LICENSE file for details

---

## 👤 Author

**Dominik** - [@mcdominik](https://github.com/mcdominik)

---

<div align="center">
Made with ❤️ for unix enthusiasts
</div>
