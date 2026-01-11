# PowerHA CLI

A command-line interface for PowerHA Copilot - AI-powered IBM PowerHA cluster management.

## Installation

```bash
pip install powerha-cli
```

## Quick Start

```bash
# Configure your server
powerha config --url https://powerha.yourcompany.com/api

# Login with your API key
powerha login

# Start chatting
powerha chat
```

## Usage

### Interactive Chat

```bash
# Start interactive chat mode
powerha chat

# Or just run powerha
powerha
```

```
╭─────────────────────────────────────────╮
│        PowerHA Copilot                  │
│  AI-powered IBM PowerHA management      │
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
powerha cluster list

# Get cluster status
powerha cluster status prod-cluster-01

# Check cluster health
powerha cluster health prod-cluster-01
```

### Authentication

```bash
# Login with API key
powerha login

# Login with specific server
powerha login --url https://powerha.example.com/api

# Check current user
powerha whoami

# Logout
powerha logout
```

### Configuration

```bash
# Show current configuration
powerha config --show

# Set API server URL
powerha config --url https://powerha.yourcompany.com/api

# Set theme
powerha config --theme dark
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

Configuration is stored in `~/.powerha/config.yaml`:

```yaml
api_url: https://powerha.yourcompany.com/api
api_version: v1
theme: dark
output_format: rich
streaming: true
timeout: 30
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `POWERHA_API_URL` | Override API server URL |
| `POWERHA_API_KEY` | API key (alternative to login) |

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
