"""
Development server command
"""
import click
import uvicorn
from rich.console import Console

console = Console()


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload/--no-reload", default=True, help="Enable auto-reload")
def dev(host: str, port: int, reload: bool):
    """
    Start the FastCMS development server

    Example: fastcms dev --port 8000 --reload
    """
    console.print(f"\n[bold cyan]Starting FastCMS development server...[/bold cyan]")
    console.print(f"[dim]Host: {host}[/dim]")
    console.print(f"[dim]Port: {port}[/dim]")
    console.print(f"[dim]Auto-reload: {reload}[/dim]\n")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
