"""
PyCloudSim Logger Utility.

Provides a Rich-powered console logger with colored output, progress bars,
panels, and formatted metric tables for terminal display.
"""

from __future__ import annotations
from typing import List, TYPE_CHECKING

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich import box

if TYPE_CHECKING:
    from cloudsim.metrics.metrics import SimulationMetrics
    from cloudsim.cloudlets.cloudlet import Cloudlet

console = Console()


def info(message: str) -> None:
    """Print a blue informational message."""
    console.print(f"[blue]ℹ  {message}[/blue]")


def success(message: str) -> None:
    """Print a green success message."""
    console.print(f"[green]✔  {message}[/green]")


def warning(message: str) -> None:
    """Print a yellow warning message."""
    console.print(f"[yellow]⚠  {message}[/yellow]")


def error(message: str) -> None:
    """Print a red error message."""
    console.print(f"[red]✖  {message}[/red]")


def metric(message: str) -> None:
    """Print a cyan metric message."""
    console.print(f"[cyan]📊 {message}[/cyan]")


def print_banner(title: str = "PyCloudSim") -> None:
    """Display a styled banner panel."""
    console.print(
        Panel.fit(
            f"[bold cyan]{title}[/bold cyan]\n"
            "[dim]Python-native Cloud Computing Simulation Framework[/dim]",
            border_style="cyan",
        )
    )


def print_metrics_table(metrics: "SimulationMetrics") -> None:
    """
    Render a Rich table summarising all simulation metrics.

    Args:
        metrics: The SimulationMetrics instance to display.
    """
    table = Table(
        title="[bold cyan]Simulation Metrics Summary[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("Metric", style="bold white", min_width=28)
    table.add_column("Value", style="cyan", justify="right")

    rows = [
        ("Makespan (s)", f"{metrics.makespan:.4f}"),
        ("Throughput (cloudlets/s)", f"{metrics.throughput:.4f}"),
        ("Total Cloudlets", str(metrics.total_cloudlets)),
        ("Completed Cloudlets", f"[green]{metrics.completed_cloudlets}[/green]"),
        ("Avg Execution Time (s)", f"{metrics.avg_execution_time:.4f}"),
        ("Avg Waiting Time (s)", f"{metrics.avg_waiting_time:.4f}"),
        ("Avg Response Time (s)", f"{metrics.avg_response_time:.4f}"),
        ("Avg CPU Utilization", f"{metrics.avg_cpu_utilization * 100:.2f}%"),
        ("Total Energy (Wh)", f"{metrics.total_energy_wh:.4f}"),
        ("Total Cost ($)", f"{metrics.total_cost:.4f}"),
        ("SLA Violations", f"[red]{metrics.sla_violations}[/red]" if metrics.sla_violations else "[green]0[/green]"),
        ("Load Balance Index", f"{metrics.load_balance_index:.4f}"),
    ]

    for name, value in rows:
        table.add_row(name, value)

    console.print(table)


def print_cloudlet_table(cloudlets: List["Cloudlet"], max_rows: int = 25) -> None:
    """
    Render a Rich table of per-cloudlet results.

    Args:
        cloudlets: Cloudlets to display.
        max_rows:  Maximum number of rows to show.
    """
    from cloudsim.core.constants import CloudletState

    table = Table(
        title="[bold cyan]Cloudlet Execution Results[/bold cyan]",
        box=box.SIMPLE_HEAVY,
        border_style="dim",
        header_style="bold blue",
        show_lines=False,
    )
    for col in ["ID", "VM", "State", "Length (MI)", "Start (s)", "Finish (s)", "Exec (s)", "Wait (s)"]:
        table.add_column(col, justify="right" if col not in ("State",) else "center")

    shown = cloudlets[:max_rows]
    for cl in shown:
        state_str = (
            f"[green]{cl.state}[/green]"
            if cl.state == CloudletState.SUCCESS
            else f"[red]{cl.state}[/red]"
        )
        table.add_row(
            str(cl.cloudlet_id),
            str(cl.assigned_vm_id),
            state_str,
            f"{cl.length:,.0f}",
            f"{cl.start_time:.3f}",
            f"{cl.finish_time:.3f}",
            f"{cl.execution_time:.3f}",
            f"{cl.waiting_time:.3f}",
        )

    if len(cloudlets) > max_rows:
        table.add_row(
            f"[dim]... and {len(cloudlets) - max_rows} more[/dim]",
            "", "", "", "", "", "", "",
        )

    console.print(table)


def make_progress() -> Progress:
    """
    Create and return a Rich Progress bar for tracking simulation steps.

    Returns:
        A configured Progress instance (use as a context manager).
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )
