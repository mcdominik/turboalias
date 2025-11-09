"""
CLI interface for turboalias
"""
import argparse
import os
import subprocess
import sys
from typing import Optional

from .config import Config
from .shell import ShellIntegration
from .sync import GitSync


class TurboaliasCLI:
    """Main CLI handler"""

    def __init__(self):
        self.config = Config()
        self.shell = ShellIntegration(self.config)

    def init(self):
        """Initialize turboalias"""
        print("🔧 Initializing turboalias...")

        shells = self.shell.detect_shells()

        if not shells:
            print("❌ No supported shell found (.bashrc or .zshrc)")
            print("   Please create ~/.bashrc or ~/.zshrc first")
            return 1

        added = []
        for shell in shells:
            if self.shell.add_source_line(shell):
                added.append(shell)
                rc_file = self.shell.get_shell_rc_file(shell)
                print(f"✓ Added turboalias to {rc_file}")
            else:
                print(f"✓ Turboalias already configured in {shell}")

        # Generate initial aliases file
        self.shell.generate_aliases_file()
        print(f"✓ Created {self.config.shell_file}")

        if added:
            print(
                f"\n⚡ Please reload your shell: {self.shell.reload_shell_message()}")

        print("\n✨ Turboalias is ready! Try: turboalias add ll 'ls -lah'")
        return 0

    def add(self, name: str, command: str, category: Optional[str] = None):
        """Add a new alias"""
        if self.config.alias_exists(name):
            print(f"❌ Alias '{name}' already exists")
            return 1

        if self.config.add_alias(name, command, category):
            self.shell.generate_aliases_file()
            cat_info = f" [{category}]" if category else ""
            print(f"✓ Added alias: {name}{cat_info} = '{command}'")
            print(f"⚡ {self.shell.reload_shell_message()}")
            return 0
        else:
            print(f"❌ Failed to add alias '{name}'")
            return 1

    def remove(self, name: str):
        """Remove an alias"""
        if self.config.remove_alias(name):
            self.shell.generate_aliases_file()
            print(f"✓ Removed alias: {name}")
            print(f"⚡ {self.shell.reload_shell_message()}")
            return 0
        else:
            print(f"❌ Alias '{name}' not found")
            return 1

    def list_aliases(self, category: Optional[str] = None):
        """List all aliases"""
        aliases = self.config.get_aliases(category)

        if not aliases:
            if category:
                print(f"No aliases in category '{category}'")
            else:
                print("No aliases found. Add one with: turboalias add <name> <command>")
            return 0

        if category:
            print(f"Aliases in '{category}':")
        else:
            print("All aliases:")

        # Group by category for display
        by_category = {}
        uncategorized = []

        for name, data in sorted(aliases.items()):
            cat = data.get("category")
            if cat:
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append((name, data["command"]))
            else:
                uncategorized.append((name, data["command"]))

        # Print categorized
        for cat in sorted(by_category.keys()):
            print(f"\n  [{cat}]")
            for name, command in by_category[cat]:
                print(f"    {name} = '{command}'")

        # Print uncategorized
        if uncategorized:
            if by_category:
                print("\n  [other]")
            for name, command in uncategorized:
                print(f"    {name} = '{command}'")

        return 0

    def list_categories(self):
        """List all categories"""
        categories = self.config.get_categories()

        if not categories:
            print("No categories found")
            return 0

        print("Categories:")
        for cat in sorted(categories):
            aliases = self.config.get_aliases(cat)
            print(f"  {cat} ({len(aliases)} aliases)")

        return 0

    def import_aliases(self):
        """Import existing aliases from shell"""
        print("🔍 Scanning for existing aliases...")

        existing = self.shell.import_existing_aliases()

        if not existing:
            print("No new aliases found to import")
            return 0

        print(f"\nFound {len(existing)} aliases:")
        for name, command in list(existing.items())[:5]:
            print(f"  {name} = '{command}'")

        if len(existing) > 5:
            print(f"  ... and {len(existing) - 5} more")

        response = input("\nImport these aliases? (y/n): ").strip().lower()

        if response != 'y':
            print("Import cancelled")
            return 0

        imported = 0
        for name, command in existing.items():
            if self.config.add_alias(name, command):
                imported += 1

        self.shell.generate_aliases_file()
        print(f"✓ Imported {imported} aliases")
        print(f"⚡ {self.shell.reload_shell_message()}")
        return 0

    def clear(self):
        """Clear all aliases"""
        aliases = self.config.get_aliases()

        if not aliases:
            print("No aliases to clear")
            return 0

        print(
            f"⚠️  This will remove all {len(aliases)} turboalias-managed aliases")
        response = input("Are you sure? (y/n): ").strip().lower()

        if response != 'y':
            print("Clear cancelled")
            return 0

        self.config.clear_aliases()
        self.shell.generate_aliases_file()
        print("✓ All aliases cleared")
        print(f"⚡ {self.shell.reload_shell_message()}")
        return 0

    def edit(self):
        """Open config file in editor"""
        editor = os.environ.get('EDITOR', 'nano')

        try:
            subprocess.run([editor, str(self.config.config_file)])
            # Regenerate aliases file after editing
            self.shell.generate_aliases_file()
            print(f"✓ Config updated")
            print(f"⚡ {self.shell.reload_shell_message()}")
            return 0
        except Exception as e:
            print(f"❌ Failed to open editor: {e}")
            return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Turboalias - Cross-workstation alias manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  turboalias init                           Initialize turboalias
  turboalias add ll 'ls -lah'               Add an alias
  turboalias add gst 'git status' --category git    Add with category
  turboalias remove ll                      Remove an alias
  turboalias list                           List all aliases
  turboalias list --category git            List aliases in category
  turboalias categories                     List all categories
  turboalias import                         Import existing aliases
  turboalias clear                          Clear all aliases
  turboalias edit                           Edit config file
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # init
    subparsers.add_parser('init', help='Initialize turboalias')

    # add
    add_parser = subparsers.add_parser('add', help='Add a new alias')
    add_parser.add_argument('name', help='Alias name')
    add_parser.add_argument('command', help='Command to alias')
    add_parser.add_argument('--category', '-c', help='Category for the alias')

    # remove
    remove_parser = subparsers.add_parser('remove', help='Remove an alias')
    remove_parser.add_argument('name', help='Alias name')

    # list
    list_parser = subparsers.add_parser('list', help='List aliases')
    list_parser.add_argument('--category', '-c', help='Filter by category')

    # categories
    subparsers.add_parser('categories', help='List all categories')

    # import
    subparsers.add_parser('import', help='Import existing aliases')

    # clear
    subparsers.add_parser('clear', help='Clear all aliases')

    # edit
    subparsers.add_parser('edit', help='Edit config file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = TurboaliasCLI()

    try:
        if args.command == 'init':
            return cli.init()
        elif args.command == 'add':
            return cli.add(args.name, args.command, args.category)
        elif args.command == 'remove':
            return cli.remove(args.name)
        elif args.command == 'list':
            return cli.list_aliases(args.category)
        elif args.command == 'categories':
            return cli.list_categories()
        elif args.command == 'import':
            return cli.import_aliases()
        elif args.command == 'clear':
            return cli.clear()
        elif args.command == 'edit':
            return cli.edit()
    except KeyboardInterrupt:
        print("\n\nCancelled")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
