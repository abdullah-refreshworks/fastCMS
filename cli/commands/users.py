"""
User management commands
"""
import click
import asyncio
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

console = Console()


@click.group()
def users():
    """User management commands"""
    pass


@users.command("list")
@click.option("--role", type=click.Choice(["user", "admin"]), help="Filter by role")
def list_users(role: str):
    """List all users"""
    console.print("[bold cyan]Users:[/bold cyan]\n")

    async def _list():
        try:
            from app.db.session import get_db_context
            from sqlalchemy import text

            async with get_db_context() as db:
                query = "SELECT id, email, role, verified, created FROM users"
                params = {}
                if role:
                    query += " WHERE role = :role"
                    params["role"] = role

                result = await db.execute(text(query), params)
                rows = result.fetchall()

                if not rows:
                    console.print("[dim]No users found[/dim]")
                    return

                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("ID")
                table.add_column("Email")
                table.add_column("Role")
                table.add_column("Verified")
                table.add_column("Created")

                for row in rows:
                    table.add_row(
                        row[0][:8] + "...",
                        row[1],
                        row[2],
                        "✓" if row[3] else "✗",
                        str(row[4])[:10],
                    )

                console.print(table)
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")

    asyncio.run(_list())


@users.command("create")
@click.argument("email", required=False)
@click.option("--password", help="User password (will prompt if not provided)")
@click.option("--admin", is_flag=True, help="Create as admin user")
@click.option("--name", help="User's display name")
@click.option("--interactive", is_flag=True, help="Interactive mode with prompts")
def create_user(email: str, password: str, admin: bool, name: str, interactive: bool):
    """Create a new user (admin or regular user)"""

    # Interactive mode for better UX
    if interactive or not email:
        console.print("\n[bold cyan]═══════════════════════════════════════════[/bold cyan]")
        console.print("[bold cyan]      Create Your First Admin User        [/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════════════════[/bold cyan]\n")
        console.print("[dim]This admin user will have full access to manage")
        console.print("your fastCMS instance, including collections, users,")
        console.print("and system settings.[/dim]\n")

        if not email:
            email = Prompt.ask("[bold]Enter admin email[/bold]", default="admin@example.com")
        if not name:
            name = Prompt.ask("[bold]Enter display name[/bold] (optional)", default="") or None
        admin = True  # Force admin in interactive mode

    if not email:
        console.print("[red]Error:[/red] Email is required")
        return

    # Prompt for password if not provided
    if not password:
        import getpass
        console.print()
        password = getpass.getpass("Enter password: ")
        password_confirm = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            console.print("[red]Error:[/red] Passwords do not match")
            return

        if len(password) < 8:
            console.print("[yellow]Warning:[/yellow] Password should be at least 8 characters for better security")

    console.print(f"\n[bold cyan]Creating {'admin' if admin else 'user'}:[/bold cyan] {email}\n")

    async def _create():
        try:
            from app.db.session import get_db_context
            from app.db.repositories.user_repository import UserRepository
            from app.schemas.auth import UserCreate

            async with get_db_context() as db:
                # Check if user already exists
                from sqlalchemy import text
                result = await db.execute(
                    text("SELECT id FROM users WHERE email = :email"),
                    {"email": email}
                )
                if result.fetchone():
                    console.print(f"[red]✗ Error:[/red] User with email '{email}' already exists")
                    console.print("[dim]Tip: Use a different email or delete the existing user first[/dim]")
                    return

                repo = UserRepository(db)
                user = await repo.create_user(
                    UserCreate(
                        email=email,
                        password=password,
                        name=name,
                    )
                )

                # Set role if admin
                if admin:
                    user.role = "admin"
                    await db.commit()

                # Auto-verify
                user.verified = True
                await db.commit()

                console.print("[bold green]✓ Success![/bold green]\n")
                if admin:
                    console.print("[bold cyan]Admin user created successfully![/bold cyan]\n")
                else:
                    console.print("[bold cyan]User created successfully![/bold cyan]\n")

                console.print(f"[bold]Email:[/bold] {user.email}")
                if name:
                    console.print(f"[bold]Name:[/bold] {name}")
                console.print(f"[bold]Role:[/bold] {user.role.upper()}")
                console.print(f"[bold]Status:[/bold] Verified ✓\n")

                if admin:
                    console.print("[bold cyan]What's Next?[/bold cyan]")
                    console.print("  • Start the server: [bold]fastcms dev[/bold]")
                    console.print("  • Access API docs: [bold]http://localhost:8000/docs[/bold]")
                    console.print("  • Visit admin dashboard: [bold]http://localhost:8000/admin[/bold]")
                    console.print("  • Login with your credentials to get started!\n")
        except Exception as e:
            console.print(f"[red]✗ Error:[/red] {str(e)}")
            console.print("[dim]Please check your database configuration and try again[/dim]")

    asyncio.run(_create())


@users.command("delete")
@click.argument("email")
@click.confirmation_option(prompt="Are you sure you want to delete this user?")
def delete_user(email: str):
    """Delete a user"""
    console.print(f"[bold yellow]Deleting user:[/bold yellow] {email}\n")

    async def _delete():
        try:
            from app.db.session import get_db_context
            from sqlalchemy import text

            async with get_db_context() as db:
                result = await db.execute(
                    text("DELETE FROM users WHERE email = :email"),
                    {"email": email}
                )
                await db.commit()

                if result.rowcount > 0:
                    console.print(f"[green]✓[/green] User deleted successfully")
                else:
                    console.print(f"[yellow]User not found[/yellow]")
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")

    asyncio.run(_delete())
