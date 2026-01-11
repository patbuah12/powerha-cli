"""
Configuration management for PowerHA CLI.

Handles:
- API endpoint configuration
- Credential storage (using system keyring)
- User preferences
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

import keyring
import yaml


APP_NAME = "powerha-cli"
CONFIG_DIR = Path.home() / ".powerha"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
KEYRING_SERVICE = "powerha-copilot"


@dataclass
class Config:
    """PowerHA CLI configuration."""

    # API Settings
    api_url: str = "https://api.powerha.ziemacs.ai"
    api_version: str = "v1"

    # Display Settings
    theme: str = "dark"  # dark, light, auto
    output_format: str = "rich"  # rich, json, plain
    language: str = "en"

    # Session Settings
    timeout: int = 30
    max_retries: int = 3

    # Feature Flags
    streaming: bool = True
    voice_enabled: bool = False

    # User info (populated after login)
    username: Optional[str] = None
    organization: Optional[str] = None

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from file."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                data = yaml.safe_load(f) or {}
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()

    def save(self) -> None:
        """Save configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(asdict(self), f, default_flow_style=False)

    @property
    def base_url(self) -> str:
        """Get full API base URL."""
        return f"{self.api_url}/{self.api_version}"

    # -------------------------------------------------------------------------
    # Credential Management (using system keyring)
    # -------------------------------------------------------------------------

    @staticmethod
    def get_api_key() -> Optional[str]:
        """Get API key from system keyring."""
        try:
            return keyring.get_password(KEYRING_SERVICE, "api_key")
        except Exception:
            return None

    @staticmethod
    def set_api_key(api_key: str) -> None:
        """Store API key in system keyring."""
        keyring.set_password(KEYRING_SERVICE, "api_key", api_key)

    @staticmethod
    def delete_api_key() -> None:
        """Remove API key from system keyring."""
        try:
            keyring.delete_password(KEYRING_SERVICE, "api_key")
        except keyring.errors.PasswordDeleteError:
            pass

    @staticmethod
    def get_refresh_token() -> Optional[str]:
        """Get refresh token from system keyring."""
        try:
            return keyring.get_password(KEYRING_SERVICE, "refresh_token")
        except Exception:
            return None

    @staticmethod
    def set_refresh_token(token: str) -> None:
        """Store refresh token in system keyring."""
        keyring.set_password(KEYRING_SERVICE, "refresh_token", token)

    @staticmethod
    def delete_refresh_token() -> None:
        """Remove refresh token from system keyring."""
        try:
            keyring.delete_password(KEYRING_SERVICE, "refresh_token")
        except keyring.errors.PasswordDeleteError:
            pass

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.get_api_key() is not None

    def clear_credentials(self) -> None:
        """Clear all stored credentials."""
        self.delete_api_key()
        self.delete_refresh_token()
        self.username = None
        self.organization = None
        self.save()


def get_config() -> Config:
    """Get or create configuration."""
    return Config.load()
