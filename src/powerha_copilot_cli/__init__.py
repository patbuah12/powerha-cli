"""
PowerHA Copilot CLI - Thin client for PowerHA Copilot API.

A lightweight CLI that connects to the PowerHA Copilot API server
for AI-powered high availability cluster management.

Installation:
    pip install git+https://github.com/patbuah12/powerha-cli.git

Usage:
    powerha-copilot login
    powerha-copilot chat
    powerha-copilot cluster list
    powerha-copilot cluster status prod-cluster-01
"""

__version__ = "1.0.0"
__author__ = "ZIEMACS AI"

from powerha_copilot_cli.client import PowerHACopilotClient
from powerha_copilot_cli.config import Config

__all__ = ["PowerHACopilotClient", "Config", "__version__"]
