import argparse
from optimizer import optimize_portfolio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

def main():
    parser = argparse.ArgumentParser(description="Yield Alpha Optimizer - Maximize yield within risk limits.")
    parser.add_argument(
        '--max-risk',
        type=float,
        default=0.15,
        help="Maximum risk tolerance score (e.g., 0.15 for 15%)."
    )
    parser.add_argument(
        '--portfolio-size',
        type=float,
        default=10000.0,
        help="Total portfolio size in USD. Affects gas fee viability."
    )

    args = parser.parse_args()
    console = Console()

    # Mock Data: Yield rates, risk scores, and gas fees for multi-chain protocols
    mock_yields = {
        'Aave (Ethereum)': 0.05,
        'Aave (Polygon)': 0.045,
        'Compound (Ethereum)': 0.045,
        'Curve (Arbitrum)': 0.07,
        'MakerDAO (Ethereum)': 0.03
    }

    mock_risks = {
        'Aave (Ethereum)': 0.05,
        'Aave (Polygon)': 0.10,
        'Compound (Ethereum)': 0.04,
        'Curve (Arbitrum)': 0.25,
        'MakerDAO (Ethereum)': 0.02
    }

    mock_gas_fees = {
        'Aave (Ethereum)': 35.0,
        'Aave (Polygon)': 0.05,
        'Compound (Ethereum)': 40.0,
        'Curve (Arbitrum)': 1.5,
        'MakerDAO (Ethereum)': 50.0
    }

    # Header Panel
    console.print(Panel(Text("Yield Alpha Optimizer Pro", justify="center", style="bold cyan"), border_style="cyan"))

    # Inputs Table
    info_table = Table(show_header=False, box=None)
    info_table.add_row("Target Max Risk:", f"[bold yellow]{args.max_risk}[/bold yellow]")
    info_table.add_row("Portfolio Size:", f"[bold green]${args.portfolio_size:,.2f}[/bold green]")
    console.print(info_table)
    console.print("\n[bold]Available Protocols[/bold]")

    # Protocols Table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Protocol (Chain)", style="dim")
    table.add_column("Expected APY", justify="right")
    table.add_column("Risk Score", justify="right")
    table.add_column("Est. Gas Fee", justify="right")

    for protocol in mock_yields.keys():
        table.add_row(
            protocol,
            f"{mock_yields[protocol]:.1%}",
            f"{mock_risks[protocol]:.2f}",
            f"${mock_gas_fees[protocol]:.2f}"
        )

    console.print(table)

    console.print("\n[dim]Calculating Optimal Allocation using Mixed-Integer Linear Programming...[/dim]")

    try:
        allocations = optimize_portfolio(mock_yields, mock_risks, mock_gas_fees, args.portfolio_size, args.max_risk)

        expected_yield_usd = sum(allocations[p] * mock_yields[p] * args.portfolio_size for p in allocations.keys())
        total_gas_fees = sum(mock_gas_fees[p] for p in allocations.keys() if allocations[p] > 0)
        net_yield_usd = expected_yield_usd - total_gas_fees
        net_apy = net_yield_usd / args.portfolio_size

        expected_risk = sum(allocations[p] * mock_risks[p] for p in allocations.keys())

        console.print("\n[bold green]Optimal Allocation Strategy Found![/bold green]")

        alloc_table = Table(show_header=True, header_style="bold green")
        alloc_table.add_column("Protocol")
        alloc_table.add_column("Weight", justify="right")
        alloc_table.add_column("Amount", justify="right")

        for protocol, weight in allocations.items():
            if weight > 0:
                alloc_table.add_row(
                    protocol,
                    f"{weight:.1%}",
                    f"${weight * args.portfolio_size:,.2f}"
                )
        console.print(alloc_table)

        summary = Table(title="Portfolio Summary", show_header=False, box=None)
        summary.add_row("Gross Expected Yield:", f"${expected_yield_usd:,.2f} USD")
        summary.add_row("Total Gas Fees Paid:", f"[red]-${total_gas_fees:,.2f} USD[/red]")
        summary.add_row("Net Expected Yield:", f"[bold green]${net_yield_usd:,.2f} USD[/bold green]")
        summary.add_row("Net APY:", f"[bold blue]{net_apy:.2%}[/bold blue]")
        summary.add_row("Portfolio Risk Score:", f"{expected_risk:.2f}")

        console.print(summary)

    except ValueError as e:
        console.print(f"\n[bold red]Optimization Error:[/bold red] {e}")
        console.print("[dim]Tip: Try increasing your portfolio size or adjusting your maximum risk tolerance.[/dim]")

if __name__ == "__main__":
    main()
