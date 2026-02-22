"""MiViA CLI application."""

import os
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from mivia.exceptions import MiviaError
from mivia.models import JobStatus
from mivia.sync_client import SyncMiviaClient

app = typer.Typer(
    name="mivia",
    help="MiViA (Microstructure Analysis) API client CLI",
    no_args_is_help=True,
)
jobs_app = typer.Typer(help="Job management commands")
report_app = typer.Typer(help="Report generation commands")

app.add_typer(jobs_app, name="jobs")
app.add_typer(report_app, name="report")

console = Console()


class CLIState:
    """Global CLI state."""

    proxy: str | None = None


cli_state = CLIState()


@app.callback()
def main_callback(
    proxy: Annotated[
        str | None,
        typer.Option(
            "--proxy",
            help="Proxy URL (e.g., http://proxy:8080)",
            envvar="MIVIA_PROXY",
        ),
    ] = None,
) -> None:
    """MiViA API client CLI."""
    cli_state.proxy = proxy


def get_client() -> SyncMiviaClient:
    """Get configured client."""
    return SyncMiviaClient(proxy=cli_state.proxy)


def handle_error(e: MiviaError) -> None:
    """Handle and display error."""
    rprint(f"[red]Error:[/red] {e.message}")
    raise typer.Exit(1)


# --- Models ---


@app.command()
def models() -> None:
    """List available models."""
    try:
        client = get_client()
        result = client.list_models()

        table = Table(title="Available Models")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("Display Name")
        table.add_column("Access")

        for m in result:
            table.add_row(
                str(m.id),
                m.name,
                m.display_name,
                m.access_type.value,
            )

        console.print(table)
    except MiviaError as e:
        handle_error(e)


# --- Customizations ---


@app.command()
def customizations(
    model_id: Annotated[str, typer.Argument(help="Model UUID")],
) -> None:
    """List customizations for a model."""
    try:
        client = get_client()
        result = client.get_model_customizations(UUID(model_id))

        if not result:
            rprint(f"[yellow]No customizations available for model {model_id}[/yellow]")
            return

        table = Table(title="Available Customizations")
        table.add_column("ID", style="dim")
        table.add_column("Name (EN)")
        table.add_column("Name (DE)")

        for c in result:
            table.add_row(
                str(c.id),
                c.name.en,
                c.name.de,
            )

        console.print(table)
    except MiviaError as e:
        handle_error(e)


# --- Upload ---


@app.command()
def upload(
    files: Annotated[list[Path], typer.Argument(help="Image files to upload")],
    forced: Annotated[
        bool, typer.Option("--forced", "-f", help="Bypass quality check")
    ] = False,
) -> None:
    """Upload image(s)."""
    try:
        client = get_client()
        forced_list = [forced] * len(files) if forced else None
        result = client.upload_images(files, forced_list)

        table = Table(title="Uploaded Images")
        table.add_column("ID", style="dim")
        table.add_column("Filename")
        table.add_column("Size")
        table.add_column("Validated")

        for img in result:
            size = f"{img.width}x{img.height}" if img.width else "-"
            table.add_row(
                str(img.id),
                img.original_filename,
                size,
                "Yes" if img.validated else "No",
            )

        console.print(table)
    except MiviaError as e:
        handle_error(e)


# --- Images ---


@app.command()
def images() -> None:
    """List uploaded images."""
    try:
        client = get_client()
        result = client.list_images()

        table = Table(title="Your Images")
        table.add_column("ID", style="dim")
        table.add_column("Filename")
        table.add_column("Created")
        table.add_column("Validated")

        for img in result:
            table.add_row(
                str(img.id),
                img.original_filename,
                img.created_at.strftime("%Y-%m-%d %H:%M"),
                "Yes" if img.validated else "No",
            )

        console.print(table)
    except MiviaError as e:
        handle_error(e)


# --- Analyze ---


def resolve_model(
    client: SyncMiviaClient,
    model: str,
) -> UUID:
    """Resolve model by UUID or name."""
    # Try UUID first
    try:
        return UUID(model)
    except ValueError:
        pass

    # Search by name
    models = client.list_models()
    model_lower = model.lower()
    for m in models:
        if model_lower in (m.name.lower(), m.display_name.lower()):
            return m.id

    # Partial match
    for m in models:
        if model_lower in m.name.lower() or model_lower in m.display_name.lower():
            return m.id

    rprint(f"[red]Error:[/red] Model '{model}' not found")
    if models:
        rprint("[yellow]Available models:[/yellow]")
        for m in models:
            rprint(f"  - {m.display_name} ({m.id})")
    raise typer.Exit(1)


def resolve_customization(
    client: SyncMiviaClient,
    model_id: UUID,
    customization: str | None,
) -> UUID | None:
    """Resolve customization by UUID or name."""
    if not customization:
        return None

    # Try UUID first
    try:
        return UUID(customization)
    except ValueError:
        pass

    # Search by name
    customs = client.get_model_customizations(model_id)
    for c in customs:
        if customization.lower() in (c.name.en.lower(), c.name.de.lower()):
            return c.id

    # Partial match
    cust_lower = customization.lower()
    for c in customs:
        if cust_lower in c.name.en.lower() or cust_lower in c.name.de.lower():
            return c.id

    rprint(f"[red]Error:[/red] Customization '{customization}' not found")
    if customs:
        rprint("[yellow]Available customizations:[/yellow]")
        for c in customs:
            rprint(f"  - {c.name.en} ({c.id})")
    raise typer.Exit(1)


