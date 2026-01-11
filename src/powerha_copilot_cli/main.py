"""
PowerHA Copilot CLI - Main entry point.

A rich terminal interface for PowerHA Copilot.
"""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from powerha_copilot_cli import __version__
from powerha_copilot_cli.config import Config, get_config
from powerha_copilot_cli.client import PowerHACopilotClient, APIError


console = Console()


# =============================================================================
# CLI Group
# =============================================================================

@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version")
@click.pass_context
def main(ctx, version):
    """
    PowerHA Copilot CLI - AI-powered high availability cluster management.

    \b
    Quick start:
      powerha-copilot login           # Authenticate
      powerha-copilot chat            # Start interactive chat
      powerha-copilot cluster list    # List clusters

    \b
    For more help:
      powerha-copilot --help
      powerha-copilot <command> --help
    """
    if version:
        console.print(f"[bold blue]PowerHA Copilot CLI[/] v{__version__}")
        return

    if ctx.invoked_subcommand is None:
        # No command specified, show interactive mode
        ctx.invoke(chat)


# =============================================================================
# Authentication Commands
# =============================================================================

@main.command()
@click.option("--api-key", help="API key (or enter interactively)")
@click.option("--url", help="API server URL")
def login(api_key: Optional[str], url: Optional[str]):
    """Authenticate with PowerHA Copilot server."""
    config = get_config()

    if url:
        config.api_url = url
        config.save()

    console.print(Panel.fit(
        "[bold blue]PowerHA Copilot Login[/]",
        border_style="blue"
    ))

    if not api_key:
        console.print(f"\nServer: [cyan]{config.api_url}[/]")
        console.print("\nGet your API key from your PowerHA Copilot administrator.")
        console.print("Or generate one at: [link]https://your-server/settings/api-keys[/link]\n")

        api_key = Prompt.ask("[bold]API Key[/]", password=True)

    if not api_key:
        console.print("[red]No API key provided.[/]")
        return

    async def do_login():
        async with PowerHACopilotClient(config) as client:
            return await client.login_with_api_key(api_key)

    with console.status("[bold green]Authenticating..."):
        try:
            result = asyncio.run(do_login())
            user = result.get("user", {})
            console.print(f"\n[green]✓[/] Logged in as [bold]{user.get('username', 'user')}[/]")
            if user.get("organization"):
                console.print(f"  Organization: {user['organization']}")
        except APIError as e:
            console.print(f"\n[red]✗[/] Login failed: {e.message}")
            sys.exit(1)


@main.command()
def logout():
    """Log out and clear stored credentials."""
    config = get_config()

    if not config.is_authenticated():
        console.print("[yellow]Not logged in.[/]")
        return

    if Confirm.ask("Are you sure you want to log out?"):
        config.clear_credentials()
        console.print("[green]✓[/] Logged out successfully.")


@main.command()
def whoami():
    """Show current user information."""
    config = get_config()

    if not config.is_authenticated():
        console.print("[yellow]Not logged in. Run 'powerha login' first.[/]")
        return

    async def get_user():
        async with PowerHACopilotClient(config) as client:
            return await client.whoami()

    try:
        result = asyncio.run(get_user())
        user = result.get("user", {})

        table = Table(show_header=False, box=None)
        table.add_column("Key", style="bold")
        table.add_column("Value")

        table.add_row("Username", user.get("username", "N/A"))
        table.add_row("Email", user.get("email", "N/A"))
        table.add_row("Organization", user.get("organization", "N/A"))
        table.add_row("Role", user.get("role", "N/A"))

        console.print(Panel(table, title="[bold]Current User[/]", border_style="blue"))

    except APIError as e:
        console.print(f"[red]Error:[/] {e.message}")


# =============================================================================
# Interactive Chat
# =============================================================================

