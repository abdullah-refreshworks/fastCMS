"""
Database migration commands
"""
import click
import subprocess
from rich.console import Console

console = Console()


@click.group()
def migrate():
    """Database migration commands"""
    pass


@migrate.command()
def up():
    """Run all pending migrations"""
    console.print("[bold cyan]Running migrations...[/bold cyan]")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print("[green]✓[/green] Migrations completed successfully")
            if result.stdout:
                console.print(result.stdout)
        else:
            console.print("[red]Error running migrations:[/red]")
            console.print(result.stderr)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@migrate.command()
def down():
    """Rollback last migration"""
    console.print("[bold yellow]Rolling back last migration...[/bold yellow]")
    try:
        result = subprocess.run(
            ["alembic", "downgrade", "-1"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print("[green]✓[/green] Rollback completed successfully")
            if result.stdout:
                console.print(result.stdout)
        else:
            console.print("[red]Error rolling back:[/red]")
            console.print(result.stderr)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@migrate.command()
def status():
    """Show migration status"""
    console.print("[bold cyan]Migration status:[/bold cyan]\n")
    try:
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print(result.stdout)
        else:
            console.print("[red]Error:[/red]")
            console.print(result.stderr)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@migrate.command()
@click.argument("message")
def create(message: str):
    """Create a new migration"""
    console.print(f"[bold cyan]Creating migration:[/bold cyan] {message}")
    try:
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", message],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print("[green]✓[/green] Migration created successfully")
            if result.stdout:
                console.print(result.stdout)
        else:
            console.print("[red]Error creating migration:[/red]")
            console.print(result.stderr)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
