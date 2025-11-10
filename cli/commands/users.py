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
@click.argument("email")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option("--admin", is_flag=True, help="Create as admin user")
@click.option("--name", help="User's display name")
def create_user(email: str, password: str, admin: bool, name: str):
    """Create a new user"""
    console.print(f"[bold cyan]Creating user:[/bold cyan] {email}\n")

    async def _create():
        try:
            from app.db.session import get_db_context
            from app.db.repositories.user_repository import UserRepository
            from app.schemas.auth import UserCreate

            async with get_db_context() as db:
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

                console.print(f"[green]✓[/green] User created successfully")
                console.print(f"[dim]ID: {user.id}[/dim]")
                console.print(f"[dim]Email: {user.email}[/dim]")
                console.print(f"[dim]Role: {user.role}[/dim]")
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")

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