@main.command()
@click.option("--no-stream", is_flag=True, help="Disable streaming responses")
def chat(no_stream: bool):
    """Start interactive chat with PowerHA Copilot."""
    config = get_config()

    console.print(Panel.fit(
        "[bold blue]PowerHA Copilot[/]\n"
        "AI-powered IBM PowerHA cluster management\n\n"
        "[dim]Type your questions or commands. Type 'exit' to quit.[/]",
        border_style="blue"
    ))

    if not config.is_authenticated():
        console.print("\n[yellow]⚠ Not authenticated.[/] Some features may be limited.")
        console.print("  Run [bold]powerha login[/] for full access.\n")

    conversation_id = None
    use_streaming = config.streaming and not no_stream

    while True:
        try:
            # Get user input
            console.print()
            user_input = Prompt.ask("[bold green]You[/]")

            if not user_input.strip():
                continue

            if user_input.lower() in ("exit", "quit", "bye", "q"):
                console.print("\n[dim]Goodbye![/]")
                break

            # Handle local commands
            if user_input.startswith("/"):
                handle_slash_command(user_input)
                continue

            # Send to API
            async def send_message():
                nonlocal conversation_id
                async with PowerHACopilotClient(config) as client:
                    if use_streaming:
                        console.print("[bold blue]Copilot[/]: ", end="")
                        full_response = ""
                        async for chunk in client.chat_stream(user_input, conversation_id):
                            console.print(chunk, end="")
                            full_response += chunk
                        console.print()
                        return {"response": full_response}
                    else:
                        return await client.chat(user_input, conversation_id)

            try:
                if use_streaming:
                    result = asyncio.run(send_message())
                else:
                    with console.status("[bold blue]Thinking..."):
                        result = asyncio.run(send_message())

                    # Display response
                    response = result.get("response", result.get("message", ""))
                    console.print(f"[bold blue]Copilot[/]: {response}")

                # Update conversation ID for context
                if "conversation_id" in result:
                    conversation_id = result["conversation_id"]

                # Show any actions taken
                if "actions" in result:
                    for action in result["actions"]:
                        console.print(f"  [dim]→ {action}[/]")

            except APIError as e:
                console.print(f"[red]Error:[/] {e.message}")

        except KeyboardInterrupt:
            console.print("\n[dim]Use 'exit' to quit.[/]")
        except EOFError:
            break


def handle_slash_command(command: str):
    """Handle slash commands in chat."""
    parts = command.split()
    cmd = parts[0].lower()

    if cmd == "/help":
        console.print(Panel(
            "[bold]Available Commands:[/]\n\n"
            "/help     - Show this help\n"
            "/clear    - Clear screen\n"
            "/clusters - List clusters\n"
            "/status   - Show connection status\n"
            "/exit     - Exit chat",
            title="Help",
            border_style="blue"
        ))
    elif cmd == "/clear":
        console.clear()
    elif cmd == "/clusters":
        asyncio.run(show_clusters())
    elif cmd == "/status":
        show_status()
    elif cmd in ("/exit", "/quit"):
        raise EOFError()
    else:
        console.print(f"[yellow]Unknown command: {cmd}[/]")


async def show_clusters():
    """Show cluster list in chat."""
    config = get_config()
    try:
        async with PowerHACopilotClient(config) as client:
            clusters = await client.list_clusters()
            if clusters:
                table = Table(title="Clusters")
                table.add_column("ID")
                table.add_column("Name")
                table.add_column("Status")
                for c in clusters:
                    table.add_row(c["id"], c["name"], c["status"])
                console.print(table)
            else:
                console.print("[yellow]No clusters found.[/]")
    except APIError as e:
        console.print(f"[red]Error:[/] {e.message}")


def show_status():
    """Show connection status."""
    config = get_config()
    console.print(f"Server: [cyan]{config.api_url}[/]")
    console.print(f"Authenticated: {'[green]Yes[/]' if config.is_authenticated() else '[red]No[/]'}")
    if config.username:
        console.print(f"User: {config.username}")


# =============================================================================
# Cluster Commands
# =============================================================================

@main.group()
def cluster():
    """Cluster management commands."""
    pass


@cluster.command("list")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def cluster_list(fmt: str):
    """List all PowerHA clusters."""
    config = get_config()

    async def get_clusters():
        async with PowerHACopilotClient(config) as client:
            return await client.list_clusters()

    with console.status("[bold green]Loading clusters..."):
        try:
            clusters = asyncio.run(get_clusters())
        except APIError as e:
            console.print(f"[red]Error:[/] {e.message}")
            return

    if fmt == "json":
        import json
        console.print_json(json.dumps(clusters, indent=2))
        return

    if not clusters:
        console.print("[yellow]No clusters found.[/]")
        return

    table = Table(title="PowerHA Clusters")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Status")
    table.add_column("Nodes")
    table.add_column("Resource Groups")

    for cluster in clusters:
        status = cluster.get("status", "unknown")
        status_style = "green" if status == "online" else "red" if status == "offline" else "yellow"

        table.add_row(
            cluster.get("id", ""),
            cluster.get("name", ""),
            f"[{status_style}]{status}[/]",
            str(cluster.get("node_count", 0)),
            str(cluster.get("resource_groups", 0)),
        )

    console.print(table)


