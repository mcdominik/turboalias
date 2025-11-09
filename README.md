# 🚀 Turboalias

**Cross-workstation alias manager for bash and zsh**

Turboalias is a simple, powerful tool to manage your shell aliases across multiple workstations. Store your aliases in a clean JSON config, organize them by category, and sync them easily.

---

## ✨ Features

- 🎯 **Simple CLI** - Easy commands to add, remove, and list aliases
- ⚡ **Auto-Reload** - Changes apply instantly without manual shell reload
- 📁 **Category Support** - Organize aliases by category (git, docker, navigation, etc.)
- 📥 **Import Existing** - Import your current shell aliases
- 🔄 **Git Sync** - Sync aliases across machines using Git
- 🐚 **Multi-shell** - Works with both bash and zsh
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

### Via pip (recommended)

````bash
pip install turboalias

### From source

```bash
git clone https://github.com/mcdominik/turboalias.git
cd turboalias
pip install -e .
````

---

## 🚀 Quick Start

**1. Initialize turboalias**

```bash
turboalias init
```

**2. Add some aliases**

```bash
turboalias add ll 'ls -lah'
turboalias add gst 'git status' --category git
turboalias add gco 'git checkout' --category git
turboalias add dps 'docker ps' --category docker
turboalias add hg 'history | grep'

```

**3. Use your aliases!**

```bash
ll
gst
dps
hg npm
```

---

## 📖 Usage

### Initialize turboalias

```bash
turboalias init
```

### Add an alias

```bash
turboalias add <name> <command> [--category <category>]
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

### Clear all aliases

```bash
turboalias clear
```

Removes all turboalias-managed aliases (with confirmation)

### Edit config directly

```bash
turboalias edit
```

Opens the config file in your `$EDITOR` (defaults to nano)

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
| **Portable**               | Easy to backup and sync (just copy `~/.config/turboalias/`)   |
| **Safe**                   | Doesn't modify your existing aliases, creates a separate file |
| **Transparent**            | Generated `aliases.sh` is human-readable                      |
| **Cross-platform**         | Works seamlessly on macOS and Linux                           |

---

## 🗺️ Roadmap

- [ ] Git sync support for automatic syncing across machines
- [ ] Alias search functionality
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
