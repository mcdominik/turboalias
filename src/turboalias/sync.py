"""
Git sync functionality for turboalias
"""
import json
import subprocess
from typing import Optional, Dict


class GitSync:
    """Handles git-based syncing of aliases"""

    def __init__(self, config):
        self.config = config
        self.sync_config_file = self.config.config_dir / "sync_config.json"

    def is_git_initialized(self) -> bool:
        """Check if git repo exists"""
        git_dir = self.config.config_dir / ".git"
        return git_dir.exists()

    def is_sync_configured(self) -> bool:
        """Check if sync is configured"""
        return self.sync_config_file.exists()

    def load_sync_config(self) -> Dict:
        """Load sync configuration"""
        if not self.sync_config_file.exists():
            return {}

        with open(self.sync_config_file, 'r') as f:
            return json.load(f)

    def save_sync_config(self, config: Dict):
        """Save sync configuration"""
        with open(self.sync_config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def init_git(self, remote_url: Optional[str] = None, branch: str = "main") -> bool:
        """Initialize git repo in config directory"""
        try:
            # Initialize git
            self._run_git("init")
            
            # Create .gitignore
            self._create_gitignore()

            # Create initial commit
            self._run_git("add", "aliases.json")
            self._run_git("commit", "-m", "Initial turboalias aliases")

            # Setup remote if provided
            if remote_url:
                self._run_git("remote", "add", "origin", remote_url)
                self._run_git("branch", "-M", branch)

            # Save sync config
            self.save_sync_config({
                "enabled": True,
                "remote_url": remote_url,
                "branch": branch,
                "auto_sync": False
            })

            return True
        except Exception as e:
            print(f"Git initialization failed: {e}")
            return False

    def clone_repo(self, remote_url: str, branch: str = "main") -> bool:
        """Clone existing turboalias repo"""
        try:
            # Remove existing config dir if empty or only has shell file
            if self.config.config_dir.exists():
                files = list(self.config.config_dir.glob("*"))
                if len(files) > 1 or (len(files) == 1 and files[0].name != "aliases.sh"):
                    print("⚠️  Config directory not empty. Backup and clear it first.")
                    return False

            # Clone repo
            subprocess.run(
                ["git", "clone", "-b", branch, remote_url,
                    str(self.config.config_dir)],
                check=True,
                cwd=self.config.config_dir.parent
            )
            
            # Ensure .gitignore exists
            self._create_gitignore()

            # Save sync config
            self.save_sync_config({
                "enabled": True,
                "remote_url": remote_url,
                "branch": branch,
                "auto_sync": False
            })

            return True
        except Exception as e:
            print(f"Clone failed: {e}")
            return False

    def commit_changes(self, message: Optional[str] = None) -> bool:
        """Commit changes to git"""
        if not self.is_git_initialized():
            return False

        try:
            # Check if there are changes
            result = self._run_git("status", "--porcelain")
            if not result.stdout.strip():
                return True  # No changes

            # Add and commit
            self._run_git("add", "aliases.json")

            if not message:
                message = "Update aliases"

            self._run_git("commit", "-m", message)
            return True
        except Exception as e:
            print(f"Commit failed: {e}")
            return False

    def push(self) -> bool:
        """Push changes to remote"""
        if not self.is_git_initialized():
            print("❌ Git not initialized. Run: turboalias sync init")
            return False

        sync_config = self.load_sync_config()
        branch = sync_config.get("branch", "main")

        try:
            # Commit any pending changes first
            self.commit_changes()

            # Push
            self._run_git("push", "origin", branch)
            return True
        except Exception as e:
            print(f"Push failed: {e}")
            return False

    def pull(self) -> bool:
        """Pull changes from remote"""
        if not self.is_git_initialized():
            print("❌ Git not initialized. Run: turboalias sync init")
            return False

        sync_config = self.load_sync_config()
        branch = sync_config.get("branch", "main")

        try:
            # Commit local changes first
            self.commit_changes("Auto-commit before pull")

            # Pull with rebase
            self._run_git("pull", "--rebase", "origin", branch)
            return True
        except Exception as e:
            print(f"Pull failed: {e}")
            print("💡 Tip: Resolve conflicts manually in ~/.config/turboalias/")
            return False

    def status(self) -> Dict:
        """Get sync status"""
        if not self.is_git_initialized():
            return {"initialized": False}

        sync_config = self.load_sync_config()

        try:
            # Check for uncommitted changes (exclude untracked files that are gitignored)
            status_result = self._run_git("status", "--porcelain")
            
            # Filter out untracked files (lines starting with ??)
            # We only care about modified/added/deleted tracked files
            has_changes = False
            for line in status_result.stdout.strip().split('\n'):
                if line and not line.startswith('??'):
                    has_changes = True
                    break

            # Check if ahead/behind remote
            try:
                fetch_result = self._run_git("fetch", "origin")
                branch = sync_config.get("branch", "main")
                rev_list = self._run_git(
                    "rev-list", "--left-right", "--count", f"origin/{branch}...HEAD")
                behind, ahead = rev_list.stdout.strip().split()

                return {
                    "initialized": True,
                    "has_changes": has_changes,
                    "ahead": int(ahead),
                    "behind": int(behind),
                    "remote_url": sync_config.get("remote_url"),
                    "branch": branch
                }
            except:
                # No remote or can't reach it
                return {
                    "initialized": True,
                    "has_changes": has_changes,
                    "remote_configured": bool(sync_config.get("remote_url")),
                    "remote_url": sync_config.get("remote_url")
                }
        except Exception as e:
            return {"initialized": True, "error": str(e)}

    def _run_git(self, *args):
        """Run git command in config directory"""
        return subprocess.run(
            ["git"] + list(args),
            cwd=self.config.config_dir,
            check=True,
            capture_output=True,
            text=True
        )

    def auto_sync_if_enabled(self):
        """Auto-sync if enabled in config"""
        sync_config = self.load_sync_config()

        if not sync_config.get("auto_sync", False):
            return

        if not self.is_git_initialized():
            return

        try:
            # Silently commit and push in background
            self.commit_changes("Auto-sync: update aliases")
            self.push()
        except:
            # Fail silently for auto-sync
            pass
    
    def _create_gitignore(self):
        """Create .gitignore to exclude local files"""
        gitignore_path = self.config.config_dir / ".gitignore"
        gitignore_content = """# Turboalias local files (not synced)
aliases.sh
sync_config.json
"""
        try:
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content)
        except Exception:
            # Non-critical, continue anyway
            pass

    def _run_git(self, *args):
        """Run git command in config directory"""
        return subprocess.run(
            ["git"] + list(args),
            cwd=self.config.config_dir,
            check=True,
            capture_output=True,
            text=True
        )
