"""
PowerHA CLI - Thin client for PowerHA Copilot API.

A lightweight CLI that connects to the PowerHA Copilot API server
for AI-powered IBM PowerHA cluster management.

Installation:
    pip install powerha-cli

Usage:
    powerha login
    powerha chat
    powerha cluster list
    powerha cluster status prod-cluster-01
"""

__version__ = "1.0.0"
__author__ = "ZIEMACS AI"

from powerha_cli.client import PowerHAClient
from powerha_cli.config import Config

__all__ = ["PowerHAClient", "Config", "__version__"]