@app.command()
def analyze(
    files: Annotated[list[Path], typer.Argument(help="Image files to analyze")],
    model: Annotated[
        str | None, typer.Option("--model", "-m", help="Model UUID or name")
    ] = None,
    customization: Annotated[
        str | None, typer.Option("--customization", "-c", help="Customization UUID")
    ] = None,
    list_customizations: Annotated[
        bool, typer.Option("--list-customizations", "-l", help="List customizations")
    ] = False,
    no_wait: Annotated[
        bool, typer.Option("--no-wait", help="Don't wait for completion")
    ] = False,
    timeout: Annotated[
        float, typer.Option("--timeout", "-t", help="Wait timeout in seconds")
    ] = 300.0,
) -> None:
    """Upload images and run analysis."""
    if not model:
        rprint("[red]Error:[/red] --model is required")
        raise typer.Exit(1)

    try:
        client = get_client()
        model_id = resolve_model(client, model)

        # List customizations if requested
        if list_customizations:
            customs = client.get_model_customizations(model_id)
            if not customs:
                rprint("[yellow]No customizations available for this model[/yellow]")
            else:
                rprint("[bold]Available customizations:[/bold]")
                for c in customs:
                    rprint(f"  - [cyan]{c.name.en}[/cyan] ({c.id})")
            return

        customization_id = resolve_customization(client, model_id, customization)

        rprint(f"[blue]Uploading {len(files)} file(s)...[/blue]")

        result = client.analyze(
            file_paths=files,
            model_id=model_id,
            customization_id=customization_id,
            wait=not no_wait,
            timeout=timeout,
        )

        table = Table(title="Analysis Results")
        table.add_column("Job ID", style="dim")
        table.add_column("Image")
        table.add_column("Status")
        table.add_column("Has Results")

        for job in result:
            status_color = {
                "CACHED": "green",
                "NEW": "green",
                "PENDING": "yellow",
                "FAILED": "red",
            }.get(job.status.value, "white")

            table.add_row(
                str(job.id),
                job.image,
                f"[{status_color}]{job.status.value}[/{status_color}]",
                "Yes" if job.has_results else "No",
            )

        console.print(table)
    except MiviaError as e:
        handle_error(e)


# --- Jobs Subcommands ---


def parse_status_filter(status_str: str | None) -> list[JobStatus] | None:
    """Parse comma-separated status filter string."""
    if not status_str:
        return None
    statuses = []
    for s in status_str.split(","):
        s = s.strip().upper()
        try:
            statuses.append(JobStatus(s))
        except ValueError:
            rprint(f"[red]Error:[/red] Invalid status '{s}'")
            valid = ", ".join(js.value for js in JobStatus)
            rprint(f"[yellow]Valid statuses:[/yellow] {valid}")
            raise typer.Exit(1)
    return statuses


@jobs_app.command("list")
def jobs_list(
    model: Annotated[
        str | None, typer.Option("--model", "-m", help="Filter by model UUID or name")
    ] = None,
    status: Annotated[
        str | None,
        typer.Option(
            "--status",
            help="Filter by status (comma-separated: CACHED,NEW,FAILED,PENDING)",
        ),
    ] = None,
    all_pages: Annotated[
        bool, typer.Option("--all", "-a", help="Fetch all pages")
    ] = False,
    page: Annotated[int, typer.Option("--page", "-p", help="Page number")] = 1,
    size: Annotated[int, typer.Option("--size", help="Page size")] = 10,
) -> None:
    """List jobs."""
    try:
        client = get_client()

        # Resolve model by UUID or name
        model_id = None
        if model:
            model_id = resolve_model(client, model)

        # Parse status filter
        status_filter = parse_status_filter(status)

        if all_pages:
            # Fetch all jobs with automatic pagination
            jobs = client.list_all_jobs(
                model_id=model_id,
                status=status_filter,
                page_size=100,
            )
            table = Table(title=f"Jobs (Total: {len(jobs)})")
        else:
            # Single page
            result = client.list_jobs(model_id=model_id, page=page, page_size=size)
            jobs = result.data
            if status_filter:
                jobs = [j for j in jobs if j.status in status_filter]
            pg = result.pagination
            table = Table(title=f"Jobs (Page {pg.page}/{pg.total_pages})")

        table.add_column("ID", style="dim")
        table.add_column("Image")
        table.add_column("Status")
        table.add_column("Created")
        table.add_column("Started")
        table.add_column("Finished")
        table.add_column("Duration")

        for job in jobs:
            status_color = {
                "CACHED": "green",
                "NEW": "green",
                "PENDING": "yellow",
                "FAILED": "red",
            }.get(job.status.value, "white")

            # Calculate duration if both times available
            duration = "-"
            if job.started_at and job.finished_at:
                delta = job.finished_at - job.started_at
                duration = f"{delta.total_seconds():.1f}s"

            table.add_row(
                str(job.id),
                job.image or "-",
                f"[{status_color}]{job.status.value}[/{status_color}]",
                job.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                job.started_at.strftime("%H:%M:%S") if job.started_at else "-",
                job.finished_at.strftime("%H:%M:%S") if job.finished_at else "-",
                duration,
            )

        console.print(table)
        if not all_pages:
            rprint(f"Total: {result.pagination.total} jobs")
    except MiviaError as e:
        handle_error(e)