@cluster.command("status")
@click.argument("cluster_id")
def cluster_status(cluster_id: str):
    """Get detailed status of a cluster."""
    config = get_config()

    async def get_status():
        async with PowerHACopilotClient(config) as client:
            return await client.get_cluster_status(cluster_id)

    with console.status(f"[bold green]Getting status for {cluster_id}..."):
        try:
            status = asyncio.run(get_status())
        except APIError as e:
            console.print(f"[red]Error:[/] {e.message}")
            return

    # Display cluster info
    console.print(Panel(
        f"[bold]{status.get('name', cluster_id)}[/]\n"
        f"Status: {status.get('status', 'unknown')}",
        title=f"Cluster: {cluster_id}",
        border_style="blue"
    ))

    # Display nodes
    nodes = status.get("nodes", [])
    if nodes:
        node_table = Table(title="Nodes")
        node_table.add_column("Name")
        node_table.add_column("Hostname")
        node_table.add_column("Status")
        node_table.add_column("Primary")
        node_table.add_column("CPU %")
        node_table.add_column("Memory %")

        for node in nodes:
            node_status = node.get("status", "unknown")
            status_style = "green" if node_status == "active" else "yellow" if node_status == "standby" else "red"

            node_table.add_row(
                node.get("name", ""),
                node.get("hostname", ""),
                f"[{status_style}]{node_status}[/]",
                "✓" if node.get("is_primary") else "",
                f"{node.get('cpu_usage', 0):.1f}",
                f"{node.get('memory_usage', 0):.1f}",
            )

        console.print(node_table)

    # Display resource groups
    rgs = status.get("resource_groups", [])
    if rgs:
        console.print(f"\n[bold]Resource Groups:[/] {', '.join(rgs)}")


@cluster.command("health")
@click.argument("cluster_id")
def cluster_health(cluster_id: str):
    """Check health of a cluster."""
    config = get_config()

    async def get_health():
        async with PowerHACopilotClient(config) as client:
            return await client.get_cluster_health(cluster_id)

    with console.status(f"[bold green]Checking health of {cluster_id}..."):
        try:
            health = asyncio.run(get_health())
        except APIError as e:
            console.print(f"[red]Error:[/] {e.message}")
            return

    # Health score
    score = health.get("health_score", 0)
    score_color = "green" if score >= 80 else "yellow" if score >= 50 else "red"

    console.print(Panel(
        f"[bold]Health Score: [{score_color}]{score}/100[/][/]\n"
        f"Status: {health.get('health_status', 'unknown')}",
        title=f"Health: {cluster_id}",
        border_style=score_color
    ))

    # Issues
    issues = health.get("issues", [])
    if issues:
        console.print("\n[bold red]Issues:[/]")
        for issue in issues:
            console.print(f"  • {issue}")

    # Recommendations
    recommendations = health.get("recommendations", [])
    if recommendations:
        console.print("\n[bold yellow]Recommendations:[/]")
        for rec in recommendations:
            console.print(f"  → {rec}")


# =============================================================================
# Configuration Commands
# =============================================================================

@main.command()
@click.option("--url", help="Set API server URL")
@click.option("--theme", type=click.Choice(["dark", "light"]), help="Set theme")
@click.option("--show", is_flag=True, help="Show current configuration")
def config(url: Optional[str], theme: Optional[str], show: bool):
    """Manage CLI configuration."""
    cfg = get_config()

    if show or (not url and not theme):
        table = Table(title="Configuration", show_header=False)
        table.add_column("Setting", style="bold")
        table.add_column("Value")

        table.add_row("API URL", cfg.api_url)
        table.add_row("Theme", cfg.theme)
        table.add_row("Output Format", cfg.output_format)
        table.add_row("Streaming", "Enabled" if cfg.streaming else "Disabled")
        table.add_row("Timeout", f"{cfg.timeout}s")
        table.add_row("Authenticated", "Yes" if cfg.is_authenticated() else "No")

        console.print(table)
        console.print(f"\n[dim]Config file: {cfg.CONFIG_FILE}[/]")
        return

    if url:
        cfg.api_url = url
        console.print(f"[green]✓[/] API URL set to: {url}")

    if theme:
        cfg.theme = theme
        console.print(f"[green]✓[/] Theme set to: {theme}")

    cfg.save()


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    main()
