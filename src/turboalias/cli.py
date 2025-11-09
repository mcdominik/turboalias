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
        shell = self.shell.detect_shells()

        if not shell:
            print("❌ No supported shell found (.bashrc or .zshrc)")
            print("   Please create ~/.bashrc or ~/.zshrc first")
            return 1

        # Check if already initialized
        rc_file = self.shell.get_shell_rc_file(shell)
        aliases_file_exists = self.config.shell_file.exists()
        
        if self.shell.add_source_line(shell):
            # First time setup
            print("🔧 Initializing turboalias...")
            print(f"✓ Added turboalias to {rc_file}")
            
            # Generate initial aliases file
            self.shell.generate_aliases_file()
            print(f"✓ Created {self.config.shell_file}")
            
            # Prompt to import existing aliases
            print("\n📥 Import your existing shell aliases?")
            response = input("   (Y/n) [default: yes]: ").strip().lower()
            
            imported = 0
            if response in ['', 'y', 'yes']:
                existing = self.shell.import_existing_aliases(shell)
                
                if existing:
                    # Show preview
                    preview_count = min(3, len(existing))
                    for i, (name, command) in enumerate(list(existing.items())[:preview_count]):
                        print(f"   • {name} = '{command}'")
                    
                    if len(existing) > preview_count:
                        print(f"   ... and {len(existing) - preview_count} more")
                    
                    # Import them
                    for name, command in existing.items():
                        if self.config.add_alias(name, command):
                            imported += 1
                    
                    self.shell.generate_aliases_file()
                
                print(f"   ✓ Imported {imported} aliases")
            else:
                print("   ✓ Skipped import")
            
            print(f"\n⚡ Please reload your shell: {self.shell.reload_shell_message()}")
            print("✨ Then turboalias will be ready to use!")
        else:
            # Already initialized
            print("✨ Turboalias is already initialized!")
            print(f"   Shell config: {rc_file}")
            print(f"   Aliases file: {self.config.shell_file}")
            
            # Regenerate aliases file in case it was deleted
            if not aliases_file_exists:
                self.shell.generate_aliases_file()
                print("\n✓ Regenerated missing aliases file")
            
            print("\n💡 Ready to use! Try: turboalias add ll 'ls -lah'")
        
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
            print(f"✨ Alias is now available in this terminal!")
            return 0
        else:
            print(f"❌ Failed to add alias '{name}'")
            return 1

    def remove(self, name: str):
        """Remove an alias"""
        if self.config.remove_alias(name):
            self.shell.generate_aliases_file()
            print(f"✓ Removed alias: {name}")
            print(f"✨ Change is now active in this terminal!")
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

        shell = self.shell.detect_shells()
        existing = self.shell.import_existing_aliases(shell)

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
        print(f"✨ Aliases are now available in this terminal!")
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
        print(f"✨ Change is now active in this terminal!")
        return 0

    def edit(self):
        """Open config file in editor"""
        editor = os.environ.get('EDITOR', 'nano')

        try:
            subprocess.run([editor, str(self.config.config_file)])
            # Regenerate aliases file after editing
            self.shell.generate_aliases_file()
            print(f"✓ Config updated")
            print(f"✨ Changes are now active in this terminal!")
            return 0
        except Exception as e:
            print(f"❌ Failed to open editor: {e}")
            return 1

    def nuke(self):
        """Completely remove turboalias configuration"""
        print("💣 This will completely remove turboalias from your system:")
        print("   • Remove turboalias from shell config")
        print("   • Delete all aliases")
        print(f"   • Delete {self.config.config_dir}")
        
        response = input("\n⚠️  Are you absolutely sure? (y/N) [default: no]: ").strip().lower()
        
        if response not in ['y', 'yes']:
            print("Nuke cancelled - nothing was removed")
            return 0
        
        shell = self.shell.detect_shells()
        removed_items = []
        
        # Remove from shell config
        if shell:
            rc_file = self.shell.get_shell_rc_file(shell)
            if rc_file.exists():
                try:
                    with open(rc_file, 'r') as f:
                        lines = f.readlines()
                    
                    # Filter out turboalias lines
                    new_lines = []
                    skip_until_end = False
                    
                    for line in lines:
                        if '# turboalias aliases' in line:
                            skip_until_end = True
                            continue
                        
                        if skip_until_end:
                            # Skip until we find the closing brace of the function
                            if line.strip() == '}':
                                skip_until_end = False
                            continue
                        
                        # Skip individual turboalias source lines
                        if 'turboalias' in line and ('source' in line or 'turboalias()' in line):
                            continue
                        
                        new_lines.append(line)
                    
                    with open(rc_file, 'w') as f:
                        f.writelines(new_lines)
                    
                    removed_items.append(f"Removed turboalias from {rc_file}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not clean {rc_file}: {e}")
        
        # Remove config directory
        if self.config.config_dir.exists():
            try:
                import shutil
                shutil.rmtree(self.config.config_dir)
                removed_items.append(f"Deleted {self.config.config_dir}")
            except Exception as e:
                print(f"⚠️  Warning: Could not remove {self.config.config_dir}: {e}")
        
        if removed_items:
            print("\n✓ Turboalias has been removed:")
            for item in removed_items:
                print(f"  • {item}")
            print("\n⚡ Please reload your shell to complete removal")
        else:
            print("\n✓ Turboalias was not found on this system")
        
        return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        prog='turboalias',
        description='🚀 Turboalias - Cross-workstation alias manager for bash and zsh',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            ✨ Examples:
            turboalias init                                 Get started with turboalias
            turboalias add ll 'ls -lah'                     Create a simple alias
            turboalias add gst 'git status' -c git          Add alias with category
            turboalias remove ll                            Remove an alias
            turboalias list                                 Show all your aliases
            turboalias list -c git                          Show aliases in a category
            turboalias categories                           View all categories
            turboalias import                               Import your existing aliases
            turboalias clear                                Remove all aliases
            turboalias edit                                 Edit config in $EDITOR
            turboalias nuke                                 Completely remove turboalias

            💡 Tip: Changes apply instantly - no shell reload needed!

            📖 Documentation: https://github.com/mcdominik/turboalias
        """
    )

    subparsers = parser.add_subparsers(
        dest='command',
        metavar='<command>',
        help='Available commands'
    )

    # init
    subparsers.add_parser(
        'init',
        help='🔧 Set up turboalias in your shell'
    )

    # add
    add_parser = subparsers.add_parser(
        'add',
        help='➕ Create a new alias'
    )
    add_parser.add_argument('name', help='Name for your alias')
    add_parser.add_argument('cmd', help='Command to run')
    add_parser.add_argument('--category', '-c', help='Optional category (git, docker, etc.)')

    # remove
    remove_parser = subparsers.add_parser(
        'remove',
        help='🗑️  Delete an alias'
    )
    remove_parser.add_argument('name', help='Alias to remove')

    # list
    list_parser = subparsers.add_parser(
        'list',
        help='📋 Show your aliases'
    )
    list_parser.add_argument('--category', '-c', help='Filter by category')

    # categories
    subparsers.add_parser(
        'categories',
        help='📁 View all categories'
    )

    # import
    subparsers.add_parser(
        'import',
        help='📥 Import aliases from your shell'
    )

    # clear
    subparsers.add_parser(
        'clear',
        help='🧹 Remove all aliases'
    )

    # edit
    subparsers.add_parser(
        'edit',
        help='✏️  Edit config file directly'
    )

    # nuke
    subparsers.add_parser(
        'nuke',
        help='💣 Completely remove turboalias'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = TurboaliasCLI()

    try:
        if args.command == 'init':
            return cli.init()
        elif args.command == 'add':
            return cli.add(args.name, args.cmd, args.category)
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
        elif args.command == 'nuke':
            return cli.nuke()
    except KeyboardInterrupt:
        print("\n\nCancelled")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
