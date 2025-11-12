"""
CLI interface for turboalias
"""
import argparse
import os
import subprocess
import sys
from typing import Optional

from . import __version__
from .config import Config
from .shell import ShellIntegration
from .sync import GitSync


class TurboaliasCLI:
    """Main CLI handler"""

    def __init__(self):
        self.config = Config()
        self.shell = ShellIntegration(self.config)
        self.git_sync = GitSync(self.config)
        self._check_sync_errors()

    def _check_sync_errors(self):
        """Check for recent sync errors and warn user"""
        if not self.git_sync.is_git_initialized():
            return
        
        sync_config = self.git_sync.load_sync_config()
        if "last_error" in sync_config:
            error_info = sync_config["last_error"]
            print(f"⚠️  Auto-sync is failing: {error_info.get('message', 'Unknown error')}")
            print(f"   Last failed: {error_info.get('timestamp', 'Unknown time')}")
            print(f"   Run 'turboalias sync status' for details")
            print(f"   Run 'turboalias sync check' to diagnose the issue")
            print()

    def init(self):
        """Initialize turboalias"""
        shell = self.shell.detect_shells()

        if not shell:
            print("❌ No supported shell found (.bashrc or .zshrc)")
            return 1

        # Check if already initialized
        rc_file = self.shell.get_shell_rc_file(shell)
        aliases_file_exists = self.config.shell_file.exists()
        config_file_exists = self.config.config_file.exists()
        
        if not self.shell.is_initialized(shell):
            # First time setup
            print("🔧 Initializing turboalias...")
            
            if not self.shell.initialize_shell_integration(shell):
                print("❌ Failed to initialize shell integration")
                return 1
            
            print(f"✓ Added turboalias to {rc_file}")
            
            # Create default config with example aliases if no config exists
            if not config_file_exists:
                self.config._create_default_config()
                print(f"✓ Created {self.config.config_file} with example aliases")
            
            self.shell.generate_aliases_file()
            print(f"✓ Created {self.config.shell_file}")
            
            if not config_file_exists:
                print("\n✨ Turboalias comes with helpful example aliases:")
                print("   • tba = 'turboalias' [general]")
                print("   • dps = 'docker ps' [docker]")
                print("   • gst = 'git status' [git]")
                print("   • hg = 'history | grep' [general]")
                print("   ... and 4 more! Run 'turboalias list' to see all")
            
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
            
            # Try auto-sync if enabled
            self._try_auto_sync()
            
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
            
            # Try auto-sync if enabled
            self._try_auto_sync()
            
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
        
        # Try auto-sync if enabled
        self._try_auto_sync()
        
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

    def sync_init(self, remote: Optional[str] = None, branch: str = "main"):
        """Initialize git sync"""
        if self.git_sync.is_git_initialized():
            print("✨ Git sync is already initialized!")
            status = self.git_sync.status()
            if status.get("remote_url"):
                print(f"   Remote: {status['remote_url']}")
                print(f"   Branch: {status.get('branch', 'main')}")
            return 0
        
        print("🔧 Initializing git sync...")
        
        if self.git_sync.init_git(remote, branch):
            print("✓ Git repository initialized")
            print(f"✓ Created {self.config.config_dir}/.git")
            
            if remote:
                print(f"✓ Added remote: {remote}")
                print(f"✓ Set branch: {branch}")
                print("\n💡 Next steps:")
                print(f"   1. Push to remote: turboalias sync push")
                print(f"   2. On other machines: turboalias sync clone {remote}")
            else:
                print("\n💡 Add a remote to sync across machines:")
                print("   git -C ~/.config/turboalias remote add origin <your-repo-url>")
                print("   turboalias sync push")
            
            return 0
        else:
            print("❌ Failed to initialize git sync")
            return 1

    def sync_clone(self, remote_url: str, branch: str = "main"):
        """Clone existing turboalias config from git"""
        print(f"📥 Cloning turboalias config from {remote_url}...")
        
        if self.git_sync.clone_repo(remote_url, branch):
            print("✓ Successfully cloned configuration")
            print(f"✓ Remote: {remote_url}")
            print(f"✓ Branch: {branch}")
            
            # Regenerate shell aliases file
            self.shell.generate_aliases_file()
            print(f"✓ Generated {self.config.shell_file}")
            
            # Count aliases
            aliases = self.config.get_aliases()
            print(f"\n✨ Restored {len(aliases)} aliases!")
            
            if aliases:
                print("\n💡 Reload your shell to use the aliases:")
                print(f"   {self.shell.reload_shell_message()}")
            
            return 0
        else:
            return 1

    def sync_push(self):
        """Push changes to remote"""
        if not self.git_sync.is_git_initialized():
            print("❌ Git sync not initialized. Run: turboalias sync init")
            return 1
        
        print("📤 Pushing changes to remote...")
        
        if self.git_sync.push():
            print("✓ Successfully pushed to remote")
            return 0
        else:
            return 1

    def sync_pull(self):
        """Pull changes from remote"""
        if not self.git_sync.is_git_initialized():
            print("❌ Git sync not initialized. Run: turboalias sync init")
            return 1
        
        print("📥 Pulling changes from remote...")
        
        if self.git_sync.pull():
            # Regenerate shell aliases file after pull
            self.shell.generate_aliases_file()
            print("✓ Successfully pulled from remote")
            print("✓ Updated local aliases")
            
            aliases = self.config.get_aliases()
            print(f"\n✨ You now have {len(aliases)} aliases!")
            return 0
        else:
            return 1

    def sync_status(self):
        """Show sync status"""
        status = self.git_sync.status()
        
        if not status.get("initialized"):
            print("❌ Git sync not initialized")
            print("\n💡 Get started:")
            print("   turboalias sync init [--remote <url>]")
            return 1
        
        print("📊 Sync Status:")
        print(f"   Repository: ✓ Initialized")
        
        if status.get("remote_url"):
            print(f"   Remote: {status['remote_url']}")
            print(f"   Branch: {status.get('branch', 'main')}")
        else:
            print(f"   Remote: ⚠️  Not configured")
        
        if status.get("has_changes"):
            print(f"   Local changes: ⚠️  Uncommitted changes")
        else:
            print(f"   Local changes: ✓ Clean")
        
        if "ahead" in status:
            if status["ahead"] > 0:
                print(f"   Ahead: ⬆️  {status['ahead']} commit(s) to push")
            else:
                print(f"   Ahead: ✓ Up to date")
            
            if status["behind"] > 0:
                print(f"   Behind: ⬇️  {status['behind']} commit(s) to pull")
            else:
                print(f"   Behind: ✓ Up to date")
        
        # Check auto-sync status
        sync_config = self.git_sync.load_sync_config()
        auto_sync = sync_config.get("auto_sync", False)
        print(f"   Auto-sync: {'✓ Enabled' if auto_sync else '○ Disabled'}")
        
        # Show last error if any
        if "last_error" in status:
            error_info = status["last_error"]
            print(f"\n⚠️  Last sync error:")
            print(f"   Operation: {error_info.get('operation', 'Unknown')}")
            print(f"   Message: {error_info.get('message', 'Unknown error')}")
            print(f"   Time: {error_info.get('timestamp', 'Unknown')}")
            print(f"\n💡 Run 'turboalias sync check' to diagnose")
            print(f"   View detailed logs: cat {self.git_sync.error_log_file}")
        
        if status.get("error"):
            print(f"\n⚠️  {status['error']}")
        
        if status.get("fetch_error"):
            print(f"\n⚠️  Cannot reach remote: {status['fetch_error']}")
            print(f"   Run 'turboalias sync check' to diagnose")
        
        return 0

    def sync_auto(self, enable: bool):
        """Enable or disable auto-sync"""
        if not self.git_sync.is_git_initialized():
            print("❌ Git sync not initialized. Run: turboalias sync init")
            return 1
        
        sync_config = self.git_sync.load_sync_config()
        sync_config["auto_sync"] = enable
        self.git_sync.save_sync_config(sync_config)
        
        if enable:
            print("✓ Auto-sync enabled")
            print("💡 Your aliases will be automatically pushed after changes")
        else:
            print("✓ Auto-sync disabled")
            print("💡 Use 'turboalias sync push' to manually sync")
        
        return 0

    def sync_check(self):
        """Check sync connectivity and diagnose issues"""
        if not self.git_sync.is_git_initialized():
            print("❌ Git sync not initialized")
            print("\n💡 Get started:")
            print("   turboalias sync init [--remote <url>]")
            return 1
        
        print("🔍 Checking sync connectivity...")
        print()
        
        results = self.git_sync.check_connectivity()
        
        if "error" in results:
            print(f"❌ {results['error']}")
            return 1
        
        print(f"Remote: {results.get('remote_url')}")
        print(f"Branch: {results.get('branch')}")
        print()
        
        # Display check results
        all_passed = True
        for check_name, check_result in results.get("checks", {}).items():
            status = check_result.get("status")
            
            if status == "pass":
                print(f"✓ {check_result.get('message')}")
                if "notes" in check_result:
                    for note in check_result["notes"]:
                        print(f"  ℹ️  {note}")
                if "warning" in check_result:
                    print(f"  ⚠️  {check_result['warning']}")
            elif status == "fail":
                all_passed = False
                print(f"✗ {check_result.get('message')}")
                if "diagnosis" in check_result:
                    print(f"  Diagnosis: {check_result['diagnosis']}")
                if "help" in check_result:
                    print(f"  How to fix:")
                    for help_item in check_result["help"]:
                        print(f"    • {help_item}")
                if "error" in check_result:
                    print(f"  Error: {check_result['error']}")
            elif status == "info":
                print(f"ℹ️  {check_result.get('message')}")
                if "notes" in check_result:
                    for note in check_result["notes"]:
                        print(f"  • {note}")
            elif status == "error":
                print(f"⚠️  {check_result.get('message')}")
            
            print()
        
        if all_passed:
            print("✨ All checks passed! Sync should work correctly.")
            return 0
        else:
            print("❌ Some checks failed. Please fix the issues above.")
            print(f"\n📝 Detailed logs: cat {self.git_sync.error_log_file}")
            return 1

    def _try_auto_sync(self):
        """Check sync connectivity and diagnose issues"""
        if not self.git_sync.is_git_initialized():
            print("❌ Git sync not initialized. Run: turboalias sync init")
            return 1
        
        print("🔍 Checking sync connectivity...\n")
        
        results = self.git_sync.check_connectivity()
        
        if "error" in results:
            print(f"❌ {results['error']}")
            return 1
        
        print(f"Remote: {results['remote_url']}")
        print(f"Branch: {results['branch']}\n")
        
        # Display check results
        checks = results.get("checks", {})
        all_passed = True
        
        for check_name, check_result in checks.items():
            status = check_result.get("status", "unknown")
            message = check_result.get("message", "")
            
            if status == "pass":
                print(f"✓ {message}")
            elif status == "fail":
                print(f"❌ {message}")
                all_passed = False
            elif status == "info":
                print(f"ℹ️  {message}")
            elif status == "error":
                print(f"⚠️  {message}")
            
            # Show notes if any
            if "notes" in check_result:
                for note in check_result["notes"]:
                    print(f"   • {note}")
            
            # Show warning if any
            if "warning" in check_result:
                print(f"   ⚠️  {check_result['warning']}")
            
            # Show help if any
            if "help" in check_result:
                print(f"   💡 Suggestions:")
                for help_text in check_result["help"]:
                    print(f"      - {help_text}")
            
            # Show diagnosis if any
            if "diagnosis" in check_result:
                print(f"   🔍 Diagnosis: {check_result['diagnosis']}")
            
            # Show error details if any
            if "error" in check_result:
                print(f"   Error: {check_result['error']}")
            
            print()
        
        if all_passed:
            print("✨ All checks passed! Sync should work correctly.")
            return 0
        else:
            print("⚠️  Some checks failed. Please address the issues above.")
            print(f"📝 Detailed logs: {self.git_sync.error_log_file}")
            return 1

    def _try_auto_sync(self):
        """Attempt background auto-sync if enabled"""
        if not self.git_sync.is_git_initialized():
            return
        
        sync_config = self.git_sync.load_sync_config()
        if not sync_config.get("auto_sync", False):
            return
        
        # Background sync - don't block the user
        try:
            import threading
            thread = threading.Thread(target=self.git_sync.auto_sync_if_enabled, daemon=False)
            thread.start()
            # Give the thread a moment to complete, but don't wait forever
            # This ensures sync happens but doesn't block user if network is slow
            thread.join(timeout=2.0)
        except Exception:
            # Silently fail - don't interrupt user's workflow
            pass

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
        description=f'🚀 Turboalias v{__version__} - Cross-workstation alias manager for bash and zsh',
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
            
            🔄 Git Sync:
            turboalias sync init --remote <url>             Set up git sync
            turboalias sync clone <url>                     Clone aliases from remote
            turboalias sync push                            Push changes to remote
            turboalias sync pull                            Pull changes from remote
            turboalias sync status                          Check sync status
            turboalias sync auto on                         Enable auto-sync
            turboalias sync check                           Diagnose sync issues

            💡 Tip: Changes apply instantly - no shell reload needed!

            📖 Documentation: https://github.com/mcdominik/turboalias
        """
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'turboalias {__version__}'
    )

    subparsers = parser.add_subparsers(
        dest='command',
        metavar='<command>',
        help='Available commands'
    )

    subparsers.add_parser(
        'init',
        help='🔧 Set up turboalias in your shell'
    )

    add_parser = subparsers.add_parser(
        'add',
        help='➕ Create a new alias'
    )
    add_parser.add_argument('name', help='Name for your alias')
    add_parser.add_argument('cmd', help='Command to run')
    add_parser.add_argument('--category', '-c', help='Optional category (git, docker, etc.)')

    remove_parser = subparsers.add_parser(
        'remove',
        help='🗑️  Delete an alias'
    )
    remove_parser.add_argument('name', help='Alias to remove')

    list_parser = subparsers.add_parser(
        'list',
        help='📋 Show your aliases'
    )
    list_parser.add_argument('--category', '-c', help='Filter by category')

    subparsers.add_parser(
        'categories',
        help='📁 View all categories'
    )

    subparsers.add_parser(
        'import',
        help='📥 Import aliases from your shell'
    )

    subparsers.add_parser(
        'clear',
        help='🧹 Remove all aliases'
    )

    subparsers.add_parser(
        'edit',
        help='✏️  Edit config file directly'
    )

    subparsers.add_parser(
        'nuke',
        help='💣 Completely remove turboalias'
    )

    sync_parser = subparsers.add_parser(
        'sync',
        help='🔄 Sync aliases via Git'
    )
    sync_subparsers = sync_parser.add_subparsers(
        dest='sync_command',
        metavar='<sync-command>',
        help='Sync operations'
    )

    sync_init_parser = sync_subparsers.add_parser(
        'init',
        help='Initialize git sync'
    )
    sync_init_parser.add_argument('--remote', '-r', help='Remote repository URL')
    sync_init_parser.add_argument('--branch', '-b', default='main', help='Branch name (default: main)')

    sync_clone_parser = sync_subparsers.add_parser(
        'clone',
        help='Clone existing config from git'
    )
    sync_clone_parser.add_argument('remote_url', help='Remote repository URL')
    sync_clone_parser.add_argument('--branch', '-b', default='main', help='Branch name (default: main)')

    sync_subparsers.add_parser(
        'push',
        help='Push changes to remote'
    )

    sync_subparsers.add_parser(
        'pull',
        help='Pull changes from remote'
    )

    sync_subparsers.add_parser(
        'status',
        help='Show sync status'
    )

    sync_auto_parser = sync_subparsers.add_parser(
        'auto',
        help='Enable/disable auto-sync'
    )
    sync_auto_parser.add_argument('mode', choices=['on', 'off'], help='Enable or disable auto-sync')

    sync_subparsers.add_parser(
        'check',
        help='Check connectivity and diagnose sync issues'
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
        elif args.command == 'sync':
            if not args.sync_command:
                print("❌ Sync command required")
                print("\n💡 Available sync commands:")
                print("   turboalias sync init [--remote <url>]")
                print("   turboalias sync clone <url>")
                print("   turboalias sync push")
                print("   turboalias sync pull")
                print("   turboalias sync status")
                print("   turboalias sync auto on|off")
                print("   turboalias sync check")
                return 1
            
            if args.sync_command == 'init':
                return cli.sync_init(args.remote, args.branch)
            elif args.sync_command == 'clone':
                return cli.sync_clone(args.remote_url, args.branch)
            elif args.sync_command == 'push':
                return cli.sync_push()
            elif args.sync_command == 'pull':
                return cli.sync_pull()
            elif args.sync_command == 'status':
                return cli.sync_status()
            elif args.sync_command == 'auto':
                return cli.sync_auto(args.mode == 'on')
            elif args.sync_command == 'check':
                return cli.sync_check()
    except KeyboardInterrupt:
        print("\n\nCancelled")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
