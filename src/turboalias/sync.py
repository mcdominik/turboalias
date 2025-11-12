"""
Git sync functionality for turboalias
"""
import json
import subprocess
import logging
from typing import Optional, Dict
from datetime import datetime


class GitSync:
    """Handles git-based syncing of aliases"""

    def __init__(self, config):
        self.config = config
        self.sync_config_file = self.config.config_dir / "sync_config.json"
        self.error_log_file = self.config.config_dir / "sync_errors.log"
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging for sync operations"""
        self.logger = logging.getLogger('turboalias.sync')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []
        
        # File handler for detailed logs
        try:
            fh = logging.FileHandler(self.error_log_file)
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        except Exception:
            pass  # If we can't log, continue anyway

    def _log_error(self, operation: str, error: Exception, context: str = ""):
        """Log sync errors for debugging"""
        try:
            self.logger.error(f"Operation: {operation}")
            if context:
                self.logger.error(f"Context: {context}")
            self.logger.error(f"Error: {str(error)}")
            self.logger.error(f"Error type: {type(error).__name__}")
            
            # Mark that an error occurred
            sync_config = self.load_sync_config()
            sync_config["last_error"] = {
                "operation": operation,
                "message": str(error),
                "timestamp": datetime.now().isoformat()
            }
            self.save_sync_config(sync_config)
        except Exception:
            pass  # Don't let logging errors break the application

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
            self._run_git("init")
            
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
            
            # Ensure .gitignore exists (in case remote doesn't have it)
            self._create_gitignore()

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
            result = self._run_git("push", "origin", branch)
            
            # Clear any previous errors
            if "last_error" in sync_config:
                del sync_config["last_error"]
                self.save_sync_config(sync_config)
            
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            
            # Provide helpful error messages
            if "rejected" in error_msg and "non-fast-forward" in error_msg:
                print(f"❌ Push failed: Your local branch has diverged from remote")
                print(f"\n💡 This happens when:")
                print(f"   • Changes were made on another machine and pushed")
                print(f"   • You're trying to push different local changes")
                print(f"\n🔧 To fix, pull remote changes first:")
                print(f"   turboalias sync pull")
                print(f"   turboalias sync push")
                print(f"\n   Or manually:")
                print(f"   git -C ~/.config/turboalias pull --rebase origin {branch}")
                print(f"   turboalias sync push")
                print(f"\n📝 Full error logged to: {self.error_log_file}")
            elif "403" in error_msg or "Permission" in error_msg or "denied" in error_msg:
                print(f"❌ Push failed: Permission denied")
                print(f"\n💡 This usually means:")
                print(f"   • You don't have write access to the repository")
                print(f"   • Wrong GitHub account is being used for authentication")
                print(f"   • Your credentials need to be updated")
                print(f"\n🔧 To fix:")
                print(f"   1. Check remote: git -C ~/.config/turboalias remote -v")
                print(f"   2. Verify your GitHub account: gh auth status")
                print(f"   3. Use SSH instead of HTTPS for multi-account setups")
                print(f"\n📝 Full error logged to: {self.error_log_file}")
            elif "fatal: Could not read from remote" in error_msg:
                print(f"❌ Push failed: Cannot access remote repository")
                print(f"\n💡 Possible causes:")
                print(f"   • Repository doesn't exist")
                print(f"   • Wrong SSH key is being used")
                print(f"   • Network connectivity issues")
                print(f"\n🔧 To fix:")
                print(f"   1. Test SSH: ssh -T git@github.com")
                print(f"   2. Check remote exists: gh repo view {sync_config.get('remote_url', 'REPO')}")
                print(f"   3. For multi-account: configure SSH config with different keys")
                print(f"\n📝 Full error logged to: {self.error_log_file}")
            else:
                print(f"❌ Push failed: {error_msg}")
                print(f"📝 Full error logged to: {self.error_log_file}")
            
            self._log_error("push", e, f"Remote: {sync_config.get('remote_url')}, Branch: {branch}")
            return False
        except Exception as e:
            print(f"❌ Push failed: {e}")
            print(f"📝 Full error logged to: {self.error_log_file}")
            self._log_error("push", e, f"Remote: {sync_config.get('remote_url')}, Branch: {branch}")
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
            
            # Clear any previous errors
            if "last_error" in sync_config:
                del sync_config["last_error"]
                self.save_sync_config(sync_config)
            
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            print(f"❌ Pull failed: {error_msg}")
            print("💡 Tip: Resolve conflicts manually in ~/.config/turboalias/")
            print(f"📝 Full error logged to: {self.error_log_file}")
            self._log_error("pull", e, f"Remote: {sync_config.get('remote_url')}, Branch: {branch}")
            return False
        except Exception as e:
            print(f"❌ Pull failed: {e}")
            print(f"📝 Full error logged to: {self.error_log_file}")
            self._log_error("pull", e, f"Remote: {sync_config.get('remote_url')}, Branch: {branch}")
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
                # Fetch latest remote state
                self._run_git("fetch", "origin")
                branch = sync_config.get("branch", "main")
                rev_list = self._run_git(
                    "rev-list", "--left-right", "--count", f"origin/{branch}...HEAD")
                behind, ahead = rev_list.stdout.strip().split()

                result = {
                    "initialized": True,
                    "has_changes": has_changes,
                    "ahead": int(ahead),
                    "behind": int(behind),
                    "remote_url": sync_config.get("remote_url"),
                    "branch": branch
                }
                
                # Include last error if any
                if "last_error" in sync_config:
                    result["last_error"] = sync_config["last_error"]
                
                return result
            except Exception as e:
                self.logger.debug(f"Could not fetch remote state: {e}")
                result = {
                    "initialized": True,
                    "has_changes": has_changes,
                    "remote_configured": bool(sync_config.get("remote_url")),
                    "remote_url": sync_config.get("remote_url"),
                    "branch": sync_config.get("branch", "main"),
                    "fetch_error": str(e)
                }
                
                # Include last error if any
                if "last_error" in sync_config:
                    result["last_error"] = sync_config["last_error"]
                
                return result
        except Exception as e:
            return {"initialized": True, "error": str(e)}

    def check_connectivity(self) -> Dict:
        """Check connectivity and authentication to remote repository"""
        if not self.is_git_initialized():
            return {"error": "Git not initialized"}
        
        sync_config = self.load_sync_config()
        remote_url = sync_config.get("remote_url")
        branch = sync_config.get("branch", "main")
        
        if not remote_url:
            return {"error": "No remote URL configured"}
        
        results = {
            "remote_url": remote_url,
            "branch": branch,
            "checks": {}
        }
        
        # Check 1: Can we reach the remote?
        try:
            self._run_git("ls-remote", "--heads", "origin")
            results["checks"]["remote_reachable"] = {
                "status": "pass",
                "message": "Can reach remote repository"
            }
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            results["checks"]["remote_reachable"] = {
                "status": "fail",
                "message": f"Cannot reach remote: {error_msg}"
            }
            
            # Add specific diagnostics based on error
            if "403" in error_msg or "Permission denied" in error_msg or "denied" in error_msg:
                results["checks"]["remote_reachable"]["diagnosis"] = "authentication_failed"
                results["checks"]["remote_reachable"]["help"] = [
                    "Wrong credentials or insufficient permissions",
                    "Check: gh auth status",
                    "For HTTPS: Update credentials in keychain/credential manager",
                    "For SSH: Verify correct SSH key is being used (ssh -T git@github.com)"
                ]
            elif "Could not resolve host" in error_msg:
                results["checks"]["remote_reachable"]["diagnosis"] = "network_error"
                results["checks"]["remote_reachable"]["help"] = [
                    "Network connectivity issue",
                    "Check your internet connection",
                    "Verify the remote URL is correct"
                ]
        except Exception as e:
            results["checks"]["remote_reachable"] = {
                "status": "fail",
                "message": str(e)
            }
        
        # Check 2: Is the remote URL using HTTPS or SSH?
        if "github.com" in remote_url or "gitlab.com" in remote_url:
            if remote_url.startswith("https://"):
                results["checks"]["auth_method"] = {
                    "status": "info",
                    "message": "Using HTTPS authentication",
                    "notes": [
                        "HTTPS uses system credential manager",
                        "May cause issues with multiple GitHub accounts",
                        "Consider using SSH for better multi-account support"
                    ]
                }
            elif remote_url.startswith("git@"):
                results["checks"]["auth_method"] = {
                    "status": "info",
                    "message": "Using SSH authentication",
                    "notes": [
                        "SSH uses SSH keys from ~/.ssh/",
                        "Test with: ssh -T git@github.com",
                        "For multiple accounts: configure ~/.ssh/config"
                    ]
                }
        
        # Check 3: Test SSH connection if using SSH
        if remote_url.startswith("git@"):
            try:
                # Extract hostname
                if "github.com" in remote_url:
                    host = "git@github.com"
                elif "gitlab.com" in remote_url:
                    host = "git@gitlab.com"
                else:
                    host = None
                
                if host:
                    ssh_test = subprocess.run(
                        ["ssh", "-T", host],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    # SSH to git hosts always returns non-zero, check output instead
                    if ssh_test.stderr and ("successfully authenticated" in ssh_test.stderr.lower() or 
                                            "hi " in ssh_test.stderr.lower()):
                        # Extract username from SSH response
                        import re
                        match = re.search(r'Hi (\S+)!', ssh_test.stderr)
                        username = match.group(1) if match else "unknown"
                        
                        results["checks"]["ssh_connection"] = {
                            "status": "pass",
                            "message": f"SSH authentication successful as '{username}'",
                            "notes": [f"Connected to {host}"]
                        }
                        
                        # Check if username matches the repo owner
                        if "github.com" in remote_url or "gitlab.com" in remote_url:
                            repo_match = re.search(r'[:/]([^/]+)/([^/]+?)(?:\.git)?$', remote_url)
                            if repo_match:
                                repo_owner = repo_match.group(1)
                                if username.lower() != repo_owner.lower():
                                    results["checks"]["ssh_connection"]["warning"] = (
                                        f"SSH authenticates as '{username}' but repository owner is '{repo_owner}'. "
                                        f"This may cause permission issues."
                                    )
                    else:
                        results["checks"]["ssh_connection"] = {
                            "status": "fail",
                            "message": "SSH authentication failed",
                            "error": ssh_test.stderr.strip()
                        }
            except subprocess.TimeoutExpired:
                results["checks"]["ssh_connection"] = {
                    "status": "fail",
                    "message": "SSH connection timeout"
                }
            except Exception as e:
                results["checks"]["ssh_connection"] = {
                    "status": "error",
                    "message": f"Could not test SSH: {e}"
                }
        
        # Check 4: Check if we can push (dry-run)
        try:
            self._run_git("push", "--dry-run", "origin", branch)
            results["checks"]["push_access"] = {
                "status": "pass",
                "message": "Have push access to remote"
            }
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            results["checks"]["push_access"] = {
                "status": "fail",
                "message": f"Cannot push to remote: {error_msg}"
            }
        except Exception as e:
            results["checks"]["push_access"] = {
                "status": "error",
                "message": f"Could not test push access: {e}"
            }
        
        return results

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
            # Commit changes
            self.commit_changes("Auto-sync: update aliases")
            
            # Try to push
            result = self._run_git("push", "origin", sync_config.get("branch", "main"))
            
            # Clear any previous errors on success
            if "last_error" in sync_config:
                del sync_config["last_error"]
                self.save_sync_config(sync_config)
                
        except Exception as e:
            # Log the error but don't block the user
            self._log_error("auto-sync", e, f"Background sync failed")
            
            # Store error in config so we can warn user later
            sync_config["last_error"] = {
                "operation": "auto-sync",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.save_sync_config(sync_config)
    
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
        except Exception as e:
            print(f"Warning: Could not create .gitignore: {e}")
            pass