@jobs_app.command("recent-ids")
def jobs_recent_ids(
    since: Annotated[
        str, typer.Option("--since", "-s", help="Duration (e.g. 1h, 30m, 2d)")
    ] = "1h",
    model: Annotated[
        str | None, typer.Option("--model", "-m", help="Filter by model UUID or name")
    ] = None,
) -> None:
    """Get IDs of recently created jobs (one per line, pipeable)."""
    try:
        client = get_client()

        model_id = None
        if model:
            model_id = resolve_model(client, model)

        ids = client.get_recent_job_ids(since=since, model_id=model_id)
        for job_id in ids:
            typer.echo(str(job_id))
    except MiviaError as e:
        handle_error(e)


@jobs_app.command("get")
def jobs_get(
    job_id: Annotated[str, typer.Argument(help="Job UUID")],
) -> None:
    """Get job details."""
    try:
        client = get_client()
        job = client.get_job(UUID(job_id))

        rprint(f"[bold]Job ID:[/bold] {job.id}")
        rprint(f"[bold]Image:[/bold] {job.image}")
        rprint(f"[bold]Model ID:[/bold] {job.model_id}")
        rprint(f"[bold]Status:[/bold] {job.status.value}")
        rprint(f"[bold]Has Results:[/bold] {job.has_results}")
        rprint(f"[bold]Created:[/bold] {job.created_at}")

        if job.results:
            rprint("\n[bold]Results:[/bold]")
            for i, r in enumerate(job.results):
                rprint(f"  {i + 1}. {r}")
    except MiviaError as e:
        handle_error(e)


@jobs_app.command("wait")
def jobs_wait(
    job_ids: Annotated[list[str], typer.Argument(help="Job UUIDs")],
    timeout: Annotated[
        float, typer.Option("--timeout", "-t", help="Timeout in seconds")
    ] = 300.0,
    interval: Annotated[
        float, typer.Option("--interval", "-i", help="Poll interval")
    ] = 2.0,
) -> None:
    """Wait for job(s) to complete."""
    try:
        client = get_client()
        uuids = [UUID(jid) for jid in job_ids]

        rprint(f"[blue]Waiting for {len(uuids)} job(s)...[/blue]")

        result = client.wait_for_jobs(uuids, timeout=timeout, poll_interval=interval)

        for job in result:
            status_color = "green" if job.status.value in ("CACHED", "NEW") else "red"
            rprint(f"Job {job.id}: [{status_color}]{job.status.value}[/{status_color}]")
    except MiviaError as e:
        handle_error(e)


# --- Report Subcommands ---


@report_app.command("pdf")
def report_pdf(
    job_ids: Annotated[list[str], typer.Argument(help="Job UUIDs")],
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Output file path")
    ] = Path("report.pdf"),
) -> None:
    """Download PDF report."""
    try:
        client = get_client()
        uuids = [UUID(jid) for jid in job_ids]

        rprint("[blue]Generating PDF report...[/blue]")
        path = client.download_pdf(uuids, output)
        rprint(f"[green]Saved to:[/green] {path}")
    except MiviaError as e:
        handle_error(e)


@report_app.command("csv")
def report_csv(
    job_ids: Annotated[list[str], typer.Argument(help="Job UUIDs")],
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Output file path")
    ] = Path("report.zip"),
    no_images: Annotated[
        bool, typer.Option("--no-images", help="Exclude images")
    ] = False,
) -> None:
    """Download CSV report (as ZIP)."""
    try:
        client = get_client()
        uuids = [UUID(jid) for jid in job_ids]

        rprint("[blue]Generating CSV report...[/blue]")
        path = client.download_csv(uuids, output, include_images=not no_images)
        rprint(f"[green]Saved to:[/green] {path}")
    except MiviaError as e:
        handle_error(e)


# --- Config ---


@app.command()
def config() -> None:
    """Show current configuration."""
    api_key = os.environ.get("MIVIA_API_KEY", "")
    base_url = os.environ.get("MIVIA_BASE_URL", "https://app.mivia.ai/api")
    proxy = cli_state.proxy or os.environ.get("MIVIA_PROXY", "")

    rprint("[bold]Configuration:[/bold]")
    key_display = "***" + api_key[-4:] if api_key else "[red]Not set[/red]"
    rprint(f"  MIVIA_API_KEY: {key_display}")
    rprint(f"  MIVIA_BASE_URL: {base_url}")
    rprint(f"  MIVIA_PROXY: {proxy if proxy else '[dim]Not set[/dim]'}")


if __name__ == "__main__":
    app()
