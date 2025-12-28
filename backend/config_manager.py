"""
Configuration Manager
Handles loading and saving configuration files
"""

import os
import secrets
from pathlib import Path
from typing import Dict, Any

import yaml


class ConfigManager:
    """Manages application configuration"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config_dir = self.config_path.parent
        self.api_key_file = self.config_dir / ".api_key"

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Load API key from file if exists
        if self.api_key_file.exists():
            with open(self.api_key_file, 'r') as f:
                api_key = f.read().strip()
                config['server']['api_key'] = api_key

        # Create logs directory if needed
        log_file = Path(config['logging']['file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)

        return config

    def save_config(self, config: Dict[str, Any]):
        """Save configuration to YAML file"""
        # Don't save API key in main config
        config_copy = config.copy()
        api_key = config_copy['server']['api_key']
        config_copy['server']['api_key'] = ""

        with open(self.config_path, 'w') as f:
            yaml.dump(config_copy, f, default_flow_style=False)

        # Save API key separately
        if api_key:
            self.save_api_key(api_key)

    def save_api_key(self, api_key: str):
        """Save API key to separate file"""
        with open(self.api_key_file, 'w') as f:
            f.write(api_key)

        # Set file permissions (read/write for owner only)
        os.chmod(self.api_key_file, 0o600)

    def get_api_key(self) -> str:
        """Get API key from file or generate new one"""
        if self.api_key_file.exists():
            with open(self.api_key_file, 'r') as f:
                return f.read().strip()

        # Generate new API key
        api_key = secrets.token_urlsafe(32)
        self.save_api_key(api_key)
        return api_key
