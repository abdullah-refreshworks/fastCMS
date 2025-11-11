"""
Collection management commands
"""
import click
import asyncio
import json
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def collections():
    """Collection management commands"""
    pass


@collections.command("list")
def list_collections():
    """List all collections"""
    console.print("[bold cyan]Collections:[/bold cyan]\n")

    async def _list():
        try:
            from app.db.session import get_db_context
            from sqlalchemy import text

            async with get_db_context() as db:
                result = await db.execute(text("SELECT name, type, system FROM collections"))
                rows = result.fetchall()

                if not rows:
                    console.print("[dim]No collections found[/dim]")
                    return

                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("Name")
                table.add_column("Type")
                table.add_column("System")

                for row in rows:
                    table.add_row(
                        row[0],
                        row[1],
                        "✓" if row[2] else "",
                    )

                console.print(table)
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")

    asyncio.run(_list())


@collections.command("show")
@click.argument("collection_name")
def show_collection(collection_name: str):
    """Show collection details"""
    console.print(f"[bold cyan]Collection:[/bold cyan] {collection_name}\n")

    async def _show():
        try:
            from app.db.session import get_db_context
            from sqlalchemy import text

            async with get_db_context() as db:
                result = await db.execute(
                    text("SELECT * FROM collections WHERE name = :name"),
                    {"name": collection_name}
                )
                row = result.fetchone()

                if not row:
                    console.print(f"[red]Collection '{collection_name}' not found[/red]")
                    return

                console.print(f"[bold]Name:[/bold] {row[1]}")
                console.print(f"[bold]Type:[/bold] {row[2]}")
                console.print(f"[bold]System:[/bold] {row[9]}")
                console.print(f"\n[bold]Schema:[/bold]")
                schema = json.loads(row[3])
                console.print_json(data=schema)
                console.print(f"\n[bold]Access Rules:[/bold]")
                console.print(f"  List: {row[5] or '[dim]null (public)[/dim]'}")
                console.print(f"  View: {row[6] or '[dim]null (public)[/dim]'}")
                console.print(f"  Create: {row[7] or '[dim]null (public)[/dim]'}")
                console.print(f"  Update: {row[8] or '[dim]null (public)[/dim]'}")
                console.print(f"  Delete: {row[10] or '[dim]null (public)[/dim]'}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")

    asyncio.run(_show())


@collections.command("create")
@click.argument("collection_name")
@click.option("--schema", type=click.Path(exists=True), help="JSON schema file")
def create_collection(collection_name: str, schema: str):
    """Create a new collection"""
    if not schema:
        console.print("[red]Error:[/red] --schema is required")
        return

    with open(schema, "r") as f:
        schema_data = json.load(f)

    console.print(f"[bold cyan]Creating collection:[/bold cyan] {collection_name}\n")

    async def _create():
        try:
            from app.db.session import get_db_context
            from app.db.repositories.collection_repository import CollectionRepository
            from app.schemas.collection import CollectionCreate

            async with get_db_context() as db:
                repo = CollectionRepository(db)
                collection = await repo.create(
                    CollectionCreate(
                        name=collection_name,
                        schema=schema_data,
                    )
                )
                await db.commit()
                console.print(f"[green]✓[/green] Collection '{collection_name}' created successfully")
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")

    asyncio.run(_create())
