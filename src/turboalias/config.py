"""
Configuration management for turboalias
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional


class Config:
    """Manages turboalias configuration and aliases storage"""
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "turboalias"
        self.config_file = self.config_dir / "aliases.json"
        self.shell_file = self.config_dir / "aliases.sh"
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _create_default_config(self):
        """Create default config with example aliases from default_aliases.json"""
        default_file = Path(__file__).parent / "default_aliases.json"
        
        try:
            with open(default_file, 'r') as f:
                default_config = json.load(f)
            self.save_aliases(default_config)
        except Exception as e:
            print(f"Warning: Could not load default aliases: {e}")
            self.save_aliases({"aliases": {}, "categories": {}})

    def load_aliases(self) -> Dict:
        """Load aliases from config file"""
        if not self.config_file.exists():
            return {"aliases": {}, "categories": {}}

        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(
                f"Warning: Invalid JSON in {self.config_file}, starting fresh")
            return {"aliases": {}, "categories": {}}

    def save_aliases(self, data: Dict):
        """Save aliases to config file"""
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_alias(self, name: str, command: str, category: Optional[str] = None) -> bool:
        """Add a new alias"""
        data = self.load_aliases()

        if name in data["aliases"]:
            return False

        data["aliases"][name] = {
            "command": command,
            "category": category
        }

        # Track category
        if category:
            if category not in data["categories"]:
                data["categories"][category] = []
            if name not in data["categories"][category]:
                data["categories"][category].append(name)

        self.save_aliases(data)
        return True

    def remove_alias(self, name: str) -> bool:
        """Remove an alias"""
        data = self.load_aliases()

        if name not in data["aliases"]:
            return False

        alias_data = data["aliases"][name]
        category = alias_data.get("category")

        # Remove from aliases
        del data["aliases"][name]

        # Remove from category tracking
        if category and category in data["categories"]:
            if name in data["categories"][category]:
                data["categories"][category].remove(name)
            # Clean up empty categories
            if not data["categories"][category]:
                del data["categories"][category]

        self.save_aliases(data)
        return True

    def get_aliases(self, category: Optional[str] = None) -> Dict:
        """Get all aliases, optionally filtered by category"""
        data = self.load_aliases()

        if category:
            if category not in data["categories"]:
                return {}
            filtered = {}
            for name in data["categories"][category]:
                if name in data["aliases"]:
                    filtered[name] = data["aliases"][name]
            return filtered

        return data["aliases"]

    def get_categories(self) -> List[str]:
        """Get all categories"""
        data = self.load_aliases()
        return list(data["categories"].keys())

    def clear_aliases(self):
        """Remove all aliases"""
        self.save_aliases({"aliases": {}, "categories": {}})

    def alias_exists(self, name: str) -> bool:
        """Check if alias exists"""
        data = self.load_aliases()
        return name in data["aliases"]
