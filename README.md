# PowerHA Copilot CLI

A command-line interface for PowerHA Copilot - AI-powered high availability cluster management.

## Installation

### Install from GitHub (Recommended)

```bash
# Install directly from GitHub
pip install git+https://github.com/patbuah12/powerha-cli.git

# Or install a specific version/tag
pip install git+https://github.com/patbuah12/powerha-cli.git@v1.0.0

# Or install from a specific branch
pip install git+https://github.com/patbuah12/powerha-cli.git@main
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/patbuah12/powerha-cli.git
cd powerha-cli

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Install from PyPI (Coming Soon)

```bash
pip install powerha-copilot-cli
```

## Quick Start

```bash
# Configure your server
powerha-copilot config --url https://copilot.yourcompany.com/api

# Login with your API key
powerha-copilot login

# Start chatting
powerha-copilot chat
```

## Command Aliases

The CLI provides multiple command aliases for convenience:

| Command | Alias | Short Alias |
|---------|-------|-------------|
| `powerha-copilot` | `pha-copilot` | `phac` |

## Usage

### Interactive Chat

```bash
# Start interactive chat mode
powerha-copilot chat

# Or use the short alias
phac chat
```

```
╭─────────────────────────────────────────╮
│        PowerHA Copilot                  │
│  AI-powered cluster management          │
╰─────────────────────────────────────────╯

You: Check health of all clusters

Copilot: I'll check the health of your clusters...

  Production Cluster (prod-cluster-01):
    Health Score: 95/100 ✓
    Status: Online
    Nodes: 2 active

  Development Cluster (dev-cluster-01):
    Health Score: 100/100 ✓
    Status: Online
    Nodes: 1 active

All clusters are healthy.

You: _
```

### Cluster Commands

```bash
# List all clusters
powerha-copilot cluster list

# Get cluster status
powerha-copilot cluster status prod-cluster-01

# Check cluster health
powerha-copilot cluster health prod-cluster-01
```

### Authentication

```bash
# Login with API key
powerha-copilot login

# Login with specific server
powerha-copilot login --url https://copilot.example.com/api

# Check current user
powerha-copilot whoami

# Logout
powerha-copilot logout
```

### Configuration

```bash
# Show current configuration
powerha-copilot config --show

# Set API server URL
powerha-copilot config --url https://copilot.yourcompany.com/api

# Set theme
powerha-copilot config --theme dark
```

## Chat Commands

While in chat mode, you can use these slash commands:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clusters` | List clusters |
| `/status` | Show connection status |
| `/clear` | Clear screen |
| `/exit` | Exit chat |

## Example Queries

```
Check the health of prod-cluster-01
What's the status of all my clusters?
Show me the nodes in the production cluster
Perform a failover on prod-cluster-01 to node2
What resource groups are running on node1?
Show recent operations history
```

## Configuration File

Configuration is stored in `~/.powerha-copilot/config.yaml`:

```yaml
api_url: https://copilot.yourcompany.com/api
api_version: v1
theme: dark
output_format: rich
streaming: true
timeout: 30
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `POWERHA_COPILOT_API_URL` | Override API server URL |
| `POWERHA_COPILOT_API_KEY` | API key (alternative to login) |

## Requirements

- Python 3.10+
- Access to a PowerHA Copilot server

## Getting Access

Contact your PowerHA Copilot administrator for:
1. Server URL
2. API key or login credentials

## License

MIT License

## Links

- [Documentation](https://github.com/patbuah12/powerha-cli#readme)
- [PowerHA Copilot](https://github.com/patbuah12/powerha-copilot) (Private)
- [Report Issues](https://github.com/patbuah12/powerha-cli/issues)
